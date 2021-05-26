from __future__ import print_function
import time
import socket


# Define hosts that can directly control the arduinos and this host
direct_control_hostnames = ['hera-mobile', 'hera-node-head']
this_host = socket.gethostname()


class UdpSenderReceiver():
    """
    This class is used for sending UDP commands to Arduino directly.
    Has ability to turn on/off FEM, PAM, relay and SNAPs. Could also
    reset the Arduino bootloader or poke.
    """

    def __init__(self, arduinoAddress,
                 throttle=0.5,
                 connected_verbosity=True,
                 serverAddress='0.0.0.0',
                 sendPort=8888,
                 rcvPort=8889):
        """
        Takes in the arduino IP address and sends commands directly, using udp.
        You have to be on the hera-digi-vm server or hera-node-head to use it.
        If the arduinoAddress == 'receive', then sets up receiver socket.

        Parameters
        ----------
        arduinoAddress : str or None
            IP address of desired arduino.
            If None, mark as not connected.
            If 'receive', then make a receive socket.
        throttle : float
            Delay time in seconds
        connected_verbosity : bool
            If True, will print out a message that the node is not connected.
            upon any action if node_is_connected is False.
        serverAddress : str
            Address for socket server
        sendPort : int
            Send port
        rcvPort : int
            Receive port
        """
        self.arduinoAddress = arduinoAddress
        self.throttle = throttle
        self.connected_verbosity = connected_verbosity
        self.sendPort = sendPort
        self.rcvPort = rcvPort
        self.serverAddress = serverAddress
        self.socketDirection = None

        if arduinoAddress is None:
            self.node_is_connected = False
        elif this_host in direct_control_hostnames:
            self.node_is_connected = True
            # define socket address for binding; necessary for communicating with Arduino
            if 'receive' in arduinoAddress.lower():
                self.localSocket = (serverAddress, rcvPort)
                self.socketDirection = 'receiver'
            else:
                self.localSocket = (serverAddress, sendPort)
                self.socketDirection = 'sender'
            # Create a UDP socket
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Make sure that specify that we want to reuse the socket address
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except socket.error as msg:
                print('Failed to create socket - set to not connected. Error Code : {}  Message {}'
                      .format(str(msg[0]), str(msg[1])))
                self.node_is_connected = False
                if self.socketDirection == 'receiver':
                    raise ValueError()

            # Bind socket to local host and port
            if self.node_is_connected:
                try:
                    self.client_socket.bind(self.localSocket)
                except socket.error as msg:
                    print('Bind failed - set to not connected. Error Code : {}  Message {}'
                          .format(str(msg[0]), msg[1]))
                    self.node_is_connected = False
                    if self.socketDirection == 'receiver':
                        raise ValueError()
        else:
            self.node_is_connected = False

    def poke(self):
        """
        Sends poke commands to the Arduino. Used by hera_node_keep_alive script
        to send keep Arduinos from resetting.
        """
        if not self._command_OK('poke', ['poke'], 'poke'):
            return
        arduinoSocket = (self.arduinoAddress, self.sendPort)
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
        arduinoSocket = (self.arduinoAddress, self.sendPort)
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
        arduinoSocket = (self.arduinoAddress, self.sendPort)
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
        arduinoSocket = (self.arduinoAddress, self.sendPort)
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
        arduinoSocket = (self.arduinoAddress, self.sendPort)
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
        arduinoSocket = (self.arduinoAddress, self.sendPort)
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
