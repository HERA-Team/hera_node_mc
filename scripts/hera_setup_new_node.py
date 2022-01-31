#! /usr/bin/env python
import argparse
import os
import time
import socket
from node_control import hosts_ethers
from node_control import send_receive
from node_control.node_util import get_redis_client
import yaml


# These are dumped from hera_mc on October 27, 2020
RDmap = {'NCMP2': 'RD31', 'NCM02': 'RD46', 'NCM06': 'RD20', 'NCM10': 'RD43', 'NCM13': 'RD18',
         'NCM15': 'RD04', 'NCM03': 'RD42', 'NCM07': 'RD15', 'NCM11': 'RD11', 'NCM04': 'RD41',
         'NCM01': 'RD45', 'NCM16': 'RD07', 'NCM05': 'RD06', 'NCM08': 'RD19', 'NCM12': 'RD17',
         'NCM09': 'RD40', 'NCM21': 'RD05', 'NCM22': 'RD09', 'NCM14': 'RD13', 'NCM20': 'RD14',
         'NCM18': 'RD16', 'NCM17': 'RD47', 'NCM19': 'RD48', 'NCMP1': 'RD02'
         }

WRmap = {'NCMP2': 'WRA000028', 'NCM03': 'WRA000084', 'NCM06': 'WRA000093', 'NCM07': 'WRA000091',
         'NCM10': 'WRA000097', 'NCM11': 'WRA000079', 'NCM13': 'WRA000096', 'NCM15': 'WRA000085',
         'NCM04': 'WRA000087', 'NCM01': 'WRA000086', 'NCM16': 'WRA000090', 'NCM05': 'WRA000089',
         'NCM08': 'WRA000094', 'NCM12': 'WRA000080', 'NCM02': 'WRA000083', 'NCM09': 'WRA000006',
         'NCM18': 'WRA000101', 'NCM22': 'WRA000102', 'NCM20': 'WRC000151', 'NCM17': 'WRC000152',
         'NCM21': 'WRC000153', 'NCM19': 'WRC000154', 'NCMP1': 'WR-len4p0', 'NCM14': 'WRA000201',
         'NCM23': 'WRA000157', 'NCM24': 'WRA000099', 'NCM25': 'WRA000098',  # Matt's update 2/8/21
         'NCM26': 'WRA000088', 'NCM27': 'WRA000155', 'NCM28': 'WRA000156',  # "
         'NCM29': 'WRA000100', 'NCM30': 'WRA000158', 'NCM31': 'WRA000095'   # "
         }

ap = argparse.ArgumentParser()
ap.add_argument('node_num', help="Node number (int)", type=int)
ap.add_argument('ncm', help="Node-control-module (NCM) number (int)", type=int)
ap.add_argument('-s', '--snaps', help='csv-list of snaps, if supplied 4-ints no spaces'
                '(if None, will ignore SNAPs which is the default)',
                default=None)
ap.add_argument('--snap-rev', help="__Shouldn't need to change__  Rev letter of SNAP (csv-list).  "
                "If one supplied, it applies to all.", dest='snap_rev', default='C')
ap.add_argument('--actually-modify', dest='modify', action='store_true',
                help='Flag to actually rewrite hosts/ethers and restart dnsmasq '
                '(ignore for rfi machine)')
args = ap.parse_args()

hostname = socket.gethostname()


# Read files and get macs and ips
hosts = hosts_ethers.HostsEthers('/etc/hosts')
ethers = hosts_ethers.HostsEthers('/etc/ethers')

snaps = None
if args.snaps is not None and send_receive.is_snap_control_host(hostname):
    # Set up SNAPs
    _snp = [int(x) for x in args.snaps.split(',')]
    snap_rev = args.snap_rev.upper().split(",")
    if len(snap_rev) == 1:
        snap_rev = snap_rev * 4
    snaps = [{}, {}, {}, {}]
    for i in range(4):
        snaps[i]['node'] = 'heraNode{}Snap{}'.format(args.node_num, i)
        snaps[i]['sn'] = 'SNP{}{:06d}'.format(snap_rev[i], _snp[i])
        snaps[i]['mac'] = ethers.by_alias[snaps[i]['sn']]
        snaps[i]['ip'] = hosts.by_alias[snaps[i]['sn']]
        if args.modify:
            hosts.update_id(snaps[i]['ip'], '{}  {}'.format(snaps[i]['sn'], snaps[i]['node']))
        else:
            print("===SNAP===")
            print(yaml.dump(snaps))
if send_receive.is_node_control_host(hostname):
    from node_control.node_util import status_node
    status_node_keys = list(status_node(None, None).keys())
    rd = {}
    for key in status_node_keys:
        rd[key] = 0
    ncm = 'NCM{:02d}'.format(args.ncm)
    rd['node'] = 'heraNode{}'.format(args.node_num)
    rd['node_ID'] = args.node_num
    rd['timestamp'] = time.time()
    rd['ncm'] = ncm
    rd['sn'] = 'arduino{}'.format(int(RDmap[ncm][2:]))
    rd['mac'] = ethers.by_alias[rd['sn']]
    rd['ip'] = hosts.by_alias[rd['sn']]
    if args.modify:
        hosts.update_id(rd['ip'], '{}  {}'.format(rd['sn'], rd['node']))
    else:
        print("===ARDUINO===")
        print(yaml.dump(rd))

    # Set up white rabbit
    wr = {'node': 'heraNode{}wr'.format(args.node_num)}
    wr['sn'] = WRmap[ncm]
    wr['mac'] = ethers.by_alias[wr['sn']]
    wr['ip'] = hosts.by_alias[wr['sn']]
    if args.modify:
        hosts.update_id(wr['ip'], '{}  {}'.format(wr['sn'], wr['node']))
    else:
        print("===WHITE-RABBIT===")
        print(yaml.dump(wr))

    print("Updating redis")
    r = get_redis_client()
    rkey = 'status:node:{}'.format(int(args.node_num))
    r.hmset(rkey, rd)

# RFI testing machine, so want to write the current node info
if hostname == 'hera-mobile' or hostname.startswith('ral'):
    import datetime
    with open('CurrentNode.txt', 'w') as fp:
        print("{}".format(args.node_num), file=fp)
        print(datetime.datetime.now().isoformat(), file=fp)
        print("Node: {}".format(args.node_num), file=fp)
        print('NCM: {}'.format(args.ncm), file=fp)
        if snaps is not None:
            for i in range(4):
                print("SNAP: {}".format(snaps[i]['node']), file=fp)
                for k in ['sn', 'mac', 'ip']:
                    print("\t{}:  {}".format(k, snaps[i][k]), file=fp)
        print("Arduino: {}".format(rd['node']), file=fp)
        for k in ['sn', 'mac', 'ip']:
            print("\t{}: {}".format(k, rd[k]), file=fp)
        print("White Rabbit: {}".format(wr['node']), file=fp)
        for k in ['sn', 'mac', 'ip']:
            print("\t{}: {}".format(k, wr[k]), file=fp)

if hostname == 'hera-mobile':
    if __file__.startswith('/usr/local'):
        args.modify = True
        os.chmod('CurrentNode.txt', 0o666)

hosts.rewrite_file(check_only=not args.modify)
if args.modify:
    os.system('sudo /etc/init.d/dnsmasq stop')
    os.system('sudo rm /var/lib/misc/dnsmasq.leases')
    os.system('sudo /etc/init.d/dnsmasq start')
