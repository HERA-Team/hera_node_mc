import nodeControlClass
import time

n = nodeControlClass.NodeControl()

while 1:
    n.power_snap_relay(0,"poke")
    time.sleep(.1)
