
# nodeControlClass usage
To clone the sensor libraries together with code use 'git clone --recursive https://github.com/reeveress/monitor-control.git'

### Usage 
* import the nodeControlClass into ipython  
* instantiate a nodeControl class object: 
* n = nodeControlClass.NodeControl() 
* Check out the available functions via n.[tab] 

you'll see something like this:

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


          

The power methods provide the ability to send power commands to Arduino, through the Redis database.
All power methods take the node number and command as arguments. Node number is a digit from 0-29 and command
is string with value 'on' or 'off'. 


# arduino-mk usage
***You must have the Arduino IDE and avr-gcc toolchain installed on the computer you're compiling mc_arduino.ino***  
Tested with Arduino 1.6.5 and Arduino 1.8.5: https://www.arduino.cc/en/Main/Software   
Once you download the Arduino IDE, you're going to have to update its path in the Makefile inside the sketch directory
you're working on. 
to create binary file out of c script (.ino) using arduino-mk:  

* go into mc_arduino folder
* run make clean to get rid of old versions
* edit mc_arduino.ino using vim or nano
* run make
* build-ethernet folder is created that has the .bin file, among others
* copy .bin file to the /srv/tftp/arduino directory on the server


