#!/usr/bin/env python2
# Copyright 2013-present Barefoot Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Adapted by Robert MacDavid (macdavid@cs.princeton.edu) from scripts found in
# the p4app repository (https://github.com/p4lang/p4app)
#
# We encourage you to dissect this script to better understand the BMv2/Mininet
# environment used by the P4 tutorial.
#
import os, sys, json, subprocess, re, argparse
from time import sleep

from p4_mininet import P4Switch, P4Host

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.cli import CLI

from p4runtime_switch import P4RuntimeSwitch
import p4runtime_lib.bmv2
import p4runtime_lib.helper
from cmd_p4 import *
from switch_state import rule

PRTMAX = 100

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


class SingleSwitchTopo(Topo):
    "Single switch connected to n (< 256) hosts."
    def __init__(self, n, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        switch = self.addSwitch('s1')

        for h in xrange(n):
            host = self.addHost('h%d' % (h + 1),
                                ip = "10.0.%d.10" % h,
                                mac = '00:04:00:00:00:%02x' %h)
            self.addLink(host, switch)


class CustomSwitchTopo(Topo):
    "Single switch connected to n (< 256) hosts."
    def __init__(self, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)

        switch1 = self.addSwitch('s1')
        switch2 = self.addSwitch('s2')
        switch3 = self.addSwitch('s3')
        switch4 = self.addSwitch('s4')
        h1 = self.addHost('h1', ip = "10.0.0.10/24", mac = '00:04:00:00:00:00')
        h2 = self.addHost('h2', ip = "10.0.1.10/24", mac = '00:04:00:00:00:01')
        self.addLink(h1, switch1)
        self.addLink(switch1, switch2)
        self.addLink(switch1, switch3)
        self.addLink(switch2, switch4)
        self.addLink(switch3, switch4)
        self.addLink(h2, switch4)


class ExerciseTopo(Topo):
    """ The mininet topology class for the P4 tutorial exercises.
        A custom class is used because the exercises make a few topology
        assumptions, mostly about the IP and MAC addresses.
    """
    def __init__(self, hosts, switches, links, log_dir, **opts):
        Topo.__init__(self, **opts)
        host_links = []
        switch_links = []
        self.sw_port_mapping = {}

        for link in links:
            if link['node1'][0] == 'h':
                host_links.append(link)
            else:
                switch_links.append(link)

        link_sort_key = lambda x: x['node1'] + x['node2']
        # Links must be added in a sorted order so bmv2 port numbers are predictable
        host_links.sort(key=link_sort_key)
        switch_links.sort(key=link_sort_key)

        for sw in switches:
            self.addSwitch(sw, log_file="%s/%s.log" %(log_dir, sw))

        for link in host_links:
            host_name = link['node1']
            host_sw   = link['node2']
            host_num = int(host_name[1:])
            sw_num   = int(host_sw[1:])
            host_ip = "10.0.%d.%d" % (sw_num, host_num)
            host_mac = '00:00:00:00:%02x:%02x' % (sw_num, host_num)
            # Each host IP should be /24, so all exercise traffic will use the
            # default gateway (the switch) without sending ARP requests.
            self.addHost(host_name, ip=host_ip+'/24', mac=host_mac)
            self.addLink(host_name, host_sw,
                         delay=link['latency'], bw=link['bandwidth'],
                         addr1=host_mac, addr2=host_mac)
            self.addSwitchPort(host_sw, host_name)

        for link in switch_links:
            self.addLink(link['node1'], link['node2'],
                        delay=link['latency'], bw=link['bandwidth'])
            self.addSwitchPort(link['node1'], link['node2'])
            self.addSwitchPort(link['node2'], link['node1'])

        self.printPortMapping()

    def addSwitchPort(self, sw, node2):
        if sw not in self.sw_port_mapping:
            self.sw_port_mapping[sw] = []
        portno = len(self.sw_port_mapping[sw])+1
        self.sw_port_mapping[sw].append((portno, node2))

    def printPortMapping(self):
        print "Switch port mapping:"
        for sw in sorted(self.sw_port_mapping.keys()):
            print "%s: " % sw,
            for portno, node2 in self.sw_port_mapping[sw]:
                print "%d:%s\t" % (portno, node2),
            print


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


    def __init__(self, topo_file, log_dir, pcap_dir,
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

        self.quiet = quiet
        self.logger('Reading topology file.')
        with open(topo_file, 'r') as f:
            topo = json.load(f)
        self.hosts = topo['hosts']
        self.switches = topo['switches']
        self.links = self.parse_links(topo['links'])

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
        sleep(1)

        self.SingleSwitchTopoConfig(p4info_file_path, bmv2_file_path)

        sleep(1)

        CLI(self.net)

        self.bufferTest(p4info_file_path)

        sleep(1)

        self.do_net_cli()
        # stop right after the CLI is exited
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

        self.topo = SingleSwitchTopo(2)
        #self.topo = CustomSwitchTopo()
        #self.topo = ExerciseTopo(self.hosts, self.switches.keys(), self.links, self.log_dir)

        switchClass = configureP4Switch(
                sw_path=self.bmv2_exe,
                json_path=self.switch_json,
                log_console=True)

        print "mininet starts"

        self.net = Mininet(topo = self.topo,
                      host = P4Host,
                      switch = switchClass,
                      controller = None)

        #sw = self.net.get('s1')
        #sw.describe()
        #sw.grpc_reconfigure(4)
        #sw.describe()
        print "mininet ends"


    def program_switches(self):
        """ If any command files were provided for the switches,
            this method will start up the CLI on each switch and use the
            contents of the command files as input.

            Assumes:
                - A mininet instance is stored as self.net and self.net.start() has
                  been called.
        """
        cli = 'simple_switch_CLI'
        for sw_name, sw_dict in self.switches.iteritems():
            if 'cli_input' not in sw_dict: continue
            # get the port for this particular switch's thrift server
            sw_obj = self.net.get(sw_name)
            thrift_port = sw_obj.thrift_port

            cli_input_commands = sw_dict['cli_input']
            self.logger('Configuring switch %s with file %s' % (sw_name, cli_input_commands))
            with open(cli_input_commands, 'r') as fin:
                cli_outfile = '%s/%s_cli_output.log'%(self.log_dir, sw_name)
                with open(cli_outfile, 'w') as fout:
                    subprocess.Popen([cli, '--thrift-port', str(thrift_port)],
                                     stdin=fin, stdout=fout)

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


    def SingleSwitchTopoConfig(self, p4info_file_path, bmv2_file_path):
        p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
        sw = p4runtime_lib.bmv2.Bmv2SwitchConnection('s1', address='localhost:50051')
        sw.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                       bmv2_json_file_path=bmv2_file_path)


        sleep(1)

        #how to construct sw_rule
        table_entry = table_entry_construct_new(p4info_helper, table_id=1)
        sw.WriteTableEntry(table_entry)

        sleep(1)

        table_entry = table_entry_construct_new(p4info_helper, table_id=2)
        sw.WriteTableEntry(table_entry)
        #init
        sw_rule = {}
        sw_rule['add'] = []
        sw_rule['del'] = []
        #sw_rule['add'].append(rule('s1', {}, 100, 0, 0, 0, 1))
        #sw_rule['add'].append(rule('s1', {'ipv4_dst':'10.0.0.0/255.0.0.0', 'ipv4_src':'10.0.0.0/255.0.0.0'}, 100, 0, -1, 0, 2))

        #writeRules(K, p4info_helper, i, "10.0.0.0", "255.0.0.0", "10.0.0.0", "255.0.0.0", rtmp_max, 0, 1, action_flag=1, priority=PRTMAX-2)
        #writeRules(K, p4info_helper, i, "0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0", rtmp_max, 0, 1, action_flag=2, priority=PRTMAX-1)
        #sw = p4runtime_lib.bmv2.Bmv2SwitchConnection(grpc2name(K, sw_id), address='localhost:%d' %(sw_id+50051))
        #table_entry = table_entry_construct(p4info_helper, src_ip_addr, src_addr_mask, dst_ip_addr, dst_addr_mask, rtmp, ttmp, out_port, action_flag, priority)
        #sw.WriteTableEntry(table_entry,update_flag=update_flag_write)

        #routing rules
        ip_src = '10.0.0.10'
        ip_dst = '10.0.1.10'
        match = {}
        match['ipv4_dst'] = ip_dst
        match['ipv4_src'] = ip_src
        match_reverse = {}
        match_reverse['ipv4_dst'] = ip_src
        match_reverse['ipv4_src'] = ip_dst
        sw_rule['add'].append(rule('s1', match, 1, 1, 2, 0, 20))
        sw_rule['add'].append(rule('s1', match_reverse, 2, 2, 1, 0, 20))

        #self.oneSwitchDeploy(p4info_helper, sw, sw_rule)
        self.oneSwitchDeployNew(p4info_helper, sw, sw_rule)



    def bufferTest(self, p4info_file_path):
        p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
        sw = p4runtime_lib.bmv2.Bmv2SwitchConnection('s1', address='localhost:50051')

        sw_rule = {}
        sw_rule['add'] = []
        sw_rule['del'] = []

        #routing rules with new tmp
        ip_src = '10.0.0.10'
        ip_dst = '10.0.1.10'
        match = {}
        match['ipv4_dst'] = ip_dst
        match['ipv4_src'] = ip_src
        sw_rule['del'].append(rule('s1', match, 1, 1, 2, 0, 20))
        sw_rule['add'].append(rule('s1', match, 2, 2, 2, 0, 20))

        #self.oneSwitchDeploy(p4info_helper, sw, sw_rule)
        self.oneSwitchDeployNew(p4info_helper, sw, sw_rule)


    def oneSwitchDeployNew(self, p4info_helper, sw, sw_rule):
        src_ip_addr_list = []
        src_addr_mask_list = []
        dst_ip_addr_list = []
        dst_addr_mask_list = []
        rtmp_list = []
        ttmp_list = []
        out_port_list= []
        priority_list = []
        update_flag_write_list = []

        for r in sw_rule['del']:
            mt = r.get_match()
            if not mt:
                dst_ip_addr_list.append('0.0.0.0')
                dst_addr_mask_list.append('0.0.0.0')
                src_ip_addr_list.append('0.0.0.0')
                src_addr_mask_list.append('0.0.0.0')
            else:
                if '/' in mt['ipv4_dst']:
                    dst_ip_addr_list.append(mt['ipv4_dst'].split('/')[0])
                    dst_addr_mask_list.append(mt['ipv4_dst'].split('/')[1])
                else:
                    dst_ip_addr_list.append(mt['ipv4_dst'])
                    dst_addr_mask_list.append('255.255.255.255')
                if '/' in mt['ipv4_src']:
                    src_ip_addr_list.append(mt['ipv4_src'].split('/')[0])
                    src_addr_mask_list.append(mt['ipv4_src'].split('/')[1])
                else:
                    src_ip_addr_list.append(mt['ipv4_src'])
                    src_addr_mask_list.append('255.255.255.255')
            rtmp_list.append(r.get_rtmp())
            ttmp_list.append(r.get_ttmp())
            out_port_list.append(r.get_action())
            priority_list.append(PRTMAX-r.get_prt())
            update_flag_write_list.append(1)

        for r in sw_rule['add']:
            mt = r.get_match()
            if not mt:
                dst_ip_addr_list.append('0.0.0.0')
                dst_addr_mask_list.append('0.0.0.0')
                src_ip_addr_list.append('0.0.0.0')
                src_addr_mask_list.append('0.0.0.0')
            else:
                if '/' in mt['ipv4_dst']:
                    dst_ip_addr_list.append(mt['ipv4_dst'].split('/')[0])
                    dst_addr_mask_list.append(mt['ipv4_dst'].split('/')[1])
                else:
                    dst_ip_addr_list.append(mt['ipv4_dst'])
                    dst_addr_mask_list.append('255.255.255.255')
                if '/' in mt['ipv4_src']:
                    src_ip_addr_list.append(mt['ipv4_src'].split('/')[0])
                    src_addr_mask_list.append(mt['ipv4_src'].split('/')[1])
                else:
                    src_ip_addr_list.append(mt['ipv4_src'])
                    src_addr_mask_list.append('255.255.255.255')
            rtmp_list.append(r.get_rtmp())
            ttmp_list.append(r.get_ttmp())
            out_port_list.append(r.get_action())
            priority_list.append(PRTMAX-r.get_prt())
            update_flag_write_list.append(0)

        table_entry_list = []
        for i in range(len(dst_ip_addr_list)):
            table_entry_list.append(table_entry_construct_new(p4info_helper, src_ip_addr_list[i], src_addr_mask_list[i], dst_ip_addr_list[i], dst_addr_mask_list[i], rtmp_list[i], ttmp_list[i], out_port_list[i], priority_list[i]))
        sw.WriteTableEntryMulti(table_entry_list, update_flag_list=update_flag_write_list)



    def oneSwitchDeploy(self, p4info_helper, sw, sw_rule):
        src_ip_addr_list = []
        src_addr_mask_list = []
        dst_ip_addr_list = []
        dst_addr_mask_list = []
        rtmp_list = []
        ttmp_list = []
        out_port_list= []
        priority_list = []
        action_flag_list = []
        update_flag_write_list = []

        for r in sw_rule['del']:
            mt = r.get_match()
            if not mt:
                dst_ip_addr_list.append('0.0.0.0')
                dst_addr_mask_list.append('0.0.0.0')
                src_ip_addr_list.append('0.0.0.0')
                src_addr_mask_list.append('0.0.0.0')
            else:
                if '/' in mt['ipv4_dst']:
                    dst_ip_addr_list.append(mt['ipv4_dst'].split('/')[0])
                    dst_addr_mask_list.append(mt['ipv4_dst'].split('/')[1])
                else:
                    dst_ip_addr_list.append(mt['ipv4_dst'])
                    dst_addr_mask_list.append('255.255.255.255')
                if '/' in mt['ipv4_src']:
                    src_ip_addr_list.append(mt['ipv4_src'].split('/')[0])
                    src_addr_mask_list.append(mt['ipv4_src'].split('/')[1])
                else:
                    src_ip_addr_list.append(mt['ipv4_src'])
                    src_addr_mask_list.append('255.255.255.255')
            rtmp_list.append(r.get_rtmp())
            ttmp_list.append(r.get_ttmp())
            if r.get_action() == 0:
                out_port_list.append(1)
                action_flag_list.append(2)
            if r.get_action() < 0:
                out_port_list.append(1)
                action_flag_list.append(1)
            if r.get_action() > 0:
                out_port_list.append(r.get_action())
                action_flag_list.append(0)
            priority_list.append(PRTMAX-r.get_prt())
            update_flag_write_list.append(1)

        for r in sw_rule['add']:
            mt = r.get_match()
            if not mt:
                dst_ip_addr_list.append('0.0.0.0')
                dst_addr_mask_list.append('0.0.0.0')
                src_ip_addr_list.append('0.0.0.0')
                src_addr_mask_list.append('0.0.0.0')
            else:
                if '/' in mt['ipv4_dst']:
                    dst_ip_addr_list.append(mt['ipv4_dst'].split('/')[0])
                    dst_addr_mask_list.append(mt['ipv4_dst'].split('/')[1])
                else:
                    dst_ip_addr_list.append(mt['ipv4_dst'])
                    dst_addr_mask_list.append('255.255.255.255')
                if '/' in mt['ipv4_src']:
                    src_ip_addr_list.append(mt['ipv4_src'].split('/')[0])
                    src_addr_mask_list.append(mt['ipv4_src'].split('/')[1])
                else:
                    src_ip_addr_list.append(mt['ipv4_src'])
                    src_addr_mask_list.append('255.255.255.255')
            rtmp_list.append(r.get_rtmp())
            ttmp_list.append(r.get_ttmp())
            if r.get_action() == 0:
                out_port_list.append(1)
                action_flag_list.append(2)
            if r.get_action() < 0:
                out_port_list.append(1)
                action_flag_list.append(1)
            if r.get_action() > 0:
                out_port_list.append(r.get_action())
                action_flag_list.append(0)
            priority_list.append(PRTMAX-r.get_prt())
            update_flag_write_list.append(0)

        table_entry_list = []
        for i in range(len(dst_ip_addr_list)):
            table_entry_list.append(table_entry_construct(p4info_helper, src_ip_addr_list[i], src_addr_mask_list[i], dst_ip_addr_list[i], dst_addr_mask_list[i], rtmp_list[i], ttmp_list[i], out_port_list[i], action_flag_list[i], priority_list[i]))
        sw.WriteTableEntryMulti(table_entry_list, update_flag_list=update_flag_write_list)



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
    # from mininet.log import setLogLevel
    # setLogLevel("info")

    p4info_file_path = '/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt'
    bmv2_file_path = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json"

    args = get_args()
    exercise = ExerciseRunner(args.topo, args.log_dir, args.pcap_dir,
                              args.switch_json, args.behavioral_exe, args.quiet)

    exercise.run_exercise(p4info_file_path, bmv2_file_path)
