import numpy
import threading
import time
import datetime
import struct
import redis
import socket
import sys
import smtplib

"""
This script receives UDP packets from all active Arduinos containing sensor data and misc node metadata. Captures UDP packets sent by Arduinos and pushes to Redis based on node ID. 
"""

# Define rcvPort for socket creation
rcvPort = 8889

unpacked_mac = ["" for x in range(6)]

# define socket for binding; necessary for receiving data from Arduino 
localSocket = ("localhost", rcvPort)

# Instantiate redis object connected to redis server running on localhost
r = redis.StrictRedis("localhost")

# Create a UDP socket
try:
        client_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set these options so multiple processes can connect to this socket
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Socket created")
except socket.error, msg:
        print('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1]))
        sys.exit()


# Bind socket to local host and port
try:
        client_socket.bind(localSocket)
        print('Bound socket')
except socket.error , msg:
        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
        sys.exit()

# Make a server object to send alerts by email
#server = smtplib.SMTP('smtp.gmail.com', 587)
#server.login('heranodemc@gmail.com','monitorcontrol')
#server.ehlo()
#server.starttls()

try:
    while True:
                    
            # Receive data continuously from the server (Arduino in this case)
            data, addr =  client_socket.recvfrom(1024)
            # Arduino sends a Struct via UDP so unpacking is needed 
            # struct.unpack returns a tuple with one element
            # Each struct element is 4 Bytes (c floats are packed as 4 byte strings)
            unpacked_cpu_uptime = struct.unpack('=L',data[0:4])
            print(unpacked_cpu_uptime)
            unpacked_nodeID = struct.unpack('=h',data[4:6])
            print(unpacked_nodeID)
            unpacked_mcptemp_top = struct.unpack('=f',data[6:10])
            unpacked_mcptemp_mid = struct.unpack('=f',data[10:14])
            unpacked_htutemp = struct.unpack('=f',data[14:18])
            unpacked_htuhumid = struct.unpack('=f',data[18:22])
            unpacked_mac[0]=hex(ord(struct.unpack('=s',data[22])[0]))
            unpacked_mac[1]=hex(ord(struct.unpack('=s',data[23])[0]))
            unpacked_mac[2]=hex(ord(struct.unpack('=s',data[24])[0]))
            unpacked_mac[3]=hex(ord(struct.unpack('=s',data[25])[0]))
            unpacked_mac[4]=hex(ord(struct.unpack('=s',data[26])[0]))
            unpacked_mac[5]=hex(ord(struct.unpack('=s',data[27])[0]))
            unpacked_snap_relay = struct.unpack('=?',data[28])
            unpacked_fem = struct.unpack('=?',data[29])
            unpacked_pam = struct.unpack('=?',data[30])
            unpacked_snapv2_0_1 = struct.unpack('=?',data[31])
            unpacked_snapv2_2_3 = struct.unpack('=?',data[32])
            #print(unpacked_mcptemp_top)
            #print(unpacked_mcptemp_mid)
            #print(unpacked_htutemp)
            #print(unpacked_htuhumid)
            #print(unpacked_snap_relay)
            #print(unpacked_fem)
            #print(unpacked_pam)
            #print(unpacked_snapv2_0_1)
            #print(unpacked_snapv2_2_3)
            #print(unpacked_mac[0])
            #print(unpacked_mac[1])
            #print(unpacked_mac[2])
            #print(unpacked_mac[3])
            #print(unpacked_mac[4])
            #print(unpacked_mac[5])
            node = int(unpacked_nodeID[0])
            mac_str = ':'.join(unpacked_mac[i][2:] for i in range(len(unpacked_mac))) 

            r.hmset('status:node:%d'%node,
            {
            'mac':mac_str,
            'ip':addr[0],
            'node_ID':node,
            'temp_top':unpacked_mcptemp_top[0],
            'temp_mid':unpacked_mcptemp_mid[0],
            'temp_humid':unpacked_htutemp[0],
            'humid':unpacked_htuhumid[0],
            'power_snap_relay': int(unpacked_snap_relay[0]),
            'power_fem': int(unpacked_fem[0]),
            'power_pam': int(unpacked_pam[0]),
            'power_snap_0_1': int(unpacked_snapv2_0_1[0]),
            'power_snap_2_3': int(unpacked_snapv2_2_3[0]),
            'cpu_uptime_seconds': unpacked_cpu_uptime[0],
            'timestamp':datetime.datetime.now()})

            print(r.hgetall('status:node:%d'%node))

except KeyboardInterrupt:
            print('Interrupted')
            sys.exit(0)



















