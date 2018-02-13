import time
import argparse 
import redis
import udpSender
import sys

"""
This script pokes Arduino every 3 seconds to ensure Arduino's connectivity to the server.
It also checks the Redis Database flags set from the nodeControlClass and for commands and
sends those commands to the Arduino.
Takes in the IP address of the Arduino to poke as a string and the corresponding node ID as an int. 
"""

parser = argparse.ArgumentParser(description = 'This script continuously pokes an Arduinos inside the nodes specified by the node argument. It also checks for command flag change inside the Redis database that are set through the nodeControlClass.', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ip_addr', action = 'store', help = 'List of integer node IDs.')
args = parser.parse_args()

r = redis.StrictRedis('localhost')


s = udpSender.UdpSender(args.ip_addr)

# Sends poke signal to Arduino every second
try:
    while True:
        s.poke() 
        # Check if Redis flags were set through the nodeControlClass
        time.sleep(1)
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)













