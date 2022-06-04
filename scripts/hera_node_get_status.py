#! /usr/bin/env python
import sys
import argparse
from node_control import node_control
from node_control import node_util


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

print("Getting nodes.")
sys.stdout.flush()
nc = node_control.NodeControl(args.node, redisServer=args.redisServer, count=1)

if len(nc.nodes_in_redis):
    nodes_present = nc.nodes_in_redis
    nodes_missing = []
    for _i in nc.requested_nodes:
        if _i not in nodes_present:
            nodes_missing.append(_i)
    print("Requested nodes present in redis:  {}"
          .format(', '.join([str(x) for x in nodes_present])))
    if len(nodes_missing):
        print("Requested nodes missing in redis:  {}"
              .format(', '.join([str(x) for x in nodes_missing])))
else:
    print("None are present")
    sys.exit()

powers = nc.get_power_status()
print("\nNode power states")
print("-----------------")
for nd in nc.requested_included['power']:
    pwr = powers[nd]
    if node_util.stale_data(pwr, 'age', args.stale, f"Node {nd} -- ") and not args.show_stale:
        continue
    print(node_util.node_power_entry(nd, pwr))

if args.temperature:
    sensors = nc.get_sensors()
    print("\nNode values")
    print("-----------")
    for nd in nc.requested_included['sensor']:
        sens = sensors[nd]
        if node_util.stale_data(sens, 'age', args.stale, f"Node {nd} -- ") and not args.show_stale:
            continue
        print(node_util.node_sensor_entry(nd, sens))

if args.wr:
    wr = nc.get_wr_status()
    print("\nWhite Rabbit")
    print("------------")
    args.show_stale = True  # Always show (but maybe will change when update hera_wr_cm)
    for nd in nc.requested_included['wr']:
        wrs = wr[nd]
        print("Node {} -- ".format(nd), end='')
        if node_util.stale_data(wrs, 'age', args.stale, True) and not args.show_stale:
            continue
        if 'timestamp' in wrs.keys() and wrs['timestamp'] is not None:
            print(" updated at {}".format(wrs['timestamp']))
        for key, val in sorted(wrs.items()):
            if key == 'timestamp':
                continue
            print("  {:20s} {}".format(key, val))
