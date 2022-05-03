import json
from datetime import datetime
import time
from os import path as osp
from . import send_receive, node_util, __version__


MAX_NODES = 30


def get_redis_nodes(redisServer='redishost', count=None):
    nc = NodeControl(None, redisServer, count)
    return nc.nodes_in_redis


class NodeControl():
    """
    This class is used to control power to PAM, FEM, and SNAP boards and
    get node status information through a Redis database.

    A range of nodes is requested when instantiated, then those are looked for
    in redis, then those are attempted to be connected. So:
        connected_nodes is a subset of nodes_in_redis is a subset of request_nodes
    Note that connected_nodes aren't necessarily connected, but the attempt just
    doesn't error out in a higher level sense.  Using verdict/sentence can reduce
    to actually connected.

    It also provides a status for the White Rabbit

    Attributes
    ----------
    NC_KEY_INFO : dict
        Dictionary containing the redis status pre/post-fix information.
    hw : list
        List of hardware to check.
    power_switch : dict
        Power switch state.
    """

    NC_KEY_INFO = {'wr_stat': ['status:wr:heraNode', 'wr', 'status:wr:'],
                   'nc_stat': ['status:node:', ''],
                   'nc_cmd': ['commands:node:', '']}
    hw = ['snap_relay', 'snap_0', 'snap_1', 'snap_2', 'snap_3', 'fem', 'pam']
    power_switch = {True: 'on', False: 'off'}

    def __init__(self, nodes, redisServer="redishost", count=None):
        """
        Create a NodeControl class instance to query/control nodes.

        Parameters
        ----------
        nodes : int, list of int, 'all', None
            ID numbers of the nodes with which this instance of NodeControl will interact.
            If 'all', will try 0-29.
            If None, it will _not_ get nodes_in_redis
        redisServer : str
            The hostname, or dotted quad IP address, of the machine running the node control and
            monitoring redis server
        count : int or None
            Number of status fields to make a node count as actually used.
            If None, reads from node_util.status_node

        Attributes
        ----------
        request_nodes : list or None
            List of requested nodes (supplied)
        r : redis class
            Redis class to use
        nodes_in_redis : list
            List of all request_nodes in redis
        connected_nodes : list
            List of connected_nodes in nodes_in_redis
        sc_node : str
            String to print connected nodes
        status_node_keys : list
            List of the status:node keys
        """
        self.set_request(nodes)
        self.r = node_util.get_redis_client(redisServer)
        self.nodes_in_redis = []
        self.connected_nodes = []
        self.senders = {}
        self.sc_node = ''
        self.status_node_keys = list(node_util.status_node(None, None).keys())
        self.get_nodes_in_redis(count)
        self.requested_included = {}

    def _get_stat_keys_from_redis(self):
        """
        Go through redis and get all keys that start with the desired patterns.

        Called in get_nodes_in_redis.

        Attributes (from NC_KEY_INFO)
        ----------
        nc_stat : dict
            Redis key entries for status per node.
        nc_cmd : dict
            Redis key entries for commands per node.
        wr_stat : dict
            Redis key entries for wr status per node.

        """
        for this_attr, key_info in self.NC_KEY_INFO.items():
            setattr(self, this_attr, {})  # set dictionary for nodes present
        for this_key in self.r.keys():
            for this_attr, key_info in self.NC_KEY_INFO.items():
                if this_key.startswith(key_info[0]):
                    lstart = len(key_info[0])
                    lstop = len(this_key) - len(key_info[1])
                    try:
                        this_node = int(this_key[lstart: lstop])
                    except ValueError:
                        continue
                    getattr(self, this_attr)[this_node] = this_key

    def redis_keygen(self, rtype, nodeID):
        if rtype == 'wr_stat' and str(nodeID).startswith('heraNode'):
            return "{}{}".format(self.NC_KEY_INFO[rtype][2], nodeID)
        return "{}{}{}".format(self.NC_KEY_INFO[rtype][0], nodeID, self.NC_KEY_INFO[rtype][1])

    def log_service_in_redis(self, this_file):
        rkey = "version:{}:{}".format(__package__, osp.basename(this_file))
        rval = {"version": __version__,
                "timestamp": datetime.now().isoformat()}
        self.r.hmset(rkey, rval)
        self.status_scriptname = "status:script:{}:{}".format(send_receive.THIS_HOST, this_file)

    def set_request(self, nodes):
        if isinstance(nodes, str) and nodes.lower() == 'all':
            self.request_nodes = list(range(MAX_NODES))
        elif isinstance(nodes, (int, float)):
            self.request_nodes = [int(nodes)]
        elif isinstance(nodes, list) or nodes is None:
            self.request_nodes = nodes
        else:
            raise ValueError(f"Invalid 'nodes' type: {nodes}")

    def get_nodes_in_redis(self, count=None):
        """
        Get redis nodes list for those in request_nodes.

        Parameters
        ----------
        count : int or None
            Number of status fields to make a node count as actually used.
            If None, get length from status_node_keys (all)

        Attributes
        ----------
        nodes_in_redis : list
            List of all request_nodes in redis with >count status fields
        """
        if self.request_nodes is None:
            return
        if count is None:
            count = len(self.status_node_keys)
        self._get_stat_keys_from_redis()  # gets self.nc_stat (and self.wr_stat and self.nc_cmd)
        self.nodes_in_redis = []
        for node in self.request_nodes:
            if node not in self.nc_stat:
                continue
            try:
                ts = self.r.hget(self.nc_stat[node], 'timestamp')
            except KeyError:
                ts = 0
            if ts == -1:
                len_entries = len(self.status_node_keys) + 1
            else:
                len_entries = len(self.r.hgetall(self.nc_stat[node]))
            if node in self.nc_stat and len_entries >= count:
                self.nodes_in_redis.append(node)

    def reset_node_senders(self):
        self.connected_nodes = []
        self.senders = {}

    def get_node_senders(self, throttle=0.1):
        """
        Get udp node class for requested nodes that are in redis.

        Every node in redis gets a sender class, differ by sender.node_is_connected flag.

        Attributes
        ----------
        senders : dict
            Sender classes keyed on node_id (int)
        connected_nodes : list
            List of all udp connected request_nodes
        sc_node : str
            String to print connected nodes
        """
        self.connected_nodes = []
        for node in self.nodes_in_redis:
            if node in self.senders.keys():
                if self.senders[node].node_is_connected:
                    self.connected_nodes.append(node)
            else:
                hkey = self.redis_keygen('nc_stat', node)
                # ip = self.r.hget(hkey, 'ip')  # use name not number
                ip = f"heraNode{node}"
                self.senders[node] = send_receive.UdpSenderReceiver(ip, throttle=throttle)
                if self.senders[node].node_is_connected:
                    self.connected_nodes.append(node)
                    _ping = self.senders[node].pingable
                    self.r.hset(hkey, 'udp_status', 'ping {}/{} : {}s'
                                .format(_ping['rcvd'], _ping['sent'], _ping['avg']))
                else:
                    self.r.hset(hkey, 'udp_status', 'not connected')
        if len(self.connected_nodes):
            s = 's' if len(self.connected_nodes) > 1 else ''
            self.sc_node = "Node{} {}".format(s, ', '.join([str(x) for x in self.connected_nodes]))
        else:
            self.sc_node = "No requested nodes connected."

    def get_sensors(self):
        """
        Get the current node sensor values from redis.

        Returns a dict where `timestamp` is a python `time` float describing when the
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
            "timestamp": float
        }
        sensors = {}
        now = time.time()
        self.requested_included['sensor'] = []
        for node, stat_key in self.nc_stat.items():
            if self.request_nodes is not None and node in self.request_nodes:
                self.requested_included['sensor'].append(node)
            stats = self.r.hgetall(stat_key)
            sensors[node] = {'age': None}
            for key, convfunc in conv_methods.items():
                try:
                    sensors[node][key] = convfunc(stats[key])
                    if key == 'timestamp':
                        try:
                            sensors[node]['age'] = now - sensors[node][key]
                        except ValueError:
                            pass
                except:  # noqa
                    sensors[node][key] = None
        self.requested_included['sensor'] = sorted(self.requested_included['sensor'])
        return sensors

    def get_power_command_list(self):
        """
        Get the current node power commands from redis.

        Returns a dict keyed on node|part|timestamp/age/command

        Valid power command keys are:
            power_snap_relay_cmd
            power_snap_0_cmd
            power_snap_1_cmd
            power_snap_2_cmd
            power_snap_3_cmd
            power_fem_cmd
            power_pam_cmd
            reset
        Format of values for all is on/off/reset|time(unix)
        """
        valid = ["power_{}_cmd".format(x) for x in self.hw] + ['reset']
        power = {}
        now = time.time()
        for node, cmd_key in self.nc_cmd.items():
            statii = self.r.hgetall(cmd_key)
            power[node] = {}
            for key in list(statii.keys()):
                if key not in valid:
                    continue
                if 'relay' in key:
                    this_key = 'snap_relay'
                elif 'snap' in key:
                    this_key = "snap{}".format(key.split('_')[2])
                elif 'reset' in key:
                    this_key = 'reset'
                else:
                    this_key = key.split('_')[1]
                stad = statii[key].split('|')
                try:
                    this_timestamp = float(stad[1])
                    this_age = now - this_timestamp
                except (IndexError, ValueError):
                    this_timestamp = -99
                    this_age = -99
                power[node][this_key] = {'timestamp': this_timestamp,
                                         'age': this_age,
                                         'command': stad[0]}
        return power

    def enable_snap_monitor(self, disabler='IGNORE'):
        """
        If snap monitor was disabled by <disabler> re-enable it.
        """
        if self.r.exists('disable_monitoring'):
            disabled_by = self.r.get('disable_monitoring')
            if disabled_by == disabler:
                self.r.delete('disable_monitoring')
                return 'Enabling'
            return f'Not enabled since disabled by {disabled_by} not {disabler}'
        return 'Already enabled'

    def disable_snap_monitor(self, disabler='hera_node_mc.disable_snap_monitor'):
        """
        Disable snap monitor attributing to <disabler>.
        """
        if not self.r.exists('disable_monitoring'):
            distag = "{}:{}".format(disabler, datetime.now().isoformat())
            self.r.set('disable_monitoring', distag)
            return 'Disabling'
        else:
            disabled_by = self.r.get('disable_monitoring')
            return f'Already disabled by {disabled_by}'

    def snap_monitor_check_and_set(self, age_cutoff=600.0):
        """
        Check the powered state of all of the snaps and disable if appropriate.

        If nodes to use is 'all' and all snaps are off, set disable_monitoring flag
        in redis.  If any are on and the disable flag was set by this method, remove
        the flag.

        Parameter
        =========
        age_cutoff : float
            time (sec) to use to cutoff using the power state
        """
        power_data = self.get_power_status()
        # check all snaps and snap relay to allow monitoring.
        all_snap_off = True
        for node, pwr in power_data.items():
            if 'age' in pwr.keys() and pwr['age'] < age_cutoff:
                for key in ['power_snap_0', 'power_snap_1', 'power_snap_2', 'power_snap_3']:
                    if key in pwr.keys() and pwr[key] is True:
                        all_snap_off = False
                        break
            if not all_snap_off:
                break
        if all_snap_off:
            return self.disable_snap_monitor('hera_node_mc.snap_monitor_check_and_set')
        return self.enable_snap_monitor('hera_node_mc.snap_monitor_check_and_set')

    def get_power_status(self):
        """
        Get the current node power relay states from redis.

        Returns a dict where `timestamp` is a python `time` float
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
        now = time.time()
        self.requested_included['power'] = []
        for node, stat_key in self.nc_stat.items():
            if self.request_nodes is not None and node in self.request_nodes:
                self.requested_included['power'].append(node)
            statii = self.r.hgetall(stat_key)
            power[node] = {'age': None}
            for key in list(statii.keys()):
                if key == 'timestamp':
                    try:
                        power[node]['timestamp'] = float(statii[key])
                        power[node]['age'] = now - float(statii[key])
                    except ValueError:
                        power[node]['timestamp'] = -99
                        power[node]['age'] = -99
                elif key.startswith("power"):
                    power[node][key] = node_util.str2bool(statii[key])
        self.requested_included['power'] = sorted(self.requested_included['power'])
        return power

    def get_wr_status(self):
        """
        Get the current status of this node's White Rabbit endpoint (assumed to have hostname
        `heraNode<node-number>wr`) from redis.

        If no stats exist for this White Rabbit endpoint, returns `None`.

        Otherwise Returns a dict where `timestamp` is a python `timestamp` describing when
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
            'temperature' (float)       : WR-LEN temperature in degrees C
            'sw_build_date' (timestamp) : Build date of WR-LEN software
            'wr_gw_date' (timestamp)    : WR-LEN gateware build date
            'wr_gw_version' (str)       : WR-LEN gateware version number
            'wr_gw_id' (str)            : WR-LEN gateware ID number
            'wr_build' (str)            : WR-LEN build git hash
            'wr_fru_custom' (str)       : Custom manufacturer tag'
            'wr_fru_device' (str)       : Manufacturer device name designation
            'wr_fru_fid' (timestamp)    : Manufacturer invoice(?) date
            'wr_fru_partnum' (str)      : Manufacturer part number
            'wr_fru_serial' (str)       : Manufacturer serial number
            'wr_fru_vendor' (str)       : Vendor name
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
            'timestamp': str,
            'sw_build_date': str,
            'wr_gw_date': str,
            'wr_gw_version': str,
            'wr_gw_id': str,
            'wr_build': str,
            'wr_fru_custom': str,
            'wr_fru_device': str,
            'wr_fru_fid': str,
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
            '_sec': int
        }
        wrstat = {}
        self.requested_included['wr'] = []
        for node, stat_key in self.wr_stat.items():
            if self.request_nodes is not None and node in self.request_nodes:
                self.requested_included['wr'].append(node)
            stats = self.r.hgetall(stat_key)
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
        self.requested_included['wr'] = sorted(self.requested_included['wr'])
        return wrstat

    def verdict(self, hwcmd, verbose=True, hold_for_verify=120, verify_mode='all',
                log_verdict=True, show_success=False):
        """
        Checks if commands are actually carried out - needs hera-node-receiver service running.

        Uses _verify_states to make sure the hardware commands were set as requested.
        Note that it bases off of connected_nodes, not requested_nodes.

        Parameters
        ----------
        hwcmd : dict
            Dict of hardware to check and the commands (on or off)
        hold_for_verify : int
            Length of time till timeout (seconds)
        verify_mode : str
            Type of verification to check (see _verify_states)
        log_verdict : bool
            Flag to log the final verdict to redis.
        show_success : bool
            Flag to also show success rather than just failure.
        """
        if verbose:
            print("...Verifying...", end='')
        lenhw = len(hwcmd.keys())
        if hold_for_verify <= 0:
            print("No verdict hold time - not checking.")
            return
        elif not lenhw:
            print("No hardware to check verdict.")
            return
        started = time.time()
        age = 0.0
        node_counter = {}
        all_verified = False
        while age < hold_for_verify:
            countdown = len(self.connected_nodes) * lenhw  # total to check
            _verdict = self._verify_states(hwcmd)
            for node in self.connected_nodes:
                node_counter[node] = lenhw
                for this_hw in hwcmd.keys():
                    if _verdict[node][this_hw][verify_mode]:
                        countdown -= 1
                        node_counter[node] -= 1
            if not countdown:  # all OK so can quit loop
                all_verified = True
                if verbose:
                    print("...all ok")
                break
            time.sleep(1)  # Wait 1 second for next check.
            age = time.time() - started
        if verbose and not all_verified:
            print("...timeout {:.1f}".format(age))
        node_counter['hwcmd'] = hwcmd
        node_counter['mode'] = verify_mode
        node_counter['timeout'] = hold_for_verify
        node_counter['age'] = age
        node_counter['time'] = time.time()
        if log_verdict:
            self._log_verdict_in_redis(_verdict, node_counter)
        if verbose:
            for node in self.connected_nodes:
                for this_hw in _verdict[node].keys():
                    if not _verdict[node][this_hw][verify_mode]:
                        print("FAIL Node {} turned {} {}".format(
                                node, this_hw, hwcmd[this_hw]))
                    elif show_success:
                        print("SUCCESS Node {} turned {} {}".format(
                                node, this_hw, hwcmd[this_hw]))
        return node_counter

    def sentence(self, results, error_threshold=1.0, purge=True):
        """
        Determine what to do with the verdict.

        Computes error fraction and will error out if exceeds threshold.

        Parameters
        ----------
        results : bool or dict
            Returned from self.verdict
        error_threshold : int
            Threshold fractional value per node over which to raise an error.
            0.0 will error if there are any unsuccessful
            1.0 will never error
        purge : bool
            If True, remove unsuccessful nodes from self.connected_nodes.

        Returns
        -------
        float
            computed error fraction: 0 - 1
        """
        if results is None:
            return 0.0
        if isinstance(results, bool) and results:
            return 0.0  # All good (none failed)!
        failed = []
        incoming_total = len(self.connected_nodes)
        for node in self.connected_nodes:
            if results[node]:  # there were some left over so didn't all work
                failed.append(node)
                if purge:
                    self.connected_nodes.remove(node)
        error_fraction = len(failed) / incoming_total
        if error_fraction > error_threshold:
            msg = "{} of {} nodes failed.".format(len(failed), incoming_total)
            raise RuntimeError(msg)
        if purge and len(failed) > 0:
            print("{} removed from connected_nodes.".format(failed))
        return error_fraction

    def _verify_states(self, hwcmd):
        """
        Check the state of hardware in nodes - command and status.

        Parameters
        ----------
        hwcmd : dictionary of hardware and on/off command.

        Returns
        -------
        dict
            keyed on node, and mode: 'time', 'agree', 'cmd', 'stat', 'all'
            each one is a bool
        """
        # Prep the lists.
        if 'all' in hwcmd.keys():
            verify_hw = self.hw
            verify_cmd = [hwcmd['all'] for x in verify_hw]
        else:
            verify_hw = list(hwcmd.keys())
            verify_cmd = [hwcmd[x] for x in verify_hw]
        verify_hw = [x.lower() for x in verify_hw]
        verify_cmd = [x.lower() for x in verify_cmd]

        # Get from redis
        pcmd = self.get_power_command_list()
        pstat = self.get_power_status()

        # Verify
        verification = {}
        for node in self.connected_nodes:
            verification[node] = {}
            for vhw, vcmd in zip(verify_hw, verify_cmd):
                verification[node][vhw] = {}
                shw = 'power_{}'.format(vhw)
                chw = vhw.replace('_', '') if 'relay' not in vhw else vhw
                try:
                    verification[node][vhw]['time'] = (pcmd[node][chw]['timestamp'] <
                                                       pstat[node]['timestamp'])
                except KeyError:
                    verification[node][vhw]['time'] = False
                try:
                    pcmdvhw = pcmd[node][chw]['command']
                except KeyError:
                    pcmdvhw = None
                verification[node][vhw]['cmd'] = pcmdvhw == vcmd
                pstatvhw = 'on' if pstat[node][shw] else 'off'
                verification[node][vhw]['stat'] = pstatvhw == vcmd
                verification[node][vhw]['agree'] = pcmdvhw == pstatvhw
                verification[node][vhw]['all'] = True
                for thisv in ['time', 'cmd', 'stat', 'cmd']:
                    if not verification[node][vhw][thisv]:
                        verification[node][vhw]['all'] = False
                        break
        return verification

    def _log_verdict_in_redis(self, vdt, nc, expire_time_hr=24.0):
        """
        Log the final verification dictionary to redis under verdict:node:
        """
        vpar = {'mode': nc['mode'], 'timeout': nc['timeout'],
                'time': nc['time'], 'age': nc['age']}
        vpar['hw'] = ','.join(nc['hwcmd'].keys())
        vpar['cmd'] = ','.join([nc['hwcmd'][x] for x in vpar['hw'].split(',')])

        for this_key in self.r.keys():  # purge all old values
            if this_key.startswith('verdict:node:'):
                self.r.delete(this_key)
        self.r.hmset('verdict:node:par', vpar)
        self.r.expire('verdict:node:par', int(expire_time_hr * 3600.0))
        for node, vals in vdt.items():
            for hw, _stg in vals.items():
                _tvd = {}
                for _aa, _bb in _stg.items():
                    _tvd[_aa] = 1 if _bb else 0
                key = "verdict:node:{}:{}".format(node, hw)
                self.r.hmset(key, _tvd)
                self.r.expire(key, int(expire_time_hr * 3600.0))
        for node in self.connected_nodes:
            key = "verdict:node:{}:valid".format(node)
            if nc[node]:
                self.r.set(key, 0)
            else:
                self.r.set(key, 1)
            self.r.expire(key, int(expire_time_hr * 3600.0))

    def _log_cmd_to_redis(self, node, component, tstamp, cmd):
        key = self.redis_keygen('nc_cmd', node)
        val = "{}|{}".format(cmd, tstamp)
        cmp = "{}_cmd".format(component)
        self.r.hset(key, cmp, val)

    def _change_state_nodes(self, command, hw, print_stat=False):
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return []
        pstat = self.get_power_status()
        change_node = []
        for cnode in self.connected_nodes:
            if command != self.power_switch[pstat[cnode][hw]]:
                change_node.append(cnode)
        if print_stat:
            prhw = hw.strip('power').replace('_', ' ').strip()
            if len(change_node):
                s = 's' if len(change_node) > 1 else ''
                prnd = "Node{} {}".format(s, ', '.join([str(x) for x in change_node]))
                print("Turning {} {}{} for {}".format(command, prhw, s, prnd))
            else:
                s = 's' if len(self.connected_nodes) > 1 else ''
                print("{}{} already {}".format(prhw, s, command))
        return change_node

    def power_snap_relay(self, command, hold_for_verify=120, verify_mode='all'):
        """
        Controls the node snap relay via arduino.

        The SNAP relay has to be turn on before sending commands to individual SNAPs.
        It logs the command to redis as status:node:N->power_snap_relay_cmd. If turning on,
        it checks for success, since 1st of 2 stages to turn on SNAPs.

        Parameter
        ---------
        command : str
            on or off
        hold_for_verify : int
            Since the snap_relay has to be on first, you can hold that many seconds until
            it is verified that it is on (only on, not off). Ignore if 0.
        verify_mode : str
            One of the keys in the verification dict
        """
        change_node = self._change_state_nodes(command, 'power_snap_relay', print_stat=True)
        if not len(change_node):
            return
        tstamp = int(time.time())
        for node in change_node:
            self._log_cmd_to_redis(node, 'power_snap_relay', tstamp, command)
            self.senders[node].power_snap_relay(command)
        if command == 'on' and hold_for_verify > 0:
            _r = self.verdict({'snap_relay': 'on'}, False,
                              hold_for_verify=hold_for_verify, verify_mode=verify_mode)
            self.snap_relay_error_fraction = self.sentence(_r, 1.0, purge=True)

    def power_snap(self, snap_n, command):
        """
        Controls the power to snaps via arduino.

        It logs the command to redis as status:node:N->power_snap_N_cmd.

        Parameters
        ----------
        snap_n : int (or str representation of int)
            Number of snap to address.
        command : str
            on or off
        """
        this_snap = f"power_snap_{snap_n}"
        change_node = self._change_state_nodes(command, this_snap, print_stat=True)
        if not len(change_node):
            return
        tstamp = int(time.time())
        for node in change_node:
            self._log_cmd_to_redis(node, this_snap, tstamp, command)
            self.senders[node].power_snap(snap_n, command)

    def power_fem(self, command):
        """
        Controls the power to FEM via arduino.

        It logs the command to redis as status:node:N->power_fem_cmd.

        Parameter
        ---------
        command : str
            on or off
        """
        change_node = self._change_state_nodes(command, 'power_fem', print_stat=True)
        if not len(change_node):
            return
        tstamp = int(time.time())
        for node in change_node:
            self._log_cmd_to_redis(node, 'power_fem', tstamp, command)
            self.senders[node].power_fem(command)

    def power_pam(self, command):
        """
        Controls the power to PAM via arduino.

        It logs the command to redis as status:node:N->power_pam_cmd.

        Parameter
        ---------
        command : str
            on or off
        """
        change_node = self._change_state_nodes(command, 'power_pam', print_stat=True)
        if not len(change_node):
            return
        tstamp = int(time.time())
        for node in change_node:
            self._log_cmd_to_redis(node, 'power_pam', tstamp, command)
            self.senders[node].power_pam(command)

    def reset(self):
        """
        Sends the reset command to Arduino which restarts the bootloader.

        It logs the command to redis as status:node:N->reset
        """
        if not len(self.connected_nodes):
            print("No nodes connected.")
            return
        tstamp = int(time.time())
        print("Resetting {}".format(self.sc_node))
        for node in self.connected_nodes:
            self._log_cmd_to_redis(node, 'reset', tstamp, 'reset')
            self.senders[node].reset()
