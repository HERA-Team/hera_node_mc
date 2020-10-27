#! /usr/bin/env python
"""
Checks Redis for commands sent by the monitor-control user.
Makes sure commands are spaced out properly to prevent rapid power cycling and
turning everything on at once. Uses throttle:node:x flag to enforce a 2 second delay
between commands. Checks for command triggers inside the commands:status:node key.
"""

from __future__ import print_function
import redis
import argparse
from nodeControl import nodeControl
import time
import sys
import os
import datetime
import socket


hostname = socket.gethostname()
script_redis_key = "status:script:{}:{}".format(hostname, __file__)

parser = argparse.ArgumentParser(description='Script to watch redis for commands '
                                 'and send them on to nodes',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--cmd_check_sec', help="Time between checks for new commands",
                    type=float, default=0.05)
parser.add_argument('--cmd_time_sec', help="Time to wait between commands",
                    type=float, default=2.0)
parser.add_argument('--node_refresh_sec', help="Time between checks for new/changed nodes",
                    type=float, default=10.0)
parser.add_argument('--throttle', help="Time to wait to throttle each command check",
                    type=float, default=0.1)
parser.add_argument('--heartbeat', help="Time to keep alive flag", type=int, default=60)
args = parser.parse_args()

# Instantiate redis object connected to redis server running on serverAddress
r = redis.StrictRedis(host="redishost")

# Define a dict of udpSender objects to send commands to Arduinos.
# If nodes to check and throttle are specified, use those values.
# If not, use all the nodes that have Redis entries.
nodes = nodeControl.refresh_node_list({}, r)
last_node_refresh_time = time.time()
print("Using nodes {}:".format(list(nodes.keys())), file=sys.stderr)

# Check command keys for triggers and command sent, throttle those commands to
# not exceed the cmd_time_sec
try:
    while True:
        r.hmset("version:{}:{}".format(nodeControl.__package__, os.path.basename(__file__)), {
            "version": nodeControl.__version__, "timestamp": datetime.datetime.now().isoformat(),
        })
        r.set(script_redis_key, "alive", ex=args.heartbeat)

        for node_id, node in nodes.items():
            command_node = 'commands:node:{:d}'.format(node_id)
            throttle_node = 'throttle:node:{:d}'.format(node_id)
            if ((r.hget(command_node, 'power_snap_relay_ctrl_trig').decode()) == 'True'):
                last_command_sec = float(r.hget(throttle_node, 'last_command_sec').decode())
                while ((time.time() - last_command_sec) < args.cmd_time_sec):
                    # print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(args.throttle)
                # print("Sent!")
                if ((r.hget(command_node, 'power_snap_relay_cmd').decode()) == 'on'):
                    node.power_snap_relay('on')
                else:
                    node.power_snap_relay('off')
                r.hset(command_node, 'power_snap_relay_ctrl_trig', 'False')
                # reset the last command flag
                r.hset(throttle_node, 'last_command_sec', time.time())

            for inode in range(4):
                snap_trig = 'power_snap_{}_ctrl_trig'.format(inode)
                snap_cmd = 'power_snap_{}_cmd'.format(inode)
                if ((r.hget(command_node, snap_trig).decode()) == 'True'):
                    last_command_sec = float(r.hget(throttle_node, 'last_command_sec').decode())
                    while ((time.time() - last_command_sec) < args.cmd_time_sec):
                        # print('Command sent too soon, waiting 100ms and trying again...')
                        time.sleep(args.throttle)
                    # print("Sent!")
                    if (r.hget(command_node, snap_cmd).decode() == 'on'):
                        node.power_snap(inode, 'on')
                    else:
                        node.power_snap(inode, 'off')
                    r.hset(command_node, snap_trig, 'False')
                    r.hset(throttle_node, 'last_command_sec', time.time())

            if (r.hget(command_node, 'power_fem_ctrl_trig').decode() == 'True'):
                last_command_sec = float(r.hget(throttle_node, 'last_command_sec').decode())
                while ((time.time() - last_command_sec) < args.cmd_time_sec):
                    # print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(args.throttle)
                # print("Sent!")
                if (r.hget(command_node, 'power_fem_cmd').decode() == 'on'):
                    node.power_fem('on')
                else:
                    node.power_fem('off')
                r.hset(command_node, 'power_fem_ctrl_trig', 'False')
                r.hset(throttle_node, 'last_command_sec', time.time())

            if (r.hget(command_node, 'power_pam_ctrl_trig').decode() == 'True'):
                last_command_sec = float(r.hget(throttle_node, 'last_command_sec').decode())
                while ((time.time() - last_command_sec) < args.cmd_time_sec):
                    # print('Command sent too soon, waiting 100ms and trying again...')
                    time.sleep(args.throttle)
                # print("Sent!")
                if (r.hget(command_node, 'power_pam_cmd').decode() == 'on'):
                    node.power_pam('on')
                else:
                    node.power_pam('off')
                r.hset(command_node, 'power_pam_ctrl_trig', 'False')
                r.hset(throttle_node, 'last_command_sec', time.time())

            if (r.hget(command_node, 'reset').decode() == 'True'):
                node.reset()
                r.hset(command_node, 'reset', 'False')

            if (time.time() > last_node_refresh_time + args.node_refresh_sec):
                nodes = nodeControl.refresh_node_list(nodes, r)
                last_node_refresh_time = time.time()
            time.sleep(args.cmd_check_sec)

except KeyboardInterrupt:
    print("Interrupted", file=sys.stderr)
    sys.exit(0)
