from __future__ import print_function
import time
import socket


# Define sendPort/rcvPort for socket creation
sendPort = 8888
rcvPort = 8889
serverAddress = '0.0.0.0'
# Define hosts that can directly control the arduinos
direct_control_hostnames = ['hera-mobile', 'hera-node-head']


class UdpSenderReceiver():
    """
    This class is used for sending UDP commands to Arduino directly.
    Has ability to turn on/off FEM, PAM, relay and SNAPs. Could also
    reset the Arduino bootloader or poke.

    If it can't find an arduino, the attribute node_is_connected is set
    to False.
    """

    def __init__(self, arduinoAddress,
                 throttle=0.5,
                 sndrcv='send',
                 connected_verbosity=True,
                 force_direct=False):
        """
        Takes in the arduino IP address and sends commands directly, using udp.
        You have to be on the hera-digi-vm server or hera-node-head to use it.

        Parameters
        ----------
        arduinoAddress : str or None
            IP address of desired arduino.  If not valid IP or None, mark as not connected.
        throttle : float
            Delay time in seconds
        sndrcv : str
            Choose between send or receive
        connected_verbosity : bool
            If True, will print out a message that the node is not connected.
            upon any action if node_is_connected is False.
        force_direct : bool
            If True, will ignore hostname list for direct control.
        """
        self.arduinoAddress = arduinoAddress
        self.throttle = throttle
        self.connected_verbosity = connected_verbosity

        if arduinoAddress is None or '.' not in arduinoAddress:
            self.node_is_connected = False
        elif socket.gethostname() in direct_control_hostnames or force_direct:
            self.node_is_connected = True
            # define socket address for binding; necessary for receiving data from Arduino
            if sndrcv == 'send':
                self.localSocket = (serverAddress, sendPort)
            elif sndrcv == 'receive':
                self.localSocket = (serverAddress, rcvPort)
            else:
                raise ValueError('Must be send or receive, you provided {}.'.format(sndrcv))
            # Create a UDP socket
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Make sure that specify that we want to reuse the socket address
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except socket.error as msg:
                print('Failed to create socket - set to not connected. Error Code : {}  Message {}'
                      .format(str(msg[0]), str(msg[1])))
                self.node_is_connected = False

            # Bind socket to local host and port
            if self.node_is_connected:
                try:
                    self.client_socket.bind(self.localSocket)
                except socket.error as msg:
                    print('Bind failed - set to not connected. Error Code : {}  Message {}'
                          .format(str(msg[0]), msg[1]))
                    self.node_is_connected = False
        else:
            self.node_is_connected = False

    def poke(self):
        """
        Sends poke commands to the Arduino. Used by hera_node_keep_alive script
        to send keep Arduinos from resetting.
        """
        if not self._command_OK('poke', ['poke'], 'poke'):
            return
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(b'poke', arduinoSocket)

    def power_snap_relay(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP relay, must be turned on first before gaining
        control over individual SNAPs.
        """
        if not self._command_OK(command.lower(), ['on', 'off'], 'snap relay'):
            return

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(('snapRelay_%s' % command).encode(), arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def power_fem(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to FEM.
        """
        if not self._command_OK(command.lower(), ['on', 'off'], 'fem'):
            return

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(('FEM_%s' % command).encode(), arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def power_pam(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to PAM.
        """
        if not self._command_OK(command.lower(), ['on', 'off'], 'pam'):
            return

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(('PAM_%s' % command).encode(), arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def power_snap(self, snap_n, command):
        """
        Takes in a command "on"/"off".
        Controls the power to SNAP snap_n.
        """
        if not self._command_OK(int(snap_n), [0, 1, 2, 3], 'snap_n'):
            return
        if not self._command_OK(command.lower(), ['on', 'off'], 'snap'):
            return

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto('snapv2_{}_{}'.format(snap_n, command).encode(), arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def reset(self):
        """
        Resets the Arduino bootloader.
        """
        if not self._command_OK('reset', ['reset'], 'reset'):
            return
        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(b'reset', arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def _command_OK(self, command, allowed, call_cmd):
        if self.node_is_connected and command in allowed:
            return True
        if self.connected_verbosity:
            if not self.node_is_connected:
                print("Node not connected ({})".format(call_cmd))
            else:
                print("{}: {} not in {}".format(call_cmd, command, allowed))
        return False
