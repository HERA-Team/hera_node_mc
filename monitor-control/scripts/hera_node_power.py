import argparse
import nodeControl

parser = argparse.ArgumentParser(description='Turn on SNAP relay, SNAPs, FEM and PAM via flags',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('node', help='Specify the list of node (csv).')
parser.add_argument('switch', help="Specify 'on' or 'off'", choices=['on', 'off'])
parser.add_argument('-r', dest='snapRelay', action='store_true',
                    help='Use this flag to turn on the snapRelay (redundant if turning on any snap)')  # noqa
parser.add_argument('-s', dest='snaps', action='store_true',
                    help='Use this flag to turn on all the snaps')
parser.add_argument('-s0', dest='snap0', action='store_true',
                    help='Use this flag to turn on SNAP 0')
parser.add_argument('-s1', dest='snap1', action='store_true',
                    help='Use this flag to turn on SNAP 1')
parser.add_argument('-s2', dest='snap2', action='store_true',
                    help='Use this flag to turn on SNAP 2')
parser.add_argument('-s3', dest='snap3', action='store_true',
                    help='Use this flag to turn on SNAP 3')
parser.add_argument('-p', dest='pam', action='store_true',
                    help='Use this flag to turn on the PAM')
parser.add_argument('-f', dest='fem', action='store_true',
                    help='Use this flag to turn on the FEM')
parser.add_argument('--reset', dest='reset', action='store_true',
                    help='Use this flag to reset Arduino (turn everything off abruptly')
args = parser.parse_args()

nodes2use = [int(x) for x in args.node.split(',')]
n = nodeControl.NodeControl(nodes2use)
if args.snaps:
    args.snap0 = True
    args.snap1 = True
    args.snap2 = True
    args.snap3 = True

if args.snapRelay or args.snap0 or args.snap1 or args.snap2 or args.snap3:
    n.power_snap_relay(args.switch)

if args.snap0:
    n.power_snap_0(args.switch)

if args.snap1:
    n.power_snap_1(args.switch)

if args.snap2:
    n.power_snap_2(args.switch)

if args.snap3:
    n.power_snap_3(args.switch)

if args.pam:
    n.power_pam(args.switch)

if args.fem:
    n.power_fem(args.switch)

if args.reset:
    print("Resetting Arduino/Turning everything off at once")
    n.reset()
