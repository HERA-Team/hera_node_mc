import redis
import time
        
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


    def get_sensors(self):
        """
        Returns the a tuple (timestamp, sensors), where
        sensors is a dictionary of sensor values, and timestamp
        is a string describing when the values were last updated in redis
        """
            
        timestamp = self.r.hget("status:node:%d"%self.node, "timestamp") 
        temp_mid = float(self.r.hget("status:node:%d"%self.node,"temp_mid"))
        temp_top = float(self.r.hget("status:node:%d"%self.node,"temp_top"))
        temp_humid = float(self.r.hget("status:node:%d"%self.node,"temp_humid"))
        humid = float(self.r.hget("status:node:%d"%self.node,"humid"))
        sensors = {'temp_top':temp_top,'temp_mid':temp_mid,
                    'temp_humid':temp_humid,'humid':humid}
        return timestamp, sensors


    def get_power_status(self):
        """
        Returns the a tuple (timestamp, statii), where
        statii is a dictionary of power status values, and timestamp
        is a string describing when the values were last updated in redis
        """

        timestamp = self.r.hget("status:node:%d"%self.node, "timestamp") 
        power_snap_relay = self.r.hget("status:node:%d"%self.node,"power_snap_relay")
        power_snap_0 = self.r.hget("status:node:%d"%self.node,"power_snap_0")
        power_snap_1 = self.r.hget("status:node:%d"%self.node,"power_snap_1")
        power_snap_2 = self.r.hget("status:node:%d"%self.node,"power_snap_2")
        power_snap_3 = self.r.hget("status:node:%d"%self.node,"power_snap_3")
        power_pam = self.r.hget("status:node:%d"%self.node,"power_pam")
        power_fem = self.r.hget("status:node:%d"%self.node,"power_fem")
        statii = {'power_snap_relay':power_snap_relay,'power_snap_0':power_snap_0,'power_snap_1':power_snap_1,'power_snap_2':power_snap_2,'power_snap_3':power_snap_3,
        'power_pam':power_pam,'power_fem':power_fem}
        return timestamp, statii

    def check_exists(self):
        """
        Check that the status key corresponding to this node exists.
        Return True if it does, else False.
        """
        return "status:node:%d" % self.node in self.r.keys()

    # Power Control Methods 
    def power_snap_relay(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP relay. The SNAP relay
        has to be turn on before sending commands to individual SNAPs.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_relay_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_snap_relay_cmd",command)
        print("SNAP relay power is %s"%command)


    def power_snap_0(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 0.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_0_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_snap_0_cmd",command)
        print("SNAP 0 power is %s"%command)


    def power_snap_1(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 1.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_1_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_snap_1_cmd",command)
        print("SNAP 1 power is %s"%command)


    def power_snap_2(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 2.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_2_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_snap_2_cmd",command)
        print("SNAP 2 power is %s"%command)


    def power_snap_3(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to SNAP 3.
        """

        self.r.hset("commands:node:%d"%self.node,"power_snap_3_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_snap_3_cmd",command)
        print("SNAP 3 power is %s"%command)


    def power_fem(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to FEM.
        """

        self.r.hset("commands:node:%d"%self.node,"power_fem_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_fem_cmd",command)
        print("FEM power is %s"%command)


    def power_pam(self, command):
        """
        Takes in a string value of 'on' or 'off'.
        Controls the power to PAM.
        """

        self.r.hset("commands:node:%d"%self.node,"power_pam_ctrl_trig",True)
        self.r.hset("commands:node:%d"%self.node,"power_pam_cmd",command)
        print("PAM power is %s"%command)


    def reset(self):
        """
        Sends the reset command to Arduino which restarts the bootloader. 
        """

        self.r.hset("commands:node:%d"%self.node,"reset",True)
        print("Arduino is resetting...")
     

