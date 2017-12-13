import os 
import time
import argparse

parser = argparse.ArgumentParser(description = 'This scripts dumps the contents of the Redis database into a text file every x seconds - default is 300.',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('file_name', action = 'store', help = 'Specify the file name to dump Redis data to i.e. datasetMMDDYY.txt')
parser.add_argument('-t', action = 'store', dest = 'interval', help = 'Specify the time interval, in seconds, for data collection')

args = parser.parse_args()

while True:
    os.system("redis-cli hgetall status:node:0 >> %s"%args.file_name)
    time.sleep(300)

    
