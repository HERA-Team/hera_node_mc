import udpSenderClass
import time
import argparse

parser = argparse.ArgumentParser(description = 'Specify the things for PCB to turn off via flags',
                                 formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-r', dest = 'snapRelay', action = 'store_true', default = False,
                    help = 'Use this flag to turn off the snapRelay')
parser.add_argument('-s', dest = 'snaps', action = 'store_true', default = False,
                    help = 'Use this flag to turn off all the snaps')
parser.add_argument('-s0', dest = 'snap0', action = 'store_true', default = False,
                    help = 'Use this flag to turn off SNAP 0')
parser.add_argument('-s1', dest = 'snap1', action = 'store_true', default = False,
                    help = 'Use this flag to turn off SNAP 1')
parser.add_argument('-s2', dest = 'snap2', action = 'store_true', default = False,
                    help = 'Use this flag to turn off SNAP 2')
parser.add_argument('-s3', dest = 'snap3', action = 'store_true', default = False,
                    help = 'Use this flag to turn off SNAP 3')
parser.add_argument('-p', dest = 'pam', action = 'store_true', default = False,
                    help = 'Use this flag to turn off the PAM')
parser.add_argument('-f', dest = 'fem', action = 'store_true', default = False,
                    help = 'Use this flag to turn off the FEM')
parser.add_argument('--reset', dest = 'reset', action = 'store_true', default = False,
                    help = 'Use this flag to reset Arduino (turn everything off abruptly')

args = parser.parse_args()
s = udpSenderClass.UdpSender()

if args.snaps:
    print("Turning snapv2_0 off")
    s.snapv2_0('10.1.1.200','off')
    time.sleep(1)
    print("Turning snapv2_1 off")
    s.snapv2_1('10.1.1.200','off')
    time.sleep(1)
    print("Turning snapv2_2 off")
    s.snapv2_2('10.1.1.200','off')
    time.sleep(1)
    print("Turning snapv2_3 off")
    s.snapv2_3('10.1.1.200','off')
    time.sleep(1)
    print("Turning snapRelay off")
    s.snapRelay('10.1.1.200','off')
    time.sleep(.1)

if args.snapRelay:
    print("Turning snapRelay off")
    s.snapRelay('10.1.1.200','off')
    time.sleep(.1)

if args.snap0:
    print("Turning SNAP 0 off")
    s.snapv2_0('10.1.1.200','off')
    time.sleep(1)

if args.snap1:
    print("Turning SNAP 1 off")
    s.snapv2_1('10.1.1.200','off')
    time.sleep(1)

if args.snap2:
    print("Turning SNAP 2 off")
    s.snapv2_2('10.1.1.200','off')
    time.sleep(1)

if args.snap3:
    print("Turning SNAP 3 off")
    s.snapv2_3('10.1.1.200','off')
    time.sleep(1)

if args.pam:
    print("Turning PAM off")
    s.pam('10.1.1.200','off')
    time.sleep(1)

if args.fem:
    print("Turning FEM off")
    s.fem('10.1.1.200','off')
    time.sleep(1)

if args.reset:
    print("Resetting Arduino/Turning everything off at once")
    s.reset('10.1.1.200')
