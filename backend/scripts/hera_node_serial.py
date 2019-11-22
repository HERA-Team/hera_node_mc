"""
This class is used for receiving debug messages on port 8890 from all the active Arduinos.
"""

import datetime
import socket
import sys

# Define PORT for socket creation
serialPort = 8890
serverAddress = '10.80.2.1'

# define socket address for binding; necessary for receiving data from Arduino 
localSocket = (serverAddress, serialPort)

# Create a UDP socket
try:
    client_socket= socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Set these options so multiple processes can connect to this socket
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('Socket created')
except socket.error as msg:
    print(('Failed to create socket. Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1])))
    sys.exit()

# Bind socket to local host and port
try:
    client_socket.bind(localSocket)
    print('Bound socket')
except socket.error as msg:
    print(('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]))
    sys.exit()

try:
    while True:
        # Receive data continuously from all active Arduinos
        data, addr =  client_socket.recvfrom(2048)
        print(data)
        print((datetime.datetime.now()))
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)
