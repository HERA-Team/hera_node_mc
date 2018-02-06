// This script, "sketch", is used to gather sensor data with an Arduino and 
// send it over the White Rabbit Network to a server inside a HERA container. 
// On boot, Arduino will request to get an IP address along with a latest
// sketch stored on the TFTP server in the container. Note that in order
// to get an IP, the Arduino needs to specify its MAC address - which does
// come with Arduino off the shelf. The initial bootloader MAC address
// is hardwired into the arduino-netboot software available in the
//  






//================ EEPROM Memory Map ================= 
// Address Byte       Data(8 bits)        Type                
//      0              ---- ----       MAC byte 0       
//      1              ---- ----       MAC byte 1       
//      2              ---- ----       MAC byte 2
//      3              ---- ----       MAC byte 3
//      4              ---- ----       MAC byte 4
//      5              ---- ----       MAC byte 5
//      6              ---- ----       unassigned 
//      7              ---- ----       unassigned
//      8              ---- ----       unassigned
//      9              ---- ----       unassigned
//      10             ---- ----       unassigned
//      .              ---- ----       unassigned
//      ..             ---- ----       unassigned
//      ...            ---- ----       unassigned
//      1024           ---- ----       unassigned





#include <Adafruit_SleepyDog.h>
#include <EEPROM.h>
#include <Ethernet.h>
#include <SPI.h>
#include <Adafruit_MCP9808.h>
#include <Adafruit_HTU21DF.h>
#include <SparkFunSX1509.h> // Include SX1509 library





// Define Arduino pins 
#define SNAP_RELAY_PIN 2 
#define FEM_PIN 5
#define PAM_PIN 6
#define SNAPv2_0_1_PIN 3
#define SNAPv2_2_3_PIN 7
#define RESET_PIN 4

// Redefine HIGH and LOW 
#define SNAP_RELAY_ON HIGH
#define SNAP_RELAY_OFF LOW
#define FEM_ON HIGH
#define FEM_OFF LOW
#define PAM_ON HIGH
#define PAM_OFF LOW
#define SNAPv2_0_1_ON LOW
#define SNAPv2_0_1_OFF HIGH
#define SNAPv2_2_3_ON LOW
#define SNAPv2_2_3_OFF HIGH 
#define RESET_OFF HIGH
#define RESET_ON LOW

// I2C addresses for the two MCP9808 temperature sensors
#define TEMP_TOP_ADDR 0x1B
#define TEMP_MID_ADDR 0x1A


#define VERBOSE

IPAddress serverIp(10, 1, 1, 1); // Server ip address
EthernetUDP UdpRcv; // UDP object to receive packets
EthernetUDP UdpSnd; // UDP object to send packets
EthernetUDP UdpSer; // UDP object to print serial debug info

byte mac[6];
unsigned int rcvPort = 8888;  // Assign port to receive commands on
unsigned int sndPort = 8889;  // Assign port to send data on
unsigned int serPort = 8890;  // Assign port to print debug statements


// Initializing buffer and data variables for receiving packets from the server
int packetSize;
char packetBuffer[UDP_TX_PACKET_MAX_SIZE];
String command; // String for data


unsigned int EEPROM_SIZE = 1024;
unsigned int eeadr = 0; // MACburner.bin writes MAC addres to the first 6 addresses of EEPROM

// I2C digital i/o serial board
const byte SX1509_ADDRESS = 0x3E;
SX1509 io;

unsigned int old_millis = millis();

// Sensor objects
Adafruit_MCP9808 mcpTop = Adafruit_MCP9808(); 
Adafruit_MCP9808 mcpMid = Adafruit_MCP9808(); 
Adafruit_HTU21DF htu = Adafruit_HTU21DF();



// struct for a UDP packet
struct status {
  unsigned long cpu_uptime_ms = -99;  // Arduino uptime since last reset
  float mcpTempTop = -99;             // Top temperature sensor value
  float mcpTempMid = -99;             // Mid temperature sensor value
  float htuTemp = -99;                // HTU21D sensor temperature value
  float htuHumid = -99;               // HTU21D sensor humidity value
  bool  snap_relay = false;           // Power status of SNAP relay
  bool  fem = false;                  // Power status of FEM 
  bool  pam = false;                  // Power status of PAM
  bool  snapv2_0_1 = false;           // Power status of SNAP 0 and 1
  bool  snapv2_2_3 = false;           // Power status of SNAP 2 and 3
  int   nodeID = -99;                 // Node ID as give by the digi I/O card hanging from PCB
  byte mac[6];                        // Arduino MAC address as assigned by arduino-netboot
} statusStruct;

void bootReset();
void serialUdp(String);
void parseUdpPacket();

void setup() {
  Watchdog.enable(8000);
  unsigned int startSetup = millis();
  
  
  // Initialize Serial port
  Serial.begin(57600);
  Serial.println("Running Setup..");

  
  // Setting pins appropriately. Very important to first deactivate the digital pins
  // because setting the pin as OUTPUT changes it's state and has caused problems with the reset pin 4 before
  // PSU that turns on White Rabbit is now hard wired to be turned on by the 5V Arduino signal, this prevents 
  // indefinite power cycle in case of a reset loop (which happens when ping/poke fail, the reset command was sent 
  // or all four sensors are off line.

  // Initialize and deactivate pins to avoid glitches
  // 8 way SNAP relay
  digitalWrite(SNAP_RELAY_PIN, SNAP_RELAY_OFF);
  pinMode(SNAP_RELAY_PIN, OUTPUT);
  digitalWrite(SNAP_RELAY_PIN, SNAP_RELAY_OFF);
   
  // FEM VAC pin: Active HIGH
  digitalWrite(FEM_PIN, FEM_OFF);
  pinMode(FEM_PIN, OUTPUT);
  digitalWrite(FEM_PIN, FEM_OFF);
  
  // PAM VAC pin: Active HIGH
  digitalWrite(PAM_PIN, PAM_OFF);
  pinMode(PAM_PIN, OUTPUT);
  digitalWrite(PAM_PIN, PAM_OFF);
  
  // SNAPv2_0_1_PIN: Active LOW so HIGH is off
  digitalWrite(SNAPv2_0_1_PIN, SNAPv2_0_1_OFF);
  pinMode(SNAPv2_0_1_PIN, OUTPUT);
  digitalWrite(SNAPv2_0_1_PIN, SNAPv2_0_1_OFF);

  // SNAPv2_2_3_PIN: Active LOW so HIGH is off
  digitalWrite(SNAPv2_2_3_PIN, SNAPv2_2_3_OFF);
  pinMode(SNAPv2_2_3_PIN, OUTPUT);
  digitalWrite(SNAPv2_2_3_PIN, SNAPv2_2_3_OFF);
  
  // Reset pin, Active LOW
  digitalWrite(RESET_PIN, RESET_OFF);
  pinMode(RESET_PIN, OUTPUT); 
  digitalWrite(RESET_PIN, RESET_OFF);
 
  // Read MAC address from EEPROM (burned previously with macBurner.bin sketch)
  for (int i = 0; i < 6; i++){
    mac[i] = EEPROM.read(eeadr);
    statusStruct.mac[i] = mac[i];
    ++eeadr;
  }
  

 
  // Start Ethernet connection, automatically tries to get IP using DHCP
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP, restarting sketch...");
    delay(10000);
  }
  Serial.println("Configured IP:");
  Serial.println(Ethernet.localIP());

  // Start UDP - HAS TO BE AFTER ETHERNET.BEGIN!!!!!!
  UdpRcv.begin(rcvPort);
  UdpSnd.begin(sndPort);
  UdpSer.begin(serPort);
  delay(1500); // delay to give time for initialization

  // Now that UDP is initialized, serialUdp can be used
  serialUdp("Running Setup..."); 
  serialUdp("Contents of the statusStruct.mac:");
  serialUdp(String(mac[6]));
  serialUdp("Individual values:");
  serialUdp(String(mac[0]));
  serialUdp(String(mac[1]));
  serialUdp(String(mac[2]));
  serialUdp(String(mac[3]));
  serialUdp(String(mac[4]));
  serialUdp(String(mac[5]));
 

  Serial.print("EEPROM contents:");
  serialUdp("EEPROM contents:");
  for (int i = 0; i < 8; i++) {
    Serial.print("Address: ");
    Serial.print(i);
    Serial.print("\t");
    Serial.print("Data: ");
    Serial.print(EEPROM.read(i));
    Serial.print("\t");   
    serialUdp("Address: ");
    serialUdp(String(i));
    serialUdp("Data: ");
    serialUdp(String(EEPROM.read(i)));
    
  }

  // Find Digital IO card and initialize its pin modes 
  if (io.begin(SX1509_ADDRESS)) {
      Serial.println("Digital IO card found!");
      serialUdp("Digital IO card found!");
      io.pinMode(0,INPUT);      // Serial
      io.digitalWrite(0,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(1,INPUT);      //   .
      io.digitalWrite(1,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(2,INPUT);      //   .
      io.digitalWrite(2,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(3,INPUT);      //   .
      io.digitalWrite(3,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(4,INPUT);      //   .
      io.digitalWrite(4,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(5,INPUT);      //   .
      io.digitalWrite(5,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(6,INPUT);      // Rev Number
      io.digitalWrite(6,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(7,INPUT);      //   .
      io.digitalWrite(7,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(8,INPUT);      // 1=production, 0=prototype
      io.digitalWrite(8,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(9,INPUT);      //  TBD
      io.digitalWrite(9,LOW);   // Activating PULL DOWN resistor on pin
      io.pinMode(10,INPUT);     //   .
      io.digitalWrite(10,LOW);  // Activating PULL DOWN resistor on pin
      io.pinMode(11,INPUT);     //   .
      io.digitalWrite(11,LOW);  // Activating PULL DOWN resistor on pin
      io.pinMode(12,OUTPUT);    //   .
      io.pinMode(13,OUTPUT);    //   .
      io.pinMode(14,OUTPUT);    //   .
      io.pinMode(15,OUTPUT);    //   .

      int nodeIDByte;
      for (int i=0; i<15; i++){
          nodeIDByte |= io.digitalRead(i) << i;
          statusStruct.nodeID = nodeIDByte;
      }
  }
  else {
    Serial.println("Digital io card not found");
    serialUdp("Digital io card not found");
  }

  unsigned int endSetup = millis();
  serialUdp("Time to run the Setup");
  serialUdp(String(endSetup-startSetup));
  // Set up a variable to determine when to send a UDP packet

}

 
void loop() {
     
    unsigned int startLoop = millis();
    
    
    // Find top temp sensor and read its value
    if (mcpTop.begin(TEMP_TOP_ADDR)) {
      statusStruct.mcpTempTop = mcpTop.readTempC();    
    }
    else {
      Serial.println("MCP9808 TOP not found");
#ifdef VERBOSE
      serialUdp("MCP9808 TOP not found");
#endif
      statusStruct.mcpTempTop = -99;
    }
 
    
    // Find middle temp sensor and take read value
    if (mcpMid.begin(TEMP_MID_ADDR)) {
      statusStruct.mcpTempMid = mcpMid.readTempC();
    }
    else {
      Serial.println("MCP9808 MID not found");
#ifdef VERBOSE
      serialUdp("MCP9808 MID not found"); 
#endif
      statusStruct.mcpTempMid = -99;
    }

    
    // Read humidity and temperature from HTU21DF sensor
    if (htu.begin()) {
      statusStruct.htuTemp = htu.readTemperature();
      statusStruct.htuHumid = htu.readHumidity();
    }
    else {
      Serial.println("HTU21DF not found!");
#ifdef VERBOSE
      serialUdp("HTU21DF not found!");
#endif
      statusStruct.htuTemp = -99;
      statusStruct.htuHumid = -99;

    }
    unsigned int new_millis = millis();

    if ((new_millis - old_millis) > 2000) {
      serialUdp(String(new_millis - old_millis));

      // Calculate the cpu uptime since the last Setup in seconds.
      statusStruct.cpu_uptime_ms = millis();
      
      // Send UDP packet to the server ip address serverIp that's listening on port sndPort
      UdpSnd.beginPacket(serverIp, sndPort); // Initialize the packet send
      UdpSnd.write((byte *)&statusStruct, sizeof statusStruct); // Send the struct as UDP packet
      UdpSnd.endPacket(); // End the packet
      Serial.println("UDP packet sent...");
      #ifdef VERBOSE
        serialUdp("UDP packet sent...");
      #endif
      old_millis = new_millis;   
   }
    // Check if request was sent to Arduino
    packetSize = UdpRcv.parsePacket(); // Reads the packet size
    
    if(packetSize>0) { //if packetSize is >0, that means someone has sent a request
      parseUdpPacket();    
    } 

    
    // Renew DHCP lease - times out eventually if this is removed
    Ethernet.maintain();
     

    unsigned int endLoop = millis();
#ifdef VERBOSE
    serialUdp("Loops runs for");
    serialUdp(String(endLoop-startLoop));
#endif
    delay(1000);
}





void parseUdpPacket(){

      UdpRcv.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE); //Read the data request
      String command(packetBuffer); //Convert char array packetBuffer into a string called command
      
      if (command == "poke") {
        Serial.println("I've been poked!");
#ifdef VERBOSE
        serialUdp("I've been poked!");
#endif
        Watchdog.reset();
      }
      
      else if (command == "snapRelay_on") {
	digitalWrite(SNAP_RELAY_PIN, SNAP_RELAY_ON);
	statusStruct.snap_relay = true;
	Watchdog.reset();
      }     
      
      else if (command == "snapRelay_off") {
        digitalWrite(SNAP_RELAY_PIN, SNAP_RELAY_OFF);
        statusStruct.snap_relay = false;
	Watchdog.reset();
      }
      
      else if (command == "snapv2_0_1_on"){
        Serial.println("snapv2_0_1 on");
        digitalWrite(SNAPv2_0_1_PIN, SNAPv2_0_1_ON);
        statusStruct.snapv2_0_1 = true;
	Watchdog.reset();
        }

      else if (command == "snapv2_0_1_off"){
        Serial.println("snapv2_0_1 off");
        digitalWrite(SNAPv2_0_1_PIN, SNAPv2_0_1_OFF);
        statusStruct.snapv2_0_1 = false;
	Watchdog.reset();
        }

      else if (command == "snapv2_2_3_on"){
        Serial.println("snapv2_2_3 on");
        digitalWrite(SNAPv2_2_3_PIN, SNAPv2_2_3_ON);
        statusStruct.snapv2_2_3 = true;
	Watchdog.reset();
        }

      else if (command == "snapv2_2_3_off"){
        Serial.println("snapv2_2_3 off");
        digitalWrite(SNAPv2_2_3_PIN, SNAPv2_2_3_OFF);
        statusStruct.snapv2_2_3 = false;
	Watchdog.reset();
        }

      else if (command == "FEM_on") {
        digitalWrite(FEM_PIN, FEM_ON);
        statusStruct.fem = true;
	Watchdog.reset();
      }
      
      else if (command == "FEM_off") {
        digitalWrite(FEM_PIN, FEM_OFF);
        statusStruct.fem = false;
	Watchdog.reset();
      }
      
      else if (command == "PAM_on") {
        Serial.println("PAM on");
        digitalWrite(PAM_PIN, PAM_ON);
        statusStruct.pam = true;
	Watchdog.reset();
      }
      
      else if (command == "PAM_off") {
        digitalWrite(PAM_PIN, PAM_OFF);
        statusStruct.pam = false;
	Watchdog.reset();
      }
      else if (command == "ping"){
        serialUdp("PONG");
        Watchdog.reset();

      }
              
      else if (command == "reset") {
        bootReset();
        }
      else {
        serialUdp("Unknown command received..");
      }    
      // Clear UDP packet buffer before sending another packet
      memset(packetBuffer, 0, UDP_TX_PACKET_MAX_SIZE);
    
}


void bootReset(){
   Serial.println("Resetting Bootloader..");
   serialUdp("Resetting Bootloader..");
   delay(500);
   digitalWrite(RESET_PIN, RESET_ON);  
}


void serialUdp(String message){
    String debugMessage = String("NODE " + String(int(statusStruct.nodeID)) + ":" + String(millis()) + ": " + message);
    UdpSer.beginPacket(serverIp, serPort);
    UdpSer.print(debugMessage);
    UdpSer.endPacket();
}



