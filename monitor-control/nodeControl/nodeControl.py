import redis
import time
import dateutil.parser
import datetime
import json

def str2bool(x):
    """
    Convert the string `x` to a boolean.
    :return: bool(x == '1')
    """
    return x == "1"

def get_valid_nodes(serverAddress = "redishost"):
    """
    Return a list of all node IDs which currently have status data
    stored in the redis database hosted on `redishost`.

    :param serverAddress: The hostname, or dotted quad IP address, of the machine running the node
                          control and monitoring redis server
    :type serverAddress: String
    :return: List of integers representing the nodes whose status is currently available. Presence
             of a node in this list just means that this node has is an associated `status:node` key in
             redis. It does not mean the node is actively reporting.
    """
    valid_nodes = []
    for key in list(redis.StrictRedis(serverAddress).scan_iter("status:node:*")):
        valid_nodes += [int(key.decode().split(":")[2])]
    return valid_nodes



class NodeControl():
    """
    This class is used to control power to PAM, FEM, and SNAP boards and get node status information
    through a Redis database running on the correlator head node.
    """

    def __init__(self, node, serverAddress = "redishost"):
        """
        Create a NodeControl class instance to control a single node via the redis datastore
        hosted at `serverAddress`.

        :param node: The ID number of the node this instance of the NodeControl class will interact with.
        :type node: Integer
        :param serverAddress: The hostname, or dotted quad IP address, of the machine running the node
                              control and monitoring redis server
        :type serverAddress: String
        :return: NodeControl instance
        """

        self.node = node
        self.r = redis.StrictRedis(serverAddress)

    def _conv_float(self, v):
        """
        Try and convert v into a float. If we can't, return None.
        """
        try:
            return float(v)
        except ValueError:
            return None

    def _get_raw_node_status(self):
        """
        Return the raw content of a node status hash in redis,
        via redis's `hgetall` call. Data are returned as a dictionary,
        where the keys are the redis hash fields (strings) and the
        values are the stored values (strings).

        :returns: Whatever key-value pairs exist for this node's `status:node` hash
        """
        return {key.decode(): val.decode() for key, val in self.r.hgetall("status:node:%s" % self.node).items()}

    def get_sensors(self):
        """
        Get the current node sensor values.

        Returns a tuple `(timestamp, sensors)`, where `timestamp` is a python `datetime` object
        describing when the sensor values were last updated in redis, and `sensors` is a dictionary
        of sensor values.
        If a sensor value is not available (e.g. because the sensor cannot be reached) it will be `None`

        Valid sensor keywords are:
            'temp_top' (float) : Temperature, in degrees C, reported by top node sensor.
            'temp_mid' (float) : Temperature, in degrees C, reported by middle node sensor.
            'temp_bot' (float) : Temperature, in degrees C, reported by bottom node sensor.
            'temp_humid'     (float) : Temperature, in degrees C, reported by humidity sensor.
            'humid'          (float) : Relative Humidity, in percent, reported by humidity sensor.
            'cpu_uptime_ms'  (int)   : Uptime of this node control module, in milliseconds
            'ip'             (str)   : IP address of this node controler module, e.g. "10.1.1.123"
            'mac'            (str)   : MAC address of this node controller module, e.g. "02:03:04:05:06:07"
        """

        stats = {key.decode(): val.decode() for key, val in self.r.hgetall("status:node:%d"%self.node).items()}
        timestamp = dateutil.parser.parse(stats["timestamp"])
        conv_methods = {
            "temp_bot"       : float,
            "temp_mid"       : float,
            "temp_top"       : float,
            "temp_humid"     : float,
            "humid"          : float,
            "ip"             : str,
            "mac"            : str,
            "cpu_uptime_ms"  : int,
        }
        sensors = {}
        for key, convfunc in conv_methods.items():
            try:
                sensors[key] = convfunc(stats[key])
            except:
                sensors[key] = None

        return timestamp, sensors


    def get_power_status(self):
        """
        Get the current node power relay states.

        Returns a tuple `(timestamp, statii)`, where `timestamp` is a python `datetime` object
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

        statii = self._get_raw_node_status()
        timestamp = dateutil.parser.parse(statii["timestamp"])
        for key in list(statii.keys()):
            if key.startswith("power"):
                statii[key] = str2bool(statii[key])
            else:
                statii.pop(key)
        return timestamp, statii

    def get_wr_status(self):
        """
        Get the current status of this node's White Rabbit endpoint (assumed to have hostname
        `heraNode<node-number>wr`.

        If no stats exist for this White Rabbit endpoint, returns `None`.

        Otherwise Returns a tuple `(timestamp, statii)`, where `timestamp` is a python `datetime` object
        describing when the values were last updated in redis, and `statii` is a dictionary
        of status values.

        If a status value is not available it will be `None`

        Valid status keywords are:
            'board_info_str' (str)      : A raw string representing the WR-LEN's response to the `ver` command.
                                          Relevant parts of this string are individually unpacked in other entries.
            'aliases' (list of strings) : Hostname aliases of this node's WR-LEN
            'ip' (str)                  : IP address of this node's WR-LEN
            'mode' (str)                : WR-LEN operating mode (eg. "WRC_SLAVE_WR0")
            'serial' (str)              : Canonical HERA hostname (~= serial number) of this node's WR-LEN
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
            The following entries are prefixed `wr0` or `wr1` for WR-LEN ports 0 and 1, respectively.
            Most values will only be not None for one of the two ports.
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
            'wr[0|1]_sec'   (datetime)  : Current TAI time
        """

        stats = self.r.hgetall("status:wr:heraNode%dwr" % self.node)
        try:
            timestamp = dateutil.parser.parse(stats["timestamp"])
        except:
            return None

        conv_methods = {
            'board_info_str' : str,
            'aliases'        : json.loads,
            'ip'             : str,
            'mode'           : str,
            'serial'         : str,
            'temp'           : float,
            'sw_build_date'  : dateutil.parser.parse,
            'wr_gw_date'     : lambda x : dateutil.parser.parse('20' + x), #hack!
            'wr_gw_version'  : str,
            'wr_gw_id'       : str,
            'wr_build'       : str,
            'wr_fru_custom'  : str,
            'wr_fru_device'  : str,
            'wr_fru_fid'     : dateutil.parser.parse,
            'wr_fru_partnum' : str,
            'wr_fru_serial'  : str,
            'wr_fru_vendor'  : str,
            '_ad'          : int, 
            '_asym'        : int, 
            '_aux'         : int, 
            '_cko'         : int, 
            '_crtt'        : int, 
            '_dms'         : int, 
            '_drxm'        : int, 
            '_drxs'        : int, 
            '_dtxm'        : int, 
            '_dtxs'        : int, 
            '_hd'          : int, 
            '_lnk'         : bool, 
            '_lock'        : bool, 
            '_md'          : int, 
            '_mu'          : int, 
            '_nsec'        : int, 
            '_rx'          : int, 
            '_setp'        : int, 
            '_ss'          : int, 
            '_sv'          : int, 
            '_syncs'       : str,
            '_tx'          : int, 
            '_ucnt'        : int, 
            '_sec'         : lambda x : datetime.datetime.fromtimestamp(int(x)), 
        }

        stats_formatted = {}

        for key, convfunc in conv_methods.items():
            if key.startswith('_'):
                for i in range(2):
                    port_key = ('wr%d' % i) + key
                    try:
                        stats_formatted[port_key] = convfunc(stats[port_key])
                    except:
                        stats_formatted[port_key] = None
            else:
                try:
                    stats_formatted[key] = convfunc(stats[key])
                except:
                    stats_formatted[key] = None

        return timestamp, stats_formatted


    def check_exists(self):
        """
        Check that the status key corresponding to this node exists.
        Return True if it does, else False.
        """
        return self.r.exists("status:node:%d" % self.node) > 0

    def power_snap_relay(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP relay. The SNAP relay
        has to be turn on before sending commands to individual SNAPs.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_relay_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_snap_relay_cmd",command)
        print(("SNAP relay power is %s"%command))


    def power_snap_0(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 0.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_0_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_snap_0_cmd",command)
        print(("SNAP 0 power is %s"%command))


    def power_snap_1(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 1.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_1_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_snap_1_cmd",command)
        print(("SNAP 1 power is %s"%command))


    def power_snap_2(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 2.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_2_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_snap_2_cmd",command)
        print(("SNAP 2 power is %s"%command))


    def power_snap_3(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 3.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_3_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_snap_3_cmd",command)
        print(("SNAP 3 power is %s"%command))


    def power_fem(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to FEM.
        """

        self.r.hset("commands:node:%d"%self.node,"power_fem_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_fem_cmd",command)
        print(("FEM power is %s"%command))


    def power_pam(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to PAM.
        """

        self.r.hset("commands:node:%d"%self.node,"power_pam_ctrl_trig","True")
        self.r.hset("commands:node:%d"%self.node,"power_pam_cmd",command)
        print(("PAM power is %s"%command))


    def reset(self):
        """
        Sends the reset command to Arduino which restarts the bootloader.
        """

        self.r.hset("commands:node:%d"%self.node,"reset","True")
        print("Arduino is resetting...")


