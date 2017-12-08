'''
	monitor control database class
'''
import redis
import time
        
PORT = 6379
#serverAddress = '10.1.1.1'


class NodeControl():
    def __init__(self,serverAddress = "hera-digi-vm"):
        """ 
        Takes in the string ip address or the host name of the Redis database host server.
        Returns the NodeControlClass object
        """ 
            
    # Class object init makes a connection with our 1U server to grap redis database values
    # Redis bind to port 6379 by default
	self.r = redis.StrictRedis(serverAddress)

    # Redis key values/status methods
    def get_sensors(self,node):
        """
        Takes in the node argument, which is an integer value from
        0 to eventually 29.
        Returns the temperature sensor values inside the node. 
        """
            
        timestamp = self.r.hmget("status:node:%d"%node, "timestamp")[0] 
        temp_mid = float(self.r.hmget("status:node:%d"%node,"temp_mid")[0])
        temp_top = float(self.r.hmget("status:node:%d"%node,"temp_top")[0])
        temp_bot = float(self.r.hmget("status:node:%d"%node,"temp_bot")[0])
        temp_humid = float(self.r.hmget("status:node:%d"%node,"temp_humid")[0])
        sensors = {'timestamp':timestamp,'temp_top':temp_top,'temp_mid':temp_mid,'temp_bot':temp_bot,'temp_humid':temp_humid}
        return sensors

    def get_power_status(self,node):
        """
        Takes in the node argument, which is an integer value from 
        0 to eventually 29.
        Returns the current power status of snaps, pam and fem. 
        """
        timestamp = self.r.hmget("status:node:%d"%node, "timestamp")[0] 
        power_snap_0 = self.r.hmget("status:node%d"%node,"power_snap_0")[0]
        power_snap_1 = self.r.hmget("status:node%d"%node,"power_snap_1")[0]
        power_snap_2 = self.r.hmget("status:node%d"%node,"power_snap_2")[0]
        power_snap_3 = self.r.hmget("status:node%d"%node,"power_snap_3")[0]
        power_pam = self.r.hmget("status:node%d"%node,"power_pam")[0]
        power_fem = self.r.hmget("status:node%d"%node,"power_fem")[0]
        statii = {'timestamp':timestamp,'power_snap_0':power_snap_0,'power_snap_1':power_snap_1,'power_snap_2':power_snap_2,
        'power_snap_3':power_snap_3,'power_pam':power_pam,'power_fem':power_fem}
        return statii
        
#    def getHumid(self,node):
#        """
#        Gives back the humidity value inside the node. 
#        Takes in the node arguments, which is an integer value from
#        0 to eventually 29
#        """
#        return self.r.hmget("status:node:%d"%node,"humidities")


    # Power Control Methods 
    
    def power_snap_relay(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends a command to Arduino to turn the SNAP relay on or off. The SNAP relay
        has to be turn on before sending commands to individual SNAPs.
        """

        self.r.hset("status:node:%d"%node,"power_snap_relay_ctrl",True)
        self.r.hset("status:node:%d"%node,"power_snap_relay_cmd",command)
        print("Snap relay power is %s"%command)


    def power_snap_0(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends the on/off command to SNAP 0.
        """
        self.r.hset("status:node:%d"%node,"power_snap_0_ctrl_trig",True)
        self.r.hset("status:node:%d"%node,"power_snap_0_cmd",command)
        print("SNAPv2_0 power is %s"%command)


    def power_snap_1(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends the on/off command to SNAP 1.
        """
        self.r.hset("status:node:%d"%node,"power_snap_1_ctrl_trig",True)
        self.r.hset("status:node:%d"%node,"power_snap_1_cmd",command)
        print("SNAPv2_1 power is %s"%command)


    def power_snap_2(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends the on/off command to SNAP 2.
        """
        self.r.hset("status:node:%d"%node,"power_snap_2_ctrl_trig",True)
        self.r.hset("status:node:%d"%node,"power_snap_2_cmd",command)
        print("SNAPv2_2 power is %s"%command)


    def power_snap_3(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends the on/off command to SNAP 3.
        """
        self.r.hset("status:node:%d"%node,"power_snap_3_ctrl_trig",True)
        self.r.hset("status:node:%d"%node,"power_snap_3_cmd",command)
        print("SNAPv2_3 power is %s"%command)


    def power_fem(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends the on/off command to FEM.
        """
        self.r.hset("status:node:%d"%node,"power_fem_ctrl_trig",True)
        self.r.hset("status:node:%d"%node,"power_fem_cmd",command)
        print("FEM power is %s"%command)


    def power_pam(self, node, command):
        """
        Takes in the node number, int from 0 to 29, and a string command "on" or "off".
        Sends the on/off command to PAM.
        """
        self.r.hset("status:node:%d"%node,"power_pam_ctrl_trig",True)
        self.r.hset("status:node:%d"%node,"power_pam_cmd",command)
        print("PAM power is %s"%command)


    def reset(self,node):
        """
        Takes in the node number, int from 0 to 29.
        Sends the reset command to Arduino which restarts the bootloader, not just the sketch. 
        """
        self.r.hset("status:node:%d"%node,"reset",True)
        print("Set reset flag to True")
         

