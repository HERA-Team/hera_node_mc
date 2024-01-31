#! /usr/bin/env python
import argparse
import os
import socket
from node_control import hosts_ethers
from node_control import send_receive
from node_control.node_util import get_redis_client
import yaml
from hera_cm import cm_gsheet

ncm_info = cm_gsheet.SheetData()
ncm_info.load_ncm()

ap = argparse.ArgumentParser()
ap.add_argument('node_num', help="Node number (int)", type=int)
ap.add_argument('ncm', help="Node-control-module (NCM) number (int)", type=int)
ap.add_argument('-s', '--snaps', help='csv-list of snaps, if supplied 4-ints no spaces'
                '(if None, will ignore SNAPs which is the default)',
                default=None)
ap.add_argument('--snap-rev', help="__Shouldn't need to change__  Rev letter of SNAP (csv-list).  "
                "If one supplied, it applies to all.", dest='snap_rev', default='C')
ap.add_argument('--modify-files', dest='modify', action='store_true',
                help='Flag to actually rewrite hosts/ethers (ignore for rfi machine)')
ap.add_argument('--reset-dns', dest='reset_dnsmasq', action='store_true',
                help='Flag to reset dnsmasq server')
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
    rd['timestamp'] = -1
    rd['ncm'] = ncm
    rd['sn'] = ncm_info.ncm[ncm].rd
    rd['mac'] = ethers.by_alias[rd['sn']]
    rd['ip'] = hosts.by_alias[rd['sn']]
    if args.modify:
        hosts.update_id(rd['ip'], '{}  {}'.format(rd['sn'], rd['node']))
    else:
        print("===ARDUINO===")
        print(yaml.dump(rd))

    # Set up white rabbit
    wr = {'node': 'heraNode{}wr'.format(args.node_num)}
    wr['sn'] = ncm_info.ncm[ncm].rd
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
if args.reset_dnsmasq:
    os.system('sudo /etc/init.d/dnsmasq stop')
    os.system('sudo rm /var/lib/misc/dnsmasq.leases')
    os.system('sudo /etc/init.d/dnsmasq start')
    # os.system('pkill -HUP dnsmasq')  # Will re-read the 
