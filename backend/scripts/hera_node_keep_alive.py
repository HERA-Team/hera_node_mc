"""
Pokes Arduinos to ensure Arduino's connectivity to the server.
It pokes either specified nodes with the -n argument or
the nodes that have Redis status keys i.e. status:node:x where x is the node ID
set by the I2C digital I/O cards plugged into PCBs.  
"""



import time
import redis
import udpSender
import os
import sys
import argparse
import datetime
import socket

def refresh_node_list(curr_nodes, redis_conn):
    new_node_list = {}
    for key in redis_conn.scan_iter("status:node:*"):
        node_id = int(r.hget(key, 'node_ID'))
        ip = r.hget(key, 'ip')
        if node_id in list(curr_nodes.keys()):
            if ip == curr_nodes[node_id].arduinoAddress:
                new_node_list[node_id] = curr_nodes[node_id]
            else:
                new_node_list[node_id] = udpSender.UdpSender(ip)
                print("Updating IP address of node %d to %s" % (node_id, ip), file=sys.stderr)
        else:
            new_node_list[node_id] = udpSender.UdpSender(ip)
            print("Adding node %d with ip %s" % (node_id, ip), file=sys.stderr)
    return new_node_list

hostname = socket.gethostname()
script_redis_key = "status:script:%s:%s" % (hostname, __file__)

parser = argparse.ArgumentParser(description = 'Send keepalive pokes to all nodes with a status entry in redis', formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-r', dest='redishost', type=str, default='redishost', help = 'IP or hostname string of host running the monitor redis server.')
args = parser.parse_args()

r = redis.StrictRedis(host=args.redishost)

# Time to wait between pokes
poke_time_sec = 1

# Define a dict of udpSender objects to send commands to Arduinos.
# If nodes to check and throttle are specified, use those values.
# If not, poke all the nodes that have Redis status:node:x keys. 
nodes = refresh_node_list({}, r)
print("Using nodes %s:" % (list(nodes.keys())), file=sys.stderr)

# Sends poke signal to Arduinos inside the nodes
try:
    while True:
        r.set(script_redis_key, "alive", ex=60)
        start_poke_time = time.time()
        nodes = refresh_node_list(nodes, r)
        r.hmset("version:%s:%s" % (udpSender.__package__, os.path.basename(__file__)), {
            "version" : udpSender.__version__,
            "timestamp" : datetime.datetime.now().isoformat(),
        })
        for node_id, node in nodes.items():
            #print("Poking node %d"%node)
            node.poke()
            r.hset('throttle:node:%d'%node_id,'last_poke_sec',time.time())
        end_poke_time = time.time()
        time_to_poke = end_poke_time - start_poke_time
        if time_to_poke < poke_time_sec:
            time.sleep(poke_time_sec - time_to_poke)

except KeyboardInterrupt:
    print('Interrupted', file=sys.stderr)
    sys.exit(0)













