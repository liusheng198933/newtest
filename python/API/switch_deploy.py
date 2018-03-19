import sys
import time

if __name__ == '__main__':
    time.sleep(int(sys.argv[1]))
    filepath = "/home/shengliu/Workspace/mininet/haha/API/ping_result.txt"
    with open(filepath, 'a+') as f:
        f.write("cao ni ma: %s" %sys.argv[2])
        f.close()
