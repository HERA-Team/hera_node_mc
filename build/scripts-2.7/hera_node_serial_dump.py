import os 
import time
import argparse
import sys

parser = argparse.ArgumentParser(description = 'This scripts dumps the serial output of all of the Arduinos into a text file every x seconds - default is 300.',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('file_name', action = 'store', help = 'Specify the file name to dump Redis data to i.e. datasetMMDDYY.txt')
parser.add_argument('-t', action = 'store', dest = 'interval', default = 300, help = 'Specify the time interval, in seconds, for data collection')

args = parser.parse_args()

try:
    while True:
        os.system("python hera_node_serial.py >> %s"%args.file_name)
        time.sleep(float(args.interval))

except KeyboardInterrupt:
    print('Interrupted')
    sys.exit(0)

