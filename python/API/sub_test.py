import subprocess
import time

if __name__ == '__main__':
    subprocess.Popen(['python', 'switch_deploy.py', '20', 'aaaaaaaa\n'])
    time.sleep(5)
    subprocess.Popen(['python', 'switch_deploy.py', '2', 'bbbbbbbbb\n'])
