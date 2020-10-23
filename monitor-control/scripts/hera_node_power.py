#! /usr/bin/env
import argparse
import nodeControl

parser = argparse.ArgumentParser(description='Turn on SNAP relay, SNAPs, FEM and PAM',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('command', help="Specify 'on' or 'off'", choices=['on', 'off'])
parser.add_argument('node', help="Specify the list of nodes (csv) or 'all'", default='all')
parser.add_argument('-r', '--snap-relay', dest='snap_relay', action='store_true',
                    help='Flag to turn on the snap-relay (redundant if turning on any snap)')
parser.add_argument('-s', '--snaps', action='store_true', help='Flag to turn on all the snaps')
parser.add_argument('-0', '--snap0', action='store_true', help='Flag to turn on SNAP 0')
parser.add_argument('-1', '--snap1', action='store_true', help='Flag to turn on SNAP 1')
parser.add_argument('-2', '--snap2', action='store_true', help='Flag to turn on SNAP 2')
parser.add_argument('-3', '--snap3', action='store_true', help='Flag to turn on SNAP 3')
parser.add_argument('-p', '--pam', action='store_true', help='Flag to turn on the PAM')
parser.add_argument('-f', '--fem', action='store_true', help='Flag to turn on the FEM')
parser.add_argument('--reset', action='store_true', help='Flag to reset Arduino (abruptly')
parser.add_argument('--check', action='store_true', help='Flag to check node existence')
parser.add_argument('--init', action='store_true', help='Flag to reset power flags in redis')
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]

n = nodeControl.NodeControl(nodes2use, serverAddress=args.serverAddress)
if args.snaps:
    args.snap0 = True
    args.snap1 = True
    args.snap2 = True
    args.snap3 = True

if args.snap_relay or args.snap0 or args.snap1 or args.snap2 or args.snap3:
    n.power_snap_relay(args.command)

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

if args.reset:
    print("Resetting Arduino/turning everything off at once")
    n.reset()

if args.check:
    for key, val in n.check_exists().items():
        print('{}:  {}'.format(key, val))

if args.init:
    n.init_redis()
