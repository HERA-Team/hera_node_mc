from node_control import hosts_ethers
from argparse import Namespace
import socket


class Check:
    def __init__(self, files='local'):
        self.hosts = {}
        self.ethers = {}
        if isinstance(files, str) and files == 'local':
            hostname = socket.gethostname()
            self.hosts[hostname] = hosts_ethers.HostsEthers('/etc/hosts')
            self.ethers[hostname] = hosts_ethers.HostsEthers('/etc/ethers')
        elif isinstance(files, str) and files == 'redis':
            import redis
            r = redis.Redis('redishost', decode_responses=True)
            self.hosts['node'] = hosts_ethers.HostsEthers(r.hget('check:hosts', 'hera-node-head'),
                                                          read_from_string=True)
            self.ethers['node'] = hosts_ethers.HostsEthers(r.hget('check:ethers', 'hera-node-head'),
                                                           read_from_string=True)
            self.hosts['snap'] = hosts_ethers.HostsEthers(r.hget('check:hosts', 'hera-snap-head'),
                                                          read_from_string=True)
            self.ethers['snap'] = hosts_ethers.HostsEthers(r.hget('check:ethers', 'hera-snap-head'),
                                                           read_from_string=True)
        else:  # I've downloaded local versions from node-head and snap-head
            # files name host_node, host_snap, ethers_node, ethers_snap
            for fn in files:
                if 'hosts' in fn:
                    hn = fn.split('_')[1]
                    self.hosts[hn] = hosts_ethers.HostsEthers(fn)
                elif 'ethers' in fn:
                    hn = fn.split('_')[1]
                    self.ethers[hn] = hosts_ethers.HostsEthers(fn)
        self.data = {}
        for i in range(30):
            key = f"N{i:02d}"
            self.data[key] = Namespace(arduino={}, white_rabbit={}, snap={})

    def parse_data(self):
        for key in self.data.keys():
            this_node = int(key[1:])
            for hfn in self.hosts.keys():
                for alias, ip in self.hosts[hfn].by_alias.items():
                    if alias == f"heraNode{this_node}":
                        self.data[key].arduino['ip'] = ip
                        for _x in self.hosts[hfn].by_id[ip]:
                            if _x.startswith('arduino'):
                                self.data[key].arduino['serial'] = _x
                                self.data[key].arduino['mac'] = self.ethers[hfn].by_alias[_x]
                                break
                    elif alias == f"heraNode{this_node}wr":
                        self.data[key].white_rabbit['ip'] = ip
                        for _x in self.hosts[hfn].by_id[ip]:
                            if _x.startswith('WR'):
                                self.data[key].white_rabbit['serial'] = _x
                                self.data[key].white_rabbit['mac'] = self.ethers[hfn].by_alias[_x]
                                break
                    elif f"heraNode{this_node}Snap" in alias:
                        sno = alias[-1]
                        self.data[key].snap[sno] = {'ip': ip}
                        for _x in self.hosts[hfn].by_id[ip]:
                            if _x.startswith('SNP'):
                                self.data[key].snap[sno]['serial'] = _x
                                self.data[key].snap[sno]['mac'] = self.ethers[hfn].by_alias[_x]

    def write_csv(self, filename='hosts_ethers.csv'):
        table_dict = {}
        table_data = []
        for node, data in self.data.items():
            table_data.append(7 * [node])
            table_dict[node] = {}
            for _e in ['serial', 'mac', 'ip']:
                row = ['hosts']
                table_dict[node][_e] = {}
                try:
                    val = data.arduino[_e]
                except KeyError:
                    val = '-'
                row.append(val)
                table_dict[node][_e]['arduino'] = val
                try:
                    val = data.white_rabbit[_e]
                except KeyError:
                    val = '-'
                row.append(val)
                table_dict[node][_e]['white_rabbit'] = val
                for sno in range(4):
                    try:
                        val = data.snap[str(sno)][_e]
                    except KeyError:
                        val = '-'
                    row.append(val)
                    table_dict[node][_e][f"snap{sno}"] = val
                table_data.append(row)
        if filename == 'return_only':
            return table_dict
        else:
            with open(filename, 'w') as fp:
                for row in table_data:
                    print(','.join(row), file=fp)
