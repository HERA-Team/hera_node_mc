#! /usr/bin/env python
import os
import argparse

parser = argparse.ArgumentParser(description='This scripts dumps the contents of the Redis '
                                 'database into a text file.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('file_name', help='Specify the file name to dump Redis data to '
                    'i.e. datasetMMDDYY.txt')
parser.add_argument('node_id', help='Specify the node ID number (int from 0 to 29) to '
                    'get the corresponding Redis data')

args = parser.parse_args()

os.system("redis-cli hgetall status:node:%d >> %s" % (int(args.node_id), args.file_name))
