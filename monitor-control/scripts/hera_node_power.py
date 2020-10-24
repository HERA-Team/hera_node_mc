#! /usr/bin/env python
from __future__ import print_function
import argparse
import nodeControl

parser = argparse.ArgumentParser(description='Turn on SNAP relay, SNAPs, FEM and PAM',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('command', help="Specify 'on', 'off', 'reset', 'init'",
                    choices=['on', 'off', 'reset', 'init'])
parser.add_argument('node', help="Specify the list of nodes (csv) or 'all'", default='all')
parser.add_argument('-r', '--snap-relay', dest='snap_relay', action='store_true',
                    help='Turn on the snap-relay (redundant if turning on any snap '
                    'and needed explicitly when turning off all snaps)')
parser.add_argument('-s', '--snaps', action='store_true', help='Turn on all the snaps')
parser.add_argument('-0', '--snap0', action='store_true', help='Turn on SNAP 0')
parser.add_argument('-1', '--snap1', action='store_true', help='Turn on SNAP 1')
parser.add_argument('-2', '--snap2', action='store_true', help='Turn on SNAP 2')
parser.add_argument('-3', '--snap3', action='store_true', help='Turn on SNAP 3')
parser.add_argument('-p', '--pam', action='store_true', help='Turn on the PAM')
parser.add_argument('-f', '--fem', action='store_true', help='Turn on the FEM')
parser.add_argument('--all', action='store_true', help='Turn on snaps, pam and fem')
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
parser.add_argument('--throttle', help='Throttle time in sec', default=0.5)
args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]
args.throttle = float(args.throttle)

n = nodeControl.NodeControl(nodes2use, serverAddress=args.serverAddress, throttle=args.throttle)

if args.command == 'reset':
    print("Reset abruptly resets the arduino")
    n.reset()
elif args.command == 'init':
    print("Init resets the power flags in redis to False")
    n.init_redis()
else:
    if args.all:
        args.snaps = True
        args.snap_relay = True
        args.pam = True
        args.fem = True

    if args.snaps:
        args.snap0 = True
        args.snap1 = True
        args.snap2 = True
        args.snap3 = True

    if args.command == 'on':
        if args.snap_relay or args.snap0 or args.snap1 or args.snap2 or args.snap3:
            n.power_snap_relay('on')

    if args.snap0:
        n.power_snap_0(args.command)

    if args.snap1:
        n.power_snap_1(args.command)

    if args.snap2:
        n.power_snap_2(args.command)

    if args.snap3:
        n.power_snap_3(args.command)

    if args.pam:
        n.power_pam(args.command)

    if args.fem:
        n.power_fem(args.command)

    if args.command == 'off' and args.snap_relay:
        n.power_snap_relay('off')
