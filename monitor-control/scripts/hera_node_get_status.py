import os
import argparse

parser = argparse.ArgumentParser(description = 'This scripts outputs the current node status',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node',action='store', help='Specify the node ID number (int from 0 to 29) to get the corresponding Redis data')
args = parser.parse_args()

os.system("redis-cli -h redishost hgetall status:node:%d"%(int(args.node)))
