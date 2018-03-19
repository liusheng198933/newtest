from scapy.all import *
import time
from socket import *

class TimeStamp(Packet):
    name = "TimeStamp"
    fields_desc = [
        LongField("preamble", 0),
        IntField("pktTMP", 0),
    ]

def main(num, src, dst, delay=0, tmp=0):
    msg = "Sheng!"
    pod = int(src.split('_')[1])
    edge = int(src.split('_')[2])
    x = int(src.split('_')[3])
    src_ip='10.%d.%d.%d' %(pod, edge, x+1)
    src_mac = '00:04:00:%02x:%02x:%02x' %(pod, edge, x+1)

    pod = int(dst.split('_')[1])
    edge = int(dst.split('_')[2])
    x = int(dst.split('_')[3])
    dst_ip='10.%d.%d.%d' %(pod, edge, x+1)
    dst_mac = '00:04:00:%02x:%02x:%02x' %(pod, edge, x+1)
    #p = TimeStamp(pktTMP=tmp) / Ether(dst=dst_mac, src=src_mac) / IP(src=src_ip, dst=dst_ip) / TCP(seq=) / msg

    #p = TimeStamp(pktTMP=2) / Ether(dst='00:04:00:00:00:0%s' % h_dst) / IP(src='10.0.%s.10' % h_src, dst='10.0.%s.10' % h_dst) / TCP() / msg
    #p = TimeStamp(pktTMP=tmp) / Ether(dst='00:04:00:00:00:%02x' %(dst-1)) / IP(src='10.0.%d.10' %(src-1), dst='10.0.%d.10' %(dst-1), ttl=32) / TCP() / msg
    #hexdump(p)
    #print p.show()

    s = socket(AF_PACKET, SOCK_RAW)
    s.bind(('%s-eth0' %src, 0))
    #s.bind(('h1-eth0', 0))
    p = TimeStamp(pktTMP=tmp) / Ether(dst=dst_mac, src=src_mac) / IP(src=src_ip, dst=dst_ip, ttl=15) / TCP() / msg
    start_time = time.time()
    for i in range(num):
        #sendp(p, iface='h%d-eth0' %src)
        #msg = "Sheng!" + str(i)
        s.send(str(p))
        #print len(str(p))
        #print str(p)[46:]
        #hexdump(p)
        #print p.show()
        #print struct.unpack("!I", str(p)[62:66])[0]
        #print int(str(p)[62:66],16)
        time.sleep(delay)
    print "sent" + str(num)
    print time.time() - start_time

if __name__ == '__main__':
    if len(sys.argv) == 4:
        main(int(sys.argv[1]), sys.argv[2], sys.argv[3])
    if len(sys.argv) == 5:
        main(int(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4]))
    if len(sys.argv) == 6:
        main(int(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5]))
