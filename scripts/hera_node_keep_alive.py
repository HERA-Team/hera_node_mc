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
from node_control import node_control, __package__, __version__
import os
import sys
import argparse
import datetime
import socket


hostname = socket.gethostname()
script_redis_key = "status:script:{}:{}".format(hostname, __file__)

parser = argparse.ArgumentParser(description='Send keepalive pokes to all nodes with '
                                 'a status entry in redis and connected',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--poke_time_sec', type=float,
                    help="Extra time to wait between pokes", default=2.0)
parser.add_argument('-r', '--redishost', type=str, default='redishost',
                    help='IP or hostname string of host running the monitor redis server.')
parser.add_argument('--force-direct', dest='force_direct', help="Flag to ignore hostname.",
                    action='store_true')
args = parser.parse_args()

r = redis.StrictRedis(host=args.redishost)
r.hmset("version:{}:{}".format(__package__, os.path.basename(__file__)), {
        "version": __version__, "timestamp": datetime.datetime.now().isoformat()})
node_ctrl = node_control.NodeControl(None, args.redishost, count=None)

heartbeat = 60

# Sends poke signal to Arduinos inside the nodes
try:
    while True:
        r.set(script_redis_key, "alive", ex=heartbeat)
        node_ctrl.get_nodes_in_redis(count=None)
        node_ctrl.get_node_senders(throttle=0.02, force_direct=args.force_direct)
        for node_id in node_ctrl.connected_nodes:
            node_ctrl.senders[node_id].poke()
            r.hset(f'throttle:node:{node_id}', 'last_poke_sec', time.time())
        time.sleep(args.poke_time_sec)  # actual time is this + poke time (~1s)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
