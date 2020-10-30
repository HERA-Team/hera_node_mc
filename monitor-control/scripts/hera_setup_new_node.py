#! /usr/bin/env python
from __future__ import print_function
import argparse
import os
import redis
import socket
from node_control import hosts_ethers


# These are dumped from hera_mc on October 27, 2020
RDmap = {'NCMP2': 'RD31', 'NCM02': 'RD46', 'NCM06': 'RD20', 'NCM10': 'RD43', 'NCM13': 'RD18',
         'NCM15': 'RD04', 'NCM03': 'RD42', 'NCM07': 'RD15', 'NCM11': 'RD11', 'NCM04': 'RD41',
         'NCM01': 'RD45', 'NCM16': 'RD07', 'NCM05': 'RD06', 'NCM08': 'RD19', 'NCM12': 'RD17',
         'NCM09': 'RD40', 'NCM21': 'RD05', 'NCM22': 'RD09', 'NCM14': 'RD13', 'NCM20': 'RD14',
         'NCM18': 'RD16', 'NCM17': 'RD47', 'NCM19': 'RD48', 'NCMP1': 'RD02'
         }

WRmap = {'NCMP2': 'WRA000028', 'NCM03': 'WRA000084', 'NCM06': 'WRA000093', 'NCM07': 'WRA000091',
         'NCM10': 'WRA000097', 'NCM11': 'WRA000079', 'NCM13': 'WRA000096', 'NCM15': 'WRA000085',
         'NCM04': 'WR-unknown', 'NCM01': 'WRA000086', 'NCM16': 'WRA000090', 'NCM05': 'WRA000089',
         'NCM08': 'WRA000094', 'NCM12': 'WRA000080', 'NCM02': 'WRA000083', 'NCM09': 'WRA000006',
         'NCM18': 'WRA000101', 'NCM22': 'WRA000102', 'NCM20': 'WRC000151', 'NCM17': 'WRC000152',
         'NCM21': 'WRC000153', 'NCM19': 'WRC000154', 'NCMP1': 'WR-len4p0'
         }

ap = argparse.ArgumentParser()
ap.add_argument('node_num', help="Node number (int)", type=int)
ap.add_argument('ncm', help="Node-control-module (NCM) number (int)", type=int)
ap.add_argument('snap0', help="SNAP serial number (int)", type=int)
ap.add_argument('snap1', help="SNAP serial number (int)", type=int)
ap.add_argument('snap2', help="SNAP serial number (int)", type=int)
ap.add_argument('snap3', help="SNAP serial number (int)", type=int)
ap.add_argument('--snap_rev', help="__Shouldn't need to change__  Rev letter of SNAP (csv-list).  "
                "If one supplied, it applies to all.", default='C')
ap.add_argument('--dont-reset-dnsmasq', dest='reset_dnsmasq', help="Don't reset the dnsmasq",
                action='store_false')
args = ap.parse_args()

hostname = socket.gethostname()
if hostname == 'hera-mobile':  # RFI testing machine, so want to write the current node.
    with open('CurrentNode.txt', 'w') as fp:
        fp.write(str(args.node_num))

# Read files and get macs and ips
hosts = hosts_ethers.HostsEthers('/etc/hosts')
ethers = hosts_ethers.HostsEthers('/etc/ethers')

if hostname in ['hera-snap-head', 'hera-mobile']:
    # Set up SNAPs
    snap_rev = args.snap_rev.upper().split(",")
    if len(snap_rev) == 1:
        snap_rev = snap_rev * 4
    snaps = [{}, {}, {}, {}]
    for i in range(4):
        snaps[i]['node'] = 'heraNode{}Snap{}'.format(args.node_num, i)
        snaps[i]['sn'] = 'SNP{}{:06d}'.format(snap_rev[i], getattr(args, 'snap{}'.format(i)))
        snaps[i]['mac'] = ethers.by_alias[snaps[i]['sn']]
        snaps[i]['ip'] = hosts.by_alias[snaps[i]['sn']]
        hosts.update_id(snaps[i]['ip'], '{}\t{}'.format(snaps[i]['sn'], snaps[i]['node']))
if hostname in ['hera-node-head', 'hera-mobile']:
    ncm = 'NCM{:02d}'.format(args.ncm)
    # Set up arduino
    rd = {'node': 'heraNode{}'.format(args.node_num)}
    rd['sn'] = 'arduino{}'.format(RDmap[ncm][2:])
    rd['mac'] = ethers.by_alias[rd['sn']]
    rd['ip'] = hosts.by_alias[rd['sn']]
    hosts.update_id(rd['ip'], '{}\t{}'.format(rd['sn'], rd['node']))

    # Set up white rabbit
    wr = {'node': 'heraNode{}wr'.format(args.node_num)}
    wr['sn'] = 'wr{}'.format(WRmap[ncm][2:])
    wr['mac'] = ethers.by_alias[wr['sn']]
    wr['ip'] = hosts.by_alias[wr['sn']]
    hosts.update_id(wr['ip'], '{}\t{}'.format(wr['sn'], wr['node']))

    connection_pool = redis.ConnectionPool(host='redishost', decode_responses=True)
    r = redis.StrictRedis(connection_pool=connection_pool, charset='utf-8')
    rkey = 'status:node:{}'.format(int(args.node_num))
    r.hset(rkey, 'ip', rd['ip'])
    r.hset(rkey, 'mac', rd['mac'])
    r.hset(rkey, 'node_ID', args.node_num)

hosts.rewrite_file()
if args.reset_dnsmasq:
    os.system('sudo /etc/init.d/dnsmasq stop')
    os.system('sudo rm /var/lib/misc/dnsmasq.leases')
    os.system('sudo /etc/init.d/dnsmasq start')
