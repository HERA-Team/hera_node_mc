'''
Simple script to poll WR-LEN endpoints by hostname and
write stats to redis
'''


import socket
import argparse
import redis
import time
import datetime
import os
from node_control import wr_len
from node_control import __version__

hostname = socket.gethostname()

parser = argparse.ArgumentParser(description='VUART shell for WR-LEN')
parser.add_argument('hosts', metavar='hosts', type=str, nargs='*',
                    help='WR hosts to poll. Default: heraNode{0..29}wr')
parser.add_argument('-t', dest='polltime', type=float, default=30,
                    help='Minimum time between polling cycles in seconds. Default: 30s')
r = redis.Redis('redishost')
args = parser.parse_args()

if len(args.hosts) == 0:
    hosts = ['heraNode%dwr' % x for x in range(30)]
else:
    hosts = args.hosts

r.hmset("version:%s:%s" % (__package__, os.path.basename(__file__)),
        {"version": __version__, "timestamp": datetime.datetime.now().isoformat()})

print('Begining WR-LEN status polling. Hosts are:')
print(hosts)
script_redis_key = "status:script:%s:%s" % (hostname, __file__)
wr_devices = {}
count = 0
while(True):
    r.set(script_redis_key, "alive", ex=60)
    start_time = time.time()
    count += 1
    for host in hosts:
        hash_key = 'status:wr:%s' % host
        if host not in wr_devices.keys():
            try:
                ip = socket.gethostbyname(host)
            except socket.gaierror:
                continue
            try:
                wr_devices[host] = wr_len.WrLen(host)
            except:  # noqa
                print("Error while connecting to %s" % host)
                continue
        print("%d: polling %s" % (count, host))
        try:
            stats = wr_devices[host].gather_keys(include_ver=False)
            r.hmset(hash_key, stats)
            # Delete old keys in case there is some weird stale stuff
            old_keys = [k for k in r.hkeys(hash_key) if k not in stats.keys()]
            if len(old_keys) > 0:
                r.hdel(hash_key, *old_keys)
        except:  # noqa
            print("Error while polling %s" % host)
    extra_wait = args.polltime - (time.time() - start_time)
    while extra_wait > 0:
        r.set(script_redis_key, "alive", ex=60)
        time.sleep(min(extra_wait, 60))
        extra_wait -= 60
