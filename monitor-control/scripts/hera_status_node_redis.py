#! /usr/bin/env python
"""
Puts the "minimum" node information into redis to allow node_mc to find it,
or removes its status from redis if remove-nodes flag is set.

Set node_ID under status:node:*
"""

import redis
import argparse

ap = argparse.ArgumentParser()
ap.add_argument('nodes', help='List of node numbers.')
ap.add_argument('--remove-nodes', dest='remove_nodes',
                help='Flag to remove node status from redis.',
                action='store_true')
args = ap.parse_args()

min_nodes = [int(x) for x in args.nodes.split(',')]

connection_pool = redis.ConnectionPool(host='redishost', decode_responses=True)
r = redis.StrictRedis(connection_pool=connection_pool, charset='utf-8')

for node in min_nodes:
    status_node = f"status:node:{node}"
    if args.remove_nodes:
        for k in r.hgetall(status_node):
            r.hdel(status_node, k)
            print(f"removing {status_node}:  {k}")
    else:
        r.hset(status_node, 'node_ID', node)
