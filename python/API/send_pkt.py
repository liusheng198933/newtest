from scapy.all import send, IP, TCP, Ether, Dot1Q, ICMP
import sys
import time

def trafficGenerate(num, h_src, h_dst):
    for i in range(num):
        #data = "This is Sheng! %d" %(i+1)
	    #data = "This is Sheng! %f" %(time.time())
        #pk = IP(src='10.3.0.1', dst='10.2.0.1')/TCP()/data
        pk = IP(src='%s' % h_src, dst='%s' % h_dst)/ICMP()
        send(pk)
        #send(Ether()/Dot1Q(vlan=10)/data)

if __name__ == '__main__':
    # need to provide mac address to avoid broadcast
    cur = time.time()
    trafficGenerate(int(sys.argv[1]), sys.argv[2], sys.argv[3])
    print time.time() - cur
