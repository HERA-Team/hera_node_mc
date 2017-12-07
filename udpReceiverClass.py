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

# Define PORT for socket creation
PORT = 8889
sendPort = 8888


unpacked_mac = ["" for x in range(6)]

class UdpClient():
    """
    This class received UDP packets from Arduino containing sensor data and misc node metadata.
    Class goes into an infinite loop when receiveUDP method is called.

    """

    def __init__(self):

        # define socket address for binding; necessary for receiving data from Arduino 
        self.localSocket = (serverAddress, PORT)


        # Instantiate redis object connected to redis server running on serverAddress
        self.r = redis.StrictRedis(serverAddress)

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


    def __poke(self):

        print('Poking..')
        self.client_socket.sendto('poke',self.arduinoSocket) 
        t = threading.Timer(3,self.__poke)
        print("Timer Set.")
        t.daemon = True
        t.start()





    def receiveUDP(self, arduinoAddress):
        """
        Captures UDP packets sent by Arduino an pushes to Redis. 
        Sends poke signal to Arduino every 3 seconds.
        Checks for control flags in Redis database set by the nodeControlClass.
        """

        # define socket necessary for sending poke command to Arduino
        self.arduinoSocket = (arduinoAddress, sendPort)
        
        # Start the timer to send poke command to the Arduino
        self.__poke()

        # Loop to grap UDP packets from Arduino and push to Redis
        while True:
             
            
            # Receive data continuously from the server (Arduino in this case)
            data, addr =  self.client_socket.recvfrom(1024)

            # Arduino sends a Struct via UDP so unpacking is needed 
            # struct.unpack returns a tuple with one element
            # Each struct element is 4 Bytes (c floats are packed as 4 byte strings)

            unpacked_nodeID = struct.unpack('=f',data[0:4])
            unpacked_cpu_uptime = struct.unpack('=f',data[4:8])
            unpacked_mcptemp_top = struct.unpack('=f',data[8:12])
            unpacked_mcptemp_mid = struct.unpack('=f',data[12:16])
            unpacked_mcptemp_bot = struct.unpack('=f',data[16:20])
            unpacked_htutemp = struct.unpack('=f', data[20:24])
            unpacked_htuhumid = struct.unpack('=f', data[24:28])
            unpacked_snap_relay = struct.unpack('=?',data[28])
            unpacked_fem = struct.unpack('=?',data[29])
            unpacked_pam = struct.unpack('=?',data[30])
            unpacked_snapv2_0 = struct.unpack('=?',data[31])
            unpacked_snapv2_1 = struct.unpack('=?',data[32])
            unpacked_snapv2_2 = struct.unpack('=?',data[33])
            unpacked_snapv2_3 = struct.unpack('=?',data[34])
            unpacked_serialLb = struct.unpack('=s',data[35])
            unpacked_serialHb = struct.unpack('=s',data[36])
            unpacked_mac[0]=hex(ord(struct.unpack('=s',data[37])[0]))
            unpacked_mac[1]=hex(ord(struct.unpack('=s',data[38])[0]))
            unpacked_mac[2]=hex(ord(struct.unpack('=s',data[39])[0]))
            unpacked_mac[3]=hex(ord(struct.unpack('=s',data[40])[0]))
            unpacked_mac[4]=hex(ord(struct.unpack('=s',data[41])[0]))
            unpacked_mac[5]=hex(ord(struct.unpack('=s',data[42])[0]))


            node = int(unpacked_nodeID[0])
             
            # if (unpacked_mcptemp_top > 27 && unpacked_mcptemp_mid > 27 && unpacked_htutemp > 27):
               #server.send('heranodemc@gmail.com','recipientemail@gmail.com','The temperature values are approaching critical levels, shutdown sequence initiated') 
            # Set hashes in Redis composed of sensor temperature values

            self.r.hmset('status:node:%d'%node,
            {'serial_Lbyte':hex(ord(unpacked_serialLb[0])),
            'serial_Hbyte':hex(ord(unpacked_serialHb[0])),
            'mac':unpacked_mac,
            'temp_top':unpacked_mcptemp_top[0],
            'temp_mid':unpacked_mcptemp_mid[0],
            'temp_bot':unpacked_mcptemp_bot[0],
            'temp_humid':unpacked_htutemp[0],
            'humid':unpacked_htuhumid[0],
            'power_snap_relay': bin(unpacked_snap_relay[0]),
            'power_fem': bin(unpacked_fem[0]),
            'power_pam': bin(unpacked_pam[0]),
            'power_snapv2_0': bin(unpacked_snapv2_0[0]),
            'power_snapv2_1': bin(unpacked_snapv2_1[0]),
            'power_snapv2_2': bin(unpacked_snapv2_2[0]),
            'power_snapv2_3': bin(unpacked_snapv2_3[0]),
            'cpu_uptime_seconds': unpacked_cpu_uptime[0],
            'timestamp':datetime.datetime.now()})


            # Check if Redis flags were set through the nodeControlClass

            if ((self.r.hmget('status:node:%d'%node, 'power_snap_relay_ctrl')[0]) == 'True'):
                if ((self.r.hmget('status:node:%d'%node, 'power_snap_relay_cmd')[0]) == 'on'):
                    self.client_socket.sendto("snapRelay_on",self.arduinoSocket) 
                else: 
                    self.client_socket.sendto('snapRelay_off',self.arduinoSocket) 
                self.r.hmset('status:node:%d'%node, {'power_snap_relay_ctrl': False})
            
            if ((self.r.hmget('status:node:%d'%node, 'power_snapv2_0_ctrl')[0]) == 'True'):
                if (self.r.hmget('status:node:%d'%node, 'power_snapv2_0_cmd')[0] == 'on'):
                    self.client_socket.sendto('snapv2_0_on',self.arduinoSocket) 
                else:
                    self.client_socket.sendto('snapv2_0_off',self.arduinoSocket) 
                self.r.hset('status:node:%d'%node, 'power_snapv2_0_ctrl', False)

            if ((self.r.hmget('status:node:%d'%node, 'power_snapv2_1_ctrl')[0]) == 'True'):
                if (self.r.hmget('status:node:%d'%node, 'power_snapv2_1_cmd')[0] == 'on'):
                    self.client_socket.sendto('snapv2_1_on',self.arduinoSocket)
                else:
                    self.client_socket.sendto('snapv2_1_off',self.arduinoSocket)
                self.r.hset('status:node:%d'%node, 'power_snapv2_1_ctrl', False)

            if ((self.r.hmget('status:node:%d'%node, 'power_snapv2_2_ctrl')[0]) == 'True'):
                if (self.r.hmget('status:node:%d'%node, 'power_snapv2_2_cmd')[0] == 'on'):
                    self.client_socket.sendto('snapv2_2_on',self.arduinoSocket)
                else:
                    self.client_socket.sendto('snapv2_2_off',self.arduinoSocket)
                self.r.hset('status:node:%d'%node, 'power_snapv2_2_ctrl', False)

            if ((self.r.hmget('status:node:%d'%node, 'power_snapv2_3_ctrl')[0]) == 'True'):
                if (self.r.hmget('status:node:%d'%node, 'power_snapv2_3_cmd')[0] == 'on'):
                    self.client_socket.sendto('snapv2_3_on',self.arduinoSocket)
                else:
                    self.client_socket.sendto('snapv2_3_off',self.arduinoSocket)
                self.r.hset('status:node:%d'%node, 'power_snapv2_3_ctrl', False)



            if (self.r.hmget('status:node:%d'%node, 'power_fem_ctrl')[0] == 'True'):
                if (self.r.hmget('status:node:%d'%node, 'power_fem_cmd')[0] == 'on'):
                    self.client_socket.sendto('FEM_on',self.arduinoSocket) 
                else:
                    self.client_socket.sendto('FEM_off',self.arduinoSocket) 
                self.r.hset('status:node:%d'%node, 'power_fem_ctrl', False)

            if (self.r.hmget('status:node:%d'%node, 'power_pam_ctrl')[0] == 'True'):
                if (self.r.hmget('status:node:%d'%node, 'power_pam_cmd')[0] == 'on'):
                    self.client_socket.sendto('PAM_on',self.arduinoSocket) 
                else:
                    self.client_socket.sendto('PAM_off',self.arduinoSocket) 
                self.r.hset('status:node:%d'%node, 'power_pam_ctrl', False)




            print(self.r.hgetall('status:node:%d'%node))





















