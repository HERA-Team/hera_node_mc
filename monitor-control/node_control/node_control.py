from __future__ import print_function
import redis
import dateutil.parser
import json
import datetime
import time
from . import udp_sender, status_node


def str2bool(x):
    """
    Convert the string `x` to a boolean.
    :return: bool(x == '1')
    """
    return x == "1"


def stale_data(age, stale=10.0, show_warning=True):
    """
    Print warning if data are too stale.

    Parameters
    ----------
    age : timedelta, int, float or None
        Age in seconds or timedelta
    state : float
        Stale timeframe in seconds
    show_warning : bool
        Flag to actually show the warning.

    Returns
    -------
    True if stale, None if None else False
    """
    if age is None:
        if show_warning:
            print("***Warning: no age found.")
        return None
    if isinstance(age, datetime.timedelta):
        age = age.days*(24.0 * 3600.0) + age.seconds + age.microseconds/1E6
    if age > stale:
        if show_warning:
            print("***Warning:  data are {} seconds old".format(int(age)))
        return True
    return False


def get_redis_nodes(serverAddress='redishost', count=None):
    nc = NodeControl(None, serverAddress, count)
    return nc.nodes_in_redis


class NodeControl():
    """
    This class is used to control power to PAM, FEM, and SNAP boards and
    get node status information through a Redis database.

    It also provides a status for the White Rabbit

    Attributes
    ----------
    sr_stat : str
        status hash prefix for redis
    sr_cmd : str
        command hash prefix for redis
    """

    sr_stat = 'status:node:'
    sr_cmd = 'commands:node:'

    def __init__(self, nodes, serverAddress="redishost", count=None):
        """
        Create a NodeControl class instance to query/control nodes.

        Parameters
        ----------
        nodes : list of int or None
            ID numbers of the nodes with which this instance of NodeControl will interact.
            If None, it will check them all (0-29).
        serverAddress : str
            The hostname, or dotted quad IP address, of the machine running the node control and
            monitoring redis server
        count : int or None
            Number of status fields to make a node count as actually used.
            If None, reads from status_nodes

        Attributes
        ----------
        request_nodes : list
            List of requested nodes (supplied)
        r : redis class
            Redis class to use
        nodes_in_redis : list
            List of all request_nodes in redis (created and called)
        connected_nodes : list
            List of connected_nodes in nodes_in_redis (created)
        sc_node : str
            String to print connected nodes (created)
        status_node_keys : list
            List of the status:node keys
        """
        if nodes is None:
            self.request_nodes = list(range(30))
        else:
            self.request_nodes = nodes
        connection_pool = redis.ConnectionPool(host=serverAddress, decode_responses=True)
        self.r = redis.StrictRedis(connection_pool=connection_pool, charset='utf-8')
        self.nodes_in_redis = []
        self.get_nodes_in_redis(count)
        self.connected_nodes = []
        self.sc_node = ''
        self.status_node_keys = list(status_node.status_node(None, None).keys())

    def get_nodes_in_redis(self, count=None):
        """
        Get redis nodes list for those in request_nodes.

        Parameters
        ----------
        count : int or None
            Number of status fields to make a node count as actually used.
            If None, get from status_node_keys

        Attributes
        ----------
        nodes_in_redis : list
            List of all request_nodes in redis with >count status fields
        """
        if count is None:
            count = len(self.status_node_keys)
        for node in self.request_nodes:
            if len(self.r.hgetall(f"{self.sr_stat}{node}")) >= count:
                self.nodes_in_redis.append(node)

    def get_node_senders(self, throttle=0.1):
        """
        Get udp node class for requested nodes that are in redis.

        Every node in redis gets a sender class, differ by sender.node_is_connected flag.

        Attributes
        ----------
        senders : dict
            Sender classes keyed on node_id (int) - one for every nodes_in_redis
        connected_nodes : list
            List of all udp connected request_nodes
        """
        self.connected_nodes = []
        self.senders = {}
        for node in self.nodes_in_redis:
            hkey = f"{self.sr_stat}{node}"
            ip = self.r.hget(hkey, 'ip')
            self.senders[node] = udp_sender.UdpSender(ip, throttle=self.throttle)
            if self.senders[node].node_is_connected:
                self.connected_nodes.append(node)
                self.r.hset(hkey, 'udp_status', 'connected')
            else:
                self.r.hset(hkey, 'udp_status', 'not_connected')
        if len(self.connected_nodes) == 1:
            self.sc_node = f"Node {self.connected_nodes[0]}"
        elif len(self.connected_nodes) > 1:
            self.sc_node = f"Nodes {', '.join(self.connected_nodes)}"

    def _get_raw_node_hash(self, this_key):
        """
        Return the raw content of a node status hash in redis,
        via redis's `hgetall` call. Data are returned as a dictionary,
        where the keys are the redis hash fields (strings) and the
        values are the stored values (strings).

        :returns: Whatever key-value pairs exist for this node's hash
        """
        rawstat = {}
        for node in self.nodes_in_redis:
            nkey = this_key.replace('*', f'{node}')
            rawstat[node] = self.r.hgetall(nkey)
        return rawstat

    def get_sensors(self):
        """
        Get the current node sensor values.

        Returns a dict where `timestamp` is a python `datetime` object describing when the
        sensor values were last updated in redis, and `sensors` is a dictionary of sensor values.
        If a sensor value is not available (e.g. because it cannot be reached) it will be `None`

        Valid sensor keywords are:
            'temp_top' (float) : Temperature, in degrees C, reported by top node sensor.
            'temp_mid' (float) : Temperature, in degrees C, reported by middle node sensor.
            'temp_bot' (float) : Temperature, in degrees C, reported by bottom node sensor.
            'temp_humid' (float) : Temperature, in degrees C, reported by humidity sensor.
            'humid' (float) : Relative Humidity, in percent, reported by humidity sensor.
            'cpu_uptime_ms' (int) : Uptime of this node control module, in milliseconds
            'ip' (str) : IP address of node controller module, e.g. "10.1.1.123"
            'mac' (str) : MAC address of node controller module, e.g. "02:03:04:05:06:07"
        """
        conv_methods = {
            "temp_bot": float,
            "temp_mid": float,
            "temp_top": float,
            "temp_humid": float,
            "humid": float,
            "ip": str,
            "mac": str,
            "cpu_uptime_ms": int,
            "timestamp": dateutil.parser.parse
        }
        sensors = {}
        now = datetime.datetime.now()
        for node, stats in self._get_raw_node_hash(f"{self.sr_stat}*").items():
            sensors[node] = {'age': None}
            for key, convfunc in conv_methods.items():
                try:
                    sensors[node][key] = convfunc(stats[key])
                    if key == 'timestamp':
                        sensors[node]['age'] = now - sensors[node][key]
                except:  # noqa
                    sensors[node][key] = None
        return sensors

    def get_power_command_list(self):
        """
        Get the current node power commands.

        Returns a dict keyed on node and one of [time, part, command].

        Valid power command keys are:
            power_snap_relay_cmd
            power_snap_0_cmd
            power_snap_1_cmd
            power_snap_2_cmd
            power_snap_3_cmd
            power_fem_cmd
            power_pam_cmd
            reset
        Format of values for all is command|time(unix)
        """
        power = {}
        for node, statii in self._get_raw_node_hash(f"{self.sr_cmd}*").items():
            power[node] = {}
            for key in list(statii.keys()):
                if 'relay' in key:
                    this_key = ['snap_relay']
                elif 'snap' in key:
                    this_key = f"snap{key.split('_')[2]}"
                elif 'reset' in key:
                    this_key = key
                else:
                    this_key = key.split('_')[1]
                power[node][this_key] = statii[key].split('|')
        return power

    def get_power_status(self):
        """
        Get the current node power relay states.

        Returns a dict where `timestamp` is a python `datetime` object
        describing when the values were last updated in redis, and `statii` is a dictionary
        of booleans for the various power switches the node can control. For each entry in this
        dictionary, `True` indicates power is on, `False` indicates power is off.

        Valid power status keys are:
          'power_fem' (Power of Front-End modules)
          'power_pam' (Power of Post-amplifier modules)
          'power_snap_0' (Power of first SNAP)
          'power_snap_1' (Power of second SNAP)
          'power_snap_2' (Power of third SNAP)
          'power_snap_3' (Power of fourth SNAP)
          'power_snap_relay' (Power of master SNAP relay)
        """
        power = {}
        now = datetime.datetime.now()
        for node, statii in self._get_raw_node_hash(f"{self.sr_stat}*").items():
            power[node] = {'age': None}
            for key in list(statii.keys()):
                if key == 'timestamp':
                    power[node][key] = dateutil.parser.parse(statii["timestamp"])
                    power[node]['age'] = now - power[node][key]
                elif key.startswith("power"):
                    power[node][key] = str2bool(statii[key])
        return power

    def check_power_status(self, stale=10.0, keystates={}):
        """
        Checks the age of node status and returns stale ones.

        Parameters
        ----------
        stale : float
            Time in seconds for something to be considered stale.
        keystates : dict
            Dictionary of requests/command

        Attributes
        ----------
        stale_nodes : list
            List of nodes that came back stale.
        active_nodes : dict
            Active nodes with status
        wrong_states : dict
            Incorrect states relative to commanded in keystates
        """
        pwr = self.get_power_status()
        self.stale_nodes = []
        self.active_nodes = {}
        self.wrong_states = {}
        for node, status in pwr.items():
            self.wrong_states[node] = []
            if stale_data(status['age'], stale, False):
                self.stale_nodes.append(node)
            else:
                self.active_nodes[node] = status
                for key, cmd in keystates.items():
                    if status[key] != (cmd == 'on'):
                        self.wrong_states[node].append(key)

    def get_wr_status(self):
        """
        Get the current status of this node's White Rabbit endpoint (assumed to have hostname
        `heraNode<node-number>wr`.

        If no stats exist for this White Rabbit endpoint, returns `None`.

        Otherwise Returns a dict where `timestamp` is a python `datetime` object describing when
        the values were last updated in redis, and `statii` is a dictionary of status values.

        If a status value is not available it will be `None`

        Valid status keywords are:
            'board_info_str' (str)      : A raw string representing the WR-LEN's response to the
                                          `ver` command.  Relevant parts of this string are
                                          individually unpacked in other entries.
            'aliases' (list of strings) : Hostname aliases of this node's WR-LEN
            'ip' (str)                  : IP address of this node's WR-LEN
            'mode' (str)                : WR-LEN operating mode (eg. "WRC_SLAVE_WR0")
            'serial' (str)              : Canonical HERA hostname (~=serial number) of node's WR-LEN
            'temp' (float)              : WR-LEN temperature in degrees C
            'sw_build_date' (datetime)  : Build date of WR-LEN software
            'wr_gw_date' (datetime)     : WR-LEN gateware build date
            'wr_gw_version' (str)       : WR-LEN gateware version number
            'wr_gw_id' (str)            : WR-LEN gateware ID number
            'wr_build' (str)            : WR-LEN build git hash
            'wr_fru_custom' (str)   : Custom manufacturer tag'
            'wr_fru_device' (str)   : Manufacturer device name designation
            'wr_fru_fid' (datetime) : Manufacturer invoice(?) date
            'wr_fru_partnum' (str)  : Manufacturer part number
            'wr_fru_serial' (str)   : Manufacturer serial number
            'wr_fru_vendor' (str)   : Vendor name
            The following entries are prefixed `wr0` or `wr1` for WR-LEN ports 0 and 1,
            respectively.  Most values will only be not None for one of the two ports.
            'wr[0|1]_ad'    (int)  : ???
            'wr[0|1]_asym'  (int)  : Total link asymmetry (ps)
            'wr[0|1]_aux'   (int)  : ??? Manual phase adjustment (ps)
            'wr[0|1]_cko'   (int)  : Clock offset (ps)
            'wr[0|1]_crtt'  (int)  : Cable round-trip delay (ps)
            'wr[0|1]_dms'   (int)  : Master-Slave delay in (ps)
            'wr[0|1]_drxm'  (int)  : Master RX PHY delay (ps)
            'wr[0|1]_drxs'  (int)  : Slave RX PHY delay (ps)
            'wr[0|1]_dtxm'  (int)  : Master TX PHY delay (ps)
            'wr[0|1]_dtxs'  (int)  : Slave TX PHY delay (ps)
            'wr[0|1]_hd'    (int)  : ???
            'wr[0|1]_lnk'   (bool) : Link up state
            'wr[0|1]_lock'  (bool) : Timing lock state
            'wr[0|1]_md'    (int)  : ???
            'wr[0|1]_mu'    (int)  : Round-trip time (ps)
            'wr[0|1]_nsec'  (int)  : ???
            'wr[0|1]_rx'    (int)  : Number of packets received
            'wr[0|1]_setp'  (int)  : Phase setpoint (ps)
            'wr[0|1]_ss'    (str)  : Servo state
            'wr[0|1]_sv'    (int)  : ???
            'wr[0|1]_syncs' (str)  : Source of synchronization (either 'wr0' or 'wr1')
            'wr[0|1]_tx'    (int)  : Number of packets transmitted
            'wr[0|1]_ucnt'  (int)  : Update counter
            'wr[0|1]_sec'   (int)  : Current TAI time in seconds from UNIX epoch
        """
        conv_methods = {
            'board_info_str': str,
            'aliases': json.loads,
            'ip': str,
            'mode': str,
            'serial': str,
            'temp': float,
            'sw_build_date': dateutil.parser.parse,
            'wr_gw_date': lambda x: dateutil.parser.parse('20' + x),  # hack!
            'wr_gw_version': str,
            'wr_gw_id': str,
            'wr_build': str,
            'wr_fru_custom': str,
            'wr_fru_device': str,
            'wr_fru_fid': dateutil.parser.parse,
            'wr_fru_partnum': str,
            'wr_fru_serial': str,
            'wr_fru_vendor': str,
            '_ad': int,
            '_asym': int,
            '_aux': int,
            '_cko': int,
            '_crtt': int,
            '_dms': int,
            '_drxm': int,
            '_drxs': int,
            '_dtxm': int,
            '_dtxs': int,
            '_hd': int,
            '_lnk': bool,
            '_lock': bool,
            '_md': int,
            '_mu': int,
            '_nsec': int,
            '_rx': int,
            '_setp': int,
            '_ss': str,
            '_sv': int,
            '_syncs': str,
            '_tx': int,
            '_ucnt': int,
            '_sec': int,
            "timestamp": dateutil.parser.parse
        }
        wrstat = {}
        for node, stats in self._get_raw_node_hash("status:wr:heraNode*wr").items():
            wrstat[node] = {}
            for key, convfunc in conv_methods.items():
                if key.startswith('_'):
                    for i in range(2):
                        port_key = ('wr%d' % i) + key
                        try:
                            wrstat[node][port_key] = convfunc(stats[port_key])
                        except:  # noqa
                            wrstat[node][port_key] = None
                else:
                    try:
                        wrstat[node][key] = convfunc(stats[key])
                    except:  # noqa
                        wrstat[node][key] = None
        return wrstat

    def power_snap_relay(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP relay. The SNAP relay
        has to be turn on before sending commands to individual SNAPs.
        """
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return
        tstamp = int(time.time())
        print("Turning {} snap relay for {}".format(command, self.sc_node))
        for node in self.connected_nodes:
            cmdstamp = f"{command}|{tstamp}"
            self.r.hset(f"{self.sr_cmd}{node}", "power_snap_relay_cmd", cmdstamp)
            self.senders[node].power_snap_relay(command)

    def power_snap(self, snap_n, command):
        """
        Takes in a string value of 'on' or 'off' for snap_n
        """
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return
        tstamp = int(time.time())
        print("Turning {} snap{} for {}".format(command, snap_n, self.sc_node))
        for node in self.connected_nodes:
            cmdstamp = f"{command}|{tstamp}"
            self.r.hset(f"{self.sr_cmd}{node}", f"power_snap_{snap_n}_cmd", cmdstamp)
            self.senders[node].power_snap(snap_n, command)

    def power_fem(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to FEM.
        """
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return
        tstamp = int(time.time())
        print("Turning {} fem for {}".format(command, self.sc_node))
        for node in self.connected_nodes:
            cmdstamp = f"{command}|{tstamp}"
            self.r.hset(f"{self.sr_cmd}{node}", "power_fem_cmd", cmdstamp)
            self.senders[node].power_fem(command)

    def power_pam(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to PAM.
        """
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return
        tstamp = int(time.time())
        print("Turning {} pam for {}".format(command, self.sc_node))
        for node in self.connected_nodes:
            cmdstamp = f"{command}|{tstamp}"
            self.r.hset(f"{self.sr_cmd}{node}", "power_pam_cmd", cmdstamp)
            self.senders[node].power_pam(command)

    def reset(self):
        """
        Sends the reset command to Arduino which restarts the bootloader.
        """
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return
        tstamp = int(time.time())
        print("Resetting nodes {}".format(self.sc_node))
        for node in self.connected_nodes:
            cmdstamp = f"reset|{tstamp}"
            self.r.hset(f"{self.sr_cmd}{node}", "reset", cmdstamp)
            self.senders[node].reset()
