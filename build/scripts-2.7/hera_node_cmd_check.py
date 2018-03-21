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


parser = argparse.ArgumentParser(description = 'Takes in an optional argument of node array, ',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-n', dest='nodes', type=int, nargs='+', help = 'List of node IDs to monitor for control flags.')
args = parser.parse_args()

# Instantiate redis object connected to redis server running on serverAddress
r = redis.StrictRedis()

# Time to wait between commands 
cmd_time_sec = 2

# Define a dict of udpSender objects to send commands to Arduinos.
# If nodes to check and throttle are specified, use those values.
# If not, use all the nodes that have Redis entries. 
s = {}
if args.nodes is None:
    i = 0
    nodes = []
    for key in r.scan_iter("status:*"):
        nodes.append(int(r.hget(key,'node_ID')))
        s['node%d'%nodes[i]] = udpSender.UdpSender(r.hget(key,'ip'))
        r.hset('throttle:node:%d'%nodes[i],'last_command_sec',time.time())
        i += 1
    print("No node arguments were passed. Using nodes %s:"%nodes)
else:
    nodes = args.nodes
    for node in nodes:
        s['node%d'%node] = udpSender.UdpSender(r.hget('status:node:%d'%node,'ip'))
        r.hset('throttle:node:%d'%node,'last_command_sec',time.time())
    print("Passed node arguments %s:"%nodes)

# Check command keys for triggers and command sent, throttle those commands to
# not exceed the cmd_time_sec
try:
    while True:
        for node in nodes:
            if ((r.hget('commands:node:%d'%node, 'power_snap_relay_ctrl_trig')) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node,'last_command_sec'))) < cmd_time_sec):
                    print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                print("Sent!")
                if ((r.hget('commands:node:%d'%node, 'power_snap_relay_cmd')) == 'on'):
                    s['node%d'%node].power_snap_relay('on') 
                else: 
                    s['node%d'%node].power_snap_relay('off') 
                r.hset('commands:node:%d'%node, 'power_snap_relay_ctrl_trig', False)
                # reset the last command flag
                r.hset('throttle:node:%d'%node,'last_command_sec',time.time())
            
            if ((r.hget('commands:node:%d'%node, 'power_snap_0_1_ctrl_trig')) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node,'last_command_sec'))) < cmd_time_sec):
                    print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                print("Sent!")
                if (r.hget('commands:node:%d'%node, 'power_snap_0_1_cmd') == 'on'):
                    s['node%d'%node].power_snap_0_1('on')
                else:
                    s['node%d'%node].power_snap_0_1('off')
                r.hset('commands:node:%d'%node, 'power_snap_0_1_ctrl_trig', False)
                r.hset('throttle:node:%d'%node,'last_command_sec',time.time())

            if ((r.hget('commands:node:%d'%node, 'power_snap_2_3_ctrl_trig')) == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node,'last_command_sec'))) < cmd_time_sec):
                    print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                print("Sent!")
                if (r.hget('commands:node:%d'%node, 'power_snap_2_3_cmd') == 'on'):
                    s['node%d'%node].power_snap_2_3('on')
                else:
                    s['node%d'%node].power_snap_2_3('off')
                r.hset('commands:node:%d'%node, 'power_snap_2_3_ctrl_trig', False)
                r.hset('throttle:node:%d'%node,'last_command_sec',time.time())

            if (r.hget('commands:node:%d'%node, 'power_fem_ctrl_trig') == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node,'last_command_sec'))) < cmd_time_sec):
                    print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                print("Sent!")
                if (r.hget('commands:node:%d'%node, 'power_fem_cmd') == 'on'):
                    s['node%d'%node].power_fem('on')
                else:
                    s["node%d"%node].power_fem('off')
                r.hset('commands:node:%d'%node, 'power_fem_ctrl_trig', False)
                r.hset('throttle:node:%d'%node,'last_command_sec',time.time())

            if (r.hget('commands:node:%d'%node, 'power_pam_ctrl_trig') == 'True'):
                while ((time.time() - float(r.hget('throttle:node:%d'%node,'last_command_sec'))) < cmd_time_sec):
                    print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(.1)
                print("Sent!")
                if (r.hget('commands:node:%d'%node, 'power_pam_cmd') == 'on'):
                    s["node%d"%node].power_pam('on')
                else:
                    s["node%d"%node].power_pam('off')
                r.hset('commands:node:%d'%node, 'power_pam_ctrl_trig', False)
                r.hset('throttle:node:%d'%node,'last_command_sec',time.time())

            if (r.hget('commands:node:%d'%node, 'reset') == 'True'):
                s["node%d"%node].reset()
                r.hset('commands:node:%d'%node, 'reset', False)

except KeyboardInterrupt:
    print("Interrupted")
    sys.exit(0)
    









