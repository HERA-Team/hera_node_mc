#! /usr/bin/env python
from __future__ import print_function
import argparse
import time
from node_control import node_control

parser = argparse.ArgumentParser(description='Turn on SNAP relay, SNAPs, FEM and PAM',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('command', help="Specify 'on', 'off', or 'reset'.  "
                    "reset doesn't use any other arguments.",
                    choices=['on', 'off', 'reset'])
parser.add_argument('node', help="Specify the list of nodes (csv list of int) or 'all'", nargs='?',
                    default='all')
parser.add_argument('-r', '--snap-relay', dest='snap_relay', action='store_true',
                    help="Turn on/off the snap-relay "
                    "(redundant if turning on _any_ snap or off _all_ snaps in one call; "
                    "needed when turning off the last snap if done separately)")
parser.add_argument('-s', '--snaps', action='store_true',
                    help='Turn on/off all the snaps.  Equivalent to -0 -1 -2 -3')
parser.add_argument('-0', '--snap0', action='store_true', help='Turn on/off SNAP 0')
parser.add_argument('-1', '--snap1', action='store_true', help='Turn on/off SNAP 1')
parser.add_argument('-2', '--snap2', action='store_true', help='Turn on/off SNAP 2')
parser.add_argument('-3', '--snap3', action='store_true', help='Turn on/off SNAP 3')
parser.add_argument('-p', '--pam', action='store_true', help='Turn on/off the PAMs')
parser.add_argument('-f', '--fem', action='store_true', help='Turn on/off the FEMs')
parser.add_argument('--allhw', action='store_true',
                    help='Turn on/off snaps, pams and fems.  Equivalent to -s -p -f')
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
parser.add_argument('--throttle', help='Throttle time in sec for udp_sender',
                    type=float, default=0.1)
parser.add_argument('--wait', dest='wait_time_in_sec', help="Seconds to wait to check results "
                    "(use 0 to disable check)", default=5.0, type=float)
parser.add_argument('--force-direct', dest='force_direct', help="Flag to ignore hostname.",
                    action='store_true')

args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]

nc = node_control.NodeControl(nodes2use, serverAddress=args.serverAddress, count=None)
nc.get_node_senders(throttle=args.throttle, force_direct=args.force_direct)
if not len(nc.connected_nodes):
    import sys
    print("No nodes are connected.")
    sys.exit()

if args.command == 'node_reset':
    print("Abruptly reseting the arduinos!")
    nc.reset()
else:
    keystates = {}
    if args.allhw:
        args.snap_relay = True
        args.snaps = True
        args.pam = True
        args.fem = True

    snaps_to_set = []
    if args.snaps:
        snaps_to_set = [0, 1, 2, 3]
    else:
        for i in range(4):
            if getattr(args, 'snap{}'.format(i)):
                snaps_to_set.append(i)
    any_snap = len(snaps_to_set) > 0
    all_snap = len(snaps_to_set) == 4

    if args.command == 'on' and (args.snap_relay or any_snap):
        nc.power_snap_relay('on')
        keystates['power_snap_relay'] = 'on'

    for snap_n in snaps_to_set:
        nc.power_snap(snap_n, args.command)
        keystates['power_snap_{}'.format(snap_n)] = args.command

    if args.pam:
        nc.power_pam(args.command)
        keystates['power_pam'] = args.command

    if args.fem:
        nc.power_fem(args.command)
        keystates['power_fem'] = args.command

    if args.command == 'off' and (args.snap_relay or all_snap):
        nc.power_snap_relay('off')
        keystates['power_snap_relay'] = 'off'

    if args.wait_time_in_sec > 0.001:
        time.sleep(args.wait_time_in_sec)
        stale_time = 1.1 * (args.wait_time_in_sec +
                            len(nc.connected_nodes) * len(keystates) * args.throttle)
        nc.check_stale_power_status(stale_time, keystates)
        if len(nc.stale_nodes):
            print("These nodes aren't updating:  {}".format(nc.stale_nodes))
        updated = sorted(nc.connected_nodes)
        if len(updated):
            print("These nodes are connected:  {}".format(updated))
            for nd in updated:
                if len(nc.wrong_states[nd]):
                    print("\tCommand not successful:  Node {} -> {} {}"
                          .format(nd, nc.wrong_states[nd], args.command))
        else:
            print("No nodes checked.")
