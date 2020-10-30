from __future__ import print_function
import time
import socket
import sys


# Define sendPort for socket creation
sendPort = 8888
# Define IP address on which to send commands
serverAddress = '0.0.0.0'
# Define hosts that can directly control the arduinos
direct_control_hostnames = ['hera-mobile', 'hera-node-head']


class UdpSender():
    """
    This class is used for sending UDP commands to Arduino directly.
    Has ability to turn on/off FEM, PAM, relay and SNAPs. Could also reset the
    Arduino bootloader.
    """

    def __init__(self, arduinoAddress, throttle=0.5, force_remote=False):
        """
        Takes in the arduino IP address and sends commands directly, using udp.
        You have to be on the hera-digi-vm server to use it, otherwise use
        the nodeControl class to send commands via Redis.

        Parameters
        ----------
        arduinoAddress : str
            IP address of desired arduino
        throttle : float
            Delay time in seconds
        """
        self.throttle = throttle
        self.arduinoAddress = arduinoAddress
        self.control_type = 'remote'
        if not force_remote and socket.gethostname() in direct_control_hostnames:
            self.control_type = 'direct'
            # define socket address for binding; necessary for receiving data from Arduino
            self.localSocket = (serverAddress, sendPort)

            # Create a UDP socket
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Make sure that specify that we want to reuse the socket address
                self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # print('Socket created')
            except socket.error as msg:
                print('Failed to create socket. Error Code : {}  Message {}'
                      .format(str(msg[0]), str(msg[1])))
                sys.exit()

            # Bind socket to local host and port
            try:
                self.client_socket.bind(self.localSocket)
                # print('Bound socket')
            except socket.error as msg:
                print('Bind failed. Error Code : {}  Message {}'.format(str(msg[0]), msg[1]))
                sys.exit()

    def poke(self):
        """
        Sends poke commands to the Arduino. Used by hera_node_keep_alive script
        to send keep Arduinos from resetting.
        """
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(b'poke', arduinoSocket)

    def power_snap_relay(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP relay, must be turned on first before gaining
        control over individual SNAPs.
        """
        command = command.lower()
        if not self._command_OK(command, allowed=['on', 'off']):
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
        command = command.lower()
        if not self._command_OK(command, allowed=['on', 'off']):
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
        command = command.lower()
        if not self._command_OK(command, ['on', 'off']):
            return

        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(('PAM_%s' % command).encode(), arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def power_snap(self, snap_n, command):
        """
        Takes in the arduino IP address string and a command "on"/"off".
        Controls the power to SNAP snap_n.
        """
        if not self._command_OK(snap_n, allowed=[0, 1, 2, 3]):
            return
        command = command.lower()
        if not self._command_OK(command, allowed=['on', 'off']):
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
        # define arduino socket to send requests
        arduinoSocket = (self.arduinoAddress, sendPort)
        self.client_socket.sendto(b'reset', arduinoSocket)

        # Set delay before receiving more data
        time.sleep(self.throttle)

    def _command_OK(self, command, allowed):
        if self.control_type == 'remote':
            print("Remote control")
            return False
        if command in allowed:
            return True
        print("{} is not allowed ({})".format(command, allowed))
        return False
