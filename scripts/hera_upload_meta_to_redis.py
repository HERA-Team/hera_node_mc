#!/usr/bin/env python

"""
Upload hosts/ethers/crontab files to redis.
"""

import redis
import argparse
import socket
import subprocess
import sys


parser = argparse.ArgumentParser(description='hosts/ethers file upload to redis',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-r', '--redishost', type=str, default='redishost',
                    help='Host servicing redis requests')
parser.add_argument('--expire', help="Set expire time in redis [3600 sec].", type=int, default=3600)

args = parser.parse_args()

r = redis.Redis(args.redishost, decode_responses=True)
hostname = socket.gethostname()
current_env = sys.executable.split('/')[-3]

crontab = subprocess.check_output(['crontab', '-l']).decode()
r.hset('check:crontab', f"{hostname}:{current_env}", crontab)
r.expire('check:crontab', args.expire)

daemon = subprocess.check_output(['systemctl']).decode()
r.hset('check:daemon', f"{hostname}:{current_env}", daemon)
r.expire('check:daemon', args.expire)

if hostname != 'qmaster':
    for cfile in ['/etc/hosts', '/etc/ethers']:
        ctype = f"check:{cfile.split('/')[-1]}"
        try:
            with open(cfile, 'r') as fh:
                config = fh.read()
                r.hset(ctype, hostname, config)
                r.expire(ctype, args.expire)
        except FileNotFoundError:
            continue
