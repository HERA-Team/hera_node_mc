import redis
import argparse 
import udpSender
import time
import sys

parser = argparse.ArgumentParser(description = 'This script continuously pokes an Arduino with the specified IP address. It also checks for command flag change inside the Redis database that are set through the nodeControlClass.',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node', metavar='node', type=int, nargs='+', help = 'List of node IDs to monitor for control flags')
args = parser.parse_args()

# Instantiate redis object connected to redis server running on serverAddress
r = redis.StrictRedis('localhost')

cmd_time_sec = 2
# Define a dict of udpSender objects to send commands to Arduinos inside the nodes specified by the node arguments
s = {}
#for node in args.node:
#    ip_addr = r.hget('status:node:%d'%node,'ip')
#    s['node%d'%node] = udpSender.UdpSender(ip_addr) 
#    r.hset('throttle:node:%d'%node,'last_command_sec',time.time())
nodes = []
i = 0
for key in r.scan_iter("status:*"):
        nodes.append(int(r.hget(key,'node_ID')))
        s['node%d'%nodes[i]] = udpSender.UdpSender(r.hget(key,'ip'))
        r.hset('throttle:node:%d'%nodes[i],'last_command_sec',time.time())
        i += 1
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
    









