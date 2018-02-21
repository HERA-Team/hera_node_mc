
# About

# Installation

#### git clone --recursive https://github.com/reeveress/monitor-control.git
--recursive specifies all the submodules.  
```shell
 cd monitor-control
 sudo python setup.py install 
```
this installs the package to your system, so you can run import nodeControl module and scripts from any directory. For example, running 'hera_node_turn_on.py 4 -p' from anywhere in your system will send a turn on command to the PAM inside node 4. 


### Usage 
#### Make sure you can connect to Redis database running on the monitor-control head node before proceeding
```python
 ipython  
 import nodeControl   
 n = nodeControlClass.NodeControl(nodeID [, redisServerHostName])   
 n.[tab] 
```
you'll see this for the prototype Node:
```python
n.get_sensors  
n.get_power_status                 
n.power_snap_relay      
n.power_snap_0_1       
n.power_snap_2_3       
n.power_fem   
n.power_pam    
n.reset  
```
The power methods provide the ability to send power commands to Arduino, through the Redis database.
All power methods take the node number and command as arguments. Node number is a digit from 0-29 and command
is string with value 'on' or 'off'. 

# arduino-mk usage
***You must have the Arduino IDE and avr-gcc toolchain installed on the computer you're compiling mc_arduino.ino***  
Tested with Arduino 1.6.5 and Arduino 1.8.5: https://www.arduino.cc/en/Main/Software   
Once you download the Arduino IDE, you're going to have to update its path in the Makefile inside the sketch directory
you're working on. Change the line with ARDUINO_DIR to point to your Arduino IDE source files. 

Once you have done that, you're ready to create a binary file out of the .ino file using arduino-mk:  

* go into mc_arduino folder
* run make clean to get rid of old versions
* edit mc_arduino.ino using vim or nano
* run make
* build-ethernet folder is created that has the .bin file, among others
* copy .bin file to the /srv/tftp/arduino directory on the server

# arduino-netboot  
To burn the bootloader onto the Arduino so it will download the sketch from the server's tftp folder you need to first edit the netboot.c file to assign the proper MAC address.  
It looks like this:

// EDIT THE LINE BELOW TO UPDATE ARDUINO MAC ADDRESS!!!!!  
#define MAC_ADDRESS { 0x00, 0x08, 0xDC, 0x00, 0x00, 0x4F }  

* Once the MAC has been updated, connect the Arduino to ICSP programmer. More detailed instruction on ICSP programmer are
in the Node Control Overleaf document: https://www.overleaf.com/read/dbfhdbcjkqvh  
* go into arduino-netboot folder and run 'make clean'  
* run 'make bootloader'
* Make sure the bootloader upload went smoothly and there are no error messages  
* run 'make fuses' 
* The bootloader is now uploaded. If you want to learn more about how it works, checkout Emil's page: https://github.com/esmil/arduino-netboot

# Arduino Sketches and Server-end Scripts
Arduinos unfortunately do not come with a built-in MAC address, that's why we had to manually edit the netboot.c file inside the arduino-netboot submodule. In order for networking to work properly in the data collection/power control script, Arduino needs to have a memory of its assigned MAC address. The current solution is to first run a sketch that burns the MAC onto the EEPROM (macBurner.bin). mc_arduino sketch will read the EEPROM memory cells and establish a connection to the server using that MAC. There's probably a better way to do this but I haven't found a solution yet. 
* go into macBurner folder inside arduino-mk  
* edit macBurner.ino with the proper MAC address  
* run 'make clean'  
* run 'make'  
* the make command should create a build-ethernet folder with .bin file in it  
* move .bin to /srv/tftp/arduino folder and power up the Arduino  
* Assuming networking was setup correctly, you should now see Arduino DHCPing and TFTPing (run 'tail -f /var/log/syslog' and that will log the DHCP activity on the server)  
* Now that Arduino has a MAC burned, you're ready to run the mc_arduino.bin sketch  
* place the sketch in the /srv/tftp/arduino folder and make sure to edit /etc/dnsmasq.conf file accordingly:  

dhcp-mac=arduino0,00:08:dc:00:00:6A  
dhcp-mac=arduino2,00:08:dc:00:02:4f  
.  
.  
.  
dhcp-boot=net:arduino0,mc_arduino.bin 

* Make sure your tags(arduino0, arduino2) and MAC addresses map correctly. Change the dhcp-boot line to macBurner.bin when you're at the MAC burning stage.  
* go into ipython  
* import udpSenderClass  
* u = udpSenderClass.UdpSender()  
* u.reset('Arduino in question IP address')  
* This should reset the Arduino bootloader and force it to look at the new sketch in the /srv/tftp folder  
* start the udpReceiver.py script in a screen session:  
screen -S udpReceiver // takes you to a screen session  
python udpReceiver.py new_arduino_ip_address > /dev/null 2>&1 & // this starts a script that grabs data packets from the Arduino and updates Redis with the new sensor and status values.  

Make sure to edit /etc/hosts and /etc/ethers so the new Arduino is recognized by the server and is given a proper IP address. 

