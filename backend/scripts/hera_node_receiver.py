"""
Receives UDP packets from all active Arduinos containing sensor data and status information and 
pushes it up to Redis with status:node:x hash key. 
"""

from __future__ import print_function

import datetime
import struct
import redis
import socket
import sys

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
    client_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set these options so multiple processes can connect to this socket
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Socket created", file=sys.stderr)
except socket.error, msg:
    print('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1]), file=sys.stderr)
    sys.exit()

# Bind socket to local host and port
try:
    client_socket.bind(localSocket)
    print('Bound socket', file=sys.stderr)
except socket.error , msg:
    print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1], file=sys.stderr)
    sys.exit()

try:
    while True:
        # Receive data continuously from the server (Arduino in this case)
        data, addr =  client_socket.recvfrom(1024)
        # Arduino sends a Struct via UDP so unpacking is needed 
        # struct.unpack returns a tuple with one element
        unpacked_cpu_uptime = struct.unpack('=L',data[0:4])
        unpacked_mcptemp_top = struct.unpack('=f',data[4:8])
        unpacked_mcptemp_mid = struct.unpack('=f',data[8:12])
        unpacked_mcptemp_bot = struct.unpack('=f',data[12:16])
        unpacked_htutemp = struct.unpack('=f',data[16:20])
        unpacked_htuhumid = struct.unpack('=f',data[20:24])
        unpacked_snap_relay = struct.unpack('=?',data[24])
        unpacked_fem = struct.unpack('=?',data[25])
        unpacked_pam = struct.unpack('=?',data[26])
        unpacked_snapv2_0 = struct.unpack('=?',data[27])
        unpacked_snapv2_1 = struct.unpack('=?',data[28])
        unpacked_snapv2_2 = struct.unpack('=?',data[29])
        unpacked_snapv2_3 = struct.unpack('=?',data[30])
        unpacked_mac[0]=hex(ord(struct.unpack('=s',data[31])[0]))
        unpacked_mac[1]=hex(ord(struct.unpack('=s',data[32])[0]))
#        print(unpacked_cpu_uptime)
#        print(unpacked_mcptemp_top)
#        print(unpacked_mcptemp_mid)
#        print(unpacked_mcptemp_bot)
#        print(unpacked_htutemp)
#        print(unpacked_htuhumid)
#        print(unpacked_snap_relay)
#        print(unpacked_fem)
#        print(unpacked_pam)
#        print(unpacked_snapv2_0)
#        print(unpacked_snapv2_1)
#        print(unpacked_snapv2_2)
#        print(unpacked_snapv2_3)
#        print(unpacked_mac[0])
#        print(unpacked_mac[1])
        unpacked_mac[2]=hex(ord(struct.unpack('=s',data[33])[0]))
        unpacked_mac[3]=hex(ord(struct.unpack('=s',data[34])[0]))
        unpacked_mac[4]=hex(ord(struct.unpack('=s',data[35])[0]))
        unpacked_mac[5]=hex(ord(struct.unpack('=s',data[36])[0]))
        unpacked_nodeID = struct.unpack('=B',data[37])
        unpacked_nodeID_metadata = struct.unpack('=B',data[38])
        
        node = unpacked_nodeID[0]
        mac_str = ':'.join((unpacked_mac[i][2:]).zfill(2) for i in range(len(unpacked_mac))) 
        r.hmset('status:node:%d'%node,
        {'mac':mac_str,
        'ip':addr[0],
        'node_ID':node,
        'node_ID_metadata':unpacked_nodeID_metadata[0],
        'temp_top':round(unpacked_mcptemp_top[0],2),
        'temp_mid':round(unpacked_mcptemp_mid[0],2),
        'temp_bot':round(unpacked_mcptemp_bot[0],2),
        'temp_humid':round(unpacked_htutemp[0],2),
        'humid':round(unpacked_htuhumid[0],2),
        'power_snap_relay': int(unpacked_snap_relay[0]),
        'power_fem': int(unpacked_fem[0]),
        'power_pam': int(unpacked_pam[0]),
        'power_snap_0': int(unpacked_snapv2_0[0]),
        'power_snap_1': int(unpacked_snapv2_1[0]),
        'power_snap_2': int(unpacked_snapv2_2[0]),
        'power_snap_3': int(unpacked_snapv2_3[0]),
        'cpu_uptime_ms': unpacked_cpu_uptime[0],
        'timestamp':datetime.datetime.now()})

        #print(r.hgetall('status:node:%d'%node))

except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)
