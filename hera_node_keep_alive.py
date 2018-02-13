import time
import redis
import udpSender
import sys

"""
This script pokes Arduino every second to ensure Arduino's connectivity to the server.
It pokes only the nodes that have Redis status keys i.e. status:node:x where x is the node ID
set by the I2C digital I/O cards plugged into PCBs.  
"""
# Dictionary to hold UdpSender objects for each node.
s={}
nodes = []
i = 0
# Iterates through all keys that start with status: and gets their node IDs and Arduino IP addresses.
for key in r.scan_iter("status:*"):
        nodes.append(int(r.hget(key,'node_ID')))
        s['node%d'%nodes[i]] = udpSender.UdpSender(r.hget(key,'ip'))
        i += 1
# Sends poke signal to Arduinos inside nodes every second
try:
    while True:
        for node in nodes:
            print("Poking node %d"%node)
            s['node%d'%node].poke() 
            # Check if Redis flags were set through the nodeControlClass
            time.sleep(1)
except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)













