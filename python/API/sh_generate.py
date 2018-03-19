import subprocess
from util import *

if __name__ == '__main__':
    # generate the sh files needed to deploy rules on switches
    K = 8

    for core in range(pow((K/2),2)):
        dp = int2dpid(1, core)
        filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/%s.sh" %(str(dp))
        f = open(filepath, 'a+')
        f.close()
        subprocess.call(['chmod','u+x','%s' %filepath])

    for pod in range(K):
        for sw in range(K/2):
            dp = int2dpid(2, sw, pod)
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/%s.sh" %(str(dp))
            f = open(filepath, 'a+')
            f.close()
            subprocess.call(['chmod','u+x','%s' %filepath])

            dp = int2dpid(3, sw, pod)
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/%s.sh" %(str(dp))
            f = open(filepath, 'a+')
            f.close()
            subprocess.call(['chmod','u+x','%s' %filepath])
