import time
import argparse
import nodeControl

parser = argparse.ArgumentParser(description = 'Turn on SNAP relay, SNAPs, FEM and PAM via flags',
			formatter_class = argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('node', action = 'store', 
			help = 'Specify the Arduino IP address to send commands to')
parser.add_argument('-r', dest = 'snapRelay', action = 'store_true', default = False,
			help = 'Use this flag to turn on the snapRelay')
parser.add_argument('-s', dest = 'snaps', action = 'store_true', default = False,
			help = 'Use this flag to turn on all the snaps')
parser.add_argument('-s0', dest = 'snap0', action = 'store_true', default = False,
			help = 'Use this flag to turn on SNAP 0')
parser.add_argument('-s1', dest = 'snap1', action = 'store_true', default = False,
			help = 'Use this flag to turn on SNAP 1')
parser.add_argument('-s2', dest = 'snap2', action = 'store_true', default = False,
			help = 'Use this flag to turn on SNAP 2')
parser.add_argument('-s3', dest = 'snap3', action = 'store_true', default = False,
			help = 'Use this flag to turn on SNAP 3')
parser.add_argument('-p', dest = 'pam', action = 'store_true', default = False,
			help = 'Use this flag to turn on the PAM')
parser.add_argument('-f', dest = 'fem', action = 'store_true', default = False,
			help = 'Use this flag to turn on the FEM')
parser.add_argument('--reset', dest = 'reset', action = 'store_true', default = False,
			help = 'Use this flag to reset Arduino (turn everything off abruptly')
args = parser.parse_args()

# Instantiate a udpSenderClass object to send commands to Arduino
n = nodeControl.NodeControl(int(args.node))
if args.snaps:
    n.power_snap_relay('on')
    n.power_snap_0('on')
    n.power_snap_1('on')
    n.power_snap_2('on')
    n.power_snap_3('on')

if args.snapRelay:
    #print("Turning SNAP relay on")
    n.power_snap_relay('on')

if args.snap0:
    n.power_snap_relay('on')
    n.power_snap_0('on')

if args.snap1:
    n.power_snap_relay('on')
    n.power_snap_1('on')

if args.snap2:
    n.power_snap_relay('on')
    n.power_snap_2('on')

if args.snap3:
    n.power_snap_relay('on')
    n.power_snap_3('on')

if args.pam:
    n.power_pam('on')

if args.fem:
    n.power_fem('on')

if args.reset:
    print("Resetting Arduino/Turning everything off at once")
    n.reset()

