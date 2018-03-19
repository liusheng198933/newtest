from util import *
from cmd_p4 import *
from timestamp import *
from readFile import *
from switch_state import rule, net, table
import copy
import subprocess
import time
import random
#from mininet.cli import CLI
from datetime import datetime
from time_process import *

PRTMAX = 100
rtmp_max = pow(2, 8)
cwdpath = '/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/python/'


def network_init(K, p4info_helper, bmv2_file_path, state, flag):
    state_cur = copy.deepcopy(state)
    table_id = 0
    sw_num = pow((K/2),2) + ((K/2)*K) + ((K/2)*K)
    dp_set = [i for i in range(sw_num)]

    for i in dp_set:
        switch_init_config(K, p4info_helper, bmv2_file_path, i)
        # switch_deploy(K, p4info_helper, 1, rule_set)
        #switch_init_config(p4info_file_path, bmv2_file_path, grpc2name(K, i), 50051+i)

    time.sleep(2)
    for i in dp_set:
        #print "drop_rule_push:"
        #print i
        if flag:
            writeRules(K, p4info_helper, i, "10.0.0.0", "255.0.0.0", "10.0.0.0", "255.0.0.0", rtmp_max, 0, 1, action_flag=1, priority=PRTMAX-2)
        writeRules(K, p4info_helper, i, "0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0", rtmp_max, 0, 1, action_flag=2, priority=PRTMAX-1)

        #switch_deploy(K, p4info_helper, 1, rule_set)
        #writeRules(K, p4info_helper, i, "0.0.0.0", "0.0.0.0", 0, 0, 0, action_flag=2, priority=PRTMAX+2)
        #writeRules(K, p4info_helper, i, "10.0.0.0", "255.0.0.0", 0, 0, 0, action_flag=1, priority=PRTMAX+1)
        #drop_rule_push(i, filepath, 1, 1, table_id, 1)
        # default rule has rtmp=1, ttmp=1 and priority=1

    for i in dp_set:
        state_cur.add_table(i, 0)
        #state_next.add_table(i,0)
        state_cur.get_table(i, 0).add_rule({}, 0, 0, 0, 0)
        #state_next.get_table(i, 0).add_rule({}, 1, 1, 0, 0)
    time.sleep(2)
    return state_cur


def old_path_deploy(phase, path_list, state_cur, prt, proto):
    state_next = copy.deepcopy(state_cur)
    bdid = bd
    clk = clock
    state_next = copy.deepcopy(state_cur)
    flow_list = {}
    for j in range(len(path_list['flow'])):
        i = path_list['flow'][j]
        f = match_parse(i)
        if f not in flow_list.keys():
            old_path = path_list['old_path'][j]['path']
            if len(old_path) == 5:
                flow_list[f] = path_list['old_path'][j]['path']
                f_reverse = match_parse(reverse_flow(i))
                old_path_reverse = copy.deepcopy(old_path)
                old_path_reverse.reverse()
                flow_list[f_reverse] = old_path_reverse
                in_port = out_port_construct(old_path, path_list['old_path'][j]['in_port'])
                out_port = out_port_construct(old_path, path_list['old_path'][j]['out_port'])

                deploy_ret = path_deploy([], old_path, i, state_next, prt, in_port, out_port, clk, bdid, 0)
                state_next = deploy_ret['state']
                clk = deploy_ret['clk']
                bdid = deploy_ret['bdid']

    return {'state': state_next, 'clk': clk, 'bdid': bdid, 'flow_list': flow_list}






def path_deploy_coco(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay):
    clk = clock + 1
    #clk = 0
    rule_set = rule_construct_coco(old_path, new_path, flow, state_cur, prt, out_port, clk)
    state_next = state_update(rule_set, state_cur)

    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    old_path_reverse = copy.deepcopy(old_path)
    old_path_reverse.reverse()
    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    rule_set_reverse = rule_construct_coco(old_path_reverse, new_path_reverse, flow_reverse, state_next, prt, in_port, clk)
    state_next_next = state_update(rule_set_reverse, state_next)

    #rule_set_reverse = setTMP(old_path_reverse, new_path_reverse, flow_reverse, state_next, state_next_next, rule_set_reverse, clk)
    #state_next_next = state_update(rule_set_reverse, state_next, clk)
    #state_next.copy_state(state_cur)

    for i in rule_set_reverse.keys():
        if i in rule_set.keys():
            for j in rule_set_reverse[i]['add']:
                rule_set[i]['add'].append(j)
            for j in rule_set_reverse[i]['del']:
                rule_set[i]['del'].append(j)
        else:
            rule_set[i] = rule_set_reverse[i]

    #table_id = 0
    #script_init(filepath)
    rule_set = set_clean(rule_set)

    if not rule_set.keys():
        return {'state': state_next_next, 'clk': clock}

    if not if_delay:
        for dp in rule_set.keys():
            switch_deploy(K, p4info_helper, dp, rule_set[dp])
            #bdid = bdid + 1
            #switch_deploy(dp, rule_set[dp], bdid)
        return {'state': state_next_next, 'clk': clk}

    delay_list = delay_generate(rule_set)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print dp_sort
    #print old_path
    #print new_path
    #print delay_list[old_path[1]] - delay_list[old_path[2]]
    #print delay_list[old_path[3]] - delay_list[old_path[2]]

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        dp = dp_sort[e]
        switch_deploy(K, p4info_helper, dp, rule_set[dp])
        #bdid = bdid + 1
        #switch_deploy(dp, rule_set[dp], bdid)

    return {'state': state_next_next, 'clk': clk}


def path_deploy_normal(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay):
    #clk = clock + 1
    #clk = 0
    rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
    state_next = state_update(rule_set, state_cur)

    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    old_path_reverse = copy.deepcopy(old_path)
    old_path_reverse.reverse()
    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    rule_set_reverse = rule_construct_normal(old_path_reverse, new_path_reverse, flow_reverse, state_next, prt, in_port)
    state_next_next = state_update(rule_set_reverse, state_next)

    #rule_set_reverse = setTMP(old_path_reverse, new_path_reverse, flow_reverse, state_next, state_next_next, rule_set_reverse, clk)
    #state_next_next = state_update(rule_set_reverse, state_next, clk)
    #state_next.copy_state(state_cur)

    for i in rule_set_reverse.keys():
        if i in rule_set.keys():
            for j in rule_set_reverse[i]['add']:
                rule_set[i]['add'].append(j)
            for j in rule_set_reverse[i]['del']:
                rule_set[i]['del'].append(j)
        else:
            rule_set[i] = rule_set_reverse[i]

    if not rule_set.keys():
        return {'state': state_next_next, 'clk': clock}

    #table_id = 0
    #script_init(filepath)

    rule_set = set_clean(rule_set)

    if not if_delay:
        for dp in rule_set.keys():
            switch_deploy(K, p4info_helper, dp, rule_set[dp])
            #switch_deploy(dp, rule_set[dp])
        return {'state': state_next_next, 'clk': clock}

    delay_list = delay_generate(rule_set)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        #switch_deploy(K, p4info_helper, dp, rule_set[dp])
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        dp = dp_sort[e]
        switch_deploy(K, p4info_helper, dp, rule_set[dp])
        #switch_deploy(dp, rule_set[dp])

    return {'state': state_next_next, 'clk': clock}


def path_deploy_cu(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay):
    clk = clock + 1

    rule_set_extra = {}
    #clk = 0
    if not old_path:
        rule_set = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)
    else:
        rule_ret = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port, clk)
        rule_set = rule_ret['rule_set']
        rule_set_extra.update(rule_ret['first_rule'])
        state_next = state_update(rule_set, state_cur)
        state_next = state_update(rule_ret['first_rule'], state_next)



    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    old_path_reverse = copy.deepcopy(old_path)
    old_path_reverse.reverse()
    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    if not old_path:
        rule_set_reverse = rule_construct_cu(old_path_reverse, new_path_reverse, flow_reverse, state_next, prt, in_port, clk)
        state_next_next = state_update(rule_set_reverse, state_next)
    else:
        rule_reverse_ret = rule_construct_cu(old_path_reverse, new_path_reverse, flow_reverse, state_next, prt, in_port, clk)
        rule_set_reverse = rule_reverse_ret['rule_set']
        rule_set_extra.update(rule_reverse_ret['first_rule'])
        state_next_next = state_update(rule_set_reverse, state_next)
        state_next_next = state_update(rule_reverse_ret['first_rule'], state_next_next)

    #rule_set_extra[new_path_reverse[0]] = rule_reverse_ret['first_rule']
    #state_next_next = state_update(rule_set_extra, state_next_next)
    #rule_set_extra.update(first_rule_reverse)
    #rule_set_reverse = setTMP(old_path_reverse, new_path_reverse, flow_reverse, state_next, state_next_next, rule_set_reverse, clk)
    #state_next_next = state_update(rule_set_reverse, state_next, clk)
    #state_next.copy_state(state_cur)

    for i in rule_set_reverse.keys():
        if i in rule_set.keys():
            for j in rule_set_reverse[i]['add']:
                rule_set[i]['add'].append(j)
            for j in rule_set_reverse[i]['del']:
                rule_set[i]['del'].append(j)
        else:
            rule_set[i] = rule_set_reverse[i]

    #table_id = 0
    #script_init(filepath)

    rule_set = set_clean(rule_set)
    rule_set_extra = set_clean(rule_set_extra)

    if not if_delay:
        for dp in rule_set.keys():
            switch_deploy(K, p4info_helper, dp, rule_set[dp])
            #bdid = bdid + 1
            #switch_deploy(dp, rule_set[dp], bdid)
        time.sleep(1)
        #print "first deploy no oldpath"
        #CLI(fat_tree_net)
        for dp in rule_set_extra.keys():
            switch_deploy(K, p4info_helper, dp, rule_set_extra[dp])
            #bdid = bdid + 1
            #switch_deploy(dp, rule_set_extra[dp], bdid)
        return {'state': state_next_next, 'clk': clk}

    delay_list = delay_generate(rule_set)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        dp = dp_sort[e]
        switch_deploy(K, p4info_helper, dp, rule_set[dp])
        #bdid = bdid + 1
        #switch_deploy(dp, rule_set[dp], bdid)

    #print 'first deploy'
    #CLI(fat_tree_net)

    delay_list = delay_generate(rule_set_extra)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        dp = dp_sort[e]
        switch_deploy(K, p4info_helper, dp, rule_set_extra[dp])
        #bdid = bdid + 1
        #switch_deploy(dp, rule_set_extra[dp], bdid)

    return {'state': state_next_next, 'clk': clk}





def path_deploy(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port_old, out_port_old, in_port_new, out_port_new, clock, if_delay):

    clk = clock + 1

    rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port_new, clk)
    state_next = state_update(rule_set, state_cur)

    rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk, in_port_old)
    state_next = state_update(rule_set, state_cur)
    #state_next.copy_state(state_cur)
    """
    for r in rule_set.keys():
        print "add rules:"
        for x in rule_set[r]['add']:
            x.print_rule()
        print "del rules:"
        for x in rule_set[r]['del']:
            x.print_rule()
    """
    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    old_path_reverse = copy.deepcopy(old_path)
    old_path_reverse.reverse()
    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    rule_set_reverse = rule_construct(old_path_reverse, new_path_reverse, flow_reverse, state_next, prt, in_port_new, clk)
    state_next_next = state_update(rule_set_reverse, state_next)

    rule_set_reverse = setTMP(old_path_reverse, new_path_reverse, flow_reverse, state_next, state_next_next, rule_set_reverse, clk, out_port_old)
    state_next_next = state_update(rule_set_reverse, state_next)
    #state_next.copy_state(state_cur)

    for i in rule_set_reverse.keys():
        if i in rule_set.keys():
            for j in rule_set_reverse[i]['add']:
                rule_set[i]['add'].append(j)
            for j in rule_set_reverse[i]['del']:
                rule_set[i]['del'].append(j)
        else:
            rule_set[i] = rule_set_reverse[i]

    if not rule_set.keys():
        return {'state': state_next_next, 'clk': clk}
    #table_id = 0
    #script_init(filepath)
    rule_set = set_clean(rule_set)

    #for i in rule_set.keys():
    #    print "sw %d add rule" %i
    #    for j in rule_set[i]['add']:
    #        j.print_rule()
    #    print "sw %d del rule" %i
    #    for j in rule_set[i]['del']:
    #        j.print_rule()

    if not if_delay:
        for dp in rule_set.keys():
            switch_deploy(K, p4info_helper, dp, rule_set[dp])
            #switch_deploy(dp, rule_set[dp], bdid)
        return {'state': state_next_next, 'clk': clk}

    delay_list = delay_generate(rule_set)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if e == 0 and h_src:
            #h_src.cmd('hping3 -1 -c 200 -i u%d %s &' %(pkt_rate, h_dst.IP()))
        dp = dp_sort[e]
        switch_deploy(K, p4info_helper, dp, rule_set[dp])

        #bdid = bdid + 1
        #switch_deploy(dp, rule_set[dp], bdid)

    return {'state': state_next_next, 'clk': clk}

    #for dp in rule_set.keys():
        #bdid = bdid + 1
        #switch_deploy(dp, rule_set[dp], bdid)
        #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
        #for r in rule_set[dp]['del']:
        #    script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "delete_strict"))
        #for r in rule_set[dp]['add']:
        #    script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "add"))
        #script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
        #subprocess.Popen("%s" %filepath)



def path_deploy_link_init(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port_old, out_port_old, in_port_new, out_port_new, clock, proto):
    #bdid = bd
    #clk = clock + 1

    if proto == 0:
        clk = clock
        rule_set = rule_construct_normal([], old_path, flow, state_cur, prt, out_port_old)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock + 1

        rule_set = rule_construct([], old_path, flow, state_cur, prt, out_port_old, clk)
        #rule_set = rule_construct([], old_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP([], old_path, flow, state_cur, state_next, rule_set, clk, in_port_old)
        #rule_set = setTMP([], old_path, flow, state_cur, state_next, rule_set, clk)
        state_next = state_update(rule_set, state_cur)

    if proto == 2:
        clk = clock + 1
        #clk = 0
        rule_set = rule_construct_cu([], old_path, flow, state_cur, prt, out_port_old, clk)
        state_next = state_update(rule_set, state_cur)

    if proto == 3:
        clk = clock + 1
        #clk = 0
        rule_set = rule_construct_coco([], old_path, flow, state_cur, prt, out_port_old, clk)
        state_next = state_update(rule_set, state_cur)


    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    rule_set_reverse = rule_construct_normal([], new_path_reverse, flow_reverse, state_next, prt, in_port_new)
    state_next_next = state_update(rule_set_reverse, state_next)

    #rule_set_reverse = setTMP(old_path_reverse, new_path_reverse, flow_reverse, state_next, state_next_next, rule_set_reverse, clk)
    #state_next_next = state_update(rule_set_reverse, state_next, clk)
    #state_next.copy_state(state_cur)

    for i in rule_set_reverse.keys():
        if i in rule_set.keys():
            for j in rule_set_reverse[i]['add']:
                rule_set[i]['add'].append(j)
            for j in rule_set_reverse[i]['del']:
                rule_set[i]['del'].append(j)
        else:
            rule_set[i] = rule_set_reverse[i]

    #table_id = 0
    #script_init(filepath)

    rule_set = set_clean(rule_set)

    for dp in rule_set.keys():
        switch_deploy(K, p4info_helper, dp, rule_set[dp])
    return {'state': state_next_next, 'clk': clk}


def setPRT(rule_set_old, old_path, new_path, prt):
    rule_set = copy.deepcopy(rule_set_old)
    for i in rule_set.keys():
        if i in new_path:
            j = prt + new_path.index(i)
        else:
            j = PRTMAX
        for r in rule_set[i]['add']:
            r.set_prt(j)
    return rule_set



def path_deploy_time(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay, proto):
    #bdid = bd
    #bdid_list = {}
    #for i in range(len(new_path)):
    #    bdid_list[new_path[i]] = 20 + i
    #bdid_list[old_path[2]] = 25

    if proto == 0:
        clk = 0
        rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock + 1

        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk, in_port)
        #rule_set = setPRT(rule_set, old_path, new_path, prt)
        state_next = state_update(rule_set, state_cur)

    if not rule_set.keys():
        return {'state': state_next, 'clk': clk}

    rule_set = set_clean(rule_set)

    if proto == 1:
        sb_set = sb_rule_construct(old_path, new_path, flow, clk, in_port)
    table_id = 0

    if not if_delay:
        flag = 0
        for dp in rule_set.keys():
            switch_deploy(K, p4info_helper, dp, rule_set[dp])
            if proto == 1 and (dp == old_path[2] or dp == old_path[1]):
                if flag == 1:
                    #sleep(0.01)
                    for sbdp in sb_set.keys():
                        switch_deploy_delay(K, p4info_helper, sbdp, sb_set[sbdp])
                    #subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/delay_deploy.py'])
                else:
                    flag = 1
        return {'state': state_next, 'clk': clk}


    delay_list = delay_generate(rule_set)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time
    #print rule_set
    #print old_path[2]
    flag = 0

    #subprocess.call(cwdpath+'/time_measure')
    fp = open('/home/shengliu/Workspace/log/start.txt', 'a+')
    fp.write('%s\n' %str(datetime.now()))
    fp.close()
    # record starting time

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
        dp = dp_sort[e]
        #bdid = bdid + 1
        switch_deploy(K, p4info_helper, dp, rule_set[dp])
        if proto == 1 and (dp == old_path[2] or dp == old_path[1]):
            if flag == 1:
                for sbdp in sb_set.keys():
                    switch_deploy_delay(K, p4info_helper, sbdp, sb_set[sbdp])
                #subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/delay_deploy.py'])
            else:
                flag = 1

    return {'state': state_next, 'clk': clk}




def path_deploy_time_cu(K, p4info_helper, fat_tree_net, old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, bd, if_delay, proto):
    #bdid = bd
    #bdid_list = {}
    #for i in range(len(new_path)):
    #    bdid_list[new_path[i]] = 20 + i
    #bdid_list[old_path[2]] = 25


    if proto == 2:
        clk = clock + 1
        del_rule = rule_construct_cu([], old_path, flow, state_cur, prt, out_port_old, clk-1)
        ret_rule = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port_new, clk)
        add_rule = ret_rule['rule_set']
        first_rule = ret_rule['first_rule']

        del del_rule[old_path[0]]
        #print del_rule
        #print add_rule
        #print first_rule

        for i in del_rule.keys():
            for j in del_rule[i]['add']:
                del_rule[i]['del'].append(j)
            del_rule[i]['add'] = []

        state_next = state_update(add_rule, state_cur)
        state_next = state_update(first_rule, state_next)
        state_next = state_update(del_rule, state_next)

        add_rule[old_path[2]] = {}
        add_rule[old_path[2]]['add'] = [rule(old_path[2], {}, 1, 1, 0, 0, 3)]
        add_rule[old_path[2]]['del'] = []

    add_rule = set_clean(add_rule)
    first_rule = set_clean(first_rule)
    del_rule = set_clean(del_rule)

    subprocess.call('/home/shengliu/Workspace/mininet/haha/API/time_measure')

    delay_list = delay_generate(add_rule)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time
    #print rule_set
    #print old_path[2]



    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
        dp = dp_sort[e]
        #bdid = bdid + 1
        bdid = bdid_list[dp]
        switch_deploy(dp, add_rule[dp], bdid)

    #CLI(fat_tree_net)

    delay_list = delay_generate(first_rule)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
        dp = dp_sort[e]
        #bdid = bdid + 1
        bdid = bdid_list[dp]
        switch_deploy(dp, first_rule[dp], bdid)

    #CLI(fat_tree_net)

    delay_list = delay_generate(del_rule)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
        dp = dp_sort[e]
        #bdid = bdid + 1
        bdid = bdid_list[dp]
        switch_deploy(dp, del_rule[dp], bdid)

    #CLI(fat_tree_net)


    return {'state': state_next, 'bdid': bdid, 'clk': clk}






def path_deploy_link(K, p4info_helper, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay, proto):

    start_time = datetime.now()

    if proto == 0:
        clk = 0
        rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock + 1

        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk, in_port)
        state_next = state_update(rule_set, state_cur)


    rule_set = set_clean(rule_set)

    print datetime.now() - start_time



    if not rule_set.keys():
        return {'state': state_next, 'clk': clk}

    if not if_delay:
        for dp in rule_set.keys():
            switch_deploy(K, p4info_helper, dp, rule_set[dp])
        return {'state': state_next, 'clk': clk}


    delay_list = delay_generate(rule_set)
    dp_sort = []
    sleep_time = [0]
    for dp in delay_list.keys():
        e = 0
        while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
            e = e + 1
        dp_sort.insert(e, dp)
        sleep_time.insert(e+1, delay_list[dp])

    #print delay_list
    #print sleep_time
    #print rule_set
    #print old_path[2]
    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
        dp = dp_sort[e]
        if dp != old_path[2]:
            switch_deploy(K, p4info_helper, dp, rule_set[dp])

    return {'state': state_next, 'clk': clk}




def path_deploy_third(fat_tree_net, old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, bd, if_delay, proto):
    bdid = bd
    bdid_list = {}
    for i in range(len(new_path)):
        bdid_list[new_path[i]] = 20 + i
    bdid_list[old_path[2]] = 25

    if proto == 3:
        clk = clock
        #clk = 0
        rule_set = rule_construct_coco_final(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clk)
        state_next = state_update(rule_set['rule_set_first'], state_cur)
        state_next = state_update(rule_set['rule_set_second'], state_next)
        state_next = state_update(rule_set['rule_set_third'], state_next)
        state_next = state_update(rule_set['rule_set_fourth'], state_next)


    rule_set['rule_set_first'][old_path[2]] = {}
    rule_set['rule_set_first'][old_path[2]]['add'] = [rule(old_path[2], {}, 1, 1, 0, 0, 3)]
    rule_set['rule_set_first'][old_path[2]]['del'] = []

    rule_set_idx = ['rule_set_first', 'rule_set_second', 'rule_set_third', 'rule_set_fourth']

    #print rule_set['rule_set_first']

    for i in range(len(rule_set_idx)):
        rule_set[rule_set_idx[i]] = set_clean(rule_set[rule_set_idx[i]])

    subprocess.call('/home/shengliu/Workspace/mininet/haha/API/time_measure')

    if not if_delay:
        for i in range(len(rule_set_idx)):
            for dp in rule_set[rule_set_idx[i]].keys():
                bdid = bdid_list[dp]
                switch_deploy(dp, rule_set[rule_set_idx[i]][dp], bdid)
                time.sleep(0.03)

        return {'state': state_next, 'bdid': bdid, 'clk': clk}

    switch_deploy_multi(rule_set, rule_set_idx, bdid_list, fat_tree_net)

    """
    for i in range(len(rule_set_idx)):
        delay_list = delay_generate(rule_set[rule_set_idx[i]])
        dp_sort = []
        sleep_time = [0]
        for dp in delay_list.keys():
            e = 0
            while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
                e = e + 1
            dp_sort.insert(e, dp)
            sleep_time.insert(e+1, delay_list[dp])

        for e in range(len(dp_sort)):
            time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
            dp = dp_sort[e]
            bdid = bdid_list[dp]
            switch_deploy(dp, rule_set[rule_set_idx[i]][dp], bdid)

        #CLI(fat_tree_net)
    """

    return {'state': state_next, 'bdid': bdid, 'clk': clk}



def path_deploy_twice(K, p4info_helper, old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, if_delay, proto, time_flag=0):


    if proto == 2:
        clk = clock + 1
        del_rule = rule_construct_cu([], old_path, flow, state_cur, prt, out_port_old, clk-1)
        ret_rule = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port_new, clk)
        #del_rule = rule_construct_cu([], old_path, flow, state_cur, prt, out_port_old, clk-1)
        #ret_rule = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port_new, clk)
        add_rule = ret_rule['rule_set']
        first_rule = ret_rule['first_rule']

        del del_rule[old_path[0]]
        #print del_rule
        #print add_rule
        #print first_rule

        for i in del_rule.keys():
            for j in del_rule[i]['add']:
                del_rule[i]['del'].append(j)
            del_rule[i]['add'] = []

        rule_set = {}
        rule_set['rule_set_first'] = add_rule
        rule_set['rule_set_second'] = first_rule
        rule_set['rule_set_third'] = del_rule


        state_next = state_update(add_rule, state_cur)
        state_next = state_update(first_rule, state_next)
        state_next = state_update(del_rule, state_next)
        rule_set_idx = ['rule_set_first', 'rule_set_second', 'rule_set_third']


    if proto == 3:
        clk = clock
        #clk = 0
        rule_set = rule_construct_coco_final(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clk)
        state_next = state_update(rule_set['rule_set_first'], state_cur)
        state_next = state_update(rule_set['rule_set_second'], state_next)
        state_next = state_update(rule_set['rule_set_third'], state_next)
        state_next = state_update(rule_set['rule_set_fourth'], state_next)

        rule_set_idx = ['rule_set_first', 'rule_set_second', 'rule_set_third', 'rule_set_fourth']


    if time_flag:
        if old_path[2] not in rule_set['rule_set_first'].keys():
            rule_set['rule_set_first'][old_path[2]] = {}
            rule_set['rule_set_first'][old_path[2]]['add'] = [rule(old_path[2], {}, 1, 1, 0, 0, 3)]
            rule_set['rule_set_first'][old_path[2]]['del'] = []
        else:
            rule_set['rule_set_first'][old_path[2]]['add'].append(rule(old_path[2], {}, 1, 1, 0, 0, 3))


    for i in range(len(rule_set_idx)):
        if old_path[2] in rule_set[rule_set_idx[i]].keys() and not time_flag:
            rule_set[rule_set_idx[i]][old_path[2]] = {}
        rule_set[rule_set_idx[i]] = set_clean(rule_set[rule_set_idx[i]])

    #print 'first deploy'
    #CLI(fat_tree_net)
    if time_flag:
        fp = open('/home/shengliu/Workspace/log/start.txt', 'a+')
        fp.write('%s\n' %str(datetime.now()))
        fp.close()
        #subprocess.call(cwdpath+'/time_measure')

    for i in range(len(rule_set_idx)):
        delay_list = delay_generate(rule_set[rule_set_idx[i]])
        dp_sort = []
        sleep_time = [0]
        for dp in delay_list.keys():
            e = 0
            while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
                e = e + 1
            dp_sort.insert(e, dp)
            sleep_time.insert(e+1, delay_list[dp])

        #print delay_list
        #print sleep_time

        for e in range(len(dp_sort)):
            time.sleep(sleep_time[e+1] - sleep_time[e])
            #if e == 0 and h_src:
                #h_src.cmd('hping3 -1 -c 200 -i u%d %s &' %(pkt_rate, h_dst.IP()))
            dp = dp_sort[e]
            switch_deploy(K, p4info_helper, dp, rule_set[rule_set_idx[i]][dp])

        #print 'nth deploy'
        #CLI(fat_tree_net)

    return {'state': state_next, 'clk': clk}


def switch_deploy_delay(K, p4info_helper, dp, sw_rule):

    src_ip_addr_list = []
    src_addr_mask_list = []
    dst_ip_addr_list = []
    dst_addr_mask_list = []
    rtmp_list = []
    ttmp_list = []
    out_port_list= []
    action_flag_list = []
    priority_list = []
    update_flag_write_list = []

    for r in sw_rule['del']:
        mt = r.get_match()
        #print "dp: %d" %dp
        #print mt['ipv4_dst']
        #print mt['ipv4_src']
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

    delay = random.normalvariate(150, 50) / 1000
    while delay <= 0:
        delay = random.normalvariate(150, 50) / 1000

    sleep(delay)

    thread = writeThread(K, p4info_helper, dp, src_ip_addr_list, src_addr_mask_list,
                    dst_ip_addr_list, dst_addr_mask_list, rtmp_list, ttmp_list,
                    out_port_list, action_flag_list, priority_list, update_flag_write_list)

    thread.start()

    return thread
    #writeMultiRules(K, p4info_helper, dp, src_ip_addr_list, src_addr_mask_list,
    #                dst_ip_addr_list, dst_addr_mask_list, rtmp_list, ttmp_list,
    #                out_port_list, action_flag_list, priority_list, update_flag_write_list)



def switch_deploy(K, p4info_helper, dp, sw_rule, delay=0):

    src_ip_addr_list = []
    src_addr_mask_list = []
    dst_ip_addr_list = []
    dst_addr_mask_list = []
    rtmp_list = []
    ttmp_list = []
    out_port_list= []
    action_flag_list = []
    priority_list = []
    update_flag_write_list = []

    for r in sw_rule['del']:
        mt = r.get_match()
        #print "dp: %d" %dp
        #print mt['ipv4_dst']
        #print mt['ipv4_src']
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

    ted = writeThread(K, p4info_helper, dp, src_ip_addr_list, src_addr_mask_list,
                    dst_ip_addr_list, dst_addr_mask_list, rtmp_list, ttmp_list,
                    out_port_list, action_flag_list, priority_list, update_flag_write_list, delay)

    ted.start()
    #writeMultiRules(K, p4info_helper, dp, src_ip_addr_list, src_addr_mask_list,
    #                dst_ip_addr_list, dst_addr_mask_list, rtmp_list, ttmp_list,
    #                out_port_list, action_flag_list, priority_list, update_flag_write_list)

    return ted

def switch_deploy_multi(rule_set, rule_set_idx, bd, fat_tree_net=None):
    bdid = bd
    for i in range(len(rule_set_idx)):
        delay_list = delay_generate(rule_set[rule_set_idx[i]])
        dp_sort = []
        sleep_time = [0]
        for dp in delay_list.keys():
            e = 0
            while e < len(dp_sort) and delay_list[dp_sort[e]] <= delay_list[dp]:
                e = e + 1
            dp_sort.insert(e, dp)
            sleep_time.insert(e+1, delay_list[dp])

        for e in range(len(dp_sort)):
            time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
            dp = dp_sort[e]
            if type(bd) == dict:
                bdid = bd[dp]
            else:
                bdid = bdid + 1
            switch_deploy(dp, rule_set[rule_set_idx[i]][dp], bdid, i+1)

        time.sleep(0.02)
        if fat_tree_net:
            CLI(fat_tree_net)

    return bdid



def clear_sb_rules(filepath, old_path, new_path, flow, old_state, clk):
    new_state = copy.deepcopy(old_state)
    sb_set = sb_rule_construct(old_path, new_path, flow, clk)
    table_id = 0
    script_init(filepath)
    for r in sb_set:
        script_write(filepath, addTMPRule(r.get_dpid(), r.get_match(), r.get_rtmp(), r.get_ttmp(), -1, table_id, PRTMAX, "delete_strict"))
        tb = new_state.get_table(r.get_dpid(), table_id)
        tb.del_rule(r.get_match(), r.get_prt())

    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    old_path_reverse = copy.deepcopy(old_path)
    old_path_reverse.reverse()
    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    sb_set = sb_rule_construct(old_path_reverse, new_path_reverse, flow_reverse, clk)
    for r in sb_set:
        script_write(filepath, addTMPRule(r.get_dpid(), r.get_match(), r.get_rtmp(), r.get_ttmp(), -1, table_id, PRTMAX, "delete_strict"))
        tb = new_state.get_table(r.get_dpid(), table_id)
        tb.del_rule(r.get_match(), r.get_prt())
    subprocess.call("%s" %filepath)
    time.sleep(1)
    return new_state


def out_port_construct(dpid_list, out_port_list):
    out_port_dic = {}
    for i in range(len(out_port_list)):
        out_port_dic[dpid_list[i]] = out_port_list[i]
    return out_port_dic


def ip2host(ip):
    ret = ip.strip('\'\"')
    if '/' in ret:
        ret = ret.split('/')[0]
    ret = ret.split('.')
    return "h_" + str(ret[1]) + "_" + str(ret[2]) + "_" + str(int(ret[3])-1)


def delay_generate(rule_set):
    delay = {}
    for i in rule_set.keys():
        delay[i] = random.normalvariate(150, 50) / 1000
        while delay[i] <= 0:
            delay[i] = random.normalvariate(150, 50) / 1000

    #return {'2001000': 0.055763203176993896, '2001001': 0.11741014177363102, '3001001': 0.2007134427993989, '3001000': 0.22471555577759653}
    return delay


def delay_generate_all(dpid_set):
    delay = {}
    for i in range(len(dpid_set)):
        delay[dpid_set[i]] = random.normalvariate(150, 50) / 1000
        while delay[dpid_set[i]] <= 0:
            delay[dpid_set[i]] = random.normalvariate(150, 50) / 1000

    #return {'2001000': 0.055763203176993896, '2001001': 0.11741014177363102, '3001001': 0.2007134427993989, '3001000': 0.22471555577759653}
    return delay


def test_run_all(K, fat_tree_net, pkt_rate, proto, phase):
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, filepath, state_cur)
    #filepath2 = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'
    filepath2 = '/home/shengliu/Workspace/mininet/haha/API/flow_update1.csv'
    path_list = path_read_time(filepath2, K)
    priority = 8
    deploy_ret = old_path_deploy(phase, path_list, state_cur, priority, proto)

    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']
    flow_list = deploy_ret['flow_list']

    time.sleep(4)

    for i in range(len(path_list['flow'])):
        flow = path_list['flow'][i]
        f = match_parse(flow)
        if f in flow_list.keys():
            if cmp(flow_list[f], path_list['old_path'][i]['path']) == 0:

                old_path = path_list['old_path'][i]['path']
                new_path = path_list['new_path'][i]['path']

                in_port = out_port_construct(new_path, path_list['new_path'][i]['in_port'])
                out_port = out_port_construct(new_path, path_list['new_path'][i]['out_port'])

                h_src = fat_tree_net.get(ip2host(flow['ipv4_src']))
                h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))

                h_src.cmd('hping3 -1 -c 100 -i u%d %s &' %(pkt_rate, h_dst.IP()))

                deploy_ret = path_deploy(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1)

                state_cur = deploy_ret['state']
                clk = deploy_ret['clk']
                bdid = deploy_ret['bdid']

                flow_list[f] = path_list['new_path'][i]['path']
                f_reverse = match_parse(reverse_flow(flow))
                old_path_reverse = copy.deepcopy(old_path)
                old_path_reverse.reverse()
                flow_list[f_reverse] = old_path_reverse




def test_run_link(K, fat_tree_net, p4info_file_path, bmv2_file_path, pkt_rate, proto, nt):
    sent_num = pkt_rate
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, p4info_helper, bmv2_file_path, state_cur, ((proto==1) or (proto==3)))
    filepath = cwdpath + 'flow_update.tsv'
    path_list = path_read(filepath, K)
    old_path = path_list['old_path'][nt]['path']
    new_path = path_list['new_path'][nt]['path']

    in_port_old = out_port_construct(old_path, path_list['old_path'][nt]['in_port'])
    out_port_old = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    flow = path_list['flow'][nt]
    priority = 8 # > 2
    clk = 7 # > 1
    out_port_new = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    in_port_new = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])


    if len(old_path) == 3:
        return 'Error'

    deploy_ret = path_deploy_link_init(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, in_port_new, out_port_new, clk, proto)

    #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    #bdid = deploy_ret['bdid']
    #path_deploy([], old_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)
    #subprocess.Popen("%s" %filepath)

    #print "old path deployed"
    #CLI(fat_tree_net)

    time.sleep(4)

    h_src = fat_tree_net.get(ip2host(flow['ipv4_src']))
    h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))
    #print ip2host(flow['ipv4_src'])
    #h_src = fat_tree_net.get('h_2_0_0')
    #print "host cmd result:"
    #h_src.cmd('ifconfig &')
    #print h_src.cmd('echo')
    #print h_src.cmd('ifconfig')
    sendpath = cwdpath + 'send_pkt.py'
    recpath = cwdpath + 'rec_pkt.py'
    #priority = 8
    delay = 1.0 / pkt_rate - 0.001


    writeRules(K, p4info_helper, old_path[2], "0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0", rtmp_max, 0, 1, action_flag=2, priority=1)


    #state_cur.print_state()
    #print 'link break'
    #CLI(fat_tree_net)

    h_dst.cmd('python', recpath, str(ip2host(flow['ipv4_dst'])), '&')
    time.sleep(1)
    h_src.cmd('python', sendpath, sent_num, str(ip2host(flow['ipv4_src'])), str(ip2host(flow['ipv4_dst'])), str(delay), '&')

    if proto == 0 or proto == 1:
        deploy_ret = path_deploy_link(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_new, clk, 1, proto)

    #if proto == 0:
    #    deploy_ret = path_deploy_normal(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
    #if proto == 1:
    #    deploy_ret = path_deploy(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, in_port_new, out_port_new, clk, 1)
    if proto == 2 or proto == 3:
        deploy_ret = path_deploy_twice(K, p4info_helper, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, 1, proto)


    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']

    #print 'new path'
    #CLI(fat_tree_net)
    #time.sleep(1)

    #state_cur.print_state()

    #CLI(fat_tree_net)


    time.sleep(10)
    #print out

    ping_ret_o = h_dst.cmd('echo')
    #print h_src.cmd('echo')
    #print ping_ret_o
    recv_num = ping_ret_o.strip().split('\n')[1]
    #state_cur = clear_sb_rules(filepath, old_path, new_path, flow, state_cur, clk)
    print recv_num
    retpath = cwdpath + '/result/run_result_%d.txt' %proto
    fp = open(retpath, 'a+')
    fp.write('idx: %d pkt_rate: %d sent_num: %d recv_num: %s\n' %(nt, pkt_rate, sent_num, recv_num))
    fp.close()

    #CLI(fat_tree_net)

    return 'True'




def test_run(K, fat_tree_net, p4info_file_path, bmv2_file_path, pkt_rate, proto, nt):

    sent_num = pkt_rate
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, p4info_helper, bmv2_file_path, state_cur, ((proto==1) or (proto==3)))
    filepath = cwdpath + 'flow_update.tsv'
    path_list = path_read(filepath, K)
    old_path = path_list['old_path'][nt]['path']
    new_path = path_list['new_path'][nt]['path']

    in_port_old = out_port_construct(old_path, path_list['old_path'][nt]['in_port'])
    out_port_old = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    flow = path_list['flow'][nt]
    priority = 8 # > 2
    clk = 7 # > 1



    if len(old_path) == 3:
        return 'Error'

    if proto == 0:
        deploy_ret = path_deploy_normal(K, p4info_helper, [], old_path, flow, state_cur, priority, in_port_old, out_port_old, clk, 0)
        #deploy_ret = path_deploy_normal([], old_path, flow, state_cur, priority, in_port, out_port, bdid, 0)
    if proto == 1:
        deploy_ret = path_deploy(K, p4info_helper, [], old_path, flow, state_cur, priority, {}, {}, in_port_old, out_port_old, clk, 0)
        #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, {}, {}, in_port_old, out_port_old, clk, 0)
    if proto == 2:
        deploy_ret = path_deploy_cu(K, p4info_helper, [], old_path, flow, state_cur, priority, in_port_old, out_port_old, clk, 0)
        #deploy_ret = path_deploy_cu([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    if proto == 3:
        deploy_ret = path_deploy_coco(K, p4info_helper, [], old_path, flow, state_cur, priority, in_port_old, out_port_old, clk, 0)
        #deploy_ret = path_deploy_coco([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)


    #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    #bdid = deploy_ret['bdid']
    #path_deploy([], old_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)
    #subprocess.Popen("%s" %filepath)



    time.sleep(4)

    #state_cur.print_state()

    #print 'path init'
    #CLI(fat_tree_net)
    #print ip2host(flow['ipv4_src'])
    #print ip2host(flow['ipv4_dst'])
    #CLI(fat_tree_net)
    h_src = fat_tree_net.get(ip2host(flow['ipv4_src']))
    h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))
    #print ip2host(flow['ipv4_src'])
    #h_src = fat_tree_net.get('h_2_0_0')
    #print "host cmd result:"
    #h_src.cmd('ifconfig &')
    #print h_src.cmd('echo')
    #print h_src.cmd('ifconfig')
    sendpath = cwdpath + 'send_pkt.py'
    recpath = cwdpath + 'rec_pkt.py'
    #priority = 8
    delay = 1.0 / pkt_rate - 0.001
    h_dst.cmd('python', recpath, str(ip2host(flow['ipv4_dst'])), '&')
    time.sleep(1)
    for y in range(6):
        h_src.cmd('python', sendpath, sent_num, str(ip2host(flow['ipv4_src'])), str(ip2host(flow['ipv4_dst'])), str(delay), '&')

    #h_src.cmd('hping3 -1 -c 200 -i u%d %s &' %(pkt_rate, h_dst.IP()))

    #print datetime.now().strftime("%H:%M:%S.%f")
    #clk = 10
    out_port_new = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    in_port_new = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])


    if proto == 0:
        pass
        #deploy_ret = path_deploy_normal(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
        #deploy_ret = path_deploy_normal(old_path, new_path, flow, state_cur, priority, in_port, out_port, bdid, 1)
    if proto == 1:
        deploy_ret = path_deploy(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, in_port_new, out_port_new, clk, 1)
        #deploy_ret = path_deploy(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1, h_src, h_dst, pkt_rate)
    if proto == 2:
        deploy_ret = path_deploy_cu(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
        #deploy_ret = path_deploy_cu(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1)
    if proto == 3:
        deploy_ret = path_deploy_coco(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
        #deploy_ret = path_deploy_coco(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1)

    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']



    time.sleep(10)
    #print out

    ping_ret_o = h_dst.cmd('echo')
    #print h_src.cmd('echo')
    #print ping_ret_o
    recv_num = ping_ret_o.strip().split('\n')[1]
    #state_cur = clear_sb_rules(filepath, old_path, new_path, flow, state_cur, clk)
    #state_cur.print_state()
    #print 'path change'
    #CLI(fat_tree_net)
    #print "ping result:" + ping_ret
    # if 'packets received' not in ping_ret_o:
    #     #print ping_ret
    #     return 'False'
    #
    # ping_ret = ping_ret_o.strip().split('\n')
    #
    # for i in range(len(ping_ret)):
    #     if ('packets transmitted' in ping_ret[i]) and ('packets received' in ping_ret[i]):
    #         x = ping_ret[i].strip().split()
    #         sent_num = x[0]
    #         recv_num = x[3]
    #         print sent_num
    #         print recv_num
    #         #if int(recv_num) < int(sent_num):
    #             #print ping_ret_o
    #             #CLI(fat_tree_net)
    #     if 'min/avg/max' in ping_ret[i]:
    #         x = ping_ret[i].strip().split()[3]
    #         rtt_min = x.split('/')[0]
    #         rtt_avg = x.split('/')[1]
    #         rtt_max = x.split('/')[2]
    #         #print rtt_min
    #         #print rtt_avg
    #         #print rtt_max
    #
    #pkt_rate = 1000
    retpath = cwdpath + '/result/run_result_%d.txt' %proto
    fp = open(retpath, 'a+')
    fp.write('idx: %d pkt_rate: %d sent_num: %d recv_num: %s\n' %(nt, pkt_rate, sent_num, recv_num))
    fp.close()

    #CLI(fat_tree_net)

    return 'True'

    #h_src.cmd('python write.py %d %s' %(5, h_dst.IP()))

    #h_dst.cmd('python write.py %d %s' %(5, h_src.IP()))
    #h_src.cmd('python write.py')





def test_run_time(K, fat_tree_net, p4info_file_path, bmv2_file_path, pkt_rate, proto, nt):
    result_dir = '/home/shengliu/Workspace/log'
    empty_directory(result_dir)

    sent_num = pkt_rate
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, p4info_helper, bmv2_file_path, state_cur, ((proto==1) or (proto==3)))
    filepath = cwdpath + 'flow_update.tsv'
    path_list = path_read(filepath, K)
    old_path = path_list['old_path'][nt]['path']
    new_path = path_list['new_path'][nt]['path']

    in_port_old = out_port_construct(old_path, path_list['old_path'][nt]['in_port'])
    out_port_old = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    flow = path_list['flow'][nt]
    priority = 8 # > 2
    clk = 7 # > 1

    out_port_new = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    in_port_new = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])

    if len(old_path) == 3:
        return 'Error'

    deploy_ret = path_deploy_link_init(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, in_port_new, out_port_new, clk, proto)

    #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']

    #path_deploy([], old_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)
    #subprocess.Popen("%s" %filepath)



    time.sleep(5)


    #out_port_new = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    #in_port = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])
    #out_port_old = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    #state_cur.print_state()
    #print 'link break'
    #CLI(fat_tree_net)

    if proto == 0 or proto == 1:
        deploy_ret = path_deploy_time(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_new, clk, 1, proto)

    #if proto == 2:
    #    deploy_ret = path_deploy_time_cu(K, p4info_helper, fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, 1, proto)

    #if proto == 3:
    #    deploy_ret = path_deploy_third(K, p4info_helper, fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, 0, proto)

    if proto == 2 or proto == 3:
        deploy_ret = path_deploy_twice(K, p4info_helper, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, 1, proto, 1)

    #CLI(fat_tree_net)

    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']

    time.sleep(5)

    dirpath = '/home/shengliu/Workspace/log/'
    sw_name = ['es_0_0', 'es_1_0', 'as_0_0', 'as_1_0', 'cs_1', 'cs_0']
    #sw_name = ['cs_1']
    sw_rule_dic = {}
    sw_rule_dic['cs_1'] = 1
    sw_name_check = ['es_1_0', 'as_0_0', 'as_1_0', 'cs_1']

    if proto == 0:
        ret = time_result_process_normal(dirpath, sw_name)
        persist_time = [0]
        complete_time = ret['complete_time']

    if proto == 1:
        ret = time_result_process(dirpath, sw_name, sw_rule_dic)
        persist_time = ret['persist_time']
        complete_time = ret['complete_time']

    if proto == 2:
        ret = time_result_process_cu(dirpath, sw_name, sw_name_check)
        persist_time = ret['persist_time']
        complete_time = ret['complete_time']

    if proto == 3:
        ret = time_result_process_coco(dirpath, sw_name, sw_name_check)
        persist_time = ret['persist_time']
        complete_time = ret['complete_time']

    retpath = cwdpath + '/result/com_result_%d.txt' %proto
    fp = open(retpath, 'a+')
    fp.write('%f\n' %complete_time)
    fp.close()

    retpath = cwdpath + '/result/per_result_%d.txt' %proto
    fp = open(retpath, 'a+')
    for r in persist_time:
        fp.write('%f ' %r)
    fp.write('\n')
    fp.close()

    return 'True'


def measure_time(K, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock):

    start_time = datetime.now()

    clk = clock + 1

    rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
    state_next = state_update(rule_set, state_cur)

    rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk, in_port)
    state_next = state_update(rule_set, state_cur)


    rule_set = set_clean(rule_set)

    print datetime.now() - start_time

    return {'state': state_next, 'clk': clk}

if __name__ == '__main__':
    #filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    K = 8
    state_cur = net()
    state_next = net()

    p4info_file_path = '/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.proto.txt'
    bmv2_file_path = "/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/test_router.json"

    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    table_id = 0
    sw_num = pow((K/2),2) + ((K/2)*K) + ((K/2)*K)
    dp_set = [i for i in range(sw_num)]

    for i in dp_set:
       state_cur.add_table(i, 0)
       state_cur.get_table(i, 0).add_rule({}, 0, 0, 0, 0)

    #state_cur = network_init(K, p4info_helper, bmv2_file_path, state_cur, 1)
    #network_init(K, filepath, state_cur, state_next)

    filepath = '/home/shengliu/Workspace/behavioral-model/targets/simple_switch_grpc/newtest/python/flow_update.tsv'
    time.sleep(1)
    path_list = path_read(filepath, K)

    old_path = path_list['old_path'][12]['path']
    new_path = path_list['new_path'][12]['path']
    print old_path
    print new_path
    print path_list['old_path'][12]['out_port']
    print path_list['new_path'][12]['out_port']
    out_port_old = out_port_construct(old_path, path_list['old_path'][12]['out_port'])
    in_port_old = out_port_construct(old_path, path_list['old_path'][12]['in_port'])
    flow = path_list['flow'][12]
    print flow
    priority = 8
    clk = 2
    out_port_new = out_port_construct(new_path, path_list['new_path'][12]['out_port'])
    in_port_new = out_port_construct(new_path, path_list['new_path'][12]['in_port'])

    #rule_set = rule_construct([], old_path, flow, state_cur, priority, out_port, clk)
    #state_update(rule_set, state_next, clk)
    #setTMP([], old_path, flow, state_cur, state_next, rule_set, clk)
    #state_update(rule_set, state_cur, clk)
    #state_next.copy_state(state_cur)
    print in_port_old
    print out_port_old


    ret = measure_time(K, [], old_path, flow, state_cur, priority, {}, out_port_old, clk)
    state_cur = ret['state']
    clk = ret['clk']

    ret = measure_time(K, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_new, clk)
    state_cur = ret['state']
    clk = ret['clk']

    # ret = path_deploy_coco(K, p4info_helper, [], old_path, flow, state_cur, priority, in_port_old, out_port_old, clk, 1)
    # #ret = path_deploy_cu(K, p4info_helper, [], old_path, flow, state_cur, priority, in_port_old, out_port_old, clk, 1)
    # #ret = path_deploy_normal(K, p4info_helper, [], old_path, flow, state_cur, priority, in_port_old, out_port_old, clk, 1)
    # #ret = path_deploy_normal(K, p4info_helper, [], old_path, flow, state_cur, priority, {}, {}, in_port_old, out_port_old, clk, 1)
    # state_cur = ret['state']
    # state_cur.print_state()
    # clk = ret['clk']
    #
    # #priority = 9
    # out_port_new = out_port_construct(new_path, path_list['new_path'][12]['out_port'])
    # in_port_new = out_port_construct(new_path, path_list['new_path'][12]['in_port'])
    #
    # print "change"
    # time.sleep(1)
    #
    # #ret = path_deploy_coco(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
    # #ret = path_deploy_cu(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
    # #ret = path_deploy_normal(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_new, out_port_new, clk, 1)
    # # ret = path_deploy(K, p4info_helper, old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, in_port_new, out_port_new, clk, 1)
    # state_cur = ret['state']
    # state_cur.print_state()
    # clk = ret['clk']
    #
    # # time.sleep(2)
    # #
    # #
    # match = {}
    # match['ipv4_dst'] = flow['ipv4_dst']
    # match['ipv4_src'] = flow['ipv4_src']
    # match["eth_type"] = 2048
    # # r = rule(12, match, [clk+1,clk+1], clk, 1, 0, 20)
    # # print "send_back rule"
    # # print r.print_rule()
    # # rule_set = {}
    # # rule_set['add'] = [r]
    # # rule_set['del'] = [rule(12, match, 0, clk, 1, 0, 8)]
    # # switch_deploy(K, p4info_helper, 12, rule_set)
    # #
    # # rule_set = {}
    # # rule_set['add'] = [rule(0, match, clk+1, clk, 2, 0, 8)]
    # # rule_set['del'] = []
    # # switch_deploy(K, p4info_helper, 0, rule_set)
    # # print "change"
    # # time.sleep(5)
    # #
    # rule_set = {}
    # #rule_set['add'] = []
    # #rule_set['del'] = [r]
    # rule_set['add'] = [rule(4, match, clk+1, clk+1, 1, 0, 8)]
    # rule_set['del'] = [rule(4, match, clk, clk, 2, 0, 8)]
    # switch_deploy(K, p4info_helper, 4, rule_set)
    #
    # print "change"
    # sleep(10)
    #
    # rule_set = {}
    # #rule_set['add'] = []
    # #rule_set['del'] = [r]
    # rule_set['add'] = [rule(0, match, clk+1, clk, 2, 0, 8)]
    # rule_set['del'] = []
    # switch_deploy(K, p4info_helper, 0, rule_set)


    #rule_set = {}
    #rule_set['add'] = []
    #rule_set['del'] = [r]
    #rule_set['add'] = [rule(12, match, clk, clk, 1, 0, 8)]
    #rule_set['del'] = [rule(12, match, 0, clk, 1, 0, 8)]
    #switch_deploy(K, p4info_helper, 12, rule_set)

    #subprocess.call("%s" %filepath)
    #clk = 10
    #out_port = out_port_construct(new_path, path_list['new_path'][0]['out_port'])
    #in_port = out_port_construct(new_path, path_list['new_path'][0]['in_port'])
    #print "\n\n\nnew route:"
    #print in_port
    #print out_port
    #path_deploy(old_path, new_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, 1)
    #state_cur.print_state()

    #state_next.print_state()
    #subprocess.call("%s" %filepath)

    #print "\n\n\nclear sb rules:"
    #clear_sb_rules(filepath, old_path, new_path, flow, state_cur, state_next, clk)
    #state_cur.print_state()
    #subprocess.call("%s" %filepath)

    """
    out_port = out_port_construct(new_path, path_list['old_path'][0]['out_port'])
    clk = clk + 1

    path_deploy(old_path, new_path, flow, state_cur, state_next, priority, out_port, clk, bdid, filepath)

    #subprocess.call("%s" %filepath)

    clear_sb_rules(filepath, old_path, new_path, flow, clk, bdid)
    #subprocess.call("%s" %filepath)
    """
