#! /usr/bin/env python
"""
Receives UDP packets from all active Arduinos containing sensor data and status
information and pushes it up to Redis with status:node:x hash key.
"""
from __future__ import print_function
import datetime
import struct
import redis
import socket
import sys
import os
from nodeControl import __version__, __package__


def noneify(v, noneval=-99.0):
    """
    Return None if v==noneval. Else return v.
    """
    if v == noneval:
        return 'None'
    else:
        return v


hostname = socket.gethostname()
script_redis_key = "status:script:{}:{}".format(hostname, __file__)

heartbeat = 60

# Define rcvPort for socket creation
rcvPort = 8889
serverAddress = '0.0.0.0'
redisAddress = 'redishost'
redisPort = 6379
# define socket for binding; necessary for receiving data from Arduino
localSocket = (serverAddress, rcvPort)

unpacked_mac = ["" for x in range(6)]

# Instantiate redis object connected to redis server running on localhost
r = redis.StrictRedis(host=redisAddress, port=redisPort)


# Create a UDP socket
try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set these options so multiple processes can connect to this socket
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created", file=sys.stderr)
except socket.error as msg:
    print('Failed to create socket. Error Code : {}  Message {}'.format(msg[0], msg[1]),
          file=sys.stderr)
    sys.exit()

# Bind socket to local host and port
try:
    client_socket.bind(localSocket)
    print('Bound socket', file=sys.stderr)
except socket.error as msg:
    print('Bind failed. Error Code : {}  Message {}'.format(msg[0], msg[1]), file=sys.stderr)
    sys.exit()

try:
    while True:
        r.set(script_redis_key, "alive", ex=heartbeat)
        # Receive data continuously from the server (Arduino in this case)
        data, addr = client_socket.recvfrom(1024)
        # Arduino sends a Struct via UDP so unpacking is needed
        # struct.unpack returns a tuple with one element
        unpacked_cpu_uptime = struct.unpack('=L', data[0:4])[0]
        unpacked_mcptemp_top = noneify(round(struct.unpack('=f', data[4:8])[0], 2))
        unpacked_mcptemp_mid = noneify(round(struct.unpack('=f', data[8:12])[0], 2))
        unpacked_mcptemp_bot = noneify(round(struct.unpack('=f', data[12:16])[0], 2))
        unpacked_htutemp = noneify(round(struct.unpack('=f', data[16:20])[0], 2))
        unpacked_htuhumid = noneify(round(struct.unpack('=f', data[20:24])[0], 2))
        unpacked_snap_relay = int(struct.unpack('=?', data[24:25])[0])
        unpacked_fem = int(struct.unpack('=?', data[25:26])[0])
        unpacked_pam = int(struct.unpack('=?', data[26:27])[0])
        unpacked_snapv2_0 = int(struct.unpack('=?', data[27:28])[0])
        unpacked_snapv2_1 = int(struct.unpack('=?', data[28:29])[0])
        unpacked_snapv2_2 = int(struct.unpack('=?', data[29:30])[0])
        unpacked_snapv2_3 = int(struct.unpack('=?', data[30:31])[0])
        unpacked_mac[0] = hex(ord(struct.unpack('=s', data[31:32])[0]))
        unpacked_mac[1] = hex(ord(struct.unpack('=s', data[32:33])[0]))
        unpacked_mac[2] = hex(ord(struct.unpack('=s', data[33:34])[0]))
        unpacked_mac[3] = hex(ord(struct.unpack('=s', data[34:35])[0]))
        unpacked_mac[4] = hex(ord(struct.unpack('=s', data[35:36])[0]))
        unpacked_mac[5] = hex(ord(struct.unpack('=s', data[36:37])[0]))
        unpacked_nodeID = struct.unpack('=B', data[37:38])
        unpacked_nodeID_metadata = struct.unpack('=B', data[38:39])[0]

        node = unpacked_nodeID[0]
        mac_str = ':'.join((unpacked_mac[i][2:]).zfill(2) for i in range(len(unpacked_mac)))
        data_dict = {'mac': mac_str,
                     'ip': addr[0],
                     'node_ID': node,
                     'node_ID_metadata': unpacked_nodeID_metadata,
                     'temp_top': unpacked_mcptemp_top,
                     'temp_mid': unpacked_mcptemp_mid,
                     'temp_bot': unpacked_mcptemp_bot,
                     'temp_humid': unpacked_htutemp,
                     'humid': unpacked_htuhumid,
                     'power_snap_relay': unpacked_snap_relay,
                     'power_fem': unpacked_fem,
                     'power_pam': unpacked_pam,
                     'power_snap_0': unpacked_snapv2_0,
                     'power_snap_1': unpacked_snapv2_1,
                     'power_snap_2': unpacked_snapv2_2,
                     'power_snap_3': unpacked_snapv2_3,
                     'cpu_uptime_ms': unpacked_cpu_uptime,
                     'timestamp': str(datetime.datetime.now()),
                     }
        r.hmset('status:node:{}'.format(node), data_dict)
        # Write the version of this software to redis
        r.hmset("version:{}:{}".format(__package__, os.path.basename(__file__)),
                {"version": __version__,
                 "timestamp": datetime.datetime.now().isoformat()})
except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
