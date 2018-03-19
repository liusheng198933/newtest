from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Controller, OVSKernelSwitch, RemoteController, Ryu
from time import sleep
import argparse
#from mininet.node import Ryu


#class ryuController( Controller ):
#    def __init__( self, name, cdir='/home/shengliu/Workspace/mininet/custom/', command='ryu-manager', cargs='/home/shengliu/Workspace/ryu/ryuApp/dummyRouter.py', **kwargs ):
#        Controller.__init__( self, name, cdir=cdir, command=command, cargs=cargs, **kwargs)




class MyTopod( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches

        host1 = self.addHost('h1', ip='10.0.1.0')
        host2 = self.addHost('h2', ip='10.0.1.1')
        host3 = self.addHost('h3', ip='10.0.1.2')
        host4 = self.addHost('h4', ip='10.0.1.3')
        host5 = self.addHost('h5', ip='10.0.1.4')
        host6 = self.addHost('h6', ip='10.0.1.5')
        host7 = self.addHost('h7', ip='10.0.1.6')
        host8 = self.addHost('h8', ip='10.0.1.7')
        host9 = self.addHost('h9', ip='10.0.1.8')
        host10 = self.addHost('h10', ip='10.0.1.9')
        host11 = self.addHost('h11', ip='10.0.1.10')
        host12 = self.addHost('h12', ip='10.0.1.11')
        host13 = self.addHost('h13', ip='10.0.1.12')
        host14 = self.addHost('h14', ip='10.0.1.13')
        host15 = self.addHost('h15', ip='10.0.1.14')
        host16 = self.addHost('h16', ip='10.0.1.15')

        switch1 = self.addSwitch('s1', protocols='OpenFlow14')
        switch2 = self.addSwitch('s2', protocols='OpenFlow14')
        switch3 = self.addSwitch('s3', protocols='OpenFlow14')
        switch4 = self.addSwitch('s4', protocols='OpenFlow14')
        switch5 = self.addSwitch('s5', protocols='OpenFlow14')
        switch6 = self.addSwitch('s6', protocols='OpenFlow14')
        switch7 = self.addSwitch('s7', protocols='OpenFlow14')
        switch8 = self.addSwitch('s8', protocols='OpenFlow14')
        switch9 = self.addSwitch('s9', protocols='OpenFlow14')
        switch10 = self.addSwitch('s10', protocols='OpenFlow14')
        switch11 = self.addSwitch('s11', protocols='OpenFlow14')
        switch12 = self.addSwitch('s12', protocols='OpenFlow14')
        switch13 = self.addSwitch('s13', protocols='OpenFlow14')
        switch14 = self.addSwitch('s14', protocols='OpenFlow14')
        switch15 = self.addSwitch('s15', protocols='OpenFlow14')
        switch16 = self.addSwitch('s16', protocols='OpenFlow14')
        switch17 = self.addSwitch('s17', protocols='OpenFlow14')
        switch18 = self.addSwitch('s18', protocols='OpenFlow14')
        switch19 = self.addSwitch('s19', protocols='OpenFlow14')
        switch20 = self.addSwitch('s20', protocols='OpenFlow14')

        switch21 = self.addSwitch('s21', protocols='OpenFlow14')
        self.addLink(switch1, switch21, 5, 1)
        self.addLink(switch2, switch21, 5, 2)
        self.addLink(switch3, switch21, 5, 3)
        self.addLink(switch4, switch21, 5, 4)
        self.addLink(switch5, switch21, 5, 5)
        self.addLink(switch6, switch21, 5, 6)
        self.addLink(switch7, switch21, 5, 7)
        self.addLink(switch8, switch21, 5, 8)


        # Add links
        self.addLink(host1, switch1, 0, 1)
        self.addLink(host2, switch1, 0, 2)
        self.addLink(host3, switch2, 0, 1)
        self.addLink(host4, switch2, 0, 2)
        self.addLink(host5, switch3, 0, 1)
        self.addLink(host6, switch3, 0, 2)
        self.addLink(host7, switch4, 0, 1)
        self.addLink(host8, switch4, 0, 2)
        self.addLink(host9, switch5, 0, 1)
        self.addLink(host10, switch5, 0, 2)
        self.addLink(host11, switch6, 0, 1)
        self.addLink(host12, switch6, 0, 2)
        self.addLink(host13, switch7, 0, 1)
        self.addLink(host14, switch7, 0, 2)
        self.addLink(host15, switch8, 0, 1)
        self.addLink(host16, switch8, 0, 2)

        self.addLink(switch1, switch9, 3, 1)
        self.addLink(switch1, switch10, 4, 1)
        self.addLink(switch2, switch9, 3, 2)
        self.addLink(switch2, switch10, 4, 2)
        self.addLink(switch3, switch11, 3, 1)
        self.addLink(switch3, switch12, 4, 1)
        self.addLink(switch4, switch11, 3, 2)
        self.addLink(switch4, switch12, 4, 2)
        self.addLink(switch5, switch13, 3, 1)
        self.addLink(switch5, switch14, 4, 1)
        self.addLink(switch6, switch13, 3, 2)
        self.addLink(switch6, switch14, 4, 2)
        self.addLink(switch7, switch15, 3, 1)
        self.addLink(switch7, switch16, 4, 1)
        self.addLink(switch8, switch15, 3, 2)
        self.addLink(switch8, switch16, 4, 2)
        self.addLink(switch9, switch17, 3, 1)
        self.addLink(switch9, switch18, 4, 1)
        self.addLink(switch11, switch17, 3, 2)
        self.addLink(switch11, switch18, 4, 2)
        self.addLink(switch13, switch17, 3, 3)
        self.addLink(switch13, switch18, 4, 3)
        self.addLink(switch15, switch17, 3, 4)
        self.addLink(switch15, switch18, 4, 4)
        self.addLink(switch10, switch19, 3, 1)
        self.addLink(switch10, switch20, 4, 1)
        self.addLink(switch12, switch19, 3, 2)
        self.addLink(switch12, switch20, 4, 2)
        self.addLink(switch14, switch19, 3, 3)
        self.addLink(switch14, switch20, 4, 3)
        self.addLink(switch16, switch19, 3, 4)
        self.addLink(switch16, switch20, 4, 4)



        #topos = { 'mytopod': ( lambda: MyTopod() )

def simpleTest():
    topo = MyTopod()

    net = Mininet( topo=topo, switch=OVSKernelSwitch, controller=Ryu('ryuController','/home/shengliu/Workspace/ryu/casualSDN/ofctl_rest.py') )
    #h1 = net.get('h1')
    #print h1.IP()
    #print h1.MAC()

    net.start()
    for i in range(20):
    	s = net.get('s%d' %(i+1))
	    s.cmd('sudo ovs-vsctl set bridge s%i protocols=OpenFlow14' %(i+1))

    #s1 = net.get('s1')
    #s1.cmd('sudo ovs-ofctl add-flow -O OpenFlow14 arp,priority=1,in_port=1,actions=2,3')
 	#s.cmd('sudo ovs-vsctl set bridge s%i protocols=OpenFlow14 stp_enable=true' %(i+1))
    # use static ARP configuration to avoid arp broadcast
    # net.staticArp()

    # deploy default rule to allow arp packet to broadcast using the following command
    # curl -X POST -d '{"dpid":1, "match":{"ipv4_dst":"10.0.0.1", "eth_type":2048}, "actions":[{"type":"OUTPUT", "port":"FLOOD"}] }' http://localhost:8080/stats/flowentry/add
    # curl -X POST -d '{"dpid":1, "match":{"ipv4_dst":"10.0.0.1", "eth_type":2048}, "actions":[{"type":"OUTPUT", "port":"FLOOD"}] }' http://localhost:8080/stats/flowentry/delete
    # deploy rule for each switch using: curl -X POST -d '{"dpid":1, "match":{eth_type":0x0806}, "priority":2, "actions":[{"type":"OUTPUT", "port":1}] }' http://localhost:8080/stats/flowentry/add
    # sudo ovs-vsctl set bridge s1 protocols=OpenFlow14
    # check the rules: ovs-ofctl -O openflow13 dump-flows s1

    CLI(net)

    net.stop()


if __name__ == '__main__':

    simpleTest()
