from scapy.all import *
import struct
import sys

num = 0

def handle_pkt(pkt):
    global num
    pkt = str(pkt)
    #preamble = pkt[:8]
    #preamble_exp = "\x00" * 8
    #if preamble != preamble_exp: return
    #print hexdump(pkt)
    #pktTMP = struct.unpack("!I", pkt[62:66])[0]
    #print "tmp: %d" % pktTMP
    msg = pkt[66:len(pkt)]
    #print msg
    #print msg
    if msg.startswith('Sheng!'):
        num = num + 1
        #print "num: %d" % num
        #sys.stdout.flush()


def main(host, tot=10):
    sniff(iface = "%s-eth0" %host, timeout = tot,
          prn = lambda x: handle_pkt(x))
    print "receive: %d" %num

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    if len(sys.argv) == 3:
        main(sys.argv[1], int(sys.argv[2]))
