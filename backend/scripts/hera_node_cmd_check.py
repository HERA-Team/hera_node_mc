"""
Checks Redis for commands sent by the monitor-control user.
Makes sure commands are spaced out properly to prevent rapid power cycling and
turning everything on at once. Uses throttle:node:x flag to enforce a 2 second delay
between commands. Checks for command triggers inside the commands:status:node key.
"""


import redis
import argparse
import udpSender
import time
import sys
import os
import datetime
import socket


def refresh_node_list(curr_nodes, redis_conn):
    new_node_list = {}
    for key in redis_conn.scan_iter("status:node:*"):
        try:
            node_id = int(r.hget(key, 'node_ID').decode())
        except ValueError:
            continue
        ip = r.hget(key, 'ip').decode()
        if node_id in list(curr_nodes.keys()):
            if ip == curr_nodes[node_id].arduinoAddress:
                new_node_list[node_id] = curr_nodes[node_id]
            else:
                new_node_list[node_id] = udpSender.UdpSender(ip)
                print("Updating IP address of node %d to %s" % (node_id, ip), file=sys.stderr)
        else:
            new_node_list[node_id] = udpSender.UdpSender(ip)
            print("Adding node %d with ip %s" % (node_id, ip), file=sys.stderr)
            # If this is a new node, default all the command triggers to idle
            r.hset('commands:node:%d'%node_id, 'power_snap_relay_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'power_snap_0_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'power_snap_1_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'power_snap_2_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'power_snap_3_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'power_fem_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'power_pam_ctrl_trig', 'False')
            r.hset('commands:node:%d'%node_id, 'reset', 'False')
            r.hset('throttle:node:%d'%node_id, 'last_command_sec', '0')
    return new_node_list

hostname = socket.gethostname()
script_redis_key = "status:script:%s:%s" % (hostname, __file__)

parser = argparse.ArgumentParser(description = 'Script to watch redis for commands and send them on to nodes',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
args = parser.parse_args()

# Instantiate redis object connected to redis server running on serverAddress
r = redis.StrictRedis(host="redishost")

# Time between checks for new commands
cmd_check_sec = 0.05
# Time to wait between commands
cmd_time_sec = 2
# Time between checks for new / changed nodes
node_refresh_sec = 10

# Define a dict of udpSender objects to send commands to Arduinos.
# If nodes to check and throttle are specified, use those values.
# If not, use all the nodes that have Redis entries.
nodes = refresh_node_list({}, r)
last_node_refresh_time = time.time()
print("Using nodes %s:" % (list(nodes.keys())), file=sys.stderr)

# Check command keys for triggers and command sent, throttle those commands to
# not exceed the cmd_time_sec
try:
    while True:
        r.hmset("version:%s:%s" % (udpSender.__package__, os.path.basename(__file__)), {
            "version" : udpSender.__version__,
            "timestamp" : datetime.datetime.now().isoformat(),
        })
        r.set(script_redis_key, "alive", ex=60)

        for node_id, node in nodes.items():
            if ((r.hget('commands:node:%d'%node_id, 'power_snap_relay_ctrl_trig').decode()) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if ((r.hget('commands:node:%d'%node_id, 'power_snap_relay_cmd').decode()) == 'on'):
                    node.power_snap_relay('on')
                else:
                    node.power_snap_relay('off')
                r.hset('commands:node:%d'%node_id, 'power_snap_relay_ctrl_trig', 'False')
                # reset the last command flag
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if ((r.hget('commands:node:%d'%node_id, 'power_snap_0_ctrl_trig').decode()) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if (r.hget('commands:node:%d'%node_id, 'power_snap_0_cmd').decode() == 'on'):
                    node.power_snap_0('on')
                else:
                    node.power_snap_0('off')
                r.hset('commands:node:%d'%node_id, 'power_snap_0_ctrl_trig', 'False')
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if ((r.hget('commands:node:%d'%node_id, 'power_snap_1_ctrl_trig').decode()) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if (r.hget('commands:node:%d'%node_id, 'power_snap_1_cmd').decode() == 'on'):
                    node.power_snap_1('on')
                else:
                    node.power_snap_1('off')
                r.hset('commands:node:%d'%node_id, 'power_snap_1_ctrl_trig', 'False')
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if ((r.hget('commands:node:%d'%node_id, 'power_snap_2_ctrl_trig').decode()) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if (r.hget('commands:node:%d'%node_id, 'power_snap_2_cmd').decode() == 'on'):
                    node.power_snap_2('on')
                else:
                    node.power_snap_2('off')
                r.hset('commands:node:%d'%node_id, 'power_snap_2_ctrl_trig', 'False')
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if ((r.hget('commands:node:%d'%node_id, 'power_snap_3_ctrl_trig').decode()) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if (r.hget('commands:node:%d'%node_id, 'power_snap_3_cmd').decode() == 'on'):
                    node.power_snap_3('on')
                else:
                    node.power_snap_3('off')
                r.hset('commands:node:%d'%node_id, 'power_snap_3_ctrl_trig', 'False')
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if (r.hget('commands:node:%d'%node_id, 'power_fem_ctrl_trig').decode() == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if (r.hget('commands:node:%d'%node_id, 'power_fem_cmd').decode() == 'on'):
                    node.power_fem('on')
                else:
                    node.power_fem('off')
                r.hset('commands:node:%d'%node_id, 'power_fem_ctrl_trig', 'False')
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if (r.hget('commands:node:%d'%node_id, 'power_pam_ctrl_trig').decode() == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node_id,'last_command_sec').decode())) < cmd_time_sec):
                    #print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                #print("Sent!")
                if (r.hget('commands:node:%d'%node_id, 'power_pam_cmd').decode() == 'on'):
                    node.power_pam('on')
                else:
                    node.power_pam('off')
                r.hset('commands:node:%d'%node_id, 'power_pam_ctrl_trig', 'False')
                r.hset('throttle:node:%d'%node_id,'last_command_sec',time.time())

            if (r.hget('commands:node:%d'%node_id, 'reset').decode() == 'True'):
                node.reset()
                r.hset('commands:node:%d'%node_id, 'reset', 'False')

            if (time.time() > last_node_refresh_time + node_refresh_sec):
                nodes = refresh_node_list(nodes, r)
                last_node_refresh_time = time.time()
            time.sleep(cmd_check_sec)

except KeyboardInterrupt:
    print("Interrupted", file=sys.stderr)
    sys.exit(0)
