from scapy.all import *
import time
from socket import *

class TimeStamp(Packet):
    name = "TimeStamp"
    fields_desc = [
        LongField("preamble", 0),
        IntField("pktTMP", 0),
    ]

def main(num, src, dst, tmp):
    msg = "Sheng!"
    #p = TimeStamp(pktTMP=2) / Ether(dst='00:04:00:00:00:0%s' % h_dst) / IP(src='10.0.%s.10' % h_src, dst='10.0.%s.10' % h_dst) / TCP() / msg
    p = TimeStamp(pktTMP=tmp) / Ether(dst='00:04:00:00:00:%02x' %(dst-1)) / IP(src='10.0.%d.10' %(src-1), dst='10.0.%d.10' %(dst-1)) / TCP() / msg
    #hexdump(p)
    #print p.show()
    start_time = time.time()
    s = socket(AF_PACKET, SOCK_RAW)
    s.bind(('h%d-eth0' %src, 0))
    for i in range(num):
        #sendp(p, iface='h%d-eth0' %src)
        s.send(str(p))
        time.sleep(0.0001)
    print time.time() - start_time

if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
