import subprocess
import sys

if __name__ == '__main__':
    filepath = '/home/shengliu/Workspace/mininet/haha/API/ping_result.txt'
    num = int(sys.argv[1])
    #p = subprocess.Popen(['sudo','hping3', '-1', '-c %d' %num, '-i u1000', '%s' % sys.argv[2]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = subprocess.Popen('./hping.sh', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = p.communicate()
    if out:
        print out
        with open(filepath, 'a+') as f:
            f.write(out)
            f.close()
