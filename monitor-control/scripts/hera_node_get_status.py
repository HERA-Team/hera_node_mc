#! /usr/bin/env python
from __future__ import print_function
import sys
import argparse
import nodeControl

parser = argparse.ArgumentParser(description='This script outputs the current node status',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node', nargs='?', help="Specify the node ID numbers (csv list of int "
                    "from 0 to 29) to get the corresponding Redis data or use 'all'",
                    default='all')
parser.add_argument('--wr', action='store_true', help="Flag to add white rabbit status")
parser.add_argument('--exists', action='store_true', help='Check node existence')
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]

print("Attempting to connect to the node control redis database on 'redishost'...", end=' ')
sys.stdout.flush()
node = nodeControl.NodeControl(nodes2use, serverAddress=args.serverAddress)
print("OK")

node_status = node.check_exists()
if args.exists:
    for key, val in node_status.items():
        print('{}:  {}'.format(key, val))
    sys.exit()
print("Nodes found in redis: {}".format(', '.join([str(x) for x in node.nodes_in_redis])))

if node_status:
    nodes_present = []
    nodes_missing = []
    for nd, stat in node_status.items():
        if stat:
            nodes_present.append(str(nd))
        else:
            nodes_missing.append(str(nd))
    print("Nodes present:  {}".format(', '.join(nodes_present)))
    if len(nodes_missing):
        print("Nodes missing:  {}".format(', '.join(nodes_missing)))
else:
    print("None are present")
    exit

powers = node.get_power_status()
sensors = node.get_sensors()

switch = {True: 'On', False: 'Off'}
print("\nNode power states")
print("-----------------")
for nd, pwr in powers.items():
    print("Node {}   updated at {}".format(nd, pwr['timestamp']))
    for key, val in sorted(pwr.items()):
        if key == 'timestamp':
            continue
        print("  {:20s} {}".format(key, switch[val]))

print("\nNode values")
print("-----------")
for nd, sens in sensors.items():
    print("Node {}   updated at {}".format(nd, sens['timestamp']))
    for key, val in sorted(sens.items()):
        if key == 'timestamp':
            continue
        print("  {:20s} {}".format(key, val))

if args.wr:
    wr = node.get_wr_status()
    print("\nWhite Rabbit")
    print("------------")
    for nd, wrs in wr.items():
        print("Node {}   updated at {}".format(nd, wrs['timestamp']))
        for key, val in sorted(wrs.items()):
            if key == 'timestamp':
                continue
            print("  {:20s} {}".format(key, val))
