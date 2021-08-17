#! /usr/bin/env python
"""
Puts the "minimum" node information into redis to allow node_mc to find it,
or removes its status from redis if remove-nodes flag is set.

Set node_ID under status:node:*
"""
from __future__ import print_function
import argparse
from node_control import node_control

ap = argparse.ArgumentParser()
ap.add_argument('command', help='Command to execute.',
                choices=['nodes', 'show', 'remove', 'checkdns', 'update'])
ap.add_argument('-n', '--nodes', help="List of node numbers to use. "
                "csv-list or 'all' (default is 'all')",
                default='all')
ap.add_argument('-k', '--key', help='If update, give status keyname', default=None)
ap.add_argument('-v', '--value', help='If update, give status key value', default=None)
args = ap.parse_args()
r = node_control.get_redis_client('redishost')
nc = node_control.NodeControl(args.nodes, count=2)

for node in nc.nodes_in_redis:
    print("Node {}".format(node))
    status_node = "status:node:{}".format(node)
    if args.command == 'show':
        for _a, _b in r.hgetall(status_node).items():
            print("\t{}: {}".format(_a, _b))
    elif args.command == 'remove':
        r.delete(status_node)
        print("\tRemoved status from redis.")
    elif args.command == 'checkdns':
        from node_control import hosts_ethers
        hosts = hosts_ethers.HostsEthers('/etc/hosts')
        ethers = hosts_ethers.HostsEthers('/etc/ethers')
        redis_ip = r.hget(status_node, 'ip')
        redis_mac = r.hget(status_node, 'mac')
        node_host = "heraNode{}".format(node)
        print("- Checking {} -> {}, {}".format(node_host, redis_ip, redis_mac))
        try:
            hosts_ip = hosts.by_alias[node_host]
            hpn = hosts.by_id[hosts_ip][0]
            if hosts_ip.strip() == redis_ip.strip():
                print("\thost/redis IP agrees at {}".format(redis_ip))
                print("\tassociated with {}".format(hpn))
            else:
                print("\thost/redis IPs disagree {}/{}".format(hosts_ip, redis_ip))
                print("\tthinks it is {} - not checking ethers".format(hpn))
                hpn = None
        except KeyError:
            print("\t{} not in hosts file.".format(node_host))
        if hpn is not None:
            try:
                ethers_mac = ethers.by_alias[hpn]
                if ethers_mac.strip() == redis_mac.strip():
                    print("\tethers/redis mac agrees at {}".format(redis_mac))
                else:
                    print("\tethers/redis macs disagree {}/{}".format(ethers_mac, redis_mac))
            except KeyError:
                print("\t{} not in ethers.".format(hpn))

    elif args.command == 'update':
        if args.key is None or args.value is None:
            print("Need key value.")
        if len(nc.nodes_in_redis) > 1:
            print("For update, please specify just one valid node.")
            r.hset(status_node, args.key, args.value)
