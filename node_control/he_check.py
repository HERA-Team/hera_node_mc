from node_control import hosts_ethers
from argparse import Namespace
import socket


class Check:
    def __init__(self):
        self.hosts = hosts_ethers.HostsEthers('/etc/hosts')
        self.ethers = hosts_ethers.HostsEthers('/etc/ethers')
        self.hostname = socket.gethostname()

    def parse_data(self):
        self.data = {}
        for i in range(30):
            key = f"N{i:02d}"
            self.data[key] = Namespace(arduino={}, white_rabbit={}, snap={})
            node_data = False
            for alias, ip in self.hosts.by_alias.items():
                if alias == f"heraNode{i}":
                    self.data[key].arduino['ip'] = ip
                    for _x in self.hosts.by_id[ip]:
                        if _x.startswith('arduino'):
                            node_data = True
                            self.data[key].arduino['serial'] = _x
                            self.data[key].arduino['mac'] = self.ethers.by_alias[_x]
                            break
                elif alias == f"heraNode{i}wr":
                    self.data[key].white_rabbit['ip'] = ip
                    for _x in self.hosts.by_id[ip]:
                        if _x.startswith('WR'):
                            node_data = True
                            self.data[key].white_rabbit['serial'] = _x
                            self.data[key].white_rabbit['mac'] = self.ethers.by_alias[_x]
                            break
                elif f"heraNode{i}Snap" in alias:
                    sno = alias[-1]
                    self.data[key].snap[sno] = {'ip': ip}
                    for _x in self.hosts.by_id['ip']:
                        if _x.startswith('SNP'):
                            node_data = True
                            self.data[key].snap[sno]['serial'] = _x
                            self.data[key].snap[sno]['mac'] = self.ethers.by_alias[_x]
            if not node_data:
                del self.dat[key]

    def write_csv(self, filename='hosts_ethers.csv'):
        with open(filename, 'w'):
            for node, data in self.data.items():
                print(','.join(7 * [node]))
                for _e in ['serial', 'mac', 'ip']:
                    row = [self.hostname]
                    try:
                        row.append(data.arduino[_e])
                    except KeyError:
                        row.append('')
                    try:
                        row.append(data.white_rabbit[_e]])
                    except KeyError:
                        row.append('')
                    try:
                        for sno in range(4):
                            row.append(data.snap[str(sno)][_e])
                    except KeyError:
                        row.append('')
                    print(','.join(row))
