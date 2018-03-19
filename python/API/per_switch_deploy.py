import sys
import subprocess

if __name__ == '__main__':
    step_ini = int(sys.argv[1])
    step_fin = int(sys.argv[2])
    dp = str(sys.argv[3])
    for i in range(step_ini, step_fin):
        filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(i, dp)
        subprocess.call("%s" %filepath)
