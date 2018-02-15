import time
import datetime
import struct
import redis
import socket
import sys
import smtplib


# Define sendPort for socket creation
sendPort = 8888
# Define IP address of the Redis server host machine
serverAddress = '10.1.1.1'


class UdpSender():
    """
    This class is used for sending UDP commands to Arduino directly.
    Has ability to turn on/off FEM, PAM, relay and SNAPs. Could also reset the Arduino bootloader. 
    """

    def __init__(self,arduinoAddress):
        """
        Takes in the arduino IP address and sends commands directly, using udp.
        You have to be on the hera-digi-vm server to use it, otherwise use
        the nodeControl class to send commands via Redis.
        """
        
        self.arduinoAddress = arduinoAddress

        # define socket address for binding; necessary for receiving data from Arduino 
        self.localSocket = (serverAddress, sendPort)


        # Create a UDP socket
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Make sure that specify that we want to reuse the socket address
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

    def poke(self):
        """
        Sends poke commands to the Arduino. Used by hera_node_keep_alive script
        to send keep Arduinos from resetting. 
        """

        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('poke', arduinoSocket)

    def power_snap_relay(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP relay, must be turned on first before gaining 
        control over individual SNAPs. 
        """

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('snapRelay_%s'%command, arduinoSocket)

        # Set delay before receiving more data
        time.sleep(2)

    def power_fem(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to FEM.
        """ 

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('FEM_%s'%command, arduinoSocket)

        # Set delay before receiving more data
        time.sleep(2)

    def power_pam(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to PAM.
        """ 
        
        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('PAM_%s'%command, arduinoSocket)

        # Set delay before receiving more data
        time.sleep(2)

    def power_snap_0_1(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 0 and 1.
        """ 

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('snapv2_0_1_%s'%command, arduinoSocket)

        # Set delay before receiving more data
        time.sleep(2)

    def power_snap_2_3(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 2 and 3.
        """ 

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('snapv2_2_3_%s'%command, arduinoSocket)

        # Set delay before receiving more data
        time.sleep(2)

    def reset(self):
        """
        Resets the Arduino bootloader. 
        """
        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('reset', arduinoSocket)

        # Set delay before receiving more data
        time.sleep(2)

