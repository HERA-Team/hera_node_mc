"""
This class is used for sending UDP commands to Arduino directly.

Has ability to turn on/off PSU, FEM and PAM. Could also reset the Arduino so it restarts the bootloader. 
"""


import time
import datetime
import struct
import redis
import socket
import sys
import smtplib

# Define IP address of the Redis server host machine
serverAddress = '10.1.1.1'

# Define sendPort for socket creation
sendPort = 8888


class UdpSender():


        def __init__(self):

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


                # Make a server object to send alerts by email
                #server = smtplib.SMTP('smtp.gmail.com', 587)
                #server.login('heranodemc@gmail.com','monitorcontrol')
                #server.ehlo()
                #server.starttls()
        

        def reset(self, arduinoAddress):
                """
                Takes in the arduino IP address as a string and resets the bootloader.
                """
                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('reset', arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_snap_relay(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Turns the SNAP relay on/off, must be turned on first before gaining 
                control over individual SNAPs. 
                """
                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('snapRelay_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_fem(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Controls the power to FEM.
                """ 
                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('FEM_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_pam(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Controls the power to PAM.
                """ 
                
                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('PAM_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_snap_0(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Controls the power to SNAP 0.
                """ 

                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('snapv2_0_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_snap_1(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Controls the power to SNAP 1.
                """ 

                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('snapv2_1_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_snap_2(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Controls the power to SNAP 2.
                """ 

                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('snapv2_2_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

        def power_snap_3(self, arduinoAddress, command):
                """
                Takes in the arduino IP address string and a command "on"/"off".
                Controls the power to SNAP 3. 
                """ 

                # define arduino socket to send requests
                arduinoSocket = (arduinoAddress, sendPort)
                self.client_socket.sendto('snapv2_3_%s'%command, arduinoSocket)

                # Set delay before receiving more data
                time.sleep(2)

