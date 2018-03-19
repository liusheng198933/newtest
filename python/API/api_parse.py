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

parser = argparse.ArgumentParser(description = 'The high-level API for the application')
parser.add_argument('-f', action = 'store', type = str, dest = 'flow')
parser.add_argument('-r', action = 'store', type = str, dest = 'path' )
parser.add_argument('--prt', action = 'store', type = int, dest = 'prt' )
args = parser.parse_args()


class MyTopod( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches

        host1 = self.addHost('h1', ip='10.0.0.1')
        host2 = self.addHost('h2', ip='10.0.0.2')



        switch1 = self.addSwitch( 's1', protocols='OpenFlow14' )


        # Add links
        self.addLink(host1, switch1, 0, 1)
        self.addLink(host2, switch1, 0, 2)



        #topos = { 'mytopod': ( lambda: MyTopod() )

def simpleTest():
    topo = MyTopod()

    net = Mininet( topo=topo, switch=OVSKernelSwitch, controller=Ryu('ryuController','/home/shengliu/Workspace/ryu/casualSDN/dummyRouter.py') )

    net.start()

    CLI(net)

    net.stop()


if __name__ == '__main__':
    flow_list = args.flow.strip().split(',')
    src_ip = flow_list[0]
    src_mask = flow_list[1]
    dst_ip = flow_list[2]
    dst_mask = flow_list[3]
    path = []
    for i in args.path.strip().split(','):
        path.append(int(i))

    print src_ip, src_mask, dst_ip, dst_mask
    print path
    print args.prt
    #simpleTest()
