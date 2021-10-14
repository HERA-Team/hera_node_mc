#! /usr/bin/env python
import sys
import argparse
from node_control import node_control
from node_control import node_util
from datetime import datetime


parser = argparse.ArgumentParser(description='This script outputs the current node status',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node', nargs='?', help="Specify the node ID numbers (csv list of int "
                    "from 0 to 29) to get the corresponding Redis data or use 'all'",
                    default='all')
parser.add_argument('-t', '--temperature', action='store_true', help="Flag to show node temps")
parser.add_argument('-w', '--wr', action='store_true', help="Flag to add white rabbit status")
parser.add_argument('--stale', help='Number of seconds for stale data',
                    type=float, default=10.0)
parser.add_argument('--show-stale', dest='show_stale', help="Flag to show stale data values",
                    action='store_true')
parser.add_argument('--redisServer', help='Name or redis server', default='redishost')
args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]

print("Getting nodes.")
sys.stdout.flush()
nc = node_control.NodeControl(nodes2use, redisServer=args.redisServer, count=1)

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
    if node_util.stale_data(pwr, 'age', args.stale, True) and not args.show_stale:
        continue
    if 'timestamp' in pwr.keys() and pwr['timestamp'] is not None:
        print(" updated at {}".format(datetime.fromtimestamp(pwr['timestamp']).isoformat()))
    for key, val in sorted(pwr.items()):
        if key in ['timestamp', 'age']:
            continue
        print("  {:20s} {}".format(key, switch[val]))

if args.temperature:
    print("\nNode values")
    print("-----------")
    for nd, sens in sensors.items():
        if node_util.stale_data(sens, 'age', args.stale, True) and not args.show_stale:
            print("Node {} has stale data.".format(nd))
            continue
        print(node_util.node_sensor_table(nd, sens))


if args.wr:
    wr = nc.get_wr_status()
    print("\nWhite Rabbit")
    print("------------")
    args.show_stale = True  # Always show (but maybe will change when update hera_wr_cm)
    for nd, wrs in wr.items():
        print("Node {} -- ".format(nd), end='')
        if node_util.stale_data(wrs, 'age', args.stale, True) and not args.show_stale:
            continue
        if 'timestamp' in wrs.keys() and wrs['timestamp'] is not None:
            print(" updated at {}".format(wrs['timestamp']))
        for key, val in sorted(wrs.items()):
            if key == 'timestamp':
                continue
            print("  {:20s} {}".format(key, val))
