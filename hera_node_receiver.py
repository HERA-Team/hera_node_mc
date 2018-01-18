import udpReceiverClass
#import argparse
#
#parser = argparse.ArgumentParser(description = 'This scripts instantiates the udpReceiverClass and kicks off the receiveUDP with Arduino IP as argument',
#                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
#parser.add_argument('ip_addr', action = 'store', help = 'Specify the Arduino IP address')
#
#args = parser.parse_args()




u = udpReceiverClass.UdpReceiver()
u.receiveUDP()

