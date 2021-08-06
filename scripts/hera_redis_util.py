#! /usr/bin/env python
"""
Puts the "minimum" node information into redis to allow node_mc to find it,
or removes its status from redis if remove-nodes flag is set.

Set node_ID under status:node:*
"""
from __future__ import print_function
import argparse
import node_control

ap = argparse.ArgumentParser()
ap.add_argument('nodes', help="List of node numbers to process. "
                "If 'list'/('listall') will just list nodes/(all data). "
                "If 'all' will use 0-29.")
ap.add_argument('--remove-nodes', dest='remove_nodes',
                help='Flag to remove node status from redis.',
                action='store_true')
args = ap.parse_args()
r = node_control.get_redis_client('redishost')

if args.nodes.lower().startswith('list'):
    for node in node_control.get_redis_nodes(count=2):
        print("{}".format(node))
        if args.node.lower() == 'listall':
            for _a, _b in r.hgetall(node):
                print(_a, _b)
else:
    if args.nodes.lower() == 'all':
        mod_nodes = list(range(30))
    else:
        mod_nodes = [int(x) for x in args.nodes.split(',')]
    for node in mod_nodes:
        status_node = "status:node:{}".format(node)
        if args.remove_nodes:
            r.delete(status_node)
            print("removing {}".format(status_node))
        else:
            r.hset(status_node, 'node_ID', node)
