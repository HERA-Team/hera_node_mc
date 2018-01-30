import udpSenderClass
import time
import argparse
import redis
import nodeControlClass

parser = argparse.ArgumentParser(description = 'Turn off the SNAP relay, SNAPs, FEM and PAM via flags',
			formatter_class = argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('node', action = 'store', 
			help = 'Specify the Arduino IP address to send commands to')

parser.add_argument('-r', dest = 'snapRelay', action = 'store_true', default = False,
			help = 'Use this flag to turn off the snapRelay')
parser.add_argument('-s', dest = 'snaps', action = 'store_true', default = False,
			help = 'Use this flag to turn off all the snaps')
parser.add_argument('-s01', dest = 'snap01', action = 'store_true', default = False,
			help = 'Use this flag to turn off SNAP 0 and 1')
parser.add_argument('-s23', dest = 'snap23', action = 'store_true', default = False,
			help = 'Use this flag to turn off SNAP 2 and 3')
parser.add_argument('-p', dest = 'pam', action = 'store_true', default = False,
			help = 'Use this flag to turn off the PAM')
parser.add_argument('-f', dest = 'fem', action = 'store_true', default = False,
			help = 'Use this flag to turn off the FEM')
parser.add_argument('--reset', dest = 'reset', action = 'store_true', default = False,
			help = 'Use this flag to reset Arduino (turn everything off abruptly')
args = parser.parse_args()

# Instantiate a udpSenderClass object to send commands to Arduino
n = nodeControlClass.NodeControl(int(args.node))
r = redis.StrictRedis(host='hera-digi-vm')
if args.snaps:
		print("Turning SNAP 0 and 1 off")
		n.power_snap_0_1('off')
		time.sleep(1)
		print("Turning SNAP 2 and 3 off")
		n.power_snap_2_3('off')
		time.sleep(1)
		print("Turning SNAP relay off")
		n.power_snap_relay('off')
		time.sleep(.1)

if args.snapRelay:
		print("Turning SNAP relay off")
		n.power_snap_relay('off')
		time.sleep(.1)

if args.snap01:
                print("Turning SNAP 0 and 1 off")
                n.power_snap_0_1('off')
                time.sleep(1)

if args.snap23:
		print("Turning SNAP 2 and 3 off")
		n.power_snap_2_3('off')
		time.sleep(1)

if args.pam:
		print("Turning PAM off")
		n.power_pam('off')
		time.sleep(1)

if args.fem:
		print("Turning FEM off")
		n.power_fem('off')
		time.sleep(1)

if args.reset:
		print("Resetting Arduino/Turning everything off at once")
		n.reset()

