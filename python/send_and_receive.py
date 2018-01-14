from scapy.all import *
import sys
import threading

def handle_pkt(pkt):
    pkt = str(pkt)
    msg = pkt[54:len(pkt)]
    print "Received packet on port 2, exiting"
    print msg
    sys.stdout.flush()
    sys.exit(0)


class Receiver(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def received(self, p):
        print "Received packet on port 2, exiting"
        sys.exit(0)

    def run(self):
        sniff(iface="veth2", prn=lambda x: handle_pkt(x))


def main():
    Receiver().start()

    p = Ether(dst='00:04:00:00:00:01') / IP(src='10.0.0.10', dst='10.0.1.10') / TCP() / "aaaaaaaaaaaaaaaaaaa"

    print "Sending packet on port 0, listening on port 2"
    time.sleep(1)
    sendp(p, iface="veth1")


if __name__ == '__main__':
    main()
