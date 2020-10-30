#! /usr/bin/env python
from __future__ import print_function
import argparse
import time
from node_control import node_control

parser = argparse.ArgumentParser(description='Turn on SNAP relay, SNAPs, FEM and PAM',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('command', help="Specify 'on', 'off'. "
                    "Also can: 'node_reset', 'redis_init', 'redis_enable', 'redis_disable'",
                    choices=['on', 'off', 'reset', 'redis_init', 'redis_enable', 'redis_disable'])
parser.add_argument('node', help="Specify the list of nodes (csv list of int) or 'all'", nargs='?',
                    default='all')
parser.add_argument('-r', '--snap-relay', dest='snap_relay', action='store_true',
                    help="Turn on/off the snap-relay "
                    "(redundant if turning on _any_ snap or off _all_ snaps in one call; "
                    "needed when turning off the last snap if done separately)")
parser.add_argument('-s', '--snaps', action='store_true', help='Turn on/off all the snaps')
parser.add_argument('-0', '--snap0', action='store_true', help='Turn on/off SNAP 0')
parser.add_argument('-1', '--snap1', action='store_true', help='Turn on/off SNAP 1')
parser.add_argument('-2', '--snap2', action='store_true', help='Turn on/off SNAP 2')
parser.add_argument('-3', '--snap3', action='store_true', help='Turn on/off SNAP 3')
parser.add_argument('-p', '--pam', action='store_true', help='Turn on/off the PAM')
parser.add_argument('-f', '--fem', action='store_true', help='Turn on/off the FEM')
parser.add_argument('--all', action='store_true', help='Turn on/off all snaps, pam and fem')
parser.add_argument('--serverAddress', help='Name or redis server', default='redishost')
parser.add_argument('--throttle', help='Throttle time in sec', type=float, default=0.5)
parser.add_argument('--wait', dest='wait_time_in_sec', help="Seconds to wait to check if"
                    "successful change (use 0 to disable check)", default=5, type=int)
args = parser.parse_args()

if args.node.lower() == 'all':
    nodes2use = list(range(30))
else:
    nodes2use = [int(x) for x in args.node.split(',')]

n = node_control.NodeControl(nodes2use, serverAddress=args.serverAddress, throttle=args.throttle)

if args.command == 'node_reset':
    print("Reset abruptly resets the arduino")
    n.reset()
elif args.command.startswith('redis'):
    print("Set 'command:node' in redis to enable/disable redis control and init")
    rcmd = args.command.split("_")[1].capitalize()
    if rcmd in ['Enable', 'Disable']:
        n.set_redis_control(rcmd)
    n.init_redis()
else:
    keystates = {}
    if args.all:
        args.snaps = True
        args.snap_relay = True
        args.pam = True
        args.fem = True

    snaps_to_set = []
    if args.snaps:
        snaps_to_set = [0, 1, 2, 3]
    else:
        for i in range(4):
            if getattr(args, 'snap{}'.format(i)):
                snaps_to_set.append(i)
    any_snap = len(snaps_to_set) > 0
    all_snap = len(snaps_to_set) == 4

    if args.command == 'on' and (args.snap_relay or any_snap):
        n.power_snap_relay('on')
        keystates['power_snap_relay'] = 'on'

    for snap_n in snaps_to_set:
        n.power_snap(snap_n, args.command)
        keystates['power_snap_{}'.format(snap_n)] = args.command

    if args.pam:
        n.power_pam(args.command)
        keystates['power_pam'] = args.command

    if args.fem:
        n.power_fem(args.command)
        keystates['power_fem'] = args.command

    if args.command == 'off' and (args.snap_relay or all_snap):
        n.power_snap_relay('off')
        keystates['power_snap_relay'] = 'off'

    if args.wait_time_in_sec > 0:
        time.sleep(args.wait_time_in_sec)
        stale_nodes, wrong_states = n.check_power_status(args.wait_time_in_sec*2, keystates)
        if len(stale_nodes):
            print("These nodes aren't updating:  {}".format(stale_nodes))
        for nd in nodes2use:
            if len(wrong_states[nd]):
                print("Command not successful:  Node {} -> {} {}"
                      .format(nd, wrong_states[nd], args.command))
