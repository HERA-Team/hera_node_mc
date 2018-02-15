import redis
import time
        
class NodeControl():
        """
        This Class is used to control power to PAM, FEM, SNAPs 0 & 1 and 2 & 3 and get status information
        through the Redis database running on the hera-digi-vm server.
        """

        def __init__(self, node, serverAddress = "hera-digi-vm"):
                """ 
                Takes in the node argument, which is an integer value from
                1 to eventually 30. It's set by the digital I/O card attached to the Power and Control Box.
                Takes in the string ip address or the host name of the Redis database host server, default
                is hera-digi-vm. Returns the NodeControlClass object.
                """ 

                self.node = node    
                self.r = redis.StrictRedis(serverAddress)

        def get_sensors(self):
                """
                Returns the sensor values inside the node. 
                """
                    
                timestamp = self.r.hget("status:node:%d"%self.node, "timestamp") 
                temp_mid = float(self.r.hget("status:node:%d"%self.node,"temp_mid"))
                temp_top = float(self.r.hget("status:node:%d"%self.node,"temp_top"))
                temp_humid = float(self.r.hget("status:node:%d"%self.node,"temp_humid"))
                sensors = {'timestamp':timestamp,'temp_top':temp_top,'temp_mid':temp_mid,'temp_humid':temp_humid}
                return sensors

        def get_power_status(self):
                """
                Returns the current power status of SNAP relay, SNAPs, PAM and FEM. 
                """

                timestamp = self.r.hget("status:node:%d"%self.node, "timestamp") 
                print(self.r.hget("status:node%d"%self.node,"power_snap_0_1"))
                power_snap_relay = self.r.hget("commands:node:%d"%self.node,"power_snap_relay")
                power_snap_0_1 = self.r.hget("commands:node:%d"%self.node,"power_snap_0_1")
                power_snap_2_3 = self.r.hget("commands:node:%d"%self.node,"power_snap_2_3")
                power_pam = self.r.hget("commands:node:%d"%self.node,"power_pam")
                power_fem = self.r.hget("commands:node:%d"%self.node,"power_fem")
                statii = {'timestamp':timestamp,'power_snap_relay':power_snap_relay,'power_snap_0_1':power_snap_0_1,'power_snap_2_3':power_snap_2_3,
                'power_pam':power_pam,'power_fem':power_fem}
                return statii

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


        def power_snap_0_1(self, command):
                """
                Takes in a string value of 'on' or 'off'.
                Controls the power to SNAP 0 and 1.
                """

                self.r.hset("commands:node:%d"%self.node,"power_snap_0_1_ctrl_trig",True)
                self.r.hset("commands:node:%d"%self.node,"power_snap_0_1_cmd",command)
                print("SNAP 0 and 1 power is %s"%command)


        def power_snap_2_3(self, command):
                """
                Takes in a string value of 'on' or 'off'.
                Controls the power to SNAP 2 and 3.
                """

                self.r.hset("commands:node:%d"%self.node,"power_snap_2_3_ctrl_trig",True)
                self.r.hset("commands:node:%d"%self.node,"power_snap_2_3_cmd",command)
                print("SNAP 2 and 3 power is %s"%command)


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
         

