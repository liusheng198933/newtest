from test_main import *
from readFile import *
from util import *
from cmd_p4 import *
from timestamp import *
import copy
import subprocess
import time
import random
#from mininet.cli import CLI
#from time_generate import *
#from read_all import *

PRTMAX = 100

def network_init_all(K, p4info_helper, bmv2_file_path, state_cur):
    table_id = 0
    sw_num = pow((K/2),2) + ((K/2)*K) + ((K/2)*K)
    dp_set = [i for i in range(sw_num)]

    for i in dp_set:
        switch_init_config(K, p4info_helper, bmv2_file_path, i)

    time.sleep(2)
    for i in dp_set:
        #print "drop_rule_push:"
        writeRules(K, p4info_helper, i, "10.0.0.0", "255.0.0.0", "10.0.0.0", "255.0.0.0", rtmp_max, 0, 1, action_flag=1, priority=PRTMAX-2)
        writeRules(K, p4info_helper, i, "0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0", rtmp_max, 0, 1, action_flag=2, priority=PRTMAX-1)

    for i in dp_set:
        state_cur.add_table(i, 0)
        #state_next.add_table(i,0)
        #state_cur.get_table(i, 0).add_rule({}, 0, 0, 0, 0)
        #state_next.get_table(i, 0).add_rule({}, 1, 1, 0, 0)
    time.sleep(2)
    return state_cur



def path_deploy_time_all(old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay, proto):

    if proto == 0:
        clk = 0
        rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock
        #print flow
        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk, in_port)
        #rule_set = setPRT(rule_set, old_path, new_path, prt)
        state_next = state_update(rule_set, state_cur)


    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    rule_set = set_clean(rule_set)

    rule_set_final = {}
    rule_set_final['rule_set_first'] = rule_set

    if old_path:
        sb_set = sb_rule_construct(old_path, new_path, flow, clk, in_port)
        #sb_set = {}
        #sb_set[old_path[2]] = {}
        #sb_set[old_path[2]]['add'] = []
        #sb_set[old_path[2]]['del'] = [rule(old_path[2], match, clk, clk, 1, 0, PRTMAX)]
        rule_set_idx = ['rule_set_first', 'rule_set_second']
        rule_set_final['rule_set_second'] = sb_set
    else:
        rule_set_idx = ['rule_set_first']

    return {'state': state_next, 'clk': clk, 'rule_set_idx': rule_set_idx, 'rule_set': rule_set_final}


def path_deploy_time_all(old_path, new_path, flow, state_cur, prt, in_port, out_port, clock, if_delay, proto):

    if proto == 0:
        clk = 0
        rule_set = rule_construct_normal(old_path, new_path, flow, state_cur, prt, out_port)
        state_next = state_update(rule_set, state_cur)

    if proto == 1:
        clk = clock
        #print flow
        rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = setTMP(old_path, new_path, flow, state_cur, state_next, rule_set, clk, in_port)
        #rule_set = setPRT(rule_set, old_path, new_path, prt)
        state_next = state_update(rule_set, state_cur)


    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    rule_set = set_clean(rule_set)

    rule_set_final = {}
    rule_set_final['rule_set_first'] = rule_set

    if old_path:
        sb_set = sb_rule_construct(old_path, new_path, flow, clk, in_port)
        #sb_set = {}
        #sb_set[old_path[2]] = {}
        #sb_set[old_path[2]]['add'] = []
        #sb_set[old_path[2]]['del'] = [rule(old_path[2], match, clk, clk, 1, 0, PRTMAX)]
        rule_set_idx = ['rule_set_first', 'rule_set_second']
        rule_set_final['rule_set_second'] = sb_set
    else:
        rule_set_idx = ['rule_set_first']

    return {'state': state_next, 'clk': clk, 'rule_set_idx': rule_set_idx, 'rule_set': rule_set_final}


def path_deploy_time_buffer(old_path, new_path, flow, state_cur, prt, in_port, out_port_old, out_port_new, clock, if_delay, proto):

    clk = clock
        #print flow

    rule_set = rule_construct(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clk)
    state_update(rule_set, state_cur)

    # print "first"
    # for dp in rule_set.keys():
    #     print dp
    #     print "add"
    #     for r in rule_set[dp]['add']:
    #         r.print_rule()
    #     print "del"
    #     for r in rule_set[dp]['del']:
    #         r.print_rule()

    rule_set_reverse = {}
    for i in rule_set.keys():
        rule_set_reverse[i] = {}
        rule_set_reverse[i]['add'] = rule_set[i]['del']
        rule_set_reverse[i]['del'] = rule_set[i]['add']

    #runtime_rule = time.time() - start_time
    #time2 = time.time()
    rule_set = setTMP(old_path, new_path, flow, state_cur, rule_set, clk, in_port)
    state_update(rule_set_reverse, state_cur)
    state_update(rule_set, state_cur)

    # print "first"
    # for dp in rule_set.keys():
    #     print dp
    #     print "add"
    #     for r in rule_set[dp]['add']:
    #         r.print_rule()
    #     print "del"
    #     for r in rule_set[dp]['del']:
    #         r.print_rule()


    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    rule_set = set_clean(rule_set)

    rule_set_final = {}
    rule_set_final['rule_set_first'] = rule_set

    #if old_path:
        #sb_set = sb_rule_construct(old_path, new_path, flow, clk, in_port)
        #sb_set = {}
        #sb_set[old_path[2]] = {}
        #sb_set[old_path[2]]['add'] = []
        #sb_set[old_path[2]]['del'] = [rule(old_path[2], match, clk, clk, 1, 0, PRTMAX)]
        #rule_set_idx = ['rule_set_first', 'rule_set_second']
        #rule_set_final['rule_set_second'] = sb_set
    #else:
    rule_set_idx = ['rule_set_first']

    # print "rule construct"
    # for i in range(len(rule_set_idx)):
    #     for dp in rule_set_final[rule_set_idx[0]]:
    #         print dp
    #         print "add"
    #         for r in rule_set_final[rule_set_idx[0]][dp]['add']:
    #             r.print_rule()
    #         print "del"
    #         for r in rule_set_final[rule_set_idx[0]][dp]['del']:
    #             r.print_rule()

    return {'rule_set_idx': rule_set_idx, 'rule_set': rule_set_final}




def path_deploy_time_all_coco(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, if_delay, proto):


    if proto == 3:
        clk = clock
        rule_set = rule_construct_coco_final(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clk)
        if old_path:
            state_next = state_update(rule_set['rule_set_first'], state_cur)
            state_next = state_update(rule_set['rule_set_second'], state_next)
            state_next = state_update(rule_set['rule_set_third'], state_next)
            state_next = state_update(rule_set['rule_set_fourth'], state_next)
            rule_set_idx = ['rule_set_first', 'rule_set_second', 'rule_set_third', 'rule_set_fourth']

            for i in range(len(rule_set_idx)):
                rule_set[rule_set_idx[i]] = set_clean(rule_set[rule_set_idx[i]])


            return {'state': state_next, 'clk': clk, 'rule_set_idx': rule_set_idx, 'rule_set': rule_set}

        else:
            state_next = state_update(rule_set, state_cur)

            rule_set = set_clean(rule_set)
            rule_set_idx = ['rule_set_first']
            rule_set_final = {}
            rule_set_final['rule_set_first'] = rule_set

            return {'state': state_next, 'clk': clk, 'rule_set_idx': rule_set_idx, 'rule_set': rule_set_final}



def path_deploy_time_all_cu(old_path, new_path, flow, state_cur, prt, out_port_old, out_port_new, clock, if_delay, proto):
    #bdid = bd

    clk = clock
    if old_path:
        del_rule = rule_construct_cu([], old_path, flow, state_cur, prt, out_port_old, clk-1)
        ret_rule = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port_new, clk)
        add_rule = ret_rule['rule_set']
        first_rule = ret_rule['first_rule']

        del del_rule[old_path[0]]

        for i in del_rule.keys():
            for j in del_rule[i]['add']:
                del_rule[i]['del'].append(j)
            del_rule[i]['add'] = []
        rule_set_final = {}
        rule_set_final['rule_set_first'] = add_rule
        rule_set_final['rule_set_second'] = first_rule
        rule_set_final['rule_set_third'] = del_rule

        state_next = state_update(rule_set_final['rule_set_first'], state_cur)
        state_next = state_update(rule_set_final['rule_set_second'], state_next)
        state_next = state_update(rule_set_final['rule_set_third'], state_next)

        rule_set_idx = ['rule_set_first', 'rule_set_second', 'rule_set_third']

        for i in range(len(rule_set_idx)):
            rule_set_final[rule_set_idx[i]] = set_clean(rule_set_final[rule_set_idx[i]])


        return {'state': state_next, 'clk': clk, 'rule_set_idx': rule_set_idx, 'rule_set': rule_set_final}

    else:
        rule_set = rule_construct_cu(old_path, new_path, flow, state_cur, prt, out_port_new, clk)
        state_next = state_update(rule_set, state_cur)

        rule_set = set_clean(rule_set)
        rule_set_idx = ['rule_set_first']
        rule_set_final = {}
        rule_set_final['rule_set_first'] = rule_set

        return {'state': state_next, 'clk': clk, 'rule_set_idx': rule_set_idx, 'rule_set': rule_set_final}





def script_init_all(K):
    for step in range(4):
        for core in range(pow((K/2),2)):
            dp = int2dpid(1, core)
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %((step+1), str(dp))
            script_init(filepath)

        for pod in range(K):
            for sw in range(K/2):
                dp = int2dpid(2, sw, pod)
                filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %((step+1), str(dp))
                script_init(filepath)

                dp = int2dpid(3, sw, pod)
                filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %((step+1), str(dp))
                script_init(filepath)



def switch_write_all(dp, sw_rule, bdid, step):
    filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
    table_id = 0
    #script_init(filepath)
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    for r in sw_rule['del']:
        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "delete_strict"))
    for r in sw_rule['add']:
        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))


def switch_write_all_idx(rule_set_idx, rule_set):
    dpid_all = {}
    #bdid = bd
    table_id = 0

    for i in range(len(rule_set_idx)):
        rset = rule_set[rule_set_idx[i]]
        dpid_all[i] = []
        for dp in rset.keys():
            if dp not in dpid_all[i]:
                dpid_all[i].append(dp)
            #filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %((i+1), str(dp))
            rlist = []
            for r in rset[dp]['del']:
                rlist.append(r)
            dnum = len(rlist)
            for r in rset[dp]['add']:
                rlist.append(r)
            #bdid = bdid + 1
            #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
            j = 0
            ct = 0
            while j < len(rlist):
                if ct < 100:
                    r = rlist[j]
                    if j < dnum:
                        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "delete_strict"))
                    else:
                        script_write(filepath, bundleAddMsg(dp, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), table_id, r.get_prt(), "add"))
                    ct = ct + 1
                    j = j + 1
                else:
                    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
                    bdid = bdid + 1
                    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
                    ct = 0
            script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    return {'dpid_all': dpid_all, 'bdid': bdid}




def switch_deploy_all(dp_set, step, if_delay, sb_set=[]):
    if not if_delay:
        for dp in dp_set:
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
            subprocess.Popen("%s" %filepath)
            time.sleep(0.3)

    else:
        delay_list = delay_generate_all(dp_set)
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

        subprocess.call('/home/shengliu/Workspace/mininet/haha/API/time_measure')

        for e in range(len(dp_sort)):
            time.sleep(sleep_time[e+1] - sleep_time[e])
            dp = dp_sort[e]
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
            subprocess.Popen("%s" %filepath)
            for k in sb_set.keys():
                if dp in sb_set[k]['requisite']:
                    sb_set[k]['requisite'].remove(dp)
                    if not sb_set[k]['requisite']:
                        r = sb_set[k]['rule']
                        del sb_set[k]
                        rad = random.randint(0, 199)
                        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/sb_cmd_%d.sh" %rad
                        script_init(filepath)
                        script_write(filepath, addTMPRule(r.get_dpid(), r.get_match(), r.get_rtmp(), r.get_ttmp(), -1, 0, PRTMAX, "delete_strict"))
                        subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/delay_deploy.py', '%d' %rad])


def switch_deploy_step(dpid_all, rule_set_idx, if_delay):
    dpid_ext = []
    for i in range(len(rule_set_idx)):
        if not if_delay:
            for j in set(dpid_all[i]) - set(dpid_ext):
                subprocess.call(['python', '/home/shengliu/Workspace/mininet/haha/API/per_switch_deploy.py', '%d' %(i+1), '%d' %(len(rule_set_idx)+1), j])
        else:
            dp_set = list(set(dpid_all[i]) - set(dpid_ext))
            delay_list = delay_generate_all(dp_set)
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
                subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/per_switch_deploy.py', '%d' %(i+1), '%d' %(len(rule_set_idx)+1), dp])

            #time.sleep(0.3)
        dpid_ext = dpid_ext + list(set(dpid_all[i]) - set(dpid_ext))


def switch_deploy_per_step(dpid_all, step, if_delay):
    dp_set = dpid_all[step-1]
    delay_list = delay_generate_all(dp_set)
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
        subprocess.Popen(['python', '/home/shengliu/Workspace/mininet/haha/API/per_switch_deploy.py', '%d' %step, '%d' %(step+1), dp])



def switch_deploy_all_coco(dp_set, step, if_delay):
    if not if_delay:
        for dp in dp_set:
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
            subprocess.Popen("%s" %filepath)
            time.sleep(0.3)
    else:
        delay_list = delay_generate_all(dp_set)
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
            filepath = "/home/shengliu/Workspace/mininet/haha/API/cmd/cmd%d/%s.sh" %(step, str(dp))
            subprocess.Popen("%s" %filepath)



def get_flow_list(filepath, K, t, num=30):
    path_list = path_read_time(filepath, K)
    j = 0
    t = 0
    #ct = 0
    flow_list = {}
    #for j in range(len(path_list['flow'])):
    #while j < len(path_list['flow']) and path_list['time'][j] >= 600*t and path_list['time'][j] < 600*(t+1):
    while j < len(path_list['flow']) and len(flow_list.keys()) < num:
        i = path_list['flow'][j]
        f = match_parse(i)
        old_path = path_list['old_path'][j]['path']
        new_path = path_list['new_path'][j]['path']
        if len(old_path) == 5:
            if f not in flow_list.keys():
                flow_list[f] = {}
                flow_list[f]['flow'] = i
                flow_list[f]['old_path'] = old_path
                flow_list[f]['out_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['out_port'])
                flow_list[f]['in_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['in_port'])
                flow_list[f]['new_path'] = new_path
                flow_list[f]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                flow_list[f]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                f_reverse = match_parse(reverse_flow(i))
                old_path_reverse = copy.deepcopy(old_path)
                old_path_reverse.reverse()
                new_path_reverse = copy.deepcopy(new_path)
                new_path_reverse.reverse()
                flow_list[f_reverse] = {}
                flow_list[f_reverse]['flow'] = reverse_flow(i)
                flow_list[f_reverse]['old_path'] = old_path_reverse
                flow_list[f_reverse]['out_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['in_port'])
                flow_list[f_reverse]['in_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['out_port'])
                flow_list[f_reverse]['new_path'] = new_path_reverse
                flow_list[f_reverse]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                flow_list[f_reverse]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                #ct = ct + 1
            else:
                flow_list[f]['new_path'] = new_path
                flow_list[f]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                flow_list[f]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                f_reverse = match_parse(reverse_flow(i))
                new_path_reverse = copy.deepcopy(new_path)
                new_path_reverse.reverse()
                flow_list[f_reverse]['new_path'] = new_path_reverse
                flow_list[f_reverse]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                flow_list[f_reverse]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])

        j = j + 1
    print "flow list:"
    print len(flow_list)
    print "all items searched:"
    print j
    ct = 0
    for f in flow_list.keys():
        if flow_list[f]['old_path'] != flow_list[f]['new_path']:
            ct = ct + 1

    print "real flow num:"
    print ct

    return flow_list


def get_flow_list_new(filepath, K, t, num=30):
    path_list = path_read_time(filepath, K)
    j = 0
    t = 0
    #ct = 0
    flow_list = {}
    knum = num
    ct = 0
    #for j in range(len(path_list['flow'])):
    #while j < len(path_list['flow']) and path_list['time'][j] >= 600*t and path_list['time'][j] < 600*(t+1):
    while ct != num:
        while j < len(path_list['flow']) and len(flow_list.keys()) < knum:
            i = path_list['flow'][j]
            f = match_parse(i)
            old_path = path_list['old_path'][j]['path']
            new_path = path_list['new_path'][j]['path']
            if len(old_path) == 5:
                if f not in flow_list.keys():
                    flow_list[f] = {}
                    flow_list[f]['flow'] = i
                    flow_list[f]['old_path'] = old_path
                    flow_list[f]['out_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['out_port'])
                    flow_list[f]['in_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['in_port'])
                    flow_list[f]['new_path'] = new_path
                    flow_list[f]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                    flow_list[f]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                    f_reverse = match_parse(reverse_flow(i))
                    old_path_reverse = copy.deepcopy(old_path)
                    old_path_reverse.reverse()
                    new_path_reverse = copy.deepcopy(new_path)
                    new_path_reverse.reverse()
                    flow_list[f_reverse] = {}
                    flow_list[f_reverse]['flow'] = reverse_flow(i)
                    flow_list[f_reverse]['old_path'] = old_path_reverse
                    flow_list[f_reverse]['out_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['in_port'])
                    flow_list[f_reverse]['in_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['out_port'])
                    flow_list[f_reverse]['new_path'] = new_path_reverse
                    flow_list[f_reverse]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                    flow_list[f_reverse]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                    #ct = ct + 1
                else:
                    flow_list[f]['new_path'] = new_path
                    flow_list[f]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                    flow_list[f]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                    f_reverse = match_parse(reverse_flow(i))
                    new_path_reverse = copy.deepcopy(new_path)
                    new_path_reverse.reverse()
                    flow_list[f_reverse]['new_path'] = new_path_reverse
                    flow_list[f_reverse]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                    flow_list[f_reverse]['in_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])

            j = j + 1
        ct = 0
        for f in flow_list.keys():
            if flow_list[f]['old_path'] != flow_list[f]['new_path']:
                ct = ct + 1

        #print j
        #print ct
        knum = knum + 1
    print "flow list:"
    print len(flow_list.keys())
    print "all items searched:"
    print j
    ct = 0
    for f in flow_list.keys():
        if flow_list[f]['old_path'] != flow_list[f]['new_path']:
            ct = ct + 1
    for f in flow_list.keys():
        if flow_list[f]['old_path'] == flow_list[f]['new_path']:
            del flow_list[f]
    print "real flow num:"
    print ct

    return flow_list


def get_flow_list_all(filepath, K, flow_list_cmp):
    path_list = path_read_time(filepath, K)
    j = 0
    #ct = 0
    flow_list = {}
    #for j in range(len(path_list['flow'])):
    while j < len(path_list['flow']):
        i = path_list['flow'][j]
        f = match_parse(i)
        old_path = path_list['old_path'][j]['path']
        new_path = path_list['new_path'][j]['path']
        if len(old_path) == 5 and f not in flow_list_cmp.keys():
            if f not in flow_list.keys():
                flow_list[f] = {}
                flow_list[f]['flow'] = i
                flow_list[f]['old_path'] = old_path
                flow_list[f]['out_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['out_port'])
                flow_list[f]['new_path'] = new_path
                flow_list[f]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['out_port'])
                f_reverse = match_parse(reverse_flow(i))
                old_path_reverse = copy.deepcopy(old_path)
                old_path_reverse.reverse()
                new_path_reverse = copy.deepcopy(new_path)
                new_path_reverse.reverse()
                flow_list[f_reverse] = {}
                flow_list[f_reverse]['flow'] = reverse_flow(i)
                flow_list[f_reverse]['old_path'] = old_path_reverse
                flow_list[f_reverse]['out_port_old'] = out_port_construct(old_path, path_list['old_path'][j]['in_port'])
                flow_list[f_reverse]['new_path'] = new_path_reverse
                flow_list[f_reverse]['out_port_new'] = out_port_construct(new_path, path_list['new_path'][j]['in_port'])
                #ct = ct + 1
        j = j + 1

    return flow_list




def snapshot_deploy_buffer(fat_tree_net, flow_list, p4info_file_path, bmv2_file_path, K):
    proto = 1
    result_dir = '/home/shengliu/Workspace/log'
    empty_directory(result_dir)


    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    #flow_list = get_flow_list(filepath, K, t, 104)

    state_cur = net()
    network_init_all(K, p4info_helper, bmv2_file_path, state_cur)

    #proto = 3
    clk = 8 # > 1
    priority = 8
    dpid_all = {}
    rule_set_all = {}
    #CLI(fat_tree_net)

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        in_port_old = flow_list[i]['in_port_old']
        in_port_new = flow_list[i]['in_port_new']

        if proto == 0 or proto == 1:

            deploy_ret = path_deploy_time_buffer([], old_path, flow, state_cur, priority, {}, {}, out_port_old, clk, 1, proto)

        #state_cur = deploy_ret['state']
        #clk = deploy_ret['clk']
        rule_set_idx = deploy_ret['rule_set_idx']
        rule_set = deploy_ret['rule_set']
        rule_set_all = rule_set_merge(rule_set_all, rule_set)


    # for i in range(len(rule_set_idx)):
    #     for dp in rule_set_all[rule_set_idx[0]]:
    #         print dp
    #         print "add"
    #         for r in rule_set_all[rule_set_idx[0]][dp]['add']:
    #             r.print_rule()
    #         print "del"
    #         for r in rule_set_all[rule_set_idx[0]][dp]['del']:
    #             r.print_rule()


    switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, 1)

    #CLI(fat_tree_net)
    time.sleep(10)

    rule_set_all = {}
    clk = clk + 1
    flow_all = []

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        in_port_old = flow_list[i]['in_port_old']
        in_port_new = flow_list[i]['in_port_new']

        h_src = fat_tree_net.get(ip2host(flow['ipv4_src']))
        h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))






        if old_path != new_path:
            if proto == 0 or proto == 1:
                deploy_ret = path_deploy_time_buffer(old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, out_port_new, clk, 1, proto)
                #state_cur = deploy_ret['state']
                #clk = deploy_ret['clk']
                #bdid = deploy_ret['bdid']
                rule_set_idx = deploy_ret['rule_set_idx']
                rule_set = deploy_ret['rule_set']
                rule_set_all = rule_set_merge(rule_set_all, rule_set)
                flow_all.append(flow)

        #print dpid
    fp = open('/home/shengliu/Workspace/log/start.txt', 'a+')
    fp.write('%s\n' %str(datetime.now()))
    fp.close()

    sendpath = cwdpath + 'send_pkt.py'
    recpath = cwdpath + 'rec_pkt.py'

    #print str(ip2host(h_dst.IP()))
    #print str(h_src.IP())
    #for flow in flow_all:
        #h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))
        #h_dst.cmd('python', recpath, str(ip2host(flow['ipv4_dst'])), '&')
        #break

    time.sleep(1)
    pkt_rate = 50
    delay = 1.0 / pkt_rate - 0.001
    sent_num = 100

    for flow in flow_all:
        #print flow
        h_src = fat_tree_net.get(ip2host(flow['ipv4_src']))
        h_src.cmd('python', sendpath, sent_num, str(ip2host(flow['ipv4_src'])), str(ip2host(flow['ipv4_dst'])), str(delay), '&')

        #print "sent"
        #break
    #for h_dst in hdst_all:
        #h_dst.cmd('python', recpath, str(ip2host(flow['ipv4_dst'])), '&')
        #h_dst.cmd('python', recpath, str(ip2host(h_dst.IP())), '&')


    #for h_src in hdst_all:
    #    h_src.cmd('python', sendpath, sent_num, str(ip2host(h_src.IP())), str(ip2host(h_dst.IP())), str(delay), '&')

    switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, 1)

    #CLI(fat_tree_net)

    time.sleep(20)
    #for flow in flow_all:
        #h_dst = fat_tree_net.get(ip2host(flow['ipv4_dst']))
        #ping_ret_o = h_dst.cmd('echo')
    #print h_src.cmd('echo')
        #print ping_ret_o
        #recv_num = ping_ret_o.strip().split('\n')[1]
    #state_cur = clear_sb_rules(filepath, old_path, new_path, flow, state_cur, clk)
        #print recv_num
        #break

    time.sleep(5)

    return 'True'


def snapshot_deploy(flow_list, p4info_file_path, bmv2_file_path, filepath, K, t):

    proto = 1
    result_dir = '/home/shengliu/Workspace/log'
    empty_directory(result_dir)

    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    #flow_list = get_flow_list(filepath, K, t, 104)

    state_cur = net()
    state_cur = network_init_all(K, p4info_helper, bmv2_file_path, state_cur)

    #proto = 3
    clk = 8 # > 1
    priority = 8
    dpid_all = {}
    rule_set_all = {}
    #CLI(fat_tree_net)

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        in_port_old = flow_list[i]['in_port_old']
        in_port_new = flow_list[i]['in_port_new']


        if proto == 0 or proto == 1:
            deploy_ret = path_deploy_time_all([], old_path, flow, state_cur, priority, {}, out_port_old, clk, 1, proto)

        state_cur = deploy_ret['state']
        clk = deploy_ret['clk']
        rule_set_idx = deploy_ret['rule_set_idx']
        rule_set = deploy_ret['rule_set']
        rule_set_all = rule_set_merge(rule_set_all, rule_set)

    switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, 1)

    time.sleep(10)

    #time.sleep(5)

    #dpid_all = {}
    rule_set_all = {}
    clk = clk + 1

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        in_port_old = flow_list[i]['in_port_old']
        in_port_new = flow_list[i]['in_port_new']

        if old_path != new_path:
            if proto == 0 or proto == 1:
                deploy_ret = path_deploy_time_all(old_path, new_path, flow, state_cur, priority, in_port_old, out_port_new, clk, 1, proto)
                state_cur = deploy_ret['state']
                clk = deploy_ret['clk']
                #bdid = deploy_ret['bdid']
                rule_set_idx = deploy_ret['rule_set_idx']
                rule_set = deploy_ret['rule_set']
                rule_set_all = rule_set_merge(rule_set_all, rule_set)

        #print dpid
    fp = open('/home/shengliu/Workspace/log/start.txt', 'a+')
    fp.write('%s\n' %str(datetime.now()))
    fp.close()
    switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, 1)


    time.sleep(5)

    return 'True'


def switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, if_delay):
    for i in range(len(rule_set_idx)):
        if not if_delay:
            for j in rule_set_all[rule_set_idx[i]].keys():
                switch_deploy(K, p4info_helper, j, rule_set_all[rule_set_idx[i]][j], 0)
        else:
            thread_list = []
            delay_list = delay_generate(rule_set_all[rule_set_idx[i]])
            #print max(delay_list.values())
            for dp in rule_set_all[rule_set_idx[i]].keys():
                #thread_list.append(switch_deploy(K, p4info_helper, dp, rule_set_all[rule_set_idx[i]][dp], 5))
                thread_list.append(switch_deploy(K, p4info_helper, dp, rule_set_all[rule_set_idx[i]][dp], delay_list[dp]))
            for t in thread_list:
                t.join()

            #for t in thread_list:
            #    print t.is_alive()
            #print "step finished"


def snapshot_deploy_coco(flow_list, p4info_file_path, bmv2_file_path, filepath, K, t, proto, fat_tree_net=None):

    result_dir = '/home/shengliu/Workspace/log'
    empty_directory(result_dir)

    #time_file_generate()
    p4info_helper = p4runtime_lib.helper.P4InfoHelper(p4info_file_path)
    #flow_list = get_flow_list(filepath, K, t, 50)
    #print flow_list

    #script_init_all(K)
    state_cur = net()
    #filepath2 = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    state_cur = network_init_all(K, p4info_helper, bmv2_file_path, state_cur)

    #proto = 3
    clk = 8 # > 1
    priority = 8
    dpid_all = {}
    rule_set_all = {}
    #CLI(fat_tree_net)

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']
        #print old_path
        #print new_path


        if proto == 2:
            deploy_ret = path_deploy_time_all_cu([], old_path, flow, state_cur, priority, {}, out_port_old, clk, 0, proto)


        if proto == 3:
            deploy_ret = path_deploy_time_all_coco([], old_path, flow, state_cur, priority, {}, out_port_old, clk, 0, proto)

        state_cur = deploy_ret['state']
        clk = deploy_ret['clk']
        #bdid = deploy_ret['bdid']
        rule_set_idx = deploy_ret['rule_set_idx']
        rule_set = deploy_ret['rule_set']
        rule_set_all = rule_set_merge(rule_set_all, rule_set)



    switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, 1)
    #switch_deploy_step(rule_set_all, rule_set_idx, 0)
    #for j in range(len(rule_set_idx)):
    #    switch_deploy_all_coco(dpid_all[j], j+1, 0)
        #print dpid_all[j]
    #CLI(fat_tree_net)
    #script_init_all(K)
    print "deploy"
    time.sleep(10)

    #time.sleep(5)

    #dpid_all = {}
    rule_set_all = {}
    rule_set_idx = []
    if proto == 2:
        clk = clk + 1

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']

        if old_path != new_path:
            if proto == 2:
                deploy_ret = path_deploy_time_all_cu(old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, 1, proto)


            if proto == 3:
                deploy_ret = path_deploy_time_all_coco(old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, 1, proto)


            state_cur = deploy_ret['state']
            clk = deploy_ret['clk']
            #bdid = deploy_ret['bdid']
            rule_set_idx = deploy_ret['rule_set_idx']
            rule_set = deploy_ret['rule_set']
            rule_set_all = rule_set_merge(rule_set_all, rule_set)
    # for i in range(len(rule_set_idx)):
    #     print i
    #     for j in rule_set_all[rule_set_idx[i]].keys():
    #         print 'del'
    #         for r in rule_set_all[rule_set_idx[i]][j]['del']:
    #             r.print_rule()
    #         print 'add'
    #         for r in rule_set_all[rule_set_idx[i]][j]['add']:
    #             r.print_rule()

    fp = open('/home/shengliu/Workspace/log/start.txt', 'a+')
    fp.write('%s\n' %str(datetime.now()))
    fp.close()
    for wori in range(len(rule_set_idx)):
        print len(rule_set_all[rule_set_idx[wori]].keys())
    switch_deploy_step_all(K, p4info_helper, rule_set_all, rule_set_idx, 1)


    return 'True'




if __name__ == '__main__':
    K = 8
    filepath = '/home/shengliu/Workspace/mininet/haha/API/flow_update1.tsv'
    t = 0
    snapshot_deploy_coco(filepath, K, 0, 3)
    #snapshot_deploy(filepath, K, t)

    """
    flow_list = get_flow_list(filepath, K, 0)
    #print flow_list
    script_init_all(K)

    state_cur = net()
    filepath2 = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    #state_next = net()
    state_cur = network_init_all(K, filepath2, state_cur)

    proto = 1
    clk = 5 # > 1
    bdid = 1
    priority = 8
    dpid1 = []
    sb_set = {}


    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']


        if proto == 0 or proto == 1:
            deploy_ret = path_deploy_time_all([], old_path, flow, state_cur, priority, out_port_old, clk, bdid, 1, proto)

        #if proto == 2:
            #deploy_ret = path_deploy_time_cu(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 1, proto)

        #if proto == 3:
        #    deploy_ret = path_deploy_third(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 0, proto)

        state_cur = deploy_ret['state']
        clk = deploy_ret['clk']
        bdid = deploy_ret['bdid']
        dpid = deploy_ret['dpid']

        for b in dpid:
            if b not in dpid1:
                dpid1.append(b)


    switch_deploy_all(dpid, 1, 0)
    script_init_all(K)
    time.sleep(4)

    for i in flow_list.keys():
        flow = flow_list[i]['flow']
        old_path = flow_list[i]['old_path']
        new_path = flow_list[i]['new_path']
        out_port_old = flow_list[i]['out_port_old']
        out_port_new = flow_list[i]['out_port_new']


        if proto == 0 or proto == 1:
            deploy_ret = path_deploy_time_all(old_path, new_path, flow, state_cur, priority, out_port_new, clk, bdid, 1, proto)

        #if proto == 2:
            #deploy_ret = path_deploy_time_cu(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 1, proto)

        #if proto == 3:
        #    deploy_ret = path_deploy_third(fat_tree_net, old_path, new_path, flow, state_cur, priority, out_port_old, out_port_new, clk, bdid, 0, proto)

        state_cur = deploy_ret['state']
        clk = deploy_ret['clk']
        bdid = deploy_ret['bdid']
        dpid = deploy_ret['dpid']

        for b in dpid:
            if b not in dpid1:
                dpid1.append(b)

        match = {}
        match['ipv4_dst'] = flow['ipv4_dst']
        match['ipv4_src'] = flow['ipv4_src']
        match["eth_type"] = 2048
        sb_set[i] = {}
        sb_set[i]['requisite'] = [old_path[1], old_path[2]]
        sb_set[i]['rule'] = rule(old_path[2], match, clk, clk, -1, 0, PRTMAX)

    switch_deploy_all(dpid, 1, 1, sb_set)


    state_cur.print_state()
    """
