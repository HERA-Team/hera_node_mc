import sys
import argparse
import nodeControl

parser = argparse.ArgumentParser(description = 'This scripts outputs the current node status',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('node',action='store', type=int, help='Specify the node ID number (int from 0 to 29) to get the corresponding Redis data')
args = parser.parse_args()

print("Attempting to connect to the node control redis database on \'redishost\'...", end=' ')
sys.stdout.flush()
node = nodeControl.NodeControl(args.node)
print("OK")

print("Checking that staus key for Node %d exists in redis" % args.node, end=' ')
if node.check_exists():
    print("OK")
else:
    print("Missing key!")
    exit

power_stat_time, power_stat = node.get_power_status()
sensors_time, sensors = node.get_sensors()

print("Node %d power states:" % args.node)
print("  (Updated at %s)" % power_stat_time)
for key, val in sorted(power_stat.items()):
    print("  %s: %s" % (key, val))

print("Node %d sensor values:" % args.node)
print("  (Updated at %s)" % sensors_time)
for key, val in sorted(sensors.items()):
    print("  %s: %s" % (key, val))
