from util import *
from cmd_p4 import *
from timestamp import *
from readFile import *
from switch_state import rule, net, table
import copy
import subprocess
import time
import random
from mininet.cli import CLI
from datetime import datetime
from time_process import *
from test_main_all import *
import os


def path_deploy_runtime(old_path, new_path, flow, state_cur, prt, in_port, out_port_old, out_port_new, clock):

    start_time = time.time()

    clk = clock

    rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clk)
    state_update(rule_set, state_cur)

    rule_set_reverse = {}
    for i in rule_set.keys():
        rule_set_reverse[i] = {}
        rule_set_reverse[i]['add'] = rule_set[i]['del']
        rule_set_reverse[i]['del'] = rule_set[i]['add']

    runtime_rule = time.time() - start_time
    #time2 = time.time()
    rule_set = setTMP(old_path, new_path, flow, state_cur, rule_set, clk, in_port)
    state_update(rule_set_reverse, state_cur)
    state_update(rule_set, state_cur)
    #time3 = time.time()
    #rule_set = set_clean(rule_set)

    runtime = time.time() - start_time

    return {'runtime': runtime, 'runtime_rule': runtime_rule}


def state_init(K, state_cur):
    #state_cur = copy.deepcopy(state)
    table_id = 0
    sw_num = pow((K/2),2) + ((K/2)*K) + ((K/2)*K)
    dp_set = [i for i in range(sw_num)]


    for i in dp_set:
        state_cur.add_table(i, 0)
        #state_cur.get_table(i, 0).add_rule({}, 0, 0, 0, 0)

    return state_cur


def test_measure(K, num, flow_list):
    #K = 8
    filepath = os.getcwd() + '/flow_update_%d.tsv' %K
    #flow_list = get_flow_list_new(filepath, K, 0, 100)

    state_cur = net()
    state_init(K, state_cur)

    #proto = 3
    clk = 8 # > 1
    priority = 8
    #CLI(fat_tree_net)

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        in_port_old = flow_list[i]['in_port_old']
        in_port_new = flow_list[i]['in_port_new']

        #path_deploy_runtime(K, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock)
        deploy_ret = path_deploy_runtime([], old_path, flow, state_cur, priority, {}, {}, out_port_old, clk)

        #state_cur = deploy_ret['state']
        #clk = deploy_ret['clk']

    #state_cur.print_state()
    clk = clk + 1
    runtime_list = []

    #flow_list = get_flow_list_new(filepath, K, 0, num)
    #flow_list = {}
    # k = 0
    # for i in flow_list1.keys():
    #     k = k + 1
    #     flow_list[i] = flow_list1[i]
    #     if k >= num:
    #         break

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        in_port_old = flow_list[i]['in_port_old']
        in_port_new = flow_list[i]['in_port_new']

        if old_path != new_path:
            #print i
            deploy_ret = path_deploy_runtime(old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, out_port_new, clk)
            #state_cur = deploy_ret['state']
            #clk = deploy_ret['clk']
            runtime_list.append(deploy_ret['runtime'])
            #print deploy_ret['time']

    retpath = '/home/shengliu/Workspace/result/result_%d_%d.txt' %(K, num)
    fp = open(retpath, 'a+')
    fp.write('%f ' %(sum(runtime_list)))
    fp.close()

    #state_cur.print_state()
    #print runtime_list
    #print "max runtime"
    #print max(runtime_list)
    #print "total runtime"
    #print sum(runtime_list)
    #print "average runtime"
    #print float(sum(runtime_list)) / len(runtime_list)

if __name__ == '__main__':
    K = 6
    filepath = os.getcwd() + '/flow_update_%d.tsv' %K

    #flow_list1 = get_flow_list_new(filepath, K, 0, 100)
    #flow_list2 = get_flow_list_new(filepath, K, 0, 20)

    #test_measure(K, 20, flow_list1)
    flow_list = get_flow_list_new(filepath, K, 0, 100)
    for i in range(1):
        num = 100
        #num = 100
        #flow_list2 = get_flow_list_new(filepath, K, 0, num)
        for j in range(100):
            test_measure(K, num, flow_list)
