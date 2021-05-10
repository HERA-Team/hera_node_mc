#! /usr/bin/env python
"""
Receives UDP packets from all active Arduinos containing sensor data and status
information and pushes it up to Redis with status:node:x hash key. <hera_node_receiver>
"""
from __future__ import print_function
import sys
import node_control as nc


node_ctrl = nc.node_control.NodeControl(None, 'redishost', count=None)
node_ctrl.log_service_in_redis(__file__)
heartbeat = 60

# Make udp object
rcvr = nc.send_receive.UdpSenderReceiver(nc.send_receive.serverAddress, sndrcv='receive')

try:
    while True:
        node_ctrl.r.set(node_ctrl.status_scriptname, "alive", ex=heartbeat)
        # Receive data continuously from the server (Arduino in this case)
        data, addr = rcvr.client_socket.recvfrom(1024)
        data_dict = nc.status_node.status_node(data, addr)
        node_ctrl.r.hmset("status:node:{}".format(data_dict['node_ID']), data_dict)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
