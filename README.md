
# About
Code to monitor and control the arduinos in the node-control-module.
See the 'Monitor and Control Subsystem Description' document for more details: https://www.overleaf.com/read/njphvbyxchfs

# Installation

pip install .

# Usage

There are basically only two user scripts:  `hera_node_power.py` and `hera_node_get_status.py`.
Simple use is `hera_node_power.py start` to turn everything on or `hera_node_power.py stop` to turn everything off.

# Backend Instructions
### redis-server
To start the redis server, change into monitor-control/backend directory and run
```
redis-server redis.conf
```
redis.conf allows connections from different computers to be made to Redis server, which is critical.

### arduino-netboot
The arduino-netboot bootloader makes it possible to program Arduinos over ethernet. If you want to learn more about how it works, check out Emil's repo: https://github.com/esmil/arduino-netboot

So, to get Arduinos to download their sketch files from a TFTP server running on head node:
* connect the Arduino to an ICSP programmer. More detailed instructions on ICSP programmer are
in the Node Control Overleaf document: https://www.overleaf.com/read/dbfhdbcjkqvh
```shell
cd arduino-netboot
python bootloader_upload.py "{0x02,0x02,0x0A,0x01,0x01,0x00}"
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
**Warning:** Running all 3 scripts in the same screen session sometimes breaks the keep_alive script, so it is best to have 3 separate screen sessions.

hera_node_keep_alive.py and hera_node_cmd_check both take an optional node array as an argument. If no values are given then it'll will keep alive and check all the nodes that have status:node:x entries in Redis.

**ADDED FROM HERA_WR_CM**
Download the SevenSolutions WR-LEN interface library:

```
git submodule init
git submodule update

cd py7slib
bash ./Install.sh
```

Install as normal

```
python setup.py install
```
