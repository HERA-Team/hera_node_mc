#! /usr/bin/env python
from __future__ import print_function
import argparse
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
parser.add_argument('--throttle', help='Throttle time in sec for udp_sender',
                    type=float, default=1.0)
parser.add_argument('--quiet', help="Don't print verification.", action='store_true')
parser.add_argument('--hold-for-verify', dest='hold_for_verify',
                    help="Seconds to wait before timing out (use 0 to disable check)",
                    default=120, type=int)
parser.add_argument('--verify-mode', dest='verify_mode', help='Type of verify mode.',
                    choices=['time', 'agree', 'cmd', 'stat', 'all'])
parser.add_argument('--error-threshold', dest='error_threshold', default=1.0, type=float,
                    help='Fractional failure rate over which to raise an error.')
parser.add_argument('--dont-purge', dest='purge', help="Flag to keep all nodes.",
                    action='store_false')
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
parser.add_argument('--force-direct', dest='force_direct', help="Flag to ignore hostname. "
                    "This is for development, so shouldn't ever need.",
                    action='store_true')

args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]
verbose = not args.quiet

nc = node_control.NodeControl(nodes2use, serverAddress=args.serverAddress, count=None)
nc.get_node_senders(throttle=args.throttle, force_direct=args.force_direct)
if not len(nc.connected_nodes):
    import sys
    print("No nodes are connected.")
    sys.exit()

if args.command == 'reset':
    print("Abruptly resetting the arduinos!")
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
        nc.power_snap_relay('on', 120, 'all')  # Defaults to verifying success.
        keystates['snap_relay'] = 'on'

    for snap_n in snaps_to_set:
        nc.power_snap(snap_n, args.command)
        keystates['snap_{}'.format(snap_n)] = args.command

    if args.command == 'off' and (args.snap_relay or all_snap):
        nc.power_snap_relay('off')
        keystates['snap_relay'] = 'off'

    if args.pam:
        nc.power_pam(args.command)
        keystates['pam'] = args.command

    if args.fem:
        nc.power_fem(args.command)
        keystates['fem'] = args.command

    if args.hold_for_verify > 0:
        hws, cmds = [], []
        for key, state in keystates.items():
            hws.append(key)
            cmds.append(state)
        results = nc.verdict(hws, cmds, verbose=verbose,
                             hold_for_verify=args.hold_for_verify, verify_mode=args.verify_mode)
        nc.sentence(results, args.error_threshold, args.purge)
