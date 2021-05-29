#! /usr/bin/env python
from __future__ import print_function
from node_control.node_control import get_redis_client

r = get_redis_client()

expected_services = {'hera_node_keep_alive': {'status': [], 'version': []},
                     'hera_node_receiver': {'status': [], 'version': []}}

for key in r.keys():
    dkey = key.decode()
    if dkey.startswith('status:script'):
        for this_service in expected_services.keys():
            if this_service in dkey:
                expected_services[this_service]['status'] = [dkey, r.get(key)]
                break
        else:
            print("Other service")
            print('\t', dkey, r.get(key))
    elif dkey.startswith('version'):
        for this_service in expected_services.keys():
            if this_service in dkey:
                expected_services[this_service]['version'] = [dkey, r.hgetall(key)]
                break
        else:
            print("Other service")
            print('\t', dkey, r.hgetall(key))

for this_service, stat in expected_services.items():
    print(this_service)
    if len(stat['version']):
        print('\ttimestamp: ', stat['version'][1]['timestamp'])
        print('\tversion: ', stat['version'][1]['version'])
    else:
        print('\tversion: N/A')
    if len(stat['status']):
        print('\tstatus: ', stat['status'][1])
    else:
        print('\tstatus: not alive')
