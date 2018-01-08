import heartbeatClass
import argparse 

parser = argparse.ArgumentParser(description = 'This script instantiates the heartbeatClass with the IP address of the Arduino.',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ip_addr', action = 'store', help = 'Specify the IP address of the Arduino to keep alive (i.e. x.x.x.x)')
parser.add_argument('node', action = 'store', help = 'Specify the node number')
args = parser.parse_args()



h = heartbeatClass.Heartbeat()
h.keepAlive(args.ip_addr, int(args.node)) 

