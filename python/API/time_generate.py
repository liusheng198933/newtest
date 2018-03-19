import subprocess

def time_file_generate():
    for i in range(200):
        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug_%d.txt" %(i)
        f = open(filepath, 'w+')
        f.close()
        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/sb_cmd_%d.sh" %(i)
        f = open(filepath, 'w+')
        f.close()
        subprocess.call(['chmod','u+x','%s' %filepath])
    filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug.txt"
    f = open(filepath, 'w+')
    f.close()

if __name__ == '__main__':

    for i in range(200):
        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug_%d.txt" %(i)
        f = open(filepath, 'w+')
        f.close()
        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/sb_cmd_%d.sh" %(i)
        f = open(filepath, 'w+')
        f.close()
        subprocess.call(['chmod','u+x','%s' %filepath])
