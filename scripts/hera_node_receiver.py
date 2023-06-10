#! /usr/bin/env python
"""
Receives UDP packets from all active Arduinos containing sensor data and status
information and pushes it up to Redis with status:node:x hash key. <hera_node_receiver>
"""
import sys
import node_control


nc = node_control.node_control.NodeControl('all', redisServer='redishost')
nc.log_service_in_redis(__file__)
heartbeat = 60


# Make udp object
rcvr = node_control.send_receive.UdpSenderReceiver('receive')

try:
    while True:
        nc.r.set(nc.status_scriptname, "alive", ex=heartbeat)
        # Receive data continuously from the server (Arduino in this case)
        data, addr = rcvr.client_socket.recvfrom(1024)
        data_dict = node_control.node_util.status_node(data, addr)
        nc.r.hmset(nc.redis_keygen('nc_stat', data_dict['node_ID']), data_dict)
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
