"""
Pokes Arduinos to ensure Arduino's connectivity to the server.
It pokes either specified nodes with the -n argument or
the nodes that have Redis status keys i.e. status:node:x where x is the node ID
set by the I2C digital I/O cards plugged into PCBs.  
"""

import time
import redis
import udpSender
import sys
import argparse

parser = argparse.ArgumentParser(description = 'Takes in an optional argument of node array i.e."python hera_node_keep_alive.py  -n 0 4 \
will send poke commands to nodes with IDs 0 and 4.', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-n', dest='nodes', type=int, nargs='+', help = 'List of node IDs to poke.')
args = parser.parse_args()

r = redis.StrictRedis()

# Time to wait between pokes
poke_time_sec = 1

# Define a dict of udpSender objects to send commands to Arduinos.
# If nodes to check and throttle are specified, use those values.
# If not, poke all the nodes that have Redis status:node:x keys. 
s = {}
if args.nodes is None:
    i = 0
    nodes = []
    for key in r.scan_iter("status:*"):
        nodes.append(int(r.hget(key,'node_ID')))
        s['node%d'%nodes[i]] = udpSender.UdpSender(r.hget(key,'ip'))
        r.hset('status:node:%d'%nodes[i],'last_poke_sec',time.time())
        i += 1
    print("No node arguments were passed. Using nodes %s:"%nodes)
else:
    nodes = args.nodes
    for node in nodes:
        s['node%d'%node] = udpSender.UdpSender(r.hget('status:node:%d'%node,'ip'))
        r.hset('status:node:%d'%node,'last_poke_sec',time.time())
    print("Passed node arguments %s:"%nodes)

# Sends poke signal to Arduinos inside the nodes
try:
    while True:
        while ((time.time() - float(r.hget('status:node:%d'%nodes[0],'last_poke_sec'))) < poke_time_sec):
            print('Too soon to poke. Too young for tragedy.')
            time.sleep(.1)
        for node in nodes:
            print("Poking node %d"%node)
            s['node%d'%node].poke() 
            r.hset('status:node:%d'%node,'last_poke_sec',time.time())

except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)













