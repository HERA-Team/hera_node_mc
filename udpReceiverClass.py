import numpy
import threading
import time
import datetime
import struct
import redis
import socket
import sys
import smtplib

# Define IP address of the Redis server host machine
serverAddress = '10.1.1.1'

# Define rcvPort for socket creation
rcvPort = 8889


unpacked_mac = ["" for x in range(6)]

class UdpReceiver():
        """
        This class receives UDP packets from all active Arduinos containing sensor data and misc node metadata.
        Class goes into an infinite loop when receiveUDP method is called.
        """

        def __init__(self):

                # define socket address for binding; necessary for receiving data from Arduino 
                self.localSocket = (serverAddress, rcvPort)


                # Instantiate redis object connected to redis server running on localhost
                self.r = redis.StrictRedis()

                # Create a UDP socket
                try:
                        self.client_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        # Set these options so multiple processes can connect to this socket
                        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        print('Socket created')
                except socket.error, msg:
                        print('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1]))
                        sys.exit()


                # Bind socket to local host and port
                try:
                        self.client_socket.bind(self.localSocket)
                        print('Bound socket')
                except socket.error , msg:
                        print('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
                        sys.exit()

                # Make a server object to send alerts by email
                #server = smtplib.SMTP('smtp.gmail.com', 587)
                #server.login('heranodemc@gmail.com','monitorcontrol')
                #server.ehlo()
                #server.starttls()





        def receiveUDP(self):
                """
                Captures UDP packets sent by Arduino an pushes to Redis. 
                Sends poke signal to Arduino every 3 seconds.
                Checks for control flags in Redis database set by the nodeControlClass.
                """
                
                # Start the timer to send poke command to the Arduino

                # Loop to grap UDP packets from Arduino and push to Redis
                while True:
                     
                    
                        # Receive data continuously from the server (Arduino in this case)
                        data, addr =  self.client_socket.recvfrom(1024)
                        # Arduino sends a Struct via UDP so unpacking is needed 
                        # struct.unpack returns a tuple with one element
                        # Each struct element is 4 Bytes (c floats are packed as 4 byte strings)
                        
                        unpacked_nodeID = struct.unpack('=i',data[0:4])
                        unpacked_cpu_uptime = struct.unpack('=i',data[4:8])
                        unpacked_mcptemp_top = struct.unpack('=f',data[8:12])
                        unpacked_mcptemp_mid = struct.unpack('=f',data[12:16])
                        unpacked_htutemp = struct.unpack('=f', data[16:20])
                        unpacked_htuhumid = struct.unpack('=f', data[20:24])
                        unpacked_snap_relay = struct.unpack('=?',data[24])
                        unpacked_fem = struct.unpack('=?',data[25])
                        unpacked_pam = struct.unpack('=?',data[26])
                        unpacked_snapv2_0_1 = struct.unpack('=?',data[27])
                        unpacked_snapv2_2_3 = struct.unpack('=?',data[28])
                        unpacked_serialLb = struct.unpack('=s',data[29])
                        unpacked_serialHb = struct.unpack('=s',data[30])
                        unpacked_mac[0]=hex(ord(struct.unpack('=s',data[31])[0]))
                        unpacked_mac[1]=hex(ord(struct.unpack('=s',data[32])[0]))
                        unpacked_mac[2]=hex(ord(struct.unpack('=s',data[33])[0]))
                        unpacked_mac[3]=hex(ord(struct.unpack('=s',data[34])[0]))
                        unpacked_mac[4]=hex(ord(struct.unpack('=s',data[35])[0]))
                        unpacked_mac[5]=hex(ord(struct.unpack('=s',data[36])[0]))


                        node = int(unpacked_nodeID[0])
                         

                        self.r.hmset('status:node:%d'%node,
                        {'serial_Lbyte':hex(ord(unpacked_serialLb[0])),
                        'serial_Hbyte':hex(ord(unpacked_serialHb[0])),
                        'mac':unpacked_mac,
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





                        print(self.r.hgetall('status:node:%d'%node))





















