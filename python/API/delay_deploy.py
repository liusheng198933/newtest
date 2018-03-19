import time
import random
import subprocess
import sys

if __name__ == '__main__':
    d = random.normalvariate(150, 50) / 1000
    while d <= 0:
        d = random.normalvariate(150, 50) / 1000
    time.sleep(d)
    filepath = "/home/shengliu/Workspace/mininet/haha/API/time/sb_cmd_%d.sh" %(int(sys.argv[1]))
    subprocess.call(filepath)
