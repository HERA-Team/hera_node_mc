#! /usr/bin/env python
"""
Pokes Arduinos to ensure Arduino's connectivity to the server.
It pokes either specified nodes with the -n argument or
the nodes that have Redis status keys i.e. status:node:x where x is the node ID
set by the I2C digital I/O cards plugged into PCBs.

Note that the Arduino watchdog time-out is 8sec, which is an Arduino hw limit.
"""
import time
import node_control
import sys
import argparse

parser = argparse.ArgumentParser(description='Send keep-alive pokes to all nodes with '
                                 'a status entry in redis and connected',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--poke_time_sec', type=float,
                    help="Extra time to wait between pokes", default=4.0)
parser.add_argument('-r', '--redishost', default='redishost',
                    help='IP or hostname string of host running the monitor redis server.')
parser.add_argument('--refresh', type=float, default=8.0,
                    help="Sender connection refresh time in hours.")
parser.add_argument('--throttle', type=float, default=0.1,
                    help="Throttle time within inner loop between node calls in sec.")
parser.add_argument('--heartbeat', type=int, default=60,
                    help='script redis heartbeat time in seconds')
args = parser.parse_args()


nc = node_control.node_control.NodeControl('all', args.redishost)
nc.log_service_in_redis(__file__)
rfrsh_sec = args.refresh * 3600.0
t0 = time.time()
t1 = t0
nc.get_nodes_in_redis(count=None)
nc.get_node_senders(throttle=args.throttle)
nc.r.hset('poke_nodes', 'time', t1)
nc.r.hset('poke_nodes', 'nodes', ','.join([str(x) for x in nc.connected_nodes]))

# Sends poke signal to Arduinos inside the nodes
try:
    while True:
        nc.r.set(nc.status_scriptname, "alive", ex=args.heartbeat)
        for node_id in nc.connected_nodes:
            nc.senders[node_id].poke()
            nc.r.hset('throttle:node:{}'.format(node_id), 'last_poke_sec', t1)
        sleep_time = args.poke_time_sec - len(nc.connected_nodes) * args.throttle
        if sleep_time > 0.0:
            time.sleep(sleep_time)
        t1 = time.time()
        if t1 - t0 > rfrsh_sec:
            nc.r.hset('poke_nodes', 'time', t1)
            nc.r.hset('poke_nodes', 'nodes', ','.join([str(x) for x in nc.connected_nodes]))
            nc.reset_node_senders()
            t0 = t1
        nc.get_nodes_in_redis(count=None)
        nc.get_node_senders(throttle=args.throttle)

except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
