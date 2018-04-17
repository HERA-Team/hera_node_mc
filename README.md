
# About
The prototype node and the production nodes have different architectures and therefore different software. For example, in prototype node, SNAP power is controlled in pairs (SNAP 0 & 1 or SNAP 2 & 3) and in production nodes, the SNAP power is controlled separately. Make sure you're using the right branch, either **prototype-node** or **production-node**.

See the 'Monitor and Control Subsystem Description' document for more details: https://www.overleaf.com/read/njphvbyxchfs
# Installation

#### git clone --recursive https://github.com/reeveress/monitor-control.git
--recursive makes sure the git clone command downloads all the submodules. 
```shell
 cd monitor-control
 sudo python setup.py install 
```
this installs the monitor-control package to your system, so you can import the nodeControl module and scripts from any directory. For example, running 'hera_node_turn_on.py 4 -p' from anywhere in your system will send 'on' command to the PAM inside node 4. 


# Usage 
### iPython
##### Make sure you can connect to Redis database running on the monitor-control head node before proceeding

```python
 ipython  
 import nodeControl   
 n = nodeControl.NodeControl(nodeID [, redisServerHostName])    
```
nodeID is a digit from 1 to 30. redisServerHostName is either a hostname or ip address of the monitor-control head node that hosts the Redis database. Default value is hera-digi-vm but that could change in the future.   
Running n.[tab key]  returns:  

```python
n.get_sensors  
n.get_power_status                 
n.power_snap_relay      
n.power_snap_0
n.power_snap_1 
n.power_snap_2      
n.power_snap_3      
n.power_fem   
n.power_pam    
n.reset  
```
The power methods provide the ability to send power commands to Arduino, through the Redis database.
All power methods take a string command 'on' or 'off' as an argument. 
### Scripts
```shell
hera_node[tab]
```
will return these scripts
```shell
hera_node_cmd_check.py           hera_node_serial.py
hera_node_data_dump.py           hera_node_turn_off.py
hera_node_get_status.py          hera_node_turn_off_sender.py
hera_node_keep_alive.py          hera_node_turn_on.py
hera_node_receiver.py            hera_node_turn_on_sender.py
hera_node_serial_dump.py
```
These are the  scripts that are available to HERA Team:
```shell
hera_node_turn_on.py     	 hera_node_get_status.py  
hera_node_turn_off.py   	 hera_node_data_dump.py 
```
* hera\_node\_turn\_on.py requires a node ID argument and a command argument in a form of a flag (-p for PAM, -r for relay, etc.)
* hera\_node\_get\_status.py returns the status:node:x Redis key contents.
* hera\_node\_data\_dump.py takes in node ID, filename and optional time interval at which to dump the Redis status:node:x contents to the file.

# Backend Instructions

### arduino-netboot  
The arduino-netboot bootloader makes it possible to program Arduinos over ethernet. If you want to learn more about how it works, check out Emil's repo: https://github.com/esmil/arduino-netboot  

So, to get Arduinos to download their sketch files from a TFTP server running on head node: 
* connect the Arduino to an ICSP programmer. More detailed instructions on ICSP programmer are
in the Node Control Overleaf document: https://www.overleaf.com/read/dbfhdbcjkqvh  
```shell
cd arduino-netboot
python netboot_upload.py "{0x00,0x08,0xdc,0x00,0x05,0x4f}"
```
note that the MAC address of your choosing should be specified just as shown above, in quotes and curly braces, for netboot_upload.py to parse it.  
 
Once MAC is burned to the Arduino, update the /etc/dnsmasq.conf file accordingly with the corresponding tab
```shell  
dhcp-mac=arduino5,00:08:DC:00:05:4F  
 ```
 
Make sure to edit /etc/hosts and /etc/ethers so the new Arduino is recognized by the server and is given a proper IP address. 
### arduino-mk

***You must have the Arduino IDE and avr-gcc toolchain installed before compiling mc_arduino.ino***  
Tested with Arduino 1.6.5 and Arduino 1.8.5: https://www.arduino.cc/en/Main/Software   
Once you download the Arduino IDE, you're going to have to update its path in the Makefile inside the sketch directory
you're working on. Change the line with ARDUINO_DIR to point to your Arduino IDE source files. 

Once you have done that, you're ready to create a binary file out of the .ino file using arduino-mk:  
```shell
cd arduino-mk/mc_arduino
make clean
# edit mc_arduino.ino   
make
```
* Running make creates a build-ethernet folder that contains a .bin file, among others.
* Copy the .bin file to the /srv/tftp/arduino directory on the monitor-control head node.
* Arduinos with a burned arduino-netboot bootloader will request mc_arduino.bin file from the TFTP server running
on monitor-control head node. 


# Poking, Capture and Command Forwarding Scripts
Order at which these scripts are started matters. You want to run these in a screen session so a broken pipe to the monitor-control head node doesn't kill the terminal session. Start with hera_node_receiver.py so hera_node_keep_alive.py script can successfully get the IP of an Arduino to poke from the status:node:x key. hera_node_cmd_check.py checks for flags set by the front end user and sends commands to the Arduinos - failing to start this will prevent user from sending commands. 

A screen session would look something like this:

```shell
screen -S backend // takes you to a screen session  
hera_node_receiver.py > /dev/null 2>&1 & 
hera_node_keep_alive.py > /dev/null 2>&1 & 
hera_node_cmd_check.py > /dev/null 2>&1 & 
ctrl-A D // exit screen session  
```
hera_node_keep_alive.py and hera_node_cmd_check both take an optional node array as an argument. If no values are given then it'll will keep alive and check all the nodes that have status:node:x entries in Redis. 
