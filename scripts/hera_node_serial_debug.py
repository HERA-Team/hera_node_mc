#! /usr/bin/env python
"""
This class is used for receiving debug messages on port 8890 from all the active Arduinos.
"""
from __future__ import print_function
import datetime
import sys
from node_control import send_receive

rcvr = send_receive.UdpSenderReceiver('receive', serverAddress='10.80.2.1', rcvPort=8890)

try:
    while True:
        # Receive data continuously from all active Arduinos
        data, addr = rcvr.client_socket.recvfrom(2048)
        print(data)
        print((datetime.datetime.now()))
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)
