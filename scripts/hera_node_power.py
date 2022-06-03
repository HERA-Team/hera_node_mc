#! /usr/bin/env python
import argparse
from node_control import node_control

parser = argparse.ArgumentParser(description='Turn on SNAP relay, SNAPs, FEM and PAM. '
                                 'No hardware choice turns all on/off.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('command', help="Specify 'on', 'off', or 'reset'.",
                    choices=['on', 'off', 'reset'])
parser.add_argument('node', help="Specify the list of nodes (csv list of int) or 'all' (default)",
                    nargs='?', default='all')
parser.add_argument('-p', '--pam', action='store_true', help='Turn on/off the PAMs')
parser.add_argument('-f', '--fem', action='store_true', help='Turn on/off the FEMs')
parser.add_argument('-s', '--snaps', action='store_true',
                    help='Turn on/off all the snaps.  Equivalent to -0 -1 -2 -3')
parser.add_argument('-0', '--snap0', action='store_true', help='Turn on/off SNAP 0')
parser.add_argument('-1', '--snap1', action='store_true', help='Turn on/off SNAP 1')
parser.add_argument('-2', '--snap2', action='store_true', help='Turn on/off SNAP 2')
parser.add_argument('-3', '--snap3', action='store_true', help='Turn on/off SNAP 3')
parser.add_argument('-r', '--snap-relay', dest='snap_relay', action='store_true',
                    help="Turn on/off the snap-relay - NOT NEEDED except "
                         "when turning off the last snap if done separately")
parser.add_argument('--throttle', help='Throttle time in sec for udp_sender (0.2s)',
                    type=float, default=0.2)
parser.add_argument('--quiet', help="Don't print verification.", action='store_true')
parser.add_argument('--hold-for-verify', dest='hold_for_verify',
                    help="Seconds to wait before timing out (use 0 to disable check)",
                    default=90, type=int)
parser.add_argument('--verify-mode', dest='verify_mode', help='Type of verify mode.',
                    choices=['time', 'agree', 'cmd', 'stat', 'all'], default='all')
parser.add_argument('--error-threshold', dest='error_threshold', default=1.0, type=float,
                    help='Fractional failure rate for error (0->any, 1->none) (default 0.0).')
parser.add_argument('--show-success', dest='show_success', action='store_true',
                    help='Show successful commands in addition to failures.')
parser.add_argument('--redisServer', help='Name of redis server', default='redishost')
parser.add_argument('--ip', help="Provide explicit IP for each node", default=None)

args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = 'all'
else:
    nodes2use = [int(x) for x in args.node.split(',')]
    if args.ip is not None:
        args.ip = args.ip.split(',')
        if len(nodes2use) != len(args.ip):
            raise ValueError("Number of nodes and IP addresses must match.")
        ips2use = {}
        for i, node in enumerate(nodes2use):
            ips2use[node] = args.ip[i]

verbose = not args.quiet

nc = node_control.NodeControl(nodes2use, redisServer=args.redisServer, count=None)
nc.get_node_senders(throttle=args.throttle, explicit_ip=args.ip)
if not len(nc.connected_nodes):
    import sys
    print("No nodes are connected.")
    sys.exit()

if args.command == 'reset':
    print("Resetting the arduinos.")
    nc.reset()
    import sys
    sys.exit()

# Preprocess hardware arguments.
all_hardware = True  # Default is to turn everything on/off, unless something specific is set.
for hw in ['fem', 'pam', 'snaps', 'snap0', 'snap1', 'snap2', 'snap3', 'snap_relay']:
    if getattr(args, hw):
        all_hardware = False
if all_hardware:
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

# Turn off snap monitoring if turning off all snaps.
if args.command == 'off' and nodes2use == 'all' and all_snap:
    nc.disable_snap_monitor()

# Run through commands.
keystates = {}

if args.command == 'on' and (args.snap_relay or any_snap):
    nc.power_snap_relay('on', args.hold_for_verify, args.verify_mode)
    keystates['snap_relay'] = 'on'

for snap_n in snaps_to_set:
    nc.power_snap(snap_n, args.command)
    keystates['snap_{}'.format(snap_n)] = args.command

if args.command == 'off' and (args.snap_relay or all_snap):
    nc.power_snap_relay('off', args.hold_for_verify, args.verify_mode)
    keystates['snap_relay'] = 'off'

if args.pam:
    nc.power_pam(args.command)
    keystates['pam'] = args.command

if args.fem:
    nc.power_fem(args.command)
    keystates['fem'] = args.command

if args.hold_for_verify > 0:
    results = nc.verdict(keystates, verbose=verbose,
                         hold_for_verify=args.hold_for_verify,
                         verify_mode=args.verify_mode,
                         show_success=args.show_success)
    nc.sentence(results, args.error_threshold, purge=False)

# Double-check snap monitoring
nc.snap_monitor_check_and_set()
