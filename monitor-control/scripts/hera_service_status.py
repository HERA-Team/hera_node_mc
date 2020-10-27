#! /usr/bin/env python
import redis

connection_pool = redis.ConnectionPool(host='redishost', decode_responses=True)
r = redis.StrictRedis(connection_pool=connection_pool, charset='utf-8')

for key in r.keys():
    if key.decode().startswith('status:script'):
        print(key.decode(), r.get(key))
    if key.decode().startswith('version'):
        print(key.decode(), r.hgetall(key))
