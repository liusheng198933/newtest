from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Controller, OVSKernelSwitch, RemoteController, Ryu
from util import *
from test_main import *
from test_main_all import *

KNUM = 4

class FatTree( Topo ):

    def __init__( self ):

        # Topology settings
        K = KNUM                           # K-ary FatTree
        podNum = K                      # Pod number in FatTree
        coreSwitchNum = pow((K/2),2)    # Core switches
        aggrSwitchNum = ((K/2)*K)       # Aggregation switches
        edgeSwitchNum = ((K/2)*K)       # Edge switches
        hostNum = (K*pow((K/2),2))      # Hosts in K-ary FatTree

        # Initialize topology
        Topo.__init__( self )

        coreSwitches = []
        aggrSwitches = []
        edgeSwitches = []

        arpSwitch = self.addSwitch("arp0", dpid='1'*7, protocols='OpenFlow14')
        # the format of switch dpid is 1-bit for switch classification, 3-bit for pod number and 3-bit for aggr or edge number
        # Core
        for core in range(0, coreSwitchNum):
            coreSwitches.append(self.addSwitch("cs_"+str(core), dpid=int2dpid(1, core), protocols='OpenFlow14'))
        # Pod
        for pod in range(0, podNum):
        # Aggregate
            for aggr in range(0, aggrSwitchNum/podNum):
                aggrThis = self.addSwitch("as_"+str(pod)+"_"+str(aggr), dpid=int2dpid(2, aggr, pod), protocols='OpenFlow14')
                aggrSwitches.append(aggrThis)
                for x in range((K/2)*aggr, (K/2)*(aggr+1)):
#                    self.addLink(aggrSwitches[aggr+(aggrSwitchNum/podNum*pod)], coreSwitches[x])
                    self.addLink(aggrThis, coreSwitches[x])
        # Edge
            for edge in range(0, edgeSwitchNum/podNum):
                edgeThis = self.addSwitch("es_"+str(pod)+"_"+str(edge), dpid=int2dpid(3, edge, pod), protocols='OpenFlow14')
                edgeSwitches.append(edgeThis)
                for x in range((edgeSwitchNum/podNum)*pod, ((edgeSwitchNum/podNum)*(pod+1))):
                    self.addLink(edgeThis, aggrSwitches[x])

        # Host
                for x in range(0, (hostNum/podNum/(edgeSwitchNum/podNum))):
                    hst = self.addHost("h_"+str(pod)+"_"+str(edge)+"_"+str(x), ip='10.%d.%d.%d' %(pod, edge, x+1))
                    self.addLink(edgeThis, hst)

        for sw in edgeSwitches:
            self.addLink(sw, arpSwitch)


topos = { 'fattree': ( lambda: FatTree() ) }


def total_switch_num(k):
    return pow((k/2),2) + k*k


def createTopo():
    K = KNUM

    topo = FatTree()

    fat_tree_net = Mininet( topo=topo, switch=OVSKernelSwitch, controller=Ryu('ryuController','/home/shengliu/Workspace/ryu/casualSDN/ofctl_rest.py') )
    #h1 = net.get('h1')
    #print h1.IP()
    #print h1.MAC()

    fat_tree_net.start()
    for i in topo.switches():
        sw = fat_tree_net.get(i)
        sw.cmd('sudo ovs-vsctl set bridge %s protocols=OpenFlow14' %i)

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



    CLI(fat_tree_net)
    #fat_tree_net.stop()
    for b in range(14, 15):
        pkt_rate = 1000*b
        q = 0
        tt = 0
        filepath = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'
        #result = snapshot_deploy(filepath, K, 0)
        #snapshot_deploy_coco(filepath, K, 0, 2)

        while tt < 10:
            result = 'False'
            while result != 'True':
                print 'idx: %d' %q
                result = test_run(K, fat_tree_net, pkt_rate, 1, 12)
                #result = test_run_time(K, fat_tree_net, pkt_rate, 3, q)
                #result = test_run_link(K, fat_tree_net, pkt_rate, 3, 12)

                if result == 'Error':
                    q = q + 1
                if result == 'True':
                    tt = tt + 1
                    q = q + 1
    #test_run_all(K, fat_tree_net, pkt_rate, 0)
    #pkt_rate = 1000
    #CLI(fat_tree_net)
    """
    for h in range(86, 100):
        pkt_rate = h * 100
        print pkt_rate
        print "traditional protocol:"
        rt = test_run(K, fat_tree_net, pkt_rate, 0)
        while not rt:
            rt = test_run(K, fat_tree_net, pkt_rate, 0)
        print "our protocol:"
        rt = test_run(K, fat_tree_net, pkt_rate, 1)
        while not rt:
            rt = test_run(K, fat_tree_net, pkt_rate, 1)
    """

    fat_tree_net.stop()


if __name__ == '__main__':

    createTopo()
