#! /usr/bin/env python
"""
Pokes Arduinos to ensure Arduino's connectivity to the server.
It pokes either specified nodes with the -n argument or
the nodes that have Redis status keys i.e. status:node:x where x is the node ID
set by the I2C digital I/O cards plugged into PCBs.
"""
from __future__ import print_function
import time
import node_control
import sys
import argparse

parser = argparse.ArgumentParser(description='Send keep-alive pokes to all nodes with '
                                 'a status entry in redis and connected',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--poke_time_sec', type=float,
                    help="Extra time to wait between pokes", default=2.0)
parser.add_argument('-r', '--redishost', type=str, default='redishost',
                    help='IP or hostname string of host running the monitor redis server.')
parser.add_argument('--force-direct', dest='force_direct', help="Flag to ignore hostname.",
                    action='store_true')
parser.add_argument('--heartbeat', type=int, default=60, help='redis heartbeat time in seconds')
args = parser.parse_args()


node_ctrl = node_control.node_control.NodeControl('all', args.redishost)
node_ctrl.log_service_in_redis(__file__)

# Sends poke signal to Arduinos inside the nodes
try:
    while True:
        node_ctrl.r.set(node_ctrl.status_scriptname, "alive", ex=args.heartbeat)
        node_ctrl.get_nodes_in_redis(count=None)
        node_ctrl.get_node_senders(throttle=0.02, force_direct=args.force_direct)
        for node_id in node_ctrl.connected_nodes:
            node_ctrl.senders[node_id].poke()
            node_ctrl.r.hset('throttle:node:{}'.format(node_id), 'last_poke_sec', time.time())
        time.sleep(args.poke_time_sec)  # actual time is this + poke time (~1s)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
