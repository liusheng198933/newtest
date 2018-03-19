from scapy.all import *
import time
from socket import *

class TimeStamp(Packet):
    name = "TimeStamp"
    fields_desc = [
        LongField("preamble", 0),
        IntField("pktTMP", 0),
    ]

def main(num, src, dst, tmp=0):
    msg = "Sheng!"
    # pod = int(src.split('_')[1])
    # edge = int(src.split('_')[2])
    # x = int(src.split('_')[3])
    # src_ip='10.%d.%d.%d' %(pod, edge, x+1)
    # src_mac = '00:04:00:%02x:%02x:%02x' %(pod, edge, x+1)
    #
    # pod = int(dst.split('_')[1])
    # edge = int(dst.split('_')[2])
    # x = int(dst.split('_')[3])
    # dst_ip='10.%d.%d.%d' %(pod, edge, x+1)
    # dst_mac = '00:04:00:%02x:%02x:%02x' %(pod, edge, x+1)
    # p = TimeStamp(pktTMP=tmp) / Ether(dst=dst_mac, src=src_mac) / IP(src=src_ip, dst=dst_ip, ttl=32) / TCP() / msg

    #p = TimeStamp(pktTMP=2) / Ether(dst='00:04:00:00:00:0%s' % h_dst) / IP(src='10.0.%s.10' % h_src, dst='10.0.%s.10' % h_dst) / TCP() / msg
    p = TimeStamp(pktTMP=tmp) / Ether(dst='00:04:00:00:00:%02x' %(dst-1)) / IP(src='10.0.%d.10' %(src-1), dst='10.0.%d.10' %(dst-1), ttl=32) / TCP() / msg
    #hexdump(p)
    #print p.show()
    start_time = time.time()
    s = socket(AF_PACKET, SOCK_RAW)
    s.bind(('h%d-eth0' %src, 0))
    #s.bind(('h1-eth0', 0))
    for i in range(num):
        #sendp(p, iface='h%d-eth0' %src)
        s.send(str(p))
        time.sleep(0.0001)
    print time.time() - start_time

if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
