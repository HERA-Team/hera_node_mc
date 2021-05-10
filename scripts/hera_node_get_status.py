#! /usr/bin/env python
from __future__ import print_function
import sys
import argparse
from node_control import node_control

parser = argparse.ArgumentParser(description='This script outputs the current node status',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node', nargs='?', help="Specify the node ID numbers (csv list of int "
                    "from 0 to 29) to get the corresponding Redis data or use 'all'",
                    default='all')
parser.add_argument('--wr', action='store_true', help="Flag to add white rabbit status")
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
parser.add_argument('--stale', help='Number of seconds for stale data warning',
                    type=float, default=10.0)
args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]

print("Attempting to connect to the node control redis database on 'redishost'...")
sys.stdout.flush()
nc = node_control.NodeControl(nodes2use, serverAddress=args.serverAddress, count=1)

if len(nc.nodes_in_redis):
    nodes_present = nc.nodes_in_redis
    nodes_missing = []
    for _i in nodes2use:
        if _i not in nodes_present:
            nodes_missing.append(_i)
    print("Requested nodes present:  {}".format(', '.join([str(x) for x in nodes_present])))
    if len(nodes_missing):
        print("Requested nodes missing:  {}".format(', '.join([str(x) for x in nodes_missing])))
else:
    print("None are present")
    sys.exit()

powers = nc.get_power_status()
sensors = nc.get_sensors()

switch = {True: 'On', False: 'Off'}
print("\nNode power states")
print("-----------------")
for nd, pwr in powers.items():
    print("Node {} -- ".format(nd), end='')
    if 'timestamp' in pwr.keys():
        print("updated at {}".format(pwr['timestamp']))
    elif 'age' in pwr.keys():
        print("updated {} seconds ago".format(pwr['age']))
    else:
        print("no timestamp")
    node_control.stale_data(pwr['age'], args.stale)
    for key, val in sorted(pwr.items()):
        if key in ['timestamp', 'age']:
            continue
        print("  {:20s} {}".format(key, switch[val]))

print("\nNode values")
print("-----------")
for nd, sens in sensors.items():
    print("Node {} -- ".format(nd), end='')
    if 'timestamp' in sens.keys():
        print("updated at {}".format(sens['timestamp']))
    elif 'age' in sens.keys():
        print("updated {} seconds ago".format(sens['age']))
    else:
        print("no timestamp")
    node_control.stale_data(sens['age'], args.stale)
    for key, val in sorted(sens.items()):
        if key in ['timestamp', 'age']:
            continue
        print("  {:20s} {}".format(key, val))

if args.wr:
    wr = nc.get_wr_status()
    print("\nWhite Rabbit")
    print("------------")
    for nd, wrs in wr.items():
        print("Node {} -- ".format(nd), end='')
        if 'timestamp' in wrs.keys():
            print("updated at {}".format(wrs['timestamp']))
        elif 'age' in wrs.keys():
            print("updated {} seconds ago".format(wrs['age']))
        else:
            print("no timestamp")
        for key, val in sorted(wrs.items()):
            if key == 'timestamp':
                continue
            print("  {:20s} {}".format(key, val))
