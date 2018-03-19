import sys
import p4runtime_lib.bmv2
import p4runtime_lib.helper
import p4runtime_lib.convert
import argparse
import os
from util import *

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default="/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt")
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default="/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json")
    parser.add_argument('--k', help='topo number',
                        type=int, action="store", required=False,
                        default=4)
    parser.add_argument('--id', help='switch id',
                        type=int, action="store", required=False,
                        default=0)
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print "\np4info file not found: %s\nHave you run 'make'?" % args.p4info
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print "\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json
        parser.exit(1)

    p4info_helper = p4runtime_lib.helper.P4InfoHelper(args.p4info)

    readTableRules(args.k, p4info_helper, args.id)
