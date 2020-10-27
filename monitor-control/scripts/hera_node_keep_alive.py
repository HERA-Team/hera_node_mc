#! /usr/bin/env python
"""
Pokes Arduinos to ensure Arduino's connectivity to the server.
It pokes either specified nodes with the -n argument or
the nodes that have Redis status keys i.e. status:node:x where x is the node ID
set by the I2C digital I/O cards plugged into PCBs.
"""
from __future__ import print_function
import time
import redis
from nodeControl import nodeControl, __package__, __version__
import os
import sys
import argparse
import datetime
import socket


hostname = socket.gethostname()
script_redis_key = "status:script:{}:{}".format(hostname, __file__)

parser = argparse.ArgumentParser(description='Send keepalive pokes to all nodes with '
                                 'a status entry in redis',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--poke_time_sec', type=float, help="Time to wait between pokes", default=1.0)
parser.add_argument('--heartbeat', type=int, help="Time to keep alive flag", default=60)
parser.add_argument('-r', '--redishost', type=str, default='redishost',
                    help='IP or hostname string of host running the monitor redis server.')
args = parser.parse_args()

r = redis.StrictRedis(host=args.redishost)

# Define a dict of udpSender objects to send commands to Arduinos.
# If nodes to check and throttle are specified, use those values.
# If not, poke all the nodes that have Redis status:node:x keys.
nodes = nodeControl.refresh_node_list({}, r)
print("Using nodes {}:".format(list(nodes.keys())), file=sys.stderr)

# Sends poke signal to Arduinos inside the nodes
try:
    while True:
        r.set(script_redis_key, "alive", ex=args.heartbeat)
        start_poke_time = time.time()
        nodes = nodeControl.refresh_node_list(nodes, r)
        r.hmset("version:{}:{}".format(__package__, os.path.basename(__file__)), {
            "version": __version__, "timestamp": datetime.datetime.now().isoformat(),
        })
        for node_id, node in nodes.items():
            # print("Poking node %d"%node)
            node.poke()
            r.hset('throttle:node:{}'.format(node_id), 'last_poke_sec', time.time())
        end_poke_time = time.time()
        time_to_poke = end_poke_time - start_poke_time
        if time_to_poke < args.poke_time_sec:
            time.sleep(args.poke_time_sec - time_to_poke)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
