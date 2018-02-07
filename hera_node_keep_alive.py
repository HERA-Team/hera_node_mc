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
parser.add_argument('node', metavar = 'node', type=int, nargs='+', help = 'List of integer node IDs.')
args = parser.parse_args()

r = redis.StrictRedis('localhost')

for node in args.node:
    ip_addr = r.hget('status:node:%d'%node, 'ip')
    s['node%d'%d] = udpSender.UdpSender(ip_addr)

# Sends poke signal to Arduino every second
try:
    while True:
        for node in args.node:
            s['node%d'%node].poke() 
            # Check if Redis flags were set through the nodeControlClass
            time.sleep(1)
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)













