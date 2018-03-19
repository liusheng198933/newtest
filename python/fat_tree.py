from test_main import *
from test_main_all import *
from time_process import *

import os, sys, json, subprocess, re, argparse
from time import sleep

from p4_mininet import P4Switch, P4Host

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import lg, debug
import logging

from p4runtime_switch import P4RuntimeSwitch

KNUM = 8

#lg.setLogLevel('debug')
#logging.basicConfig(filename='/home/shengliu/Workspace/log/mn.log')


def configureP4Switch(**switch_args):
    """ Helper class that is called by mininet to initialize
        the virtual P4 switches. The purpose is to ensure each
        switch's thrift server is using a unique port.
    """
    if "sw_path" in switch_args and 'grpc' in switch_args['sw_path']:
        # If grpc appears in the BMv2 switch target, we assume will start P4 Runtime
        class ConfiguredP4RuntimeSwitch(P4RuntimeSwitch):
            def __init__(self, *opts, **kwargs):
                kwargs.update(switch_args)
                P4RuntimeSwitch.__init__(self, *opts, **kwargs)

            def describe(self):
                print "%s -> gRPC port: %d" % (self.name, self.grpc_port)

        print "ConfiguredP4RuntimeSwitch"
        return ConfiguredP4RuntimeSwitch
    else:
        class ConfiguredP4Switch(P4Switch):
            next_thrift_port = 9090
            def __init__(self, *opts, **kwargs):
                global next_thrift_port
                kwargs.update(switch_args)
                kwargs['thrift_port'] = ConfiguredP4Switch.next_thrift_port
                ConfiguredP4Switch.next_thrift_port += 1
                P4Switch.__init__(self, *opts, **kwargs)

            def describe(self):
                print "%s -> Thrift port: %d" % (self.name, self.thrift_port)

        print "ConfiguredP4Switch"
        return ConfiguredP4Switch


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

        #arpSwitch = self.addSwitch("arp0", dpid='1'*7)
        # the format of switch dpid is 1-bit for switch classification, 3-bit for pod number and 3-bit for aggr or edge number
        # Core
        for core in range(0, coreSwitchNum):
            coreSwitches.append(self.addSwitch("cs_"+str(core)))
            #coreSwitches.append(self.addSwitch("cs_"+str(core), dpid=int2dpid(1, core), protocols='OpenFlow14'))
        # Pod
        for pod in range(0, podNum):
        # Aggregate
            for aggr in range(0, aggrSwitchNum/podNum):
                aggrThis = self.addSwitch("as_"+str(pod)+"_"+str(aggr))
                #aggrThis = self.addSwitch("as_"+str(pod)+"_"+str(aggr), dpid=int2dpid(2, aggr, pod), protocols='OpenFlow14')
                aggrSwitches.append(aggrThis)
                for x in range((K/2)*aggr, (K/2)*(aggr+1)):
#                    self.addLink(aggrSwitches[aggr+(aggrSwitchNum/podNum*pod)], coreSwitches[x])
                    self.addLink(aggrThis, coreSwitches[x])
        # Edge
            for edge in range(0, edgeSwitchNum/podNum):
                edgeThis = self.addSwitch("es_"+str(pod)+"_"+str(edge))
                #edgeThis = self.addSwitch("es_"+str(pod)+"_"+str(edge), dpid=int2dpid(3, edge, pod), protocols='OpenFlow14')
                edgeSwitches.append(edgeThis)
                for x in range((edgeSwitchNum/podNum)*pod, ((edgeSwitchNum/podNum)*(pod+1))):
                    self.addLink(edgeThis, aggrSwitches[x])

        # Host
                for x in range(0, (hostNum/podNum/(edgeSwitchNum/podNum))):
                    hst = self.addHost("h_"+str(pod)+"_"+str(edge)+"_"+str(x),
                                        ip='10.%d.%d.%d' %(pod, edge, x+1),
                                        mac = '00:04:00:%02x:%02x:%02x' %(pod, edge, x+1))
                    self.addLink(edgeThis, hst)

        #for sw in edgeSwitches:
            #self.addLink(sw, arpSwitch)


topos = { 'fattree': ( lambda: FatTree() ) }


def total_switch_num(k):
    return pow((k/2),2) + k*k



class ExerciseRunner:
    """
        Attributes:
            log_dir  : string   // directory for mininet log files
            pcap_dir : string   // directory for mininet switch pcap files
            quiet    : bool     // determines if we print logger messages

            hosts    : list<string>       // list of mininet host names
            switches : dict<string, dict> // mininet host names and their associated properties
            links    : list<dict>         // list of mininet link properties

            switch_json : string // json of the compiled p4 example
            bmv2_exe    : string // name or path of the p4 switch binary

            topo : Topo object   // The mininet topology instance
            net : Mininet object // The mininet instance

    """
    def logger(self, *items):
        if not self.quiet:
            print(' '.join(items))

    def formatLatency(self, l):
        """ Helper method for parsing link latencies from the topology json. """
        if isinstance(l, (str, unicode)):
            return l
        else:
            return str(l) + "ms"


    def __init__(self, K, topo_file, log_dir, pcap_dir,
                       switch_json, bmv2_exe='simple_switch', quiet=False):
        """ Initializes some attributes and reads the topology json. Does not
            actually run the exercise. Use run_exercise() for that.

            Arguments:
                topo_file : string    // A json file which describes the exercise's
                                         mininet topology.
                log_dir  : string     // Path to a directory for storing exercise logs
                pcap_dir : string     // Ditto, but for mininet switch pcap files
                switch_json : string  // Path to a compiled p4 json for bmv2
                bmv2_exe    : string  // Path to the p4 behavioral binary
                quiet : bool          // Enable/disable script debug messages
        """

        self.K = K
        self.quiet = quiet
        self.logger('Reading topology file.')

        # Ensure all the needed directories exist and are directories
        for dir_name in [log_dir, pcap_dir]:
            if not os.path.isdir(dir_name):
                if os.path.exists(dir_name):
                    raise Exception("'%s' exists and is not a directory!" % dir_name)
                os.mkdir(dir_name)
        self.log_dir = log_dir
        self.pcap_dir = pcap_dir
        self.switch_json = switch_json
        self.bmv2_exe = bmv2_exe


    def run_exercise(self, p4info_file_path, bmv2_file_path):
        """ Sets up the mininet instance, programs the switches,
            and starts the mininet CLI. This is the main method to run after
            initializing the object.
        """
        # Initialize mininet with the topology specified by the config
        #print "json:" + self.switch_json
        self.create_network()
        for s in self.net.switches:
            s.grpc_reconfigure(KNUM)

        self.net.start()
        sleep(1)


        for host_name in self.topo.hosts():
            h = self.net.get(host_name)
            h.defaultIntf().rename('%s-eth0' % host_name)
            print host_name


        # some programming that must happen after the net has started
        #self.program_hosts()
        #self.program_switches()



        # wait for that to finish. Not sure how to do this better
        sleep(3)
        filepath = os.getcwd() + '/flow_update_8.tsv'
        flow_list = get_flow_list(filepath, K, 0, 104)
        snapshot_deploy_buffer(self.net, flow_list, p4info_file_path, bmv2_file_path, K)
        #for ha in range(100):
            #if ha % 3 == 0:
            #    snapshot_deploy(flow_list, p4info_file_path, bmv2_file_path, filepath, self.K, 0)
            #if ha % 3 == 1:
            #    snapshot_deploy_coco(flow_list, p4info_file_path, bmv2_file_path, filepath, self.K, 0, 2, self.net)
            #if ha % 3 == 2:
            #    snapshot_deploy_coco(flow_list, p4info_file_path, bmv2_file_path, filepath, self.K, 0, 3, self.net)

            #dirpath = '/home/shengliu/Workspace/log/'
            #ret = time_result_process_all(dirpath)
            #retpath = '/home/shengliu/Workspace/result/r_%d_%d.txt' %(ha%3, ha)
            #fp = open(retpath, 'a+')
            #fp.write('%s' %str(ret))
            #fp.close()
            #CLI(self.net)





        #snapshot_deploy_coco(p4info_file_path, bmv2_file_path, filepath, self.K, 0, 2, self.net)
        #self.do_net_cli()
        for b in range(1, 1):
            pkt_rate = (11 - b) * 100
            #pkt_rate = 900
            for j in range(1):
                for i in range(1, 2):
                    #pass
                    print j
                    #test_run(self.K, self.net, p4info_file_path, bmv2_file_path, pkt_rate, 0, j)
                    #test_run(self.K, self.net, p4info_file_path, bmv2_file_path, pkt_rate, 0, j)
                    # normal update
                    test_run_link(self.K, self.net, p4info_file_path, bmv2_file_path, pkt_rate, 1, 12)
                    # link failure
                    #result = test_run_time(self.K, self.net, p4info_file_path, bmv2_file_path, pkt_rate, 2, 12)
                    #result = test_run_time(self.K, self.net, p4info_file_path, bmv2_file_path, pkt_rate, 1, 12)

        # stop right after the CLI is exited

        # for b in range(14, 15):
        #     pkt_rate = 1000*b
        #     q = 0
        #     tt = 0
        #     filepath = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'
        #     #result = snapshot_deploy(filepath, K, 0)
        #     #snapshot_deploy_coco(filepath, K, 0, 2)
        #
        #     while tt < 10:
        #         result = 'False'
        #         while result != 'True':
        #             print 'idx: %d' %q
        #             result = test_run(K, fat_tree_net, pkt_rate, 1, 12)
        #             #result = test_run_time(K, fat_tree_net, pkt_rate, 3, q)
        #             #result = test_run_link(K, fat_tree_net, pkt_rate, 3, 12)
        #
        #             if result == 'Error':
        #                 q = q + 1
        #             if result == 'True':
        #                 tt = tt + 1
        #                 q = q + 1
        #test_run_all(K, fat_tree_net, pkt_rate, 0)
        #pkt_rate = 1000
        #CLI(fat_tree_net)

        self.net.stop()


    def parse_links(self, unparsed_links):
        """ Given a list of links descriptions of the form [node1, node2, latency, bandwidth]
            with the latency and bandwidth being optional, parses these descriptions
            into dictionaries and store them as self.links
        """
        links = []
        for link in unparsed_links:
            # make sure each link's endpoints are ordered alphabetically
            s, t, = link[0], link[1]
            if s > t:
                s,t = t,s

            link_dict = {'node1':s,
                        'node2':t,
                        'latency':'0ms',
                        'bandwidth':None
                        }
            if len(link) > 2:
                link_dict['latency'] = self.formatLatency(link[2])
            if len(link) > 3:
                link_dict['bandwidth'] = link[3]

            if link_dict['node1'][0] == 'h':
                assert link_dict['node2'][0] == 's', 'Hosts should be connected to switches, not ' + str(link_dict['node2'])
            links.append(link_dict)
        return links


    def create_network(self):
        """ Create the mininet network object, and store it as self.net.

            Side effects:
                - Mininet topology instance stored as self.topo
                - Mininet instance stored as self.net
        """
        self.logger("Building mininet topology.")


        self.topo = FatTree()
        #self.topo = SingleSwitchTopo(2)
        #self.topo = CustomSwitchTopo()
        #self.topo = ExerciseTopo(self.hosts, self.switches.keys(), self.links, self.log_dir)

        #switchClass = configureP4Switch(
        #        sw_path=self.bmv2_exe,
        #        json_path=self.switch_json,
        #        log_console=True,
        #        pcap_dump=self.pcap_dir)

        switchClass = configureP4Switch(
                sw_path=self.bmv2_exe,
                json_path=self.switch_json)

        print "mininet starts"

        self.net = Mininet(topo = self.topo,
                      host = P4Host,
                      switch = switchClass,
                      controller = None)

        print "mininet ends"


    def program_hosts(self):
        """ Adds static ARP entries and default routes to each mininet host.

            Assumes:
                - A mininet instance is stored as self.net and self.net.start() has
                  been called.
        """
        for host_name in self.topo.hosts():
            h = self.net.get(host_name)
            h_iface = h.intfs.values()[0]
            link = h_iface.link

            sw_iface = link.intf1 if link.intf1 != h_iface else link.intf2
            # phony IP to lie to the host about
            host_id = int(host_name[1:])
            sw_ip = '10.0.%d.254' % host_id

            # Ensure each host's interface name is unique, or else
            # mininet cannot shutdown gracefully
            h.defaultIntf().rename('%s-eth0' % host_name)
            # static arp entries and default routes
            h.cmd('arp -i %s -s %s %s' % (h_iface.name, sw_ip, sw_iface.mac))
            h.cmd('ethtool --offload %s rx off tx off' % h_iface.name)
            h.cmd('ip route add %s dev %s' % (sw_ip, h_iface.name))
            h.setDefaultRoute("via %s" % sw_ip)


    def do_net_cli(self):
        """ Starts up the mininet CLI and prints some helpful output.

            Assumes:
                - A mininet instance is stored as self.net and self.net.start() has
                  been called.
        """
        for s in self.net.switches:
            s.describe()
        for h in self.net.hosts:
            h.describe()
        self.logger("Starting mininet CLI")
        # Generate a message that will be printed by the Mininet CLI to make
        # interacting with the simple switch a little easier.
        print('')
        print('======================================================================')
        print('Welcome to the BMV2 Mininet CLI!')
        print('======================================================================')
        print('Your P4 program is installed into the BMV2 software switch')
        print('and your initial configuration is loaded. You can interact')
        print('with the network using the mininet CLI below.')
        print('')
        if self.switch_json:
            print('To inspect or change the switch configuration, connect to')
            print('its CLI from your host operating system using this command:')
            print('  simple_switch_CLI --thrift-port <switch thrift port>')
            print('')
        print('To view a switch log, run this command from your host OS:')
        print('  tail -f %s/<switchname>.log' %  self.log_dir)
        print('')
        print('To view the switch output pcap, check the pcap files in %s:' % self.pcap_dir)
        print(' for example run:  sudo tcpdump -xxx -r s1-eth1.pcap')
        print('')

        CLI(self.net)




def get_args():
    cwd = os.getcwd()
    default_logs = os.path.join(cwd, 'logs')
    default_pcaps = os.path.join(cwd, 'pcaps')
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quiet', help='Suppress log messages.',
                        action='store_true', required=False, default=False)
    parser.add_argument('-t', '--topo', help='Path to topology json',
                        type=str, required=False, default='./topology.json')
    parser.add_argument('-l', '--log-dir', type=str, required=False, default=default_logs)
    parser.add_argument('-p', '--pcap-dir', type=str, required=False, default=default_pcaps)
    parser.add_argument('-j', '--switch_json', type=str, required=False)
    parser.add_argument('-b', '--behavioral-exe', help='Path to behavioral executable',
                                type=str, required=False, default='simple_switch_grpc')
    return parser.parse_args()


if __name__ == '__main__':

    p4info_file_path = '/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt'
    bmv2_file_path = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json"
    K = KNUM

    args = get_args()
    exercise = ExerciseRunner(K, args.topo, args.log_dir, args.pcap_dir,
                              args.switch_json, args.behavioral_exe, args.quiet)

    exercise.run_exercise(p4info_file_path, bmv2_file_path)
