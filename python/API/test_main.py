from util import *
from cmd_issue_new import *
from timestamp import *
from readFile import *
import copy
import subprocess
import time
import random
from mininet.cli import CLI
from datetime import datetime
PRTMAX = 100

def network_init(K, filepath, state):
    state_cur = copy.deepcopy(state)
    script_init(filepath)
    table_id = 0
    dpset = ['1'*7] # arp switch
    for core in range(pow((K/2),2)):
        dpset.append(int2dpid(1, core))
    for i in range(2,4):
        for pod in range(K):
            for swNum in range(K/2):
                dpset.append(int2dpid(i, swNum, pod))
    for i in dpset:
        script_write(filepath, table_clear(i))
    for i in dpset:
        if i != '1'*7:
            #print "drop_rule_push:"
            #print i
            drop_rule_push(i, filepath, 1, 1, table_id, 1)
            # default rule has rtmp=1, ttmp=1 and priority=1
    arp_rule_push('1'*7, filepath, table_id, 1)
    for pod in range(K):
        for swNum in range(K/2):
            arp_rule_push(int2dpid(3, swNum, pod), filepath, table_id, 2)
    subprocess.Popen("%s" %filepath)

    for i in dpset:
        if i != '1'*7:
            state_cur.add_table(i, 0)
            #state_next.add_table(i,0)
            state_cur.get_table(i, 0).add_rule({}, 1, 1, 0, 0)
            #state_next.get_table(i, 0).add_rule({}, 1, 1, 0, 0)
    time.sleep(1)
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



def path_deploy_cu(old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, bd, if_delay):
    bdid = bd
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
            bdid = bdid + 1
            switch_deploy(dp, rule_set[dp], bdid)
        for dp in rule_set_extra.keys():
            bdid = bdid + 1
            switch_deploy(dp, rule_set_extra[dp], bdid)
        return {'state': state_next_next, 'bdid': bdid, 'clk': clk}

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
        bdid = bdid + 1
        switch_deploy(dp, rule_set[dp], bdid)

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
        bdid = bdid + 1
        switch_deploy(dp, rule_set_extra[dp], bdid)

    return {'state': state_next_next, 'bdid': bdid, 'clk': clk}



def path_deploy_normal(old_path, new_path, flow, state_cur, prt, in_port, out_port, bd, if_delay):
    bdid = bd
    #clk = clock + 1
    clk = 0
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

    #table_id = 0
    #script_init(filepath)

    rule_set = set_clean(rule_set)

    if not if_delay:
        for dp in rule_set.keys():
            bdid = bdid + 1
            switch_deploy(dp, rule_set[dp], bdid)
        return {'state': state_next_next, 'bdid': bdid, 'clk': clk}

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
        bdid = bdid + 1
        switch_deploy(dp, rule_set[dp], bdid)

    return {'state': state_next_next, 'bdid': bdid, 'clk': clk}


def path_deploy_coco(old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, bd, if_delay):
    bdid = bd
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

    if not if_delay:
        for dp in rule_set.keys():
            bdid = bdid + 1
            switch_deploy(dp, rule_set[dp], bdid)
        return {'state': state_next_next, 'bdid': bdid, 'clk': clk}

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
        bdid = bdid + 1
        switch_deploy(dp, rule_set[dp], bdid)

    return {'state': state_next_next, 'bdid': bdid, 'clk': clk}


def path_deploy(old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, bd, if_delay, h_src=None, h_dst=None, pkt_rate=None):
    bdid = bd
    clk = clock + 1

    rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
    state_next = state_update(rule_set, state_cur)

    rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk)
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

    rule_set_reverse = rule_construct(old_path_reverse, new_path_reverse, flow_reverse, state_next, prt, in_port, clk)
    state_next_next = state_update(rule_set_reverse, state_next)

    rule_set_reverse = setTMP(old_path_reverse, new_path_reverse, flow_reverse, state_next, state_next_next, rule_set_reverse, clk)
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
        return {'state': state_next_next, 'bdid': bdid, 'clk': clk}
    #table_id = 0
    #script_init(filepath)
    rule_set = set_clean(rule_set)

    if not if_delay:
        for dp in rule_set.keys():
            bdid = bdid + 1
            switch_deploy(dp, rule_set[dp], bdid)
        return {'state': state_next_next, 'bdid': bdid, 'clk': clk}

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
        if e == 0 and h_src:
            h_src.cmd('hping3 -1 -c 200 -i u%d %s &' %(pkt_rate, h_dst.IP()))
        dp = dp_sort[e]
        bdid = bdid + 1
        switch_deploy(dp, rule_set[dp], bdid)

    return {'state': state_next_next, 'bdid': bdid, 'clk': clk}

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



def path_deploy_link_init(old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, bd, proto):
    bdid = bd
    #clk = clock + 1

    if proto == 0:
        clk = clock
        rule_set = rule_construct_normal([], old_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock + 1

        rule_set = rule_construct([], old_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP([], old_path, flow, state_cur, state_next, rule_set, clk)
        state_next = state_update(rule_set, state_cur)

    if proto == 2:
        clk = clock + 1
        #clk = 0
        rule_set = rule_construct_cu([], old_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

    if proto == 3:
        clk = clock + 1
        #clk = 0
        rule_set = rule_construct_coco([], old_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)


    flow_reverse = reverse_flow(flow)
    #flow_reverse['ipv4_src'] = flow['ipv4_dst']
    #flow_reverse['ipv4_dst'] = flow['ipv4_src']

    new_path_reverse = copy.deepcopy(new_path)
    new_path_reverse.reverse()

    rule_set_reverse = rule_construct_normal([], new_path_reverse, flow_reverse, state_next, prt, in_port)
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
        bdid = bdid + 1
        switch_deploy(dp, rule_set[dp], bdid)
    return {'state': state_next_next, 'bdid': bdid, 'clk': clk}


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


def path_deploy_time(old_path, new_path, flow, state_cur, prt, out_port, clock, bd, if_delay, proto):
    bdid = bd
    bdid_list = {}
    for i in range(len(new_path)):
        bdid_list[new_path[i]] = 20 + i
    bdid_list[old_path[2]] = 25

    if proto == 0:
        clk = 0
        rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock + 1

        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk)
        #rule_set = setPRT(rule_set, old_path, new_path, prt)
        state_next = state_update(rule_set, state_cur)

    if proto == 2:
        clk = clock + 1

        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk)
        rule_set = setPRT(rule_set, old_path, new_path, prt)
        state_next = state_update(rule_set, state_cur)



    if proto == 3:
        clk = clock + 1
        #clk = 0
        rule_set = rule_construct_coco(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)


    if not rule_set.keys():
        return {'state': state_next, 'bdid': bdid, 'clk': clk}

    rule_set = set_clean(rule_set)

    if not if_delay:
        flag = 0
        for dp in rule_set.keys():
            bdid = bdid_list[dp]
            switch_deploy(dp, rule_set[dp], bdid)
            if dp == old_path[2] or dp == old_path[1]:
                if flag == 1:
                    subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/delay_deploy.py'])
                else:
                    flag = 1
        return {'state': state_next, 'bdid': bdid, 'clk': clk}

    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    sb_set = sb_rule_construct(old_path, new_path, flow, clk)
    table_id = 0
    script_init(filepath)
    for r in sb_set:
        script_write(filepath, addTMPRule(r.get_dpid(), r.get_match(), r.get_rtmp(), r.get_ttmp(), -1, table_id, PRTMAX, "delete_strict"))

    subprocess.call('/home/shengliu/Workspace/mininet/haha/API/time_measure')

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


    for e in range(len(dp_sort)):
        time.sleep(sleep_time[e+1] - sleep_time[e])
        #if dp != old_path[2]:
        dp = dp_sort[e]
        #bdid = bdid + 1
        bdid = bdid_list[dp]
        switch_deploy(dp, rule_set[dp], bdid)
        if dp == old_path[2] or dp == old_path[1]:
            if flag == 1:
                subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/delay_deploy.py'])
            else:
                flag = 1

    return {'state': state_next, 'bdid': bdid, 'clk': clk}



def path_deploy_time_cu(fat_tree_net, old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, bd, if_delay, proto):
    bdid = bd
    bdid_list = {}
    for i in range(len(new_path)):
        bdid_list[new_path[i]] = 20 + i
    bdid_list[old_path[2]] = 25


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





def path_deploy_link(old_path, new_path, flow, state_cur, prt, out_port, clock, bd, if_delay, proto):
    bdid = bd

    if proto == 0:
        clk = 0
        rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock + 1

        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk)
        state_next = state_update(rule_set, state_cur)

    if proto == 3:
        clk = clock + 1
        #clk = 0
        rule_set = rule_construct_coco(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

    rule_set = set_clean(rule_set)

    if not rule_set.keys():
        return {'state': state_next, 'bdid': bdid, 'clk': clk}

    if not if_delay:
        for dp in rule_set.keys():
            bdid = bdid + 1
            switch_deploy(dp, rule_set[dp], bdid)
        return {'state': state_next, 'bdid': bdid, 'clk': clk}


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
            bdid = bdid + 1
            switch_deploy(dp, rule_set[dp], bdid)

    return {'state': state_next, 'bdid': bdid, 'clk': clk}



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



def path_deploy_twice(fat_tree_net, old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, bd, if_delay, proto):
    bdid = bd
    bdid_list = {}
    for i in range(len(new_path)):
        bdid_list[new_path[i]] = 20 + i
    bdid_list[old_path[2]] = 25

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

        rule_set = {}
        rule_set['rule_set_first'] = add_rule
        rule_set['rule_set_second'] = first_rule
        rule_set['rule_set_third'] = del_rule


        state_next = state_update(add_rule, state_cur)
        state_next = state_update(first_rule, state_next)
        state_next = state_update(del_rule, state_next)


    if proto == 3:
        clk = clock
        #clk = 0
        rule_set = rule_construct_coco_final(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clk)
        state_next = state_update(rule_set['rule_set_first'], state_cur)
        state_next = state_update(rule_set['rule_set_second'], state_next)
        state_next = state_update(rule_set['rule_set_third'], state_next)
        state_next = state_update(rule_set['rule_set_fourth'], state_next)

    rule_set_idx = ['rule_set_first', 'rule_set_second', 'rule_set_third']



    for i in range(len(rule_set_idx)):
        if old_path[2] in rule_set[rule_set_idx[i]].keys():
            rule_set[rule_set_idx[i]][old_path[2]] = {}
        rule_set[rule_set_idx[i]] = set_clean(rule_set[rule_set_idx[i]])

    #print 'first deploy'
    #CLI(fat_tree_net)
    subprocess.call('/home/shengliu/Workspace/mininet/haha/API/time_measure')

    bdid = switch_deploy_multi(rule_set, rule_set_idx, bdid)
    #CLI(fat_tree_net)
    time.sleep(1)
    # 1s delay for a packet to be buffered and applied by new rule
    rule_set_idx = ['rule_set_fourth']
    bdid = switch_deploy_multi(rule_set, rule_set_idx, bdid)
    #CLI(fat_tree_net)
    return {'state': state_next, 'bdid': bdid, 'clk': clk}




def switch_deploy(dp, sw_rule, bdid, step=1):
    filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
    table_id = 0
    script_init(filepath)
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    for r in sw_rule['del']:
        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "delete_strict"))
    for r in sw_rule['add']:
        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
    subprocess.Popen("%s" %filepath)


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









def test_run(K, fat_tree_net, pkt_rate, proto, nt):
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, filepath, state_cur)
    filepath2 = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'
    path_list = path_read(filepath2, K)
    old_path = path_list['old_path'][nt]['path']
    new_path = path_list['new_path'][nt]['path']

    in_port = out_port_construct(old_path, path_list['old_path'][nt]['in_port'])
    out_port = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    flow = path_list['flow'][nt]
    priority = 8 # > 2
    clk = 7 # > 1
    bdid = 1

    if len(old_path) == 3:
        return 'Error'

    if proto == 0:
        deploy_ret = path_deploy_normal([], old_path, flow, state_cur, priority, in_port, out_port, bdid, 0)
    if proto == 1:
        deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    if proto == 2:
        deploy_ret = path_deploy_cu([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    if proto == 3:
        deploy_ret = path_deploy_coco([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)


    #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']
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
    #writepath = '/home/shengliu/Workspace/mininet/haha/API/ping_result.txt'
    #priority = 8

    #h_src.cmd('hping3 -1 -c 200 -i u%d %s &' %(pkt_rate, h_dst.IP()))

    #print datetime.now().strftime("%H:%M:%S.%f")
    #clk = 10
    out_port = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    in_port = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])


    if proto == 0:
        deploy_ret = path_deploy_normal(old_path, new_path, flow, state_cur, priority, in_port, out_port, bdid, 1)
    if proto == 1:
        deploy_ret = path_deploy(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1, h_src, h_dst, pkt_rate)
    if proto == 2:
        deploy_ret = path_deploy_cu(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1)
    if proto == 3:
        deploy_ret = path_deploy_coco(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 1)

    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']


    #time.sleep(1)

    #state_cur.print_state()

    #CLI(fat_tree_net)

    #path_deploy(old_path, new_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)
    #path_deploy_normal(old_path, new_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)

    #state_next.print_state()
    #subprocess.call("%s" %filepath)

    #print ping_ret
    #with open(writepath, 'a+') as f:
    #    f.write(ping_ret)
    #    f.close()

    #state_cur = clear_sb_rules(filepath, old_path, new_path, flow, state_cur, clk)

    #time.sleep(1)

    #state_cur.print_state()

    #CLI(fat_tree_net)

    #return

    time.sleep(10)
    #print out

    ping_ret_o = h_src.cmd('echo')
    #print ping_ret_o
    #state_cur = clear_sb_rules(filepath, old_path, new_path, flow, state_cur, clk)
    #state_cur.print_state()
    #print 'path change'
    #CLI(fat_tree_net)
    #print "ping result:" + ping_ret
    if 'packets received' not in ping_ret_o:
        #print ping_ret
        return 'False'

    ping_ret = ping_ret_o.strip().split('\n')

    for i in range(len(ping_ret)):
        if ('packets transmitted' in ping_ret[i]) and ('packets received' in ping_ret[i]):
            x = ping_ret[i].strip().split()
            sent_num = x[0]
            recv_num = x[3]
            print sent_num
            print recv_num
            #if int(recv_num) < int(sent_num):
                #print ping_ret_o
                #CLI(fat_tree_net)
        if 'min/avg/max' in ping_ret[i]:
            x = ping_ret[i].strip().split()[3]
            rtt_min = x.split('/')[0]
            rtt_avg = x.split('/')[1]
            rtt_max = x.split('/')[2]
            #print rtt_min
            #print rtt_avg
            #print rtt_max

    retpath = '/home/shengliu/Workspace/mininet/haha/API/result/run_result_%d.txt' %proto
    fp = open(retpath, 'a+')
    fp.write('idx: %d pkt_rate: %d sent_num: %s recv_num: %s min: %s avg: %s max %s\n' %(nt, pkt_rate, sent_num, recv_num, rtt_min, rtt_avg, rtt_max))
    fp.close()

    #CLI(fat_tree_net)

    return 'True'

    #h_src.cmd('python write.py %d %s' %(5, h_dst.IP()))

    #h_dst.cmd('python write.py %d %s' %(5, h_src.IP()))
    #h_src.cmd('python write.py')


def test_run_link(K, fat_tree_net, pkt_rate, proto, nt):
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, filepath, state_cur)
    filepath2 = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'
    path_list = path_read(filepath2, K)
    old_path = path_list['old_path'][nt]['path']
    new_path = path_list['new_path'][nt]['path']

    in_port = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])
    out_port = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    flow = path_list['flow'][nt]
    priority = 8 # > 2
    clk = 7 # > 1
    bdid = 1

    if len(old_path) == 3:
        return 'Error'

    deploy_ret = path_deploy_link_init(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, proto)

    #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']
    #path_deploy([], old_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)
    #subprocess.Popen("%s" %filepath)



    time.sleep(4)

    #state_cur.print_state()
    #print 'route init'
    #CLI(fat_tree_net)

    h_src = fat_tree_net.get(ip2host(flow['ipv4_src']))
    h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))
    out_port_new = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    out_port_old = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    #priority = 8


    #clk = 10

    #in_port = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])

    tmp_max = 100
    prt_max = 200
    failpath = "/home/shengliu/Workspace/mininet/haha/API/cmd/%s.sh" %(str(old_path[2]))
    script_init(failpath)
    if proto == 2:
        script_write(failpath, addFlowRule(old_path[2], {}, 'drop', 0, prt_max, "add"))
    else:
        script_write(failpath, addTMPRule(old_path[2], {}, tmp_max, tmp_max, 0, 0, prt_max, "add"))



    subprocess.call("%s" %failpath)

    #state_cur.print_state()
    #print 'link break'
    #CLI(fat_tree_net)

    if proto == 0 or proto == 1:
        deploy_ret = path_deploy_link(old_path, new_path, flow, state_cur, priority, out_port_new, clk, bdid, 1, proto)
    h_src.cmd('hping3 -1 -c 200 -i u%d %s &' %(pkt_rate, h_dst.IP()))
    if proto == 2 or proto == 3:
        deploy_ret = path_deploy_twice(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 1, proto)


    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']


    #time.sleep(1)

    #state_cur.print_state()

    #CLI(fat_tree_net)


    time.sleep(10)
    #print out

    ping_ret_o = h_src.cmd('echo')
    print ping_ret_o
    #state_cur = clear_sb_rules(filepath, old_path, new_path, flow, state_cur, clk)
    #state_cur.print_state()
    #print 'change route'
    #CLI(fat_tree_net)
    #print "ping result:" + ping_ret
    if 'packets received' not in ping_ret_o:
        #print ping_ret
        return 'False'

    ping_ret = ping_ret_o.strip().split('\n')

    for i in range(len(ping_ret)):
        if ('packets transmitted' in ping_ret[i]) and ('packets received' in ping_ret[i]):
            x = ping_ret[i].strip().split()
            sent_num = x[0]
            recv_num = x[3]
            print sent_num
            print recv_num
            #if int(recv_num) < int(sent_num):
                #print ping_ret_o
                #CLI(fat_tree_net)
        if 'min/avg/max' in ping_ret[i]:
            x = ping_ret[i].strip().split()[3]
            rtt_min = x.split('/')[0]
            rtt_avg = x.split('/')[1]
            rtt_max = x.split('/')[2]
            #print rtt_min
            #print rtt_avg
            #print rtt_max

    retpath = '/home/shengliu/Workspace/mininet/haha/API/result/link_result_%d.txt' %proto
    fp = open(retpath, 'a+')
    fp.write('idx: %d pkt_rate: %d sent_num: %s recv_num: %s min: %s avg: %s max %s\n' %(nt, pkt_rate, sent_num, recv_num, rtt_min, rtt_avg, rtt_max))
    fp.close()

    #CLI(fat_tree_net)

    return 'True'


def test_run_time(K, fat_tree_net, pkt_rate, proto, nt):
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    state_cur = net()
    #state_next = net()
    state_cur = network_init(K, filepath, state_cur)
    filepath2 = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'
    path_list = path_read(filepath2, K)
    old_path = path_list['old_path'][nt]['path']
    new_path = path_list['new_path'][nt]['path']

    in_port = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])
    out_port = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    flow = path_list['flow'][nt]
    priority = 8 # > 2
    clk = 7 # > 1
    bdid = 1

    if len(old_path) == 3:
        return 'Error'

    deploy_ret = path_deploy_link_init(old_path, new_path, flow, state_cur, priority, in_port, out_port, clk, bdid, proto)

    #deploy_ret = path_deploy([], old_path, flow, state_cur, priority, in_port, out_port, clk, bdid, 0)
    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']
    #path_deploy([], old_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, filepath)
    #subprocess.Popen("%s" %filepath)



    time.sleep(2)

    #state_cur.print_state()
    #print 'route init'
    #CLI(fat_tree_net)
    #priority = priority + 2
    #clk = 10
    out_port_new = out_port_construct(new_path, path_list['new_path'][nt]['out_port'])
    #in_port = out_port_construct(new_path, path_list['new_path'][nt]['in_port'])
    out_port_old = out_port_construct(old_path, path_list['old_path'][nt]['out_port'])
    #state_cur.print_state()
    #print 'link break'
    #CLI(fat_tree_net)

    if proto == 0 or proto == 1:
        deploy_ret = path_deploy_time(old_path, new_path, flow, state_cur, priority, out_port_new, clk, bdid, 1, proto)

    if proto == 2:
        deploy_ret = path_deploy_time_cu(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 1, proto)

    if proto == 3:
        deploy_ret = path_deploy_third(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 0, proto)

    state_cur = deploy_ret['state']
    clk = deploy_ret['clk']
    bdid = deploy_ret['bdid']

    time.sleep(4)

    return 'True'




if __name__ == '__main__':
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    K = 4
    state_cur = net()
    state_next = net()
    network_init(K, filepath, state_cur, state_next)

    filepath2 = '/home/shengliu/Workspace/mininet/haha/API/flow_update.tsv'

    path_list = path_read(filepath2, K)

    old_path = path_list['old_path'][0]['path']
    new_path = path_list['new_path'][0]['path']
    print "wocao"
    print old_path
    print new_path
    print path_list['old_path'][0]['out_port']
    print path_list['new_path'][0]['out_port']
    out_port = out_port_construct(old_path, path_list['old_path'][0]['out_port'])
    in_port = out_port_construct(old_path, path_list['old_path'][0]['in_port'])
    flow = path_list['flow'][0]
    priority = 8
    clk = 8
    bdid = 1

    #rule_set = rule_construct([], old_path, flow, state_cur, priority, out_port, clk)
    #state_update(rule_set, state_next, clk)
    #setTMP([], old_path, flow, state_cur, state_next, rule_set, clk)
    #state_update(rule_set, state_cur, clk)
    #state_next.copy_state(state_cur)
    print in_port
    print out_port
    path_deploy([], old_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, 1)
    state_cur.print_state()
    subprocess.call("%s" %filepath)
    clk = 10
    out_port = out_port_construct(new_path, path_list['new_path'][0]['out_port'])
    in_port = out_port_construct(new_path, path_list['new_path'][0]['in_port'])
    print "\n\n\nnew route:"
    print in_port
    print out_port
    path_deploy(old_path, new_path, flow, state_cur, state_next, priority, in_port, out_port, clk, bdid, 1)
    state_cur.print_state()

    #state_next.print_state()
    subprocess.call("%s" %filepath)

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
