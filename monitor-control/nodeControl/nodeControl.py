from __future__ import print_function
import redis
import dateutil.parser
import json
import sys
from . import udpSender


sender_pkg = udpSender.__package__
sender_ver = udpSender.__version__


def str2bool(x):
    """
    Convert the string `x` to a boolean.
    :return: bool(x == '1')
    """
    return x == "1"


def init_trig(node_ID, redis_conn):
    command_node = 'commands:node:{}'.format(node_ID)
    redis_conn.hset(command_node, 'power_snap_relay_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'power_snap_0_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'power_snap_1_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'power_snap_2_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'power_snap_3_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'power_fem_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'power_pam_ctrl_trig', 'False')
    redis_conn.hset(command_node, 'reset', 'False')
    redis_conn.hset('throttle:node:{:d}'.format(node_ID), 'last_command_sec', '0')


def refresh_node_list(curr_nodes, redis_conn):
    new_node_list = {}
    for key in redis_conn.scan_iter("status:node:*"):
        try:
            node_id = int(redis_conn.hget(key, 'node_ID').decode())
        except ValueError:
            continue
        ip = redis_conn.hget(key, 'ip').decode()
        if node_id in list(curr_nodes.keys()):
            if ip == curr_nodes[node_id].arduinoAddress:
                new_node_list[node_id] = curr_nodes[node_id]
            else:
                new_node_list[node_id] = udpSender.UdpSender(ip)
                print("Updating IP address of node {} to {}".format(node_id, ip), file=sys.stderr)
        else:
            new_node_list[node_id] = udpSender.UdpSender(ip)
            print("Adding node {} with ip {}".format(node_id, ip), file=sys.stderr)
            # If this is a new node, default all the command triggers to idle
            init_trig(node_id, redis_conn)
    return new_node_list


class NodeControl():
    """
    This class is used to control power to PAM, FEM, and SNAP boards and get node status information
    through a Redis database running on the correlator head node.

    It also provides a status for the White Rabbit
    """

    def __init__(self, nodes, serverAddress="redishost", throttle=0.5, force_redis_only=False):
        """
        Create a NodeControl class instance to control a single node via the redis datastore
        hosted at `serverAddress`.

        Parameters
        ----------
        node : list of int or None
            ID numbers of the nodes with which this instance of NodeControl will interact.
            If None, it will check them all.
        serverAddress : str
            The hostname, or dotted quad IP address, of the machine running the node control and
            monitoring redis server
        throttle : float
            Delay in seconds between calls to turn on power
        force_redis_only : bool
            Force only using redis (won't send directly even if allowed, ignore redis commands:node)
        """
        self.nodes = nodes
        self.throttle = throttle
        self.force_redis_only = force_redis_only
        self.r = redis.StrictRedis(serverAddress)
        self.get_node_senders()
        self.redis_control = self.get_redis_control()

    def get_node_senders(self):
        """
        Get udp node class for requested nodes that are also in redis.

        Attributes
        ----------
        senders : dict
            Sender classes keyed on node_id (int)
        nodes_in_redis : list
            List of all nodes in redis
        found_nodes : list
            List of all found nodes (request+redis+arduino)
        node_string : str
            Nice string to use to print found nodes
        """
        self.nodes_in_redis = []
        self.senders = {}
        for key in self.r.scan_iter("status:node:*"):
            try:
                node_id = int(self.r.hget(key, 'node_ID').decode())
            except ValueError:
                continue
            self.nodes_in_redis.append(node_id)
            if node_id not in self.nodes:
                continue
            ip = self.r.hget(key, 'ip').decode()
            if ip is None:
                continue
            self.senders[node_id] = udpSender.UdpSender(ip, throttle=self.throttle,
                                                        force_remote=self.force_redis_only)
        self.found_nodes = sorted(self.senders.keys())
        if not len(self.found_nodes):
            self.node_string = 'No nodes found'
        else:
            plural = 'nodes' if len(self.found_nodes) > 1 else 'node'
            self.node_string = "{} {}".format(plural, ', '.join([str(x) for x in self.found_nodes]))

    def _get_raw_node_hash(self, this_key):
        """
        Return the raw content of a node status hash in redis,
        via redis's `hgetall` call. Data are returned as a dictionary,
        where the keys are the redis hash fields (strings) and the
        values are the stored values (strings).

        :returns: Whatever key-value pairs exist for this node's hash
        """
        rawstat = {}
        for node in self.found_nodes:
            nkey = this_key.replace('*', '{}'.format(node))
            rawstat[node] = {key.decode(): val.decode()
                             for key, val in self.r.hgetall(nkey).items()}
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
        for node, stats in self._get_raw_node_hash("status:node:*").items():
            sensors[node] = {}
            for key, convfunc in conv_methods.items():
                try:
                    sensors[node][key] = convfunc(stats[key])
                except:  # noqa
                    sensors[node][key] = None
        return sensors

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
        for node, statii in self._get_raw_node_hash("status:node:*").items():
            power[node] = {}
            for key in list(statii.keys()):
                if key == 'timestamp':
                    power[node][key] = dateutil.parser.parse(statii["timestamp"])
                elif key.startswith("power"):
                    power[node][key] = str2bool(statii[key])
        return power

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
        print("Turning {} snap relay for {}".format(command, self.node_string))
        for node, sender in self.senders.items():
            if self.redis_control:
                self.r.hset("commands:node:%d" % node, "power_snap_relay_ctrl_trig", "True")
                self.r.hset("commands:node:%d" % node, "power_snap_relay_cmd", command)
            if sender.control_type == 'direct':
                sender.power_snap_relay(command)

    def power_snap(self, snap_n, command):
        """
        Takes in a string value of 'on' or 'off' for snap_n
        """
        print("Turning {} snap{} for {}".format(command, snap_n, self.node_string))
        for node, sender in self.senders.items():
            if self.redis_control:
                self.r.hset("commands:node:{}".format(node),
                            "power_snap_{}_ctrl_trig".format(snap_n), "True")
                self.r.hset("commands:node:{}".format(node),
                            "power_snap_{}_cmd".format(snap_n), command)
            if sender.control_type == 'direct':
                sender.power_snap(snap_n, command)

    def power_fem(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to FEM.
        """
        print("Turning {} fem for {}".format(command, self.node_string))
        for node, sender in self.senders.items():
            if self.redis_control:
                self.r.hset("commands:node:%d" % node, "power_fem_ctrl_trig", "True")
                self.r.hset("commands:node:%d" % node, "power_fem_cmd", command)
            if sender.control_type == 'direct':
                sender.power_fem(command)

    def power_pam(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to PAM.
        """
        print("Turning {} pam for {}".format(command, self.node_string))
        for node, sender in self.senders.items():
            if self.redis_control:
                self.r.hset("commands:node:{}".format(node), "power_pam_ctrl_trig", "True")
                self.r.hset("commands:node:{}".format(node), "power_pam_cmd", command)
            if sender.control_type == 'direct':
                sender.power_pam(command)

    def reset(self):
        """
        Sends the reset command to Arduino which restarts the bootloader.
        """
        print("Resetting nodes {}".format(self.node_string))
        for node, sender in self.senders.items():
            if self.redis_control:
                self.r.hset("commands:node:%d" % node, "reset", "True")
            if sender.control_type == 'direct':
                sender.reset()

    def set_redis_control(self, allow):
        print("Setting redis control to {}".format(allow))
        if allow == 'Disable':
            self.r.set('commands:node', 'Disable')
        else:
            self.r.set('commands:node', 'Enable')

    def get_redis_control(self):
        if self.force_redis_only:
            return True
        current_control = self.r.get('commands:node')
        if current_control is None:
            return True
        return False if current_control.decode() == 'Disable' else True

    def init_redis(self):
        print("Initializing node power flags to False for nodes {}".format(self.node_string))
        for node in self.nodes:
            init_trig(node, self.r)

    def check_exists(self):
        """
        Check that the node exists.
        Return dict
        """
        ex = {}
        for node in self.nodes:
            ex[node] = node in self.senders.keys()
        if True not in ex.values():
            ex = {}
        return ex
