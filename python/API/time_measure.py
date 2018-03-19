import time
import subprocess

if __name__ == '__main__':
    cur = time.time()
    #time.sleep(0.004)
    subprocess.call(['ping', '-c', '100', '-i', '0.004', 'www.google.com'])
    print time.time() - cur
