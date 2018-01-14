from scapy.all import sniff, sendp
import struct
import sys

num = 0

def handle_pkt(pkt):
    global num
    pkt = str(pkt)
    preamble = pkt[:8]
    preamble_exp = "\x00" * 8
    if preamble != preamble_exp: return
    pktTMP = struct.unpack("!I", pkt[8:12])[0]
    print "tmp: %d" % pktTMP
    msg = pkt[66:len(pkt)]
    #print msg
    if msg == 'Sheng!':
        num = num + 1
        print "num: %d" % num
    sys.stdout.flush()


def main(host):
    sniff(iface = "h%s-eth0" %host,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main(sys.argv[1])
