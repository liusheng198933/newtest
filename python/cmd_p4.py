#!/usr/bin/env python2
import argparse
import os
from time import sleep
from util import *
import threading

# NOTE: Appending to the PYTHON_PATH is only required in the `solution` directory.
#       It is not required for mycontroller.py in the top-level directory.


import p4runtime_lib.bmv2
import p4runtime_lib.helper

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2
rtmp_max = pow(2, 8)
action_default = 0
priority_default = 100

test_json = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json"
test_proto_txt = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt"


def table_entry_construct(p4info_helper, src_ip_addr, src_addr_mask, dst_ip_addr, dst_addr_mask, rtmp, ttmp, out_port, action_flag=action_default, priority=priority_default):
    if action_flag < 0 or action_flag > 2:
        print "no corresponding action"
        return 0
    if type(rtmp) == int:
        rtmp_list = [0, rtmp]
    else:
        rtmp_list = rtmp

    if action_flag == 0:
        table_entry = p4info_helper.buildTableEntry(
            table_name="ipv4_lpm",
            match_fields={
                "ipv4.srcAddr": (src_ip_addr, src_addr_mask),
                "ipv4.dstAddr": (dst_ip_addr, dst_addr_mask),
                "pktTMP.tmp": (rtmp_list[0], rtmp_list[1]),
            },
            priority = priority,
            action_name="set_nhop",
            action_params={
                "ttmp": ttmp,
                "port": out_port,
            })

    if action_flag == 1:
        table_entry = p4info_helper.buildTableEntry(
            table_name="ipv4_lpm",
            match_fields={
                "ipv4.srcAddr": (src_ip_addr, src_addr_mask),
                "ipv4.dstAddr": (dst_ip_addr, dst_addr_mask),
                "pktTMP.tmp": (rtmp_list[0], rtmp_list[1]),
            },
            priority = priority,
            action_name="_resubmit")

    if action_flag == 2:
        table_entry = p4info_helper.buildTableEntry(
            table_name="ipv4_lpm",
            match_fields={
                "ipv4.srcAddr": (src_ip_addr, src_addr_mask),
                "ipv4.dstAddr": (dst_ip_addr, dst_addr_mask),
                "pktTMP.tmp": (rtmp_list[0], rtmp_list[1]),
            },
            priority = priority,
            action_name="_drop")

    return table_entry


class writeThread (threading.Thread):
   def __init__(self, K, p4info_helper, sw_id, src_ip_addr_list, src_addr_mask_list, dst_ip_addr_list, dst_addr_mask_list, rtmp_list, ttmp_list, out_port_list, action_flag_list, priority_list, update_flag_write_list, delay=0):
      threading.Thread.__init__(self)
      self.K = K
      self.p4info_helper = p4info_helper
      self.sw_id = sw_id
      self.src_ip_addr_list = src_ip_addr_list
      self.src_addr_mask_list = src_addr_mask_list
      self.dst_ip_addr_list = dst_ip_addr_list
      self.dst_addr_mask_list =  dst_addr_mask_list
      self.rtmp_list = rtmp_list
      self.ttmp_list = ttmp_list
      self.out_port_list = out_port_list
      self.action_flag_list = action_flag_list
      self.priority_list = priority_list
      self.update_flag_write_list = update_flag_write_list
      self.delay = delay
      
   def run(self):
       if self.delay:
           sleep(self.delay)
       writeMultiRules(self.K, self.p4info_helper, self.sw_id,
                        self.src_ip_addr_list, self.src_addr_mask_list,
                        self.dst_ip_addr_list, self.dst_addr_mask_list,
                        self.rtmp_list, self.ttmp_list, self.out_port_list,
                        self.action_flag_list, self.priority_list,
                        self.update_flag_write_list)


def writeRules(K, p4info_helper, sw_id, src_ip_addr, src_addr_mask, dst_ip_addr, dst_addr_mask, rtmp, ttmp, out_port, action_flag=action_default, priority=priority_default, update_flag_write=0):
    # the rule of priority: smaller is more priority
    sw = p4runtime_lib.bmv2.Bmv2SwitchConnection(grpc2name(K, sw_id), address='localhost:%d' %(sw_id+50051))
    table_entry = table_entry_construct(p4info_helper, src_ip_addr, src_addr_mask, dst_ip_addr, dst_addr_mask, rtmp, ttmp, out_port, action_flag, priority)
    sw.WriteTableEntry(table_entry,update_flag=update_flag_write)
    #print "Installed ingress tunnel rule on %s" % sw.name


def writeMultiRules(K, p4info_helper, sw_id, src_ip_addr_list, src_addr_mask_list, dst_ip_addr_list, dst_addr_mask_list, rtmp_list, ttmp_list, out_port_list, action_flag_list, priority_list, update_flag_write_list):
    # the rule of priority: smaller is more priority
    sw = p4runtime_lib.bmv2.Bmv2SwitchConnection(grpc2name(K, sw_id), address='localhost:%d' %(sw_id+50051))
    table_entry_list = []
    for i in range(len(dst_ip_addr_list)):
        #print "cao"
        #print sw_id
        #print update_flag_write_list[i]
        table_entry_list.append(table_entry_construct(p4info_helper, src_ip_addr_list[i], src_addr_mask_list[i], dst_ip_addr_list[i], dst_addr_mask_list[i], rtmp_list[i], ttmp_list[i], out_port_list[i], action_flag_list[i], priority_list[i]))
    sw.WriteTableEntryMulti(table_entry_list, update_flag_list=update_flag_write_list)
    #print "Installed multiple rules on %s" % sw.name


def readTableRules(K, p4info_helper, sw_id):
    '''
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    '''
    sw = p4runtime_lib.bmv2.Bmv2SwitchConnection(grpc2name(K, sw_id), address='localhost:%d' %(sw_id+50051))
    print '\n----- Reading tables rules for %s -----' % sw.name
    for response in sw.ReadTableEntries():
        for entity in response.entities:
            entry = entity.table_entry
            # TODO For extra credit, you can use the p4info_helper to translate
            #      the IDs the entry to names
            table_name = p4info_helper.get_tables_name(entry.table_id)
            print '%s: ' % table_name,
            print 'prt:%d ' % (entry.priority),
            for m in entry.match:
                mname = p4info_helper.get_match_field_name(table_name, m.field_id)
                print mname,
                if "ipv4" in mname:
                    #print len(p4info_helper.get_match_field_value(m))
                    for j in range(2):
                        print '%r' % (p4runtime_lib.convert.decodeIPv4(p4info_helper.get_match_field_value(m)[j]),),
                else:
                    for j in range(2):
                        print '%r' % (p4runtime_lib.convert.decodeNum(p4info_helper.get_match_field_value(m)[j]),),
                #print p4info_helper.get_match_field_name(table_name, m.field_id),
                    #print '%r' % (p4info_helper.get_match_field_value(m),),
            action = entry.action.action
            action_name = p4info_helper.get_actions_name(action.action_id)
            print '->', action_name,
            for p in action.params:
                print p4info_helper.get_action_param_name(action_name, p.param_id),
                print '%r' % (p4runtime_lib.convert.decodeNum(p.value)),
            print



def printCounter(p4info_helper, sw, counter_name, index):
    '''
    Reads the specified counter at the specified index from the switch. In our
    program, the index is the tunnel ID. If the index is 0, it will return all
    values from the counter.

    :param p4info_helper: the P4Info helper
    :param sw:  the switch connection
    :param counter_name: the name of the counter from the P4 program
    :param index: the counter index (in our case, the tunnel ID)
    '''
    for response in sw.ReadCounters(p4info_helper.get_counters_id(counter_name), index):
        for entity in response.entities:
            counter = entity.counter_entry
            print "%s %s %d: %d packets (%d bytes)" % (
                sw.name, counter_name, index,
                counter.data.packet_count, counter.data.byte_count
            )


def switch_init_config(K, p4info_helper, bmv2_file_path, sw_id):

    sw = p4runtime_lib.bmv2.Bmv2SwitchConnection(grpc2name(K, sw_id), address='localhost:%d' %(sw_id+50051))
    sw.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
                                   bmv2_json_file_path=bmv2_file_path)
    #print "Installed P4 Program using SetForwardingPipelineConfig on %s" % sw.name


def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4 Runtime helper from the p4info file
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)

    K = 4
    sw_id = 0
    switch_init_config(K, p4info_helper, bmv2_file_path, sw_id)
    # Create a switch connection object for s1 and s2;
    # this is backed by a P4 Runtime gRPC connection
    #s1 = p4runtime_lib.bmv2.Bmv2SwitchConnection('s1', address='localhost:50071')
    #s2 = p4runtime_lib.bmv2.Bmv2SwitchConnection('s2', address='127.0.0.1:50052')

    # Install the P4 program on the switches
    #s1.set_up_stream()
    #s1.SetForwardingPipelineConfig(p4info=p4info_helper.p4info,
    #                               bmv2_json_file_path=bmv2_file_path)
    print "Installed P4 Program using SetForwardingPipelineConfig on %s" % grpc2name(K, sw_id)

    K = 4
    writeRules(K, p4info_helper, sw_id, src_ip_addr="10.0.0.2", src_addr_mask="255.255.255.0",
                dst_ip_addr='10.1.0.2', dst_addr_mask='255.255.255.0', rtmp=5, ttmp=6, out_port=2,
                action_flag=0, priority=3, update_flag_write=0)

    writeRules(K, p4info_helper, sw_id, src_ip_addr="10.0.0.2", src_addr_mask="255.255.255.0",
                dst_ip_addr='10.1.0.2', dst_addr_mask='255.255.255.0', rtmp=5, ttmp=6, out_port=2,
                action_flag=1, priority=2, update_flag_write=0)
    writeRules(K, p4info_helper, sw_id, src_ip_addr="10.0.0.2", src_addr_mask="255.255.255.0",
                dst_ip_addr='10.1.0.2', dst_addr_mask='255.255.255.0', rtmp=5, ttmp=6, out_port=2,
                action_flag=2, priority=1, update_flag_write=0)

    readTableRules(K, p4info_helper, sw_id)

    # Write the rules that tunnel traffic from h1 to h2
    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.1.10", rtmp=[2,2], ttmp=2, out_port=2, action_flag=0, priority=1)

    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.0.10", rtmp=[1,3], ttmp=2, out_port=1, action_flag=0, priority=1)
    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.1.10", rtmp=[1,1], ttmp=1, out_port=2, action_flag=1, priority=1)
    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.1.10", rtmp=[1,5], ttmp=5, out_port=2, action_flag=2, priority=3)

    #sleep(0.8)
    #dst_ip_addr_list = ["10.0.1.10"] * 20
    #rtmp_list=[[1,1]] + [[5,5]]*18 + [[1,3]]
    #ttmp_list = [1] +[3]*19
    #out_port_list = [2]*20
    #action_flag_list = [1] + [0]*19
    #priority_list = [1] + [i+5 for i in range(18)] + [2]
    #update_flag_write_list = [1] + [0]*19
    #writeMultiRules(p4info_helper, sw_id=s1, dst_ip_addr_list=dst_ip_addr_list, rtmp_list=rtmp_list, ttmp_list=ttmp_list, out_port_list=out_port_list, action_flag_list=action_flag_list, priority_list=priority_list, update_flag_write_list=update_flag_write_list)

    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.1.10", rtmp=[1,1], ttmp=1, out_port=2, action_flag=1, priority=1, update_flag_write=1)
    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.1.10", rtmp=[1,3], ttmp=3, out_port=2, action_flag=0, priority=2)
    #writeRules(p4info_helper, sw_id=s1, dst_ip_addr="10.0.1.10", rtmp=[1,1], ttmp=1, out_port=2, action_flag=0, priority=1)
    #readTableRules(p4info_helper, sw=s1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default="/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt")
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default="/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json")
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print "\np4info file not found: %s\nHave you run 'make'?" % args.p4info
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print "\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json
        parser.exit(1)

    main(args.p4info, args.bmv2_json)
