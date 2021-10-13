#! /usr/bin/env python
"""
This class is used for receiving debug messages on port 8890 from all the active Arduinos.
"""
import datetime
import time
import sys
import argparse
from node_control import send_receive

parser = argparse.ArgumentParser(description='This script dumps the serial output of all of '
                                 'the Arduinos every x seconds - default is 300.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-f', '--file_name', help='Specify the file name to dump Redis data to e.g '
                    'datasetMMDDYY.txt If None (default) dumps to screen', default=None)
parser.add_argument('-t', '--interval', default=1,
                    help='Specify the time interval, in seconds, for data collection')
parser.add_argument('--server', help='Server IP (default 0.0.0.0)', default='0.0.0.0')
parser.add_argument('--port', help='Port to use on server (default 8890)', default=8890)

args = parser.parse_args()
if args.file_name is None:
    fp = sys.stdout
else:
    fp = open(args.file_name, 'w')

rcvr = send_receive.UdpSenderReceiver('receive', serverAddress=args.server, rcvPort=int(args.port))

try:
    while True:
        # Receive data continuously from all active Arduinos
        data, addr = rcvr.client_socket.recvfrom(2048)
        print("{}  at  {}:{}".format((datetime.datetime.now()), addr[0], addr[1]), file=fp)
        print('\t', data, file=fp)
        time.sleep(float(args.interval))
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)
