#! /usr/bin/env python
"""
Receives UDP packets from all active Arduinos containing sensor data and status
information and pushes it up to Redis with status:node:x hash key. <hera_node_receiver>
"""
from __future__ import print_function
import sys
import node_control


nc = node_control.node_control.NodeControl(-1, 'redishost')
nc.log_service_in_redis(__file__)
heartbeat = 60

# Make udp object
rcvr = node_control.send_receive.UdpSenderReceiver('receive')

try:
    while True:
        nc.r.set(nc.status_scriptname, "alive", ex=heartbeat)
        # Receive data continuously from the server (Arduino in this case)
        print("Receiving data:  ",rcvr)
        data, addr = rcvr.client_socket.recvfrom(1024)
        data_dict = node_control.status_node.status_node(data, addr)
        nc.r.hmset("{}{}".format(nc.NC_STAT, data_dict['node_ID']), data_dict)
        print(data_dict)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
