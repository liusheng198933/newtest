import sys
import p4runtime_lib.bmv2
import p4runtime_lib.helper
import p4runtime_lib.convert
import argparse
import os
from util import *

def readTableRules(K, p4info_helper, sw_id, flag=0):
    '''
    Reads the table entries from all tables on the switch.

    :param p4info_helper: the P4Info helper
    :param sw: the switch connection
    '''
    if flag:
        sw = p4runtime_lib.bmv2.Bmv2SwitchConnection('s%d' %(sw_id+1), address='localhost:%d' %(sw_id+50051))
    else:
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
    parser.add_argument('--flag', help='if fat tree',
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
