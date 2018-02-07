import redis
import argparse 
import udpSender
import sys
import time

parser = argparse.ArgumentParser(description = 'This script continuously pokes an Arduino with the specified IP address. It also checks for command flag change inside the Redis database that are set through the nodeControlClass.',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node', metavar='node', type=int, nargs='+', help = 'List of node IDs to monitor for control flags')
args = parser.parse_args()

# Instantiate redis object connected to redis server running on serverAddress
r = redis.StrictRedis('localhost')
# Define a dict of udpSender objects to send commands to Arduinos inside the nodes specified by the node arguments
s = {}
for node in args.node:
    ip_addr = r.hget('status:node:%d'%node,'ip')
    s['node%d'%node] = udpSender.UdpSender(ip_addr) 

try:
    while True:
        for node in args.node:
            # print("Checking the %d node for flags"%node)
            if ((r.hget('status:node:%d'%node, 'power_snap_relay_ctrl_trig')) == 'True'):
                    print('Detected TRUE in power_snap_relay_ctrl_trig')
                    
                    if ((r.hget('status:node:%d'%node, 'power_snap_relay_cmd')) == 'on'):
                            s['node%d'%node].power_snap_relay('on') 
                    else: 
                            s['node%d'%node].power_snap_relay('off') 
                    r.hmset('status:node:%d'%node, {'power_snap_relay_ctrl_trig': False})
                    time.sleep(1)

            if ((r.hget('status:node:%d'%node, 'power_snap_0_1_ctrl_trig')) == 'True'):
                    if (r.hget('status:node:%d'%node, 'power_snap_0_1_cmd') == 'on'):
                            s['node%d'%node].power_snap_0_1('on')
                    else:
                            s['node%d'%node].power_snap_0_1('off')
                    r.hset('status:node:%d'%node, 'power_snap_0_1_ctrl_trig', False)
                    time.sleep(1)

            if ((r.hget('status:node:%d'%node, 'power_snap_2_3_ctrl_trig')) == 'True'):
                    if (r.hget('status:node:%d'%node, 'power_snap_2_3_cmd') == 'on'):
                            s['node%d'%node].power_snap_2_3('on')
                    else:
                            s['node%d'%node].power_snap_2_3('off')
                    r.hset('status:node:%d'%node, 'power_snap_2_3_ctrl_trig', False)
                    time.sleep(1)

            if (r.hget('status:node:%d'%node, 'power_fem_ctrl_trig') == 'True'):
                    if (r.hget('status:node:%d'%node, 'power_fem_cmd') == 'on'):
                            s['node%d'%node].power_fem('on')
                    else:
                            s["node%d"%node].power_fem('off')
                    r.hset('status:node:%d'%node, 'power_fem_ctrl_trig', False)
                    time.sleep(1)

            if (r.hget('status:node:%d'%node, 'power_pam_ctrl_trig') == 'True'):
                    if (r.hget('status:node:%d'%node, 'power_pam_cmd') == 'on'):
                            s["node%d"%node].power_pam('on')
                    else:
                            s["node%d"%node].power_pam('off')
                    r.hset('status:node:%d'%node, 'power_pam_ctrl_trig', False)
                    time.sleep(1)

            if (r.hget('status:node:%d'%node, 'reset') == 'True'):
                    s["node%d"%node].reset()
                    r.hset('status:node:%d'%node, 'reset', False)
                    time.sleep(1)

except KeyboardInterrupt:
    print("Interrupted")
    sys.exit(0)
    









