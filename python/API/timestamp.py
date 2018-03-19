from switch_state import rule, net, table
from util import *
import copy

PRTMAX = 100

def setTMP(old_path, new_path, flow, new_state, rule_set, clk):
    #rule_set = copy.deepcopy(rule_set_old)
    if old_path:
        i = 0
        while old_path[i] in new_path:
            i = i + 1
        inter_node = old_path[i-1]
    else:
        inter_node = new_path[0]
    # search for the first intersection node

    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048
    for i in (set(old_path) - set(new_path)):
        if i not in rule_set.keys():
            rule_set[i] = {}
            rule_set[i]['add'] = []
            rule_set[i]['del'] = []
        rule_set[i]['add'].append(rule(i, match, clk, clk, -1, table_id, PRTMAX))

    for i in range(len(new_path)-1):
        if new_path[i] in rule_set.keys() and rule_set[new_path[i]]['add']:
            for r in rule_set[new_path[i]]['add']:
                if r.get_ttmp() == 1:
                    tb_cur = new_state.get_table(new_path[i], table_id)
                    tb_next = new_state.get_table(new_path[i+1], table_id)
                    r_exact = r.get_exact_match(tb_cur)
                    rule_inf = []
                    ttmp_list = []
                    for t in tb_next.get_all_rules():
                        tmp = []
                        for j in r_exact:
                            if intersection(t.get_match_bin(), j):
                                rule_inf.append(t)
                                ttmp_list.append(t.get_rtmp())
                            tmp = tmp + difference(j, t.get_match_bin())
                        r_exact = tmp
                    #print "\nttmp set:"
                    #print ttmp_list
                    #for rk in rule_inf:
                    #    rk.print_rule()
                    if max(ttmp_list) == clk:
                        r.set_ttmp(clk)
                        for j in range(len(ttmp_list)):
                            if ttmp_list[j] < clk:
                                rule_set[new_path[i+1]]['del'].append(rule(new_path[i+1], rule_inf[j].get_match(), rule_inf[j].get_rtmp(), rule_inf[j].get_ttmp(), rule_inf[j].get_action(), table_id, rule_inf[j].get_prt()))
                                rule_set[new_path[i+1]]['add'].append(rule(new_path[i+1], rule_inf[j].get_match(), clk, rule_inf[j].get_ttmp(), rule_inf[j].get_action(), table_id, rule_inf[j].get_prt()))
                    else:
                        r.set_ttmp(min(ttmp_list))

                    """
                    if i+2 < len(new_path)-2:
                        next = old_state.get_table(new_path[k], table_id).get_rule(flow).get_action()
                        while next in new_path[k+1:len(new_path)-1]:
                            next = old_state.get_table(next, table_id).get_rule(flow).get_action()
                        if next != new_path[len(new_path)]:
                            for j in range(inter_node, i):
                                x = new_state.get_table(new_path[j], table_id).get_rule(flow)
                                if x.get_rtmp() < clk:
                                    rule_set[new_path[j]]['del'].append(rule(new_path[j], x.get_match(), x.get_rtmp(), x.get_ttmp(), x.get_action(), table_id, x.get_prt()))
                                    rule_set[new_path[j]]['add'].append(rule(new_path[j], x.get_match(), clk, clk, x.get_action(), table_id, x.get_prt()))
                        else:
                            r.set_ttmp(min(ttmp_list))
                    """
    return rule_set


def sb_rule_construct(old_path, new_path, flow, clk):
    sb_set = []
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048
    table_id = 0
    for i in (set(old_path) - set(new_path)):
        sb_set.append(rule(i, match, clk, clk, -1, table_id, PRTMAX))
    return sb_set


def rule_construct_normal(old_path, new_path, flow, state, prt, out_port):
    rule_set = {}
    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    if old_path:
        intersect_set = []
        for i in range(len(old_path)-1):
            if (old_path[i] in new_path) and (old_path[i+1] not in new_path):
                intersect_set.append(old_path[i])

        for i in intersect_set:
            rule_set[i] = {}
            rule_set[i]['add'] = []
            rule_set[i]['del'] = []
            rext = state.get_table(i, table_id).get_rule(flow)
            if rext.get_prt() == prt:
                df = difference(rext.get_match_bin(), match_parse(flow))
                if df:
                    for j in df:
                        rule_set[i]['add'].append(rule(i, match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                rule_set[i]['del'].append(rule(i, rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
            rule_set[i]['add'].append(rule(i, match, -1, -1, out_port[i], table_id, prt))


    for i in (set(old_path) - set(new_path)):
        if i not in rule_set.keys():
            rule_set[i] = {}
            rule_set[i]['add'] = []
            rule_set[i]['del'] = []
        rext = state.get_table(i, table_id).get_rule(flow)
        if rext.get_prt() == prt:
            df = difference(rext.get_match_bin(), match_parse(flow))
            if df:
                for j in df:
                    rule_set[i]['add'].append(rule(i, match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
            rule_set[i]['del'].append(rule(i, rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))


    for i in (set(new_path) - set(old_path)):
        rule_set[i] = {}
        rule_set[i]['add'] = []
        rule_set[i]['del'] = []
        rule_set[i]['add'].append(rule(i, match, -1, -1, out_port[i], table_id, prt))


    return rule_set



def rule_construct(old_path, new_path, flow, state, prt, out_port, clk):
    rule_set = {}
    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    if old_path:
        intersect_set = []
        for i in range(len(old_path)-1):
            if (old_path[i] in new_path) and (old_path[i+1] not in new_path):
                intersect_set.append(old_path[i])

        for i in intersect_set:
            rule_set[i] = {}
            rule_set[i]['add'] = []
            rule_set[i]['del'] = []
            rext = state.get_table(i, table_id).get_rule(flow)
            if rext.get_prt() == prt:
                df = difference(rext.get_match_bin(), match_parse(flow))
                if df:
                    for j in df:
                        rule_set[i]['add'].append(rule(i, match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                rule_set[i]['del'].append(rule(i, rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
            if i == old_path[0]:
                rule_set[i]['add'].append(rule(i, match, -1, 1, out_port[i], table_id, prt))
            else:
                rule_set[i]['add'].append(rule(i, match, clk, 1, out_port[i], table_id, prt))


    for i in (set(old_path) - set(new_path)):
        if i not in rule_set.keys():
            rule_set[i] = {}
            rule_set[i]['add'] = []
            rule_set[i]['del'] = []
        rext = state.get_table(i, table_id).get_rule(flow)
        if rext.get_prt() == prt:
            df = difference(rext.get_match_bin(), match_parse(flow))
            if df:
                for j in df:
                    rule_set[i]['add'].append(rule(i, match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
            rule_set[i]['del'].append(rule(i, rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))


    for i in (set(new_path) - set(old_path)):
        rule_set[i] = {}
        rule_set[i]['add'] = []
        rule_set[i]['del'] = []
        if i == new_path[0]:
            rule_set[i]['add'].append(rule(i, match, -1, 1, out_port[i], table_id, prt))
        else:
            if i == new_path[len(new_path)-1]:
                rule_set[i]['add'].append(rule(i, match, clk, -1, out_port[i], table_id, prt))
            else:
                rule_set[i]['add'].append(rule(i, match, clk, 1, out_port[i], table_id, prt))


    return rule_set


def rule_construct_cu(old_path, new_path, flow, state, prt, out_port, clk):
    rule_set = {}
    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    if not old_path:
        for i in range(len(new_path)):
            rule_set[new_path[i]] = {}
            rule_set[new_path[i]]['add'] = []
            rule_set[new_path[i]]['del'] = []
            if i == len(new_path)-1:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, prt))
            else:
                if i == 0:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, prt))
                else:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, prt))
        return rule_set
    else:

        for i in range(1, len(new_path)):
            rule_set[new_path[i]] = {}
            rule_set[new_path[i]]['add'] = []
            rule_set[new_path[i]]['del'] = []
            if i == len(new_path)-1:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, prt))
            else:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, prt))

        first_rule = {}
        first_rule[new_path[0]] = {}
        first_rule[new_path[0]]['add'] = [rule(new_path[0], match, -1, clk, out_port[new_path[0]], table_id, prt)]
        first_rule[new_path[0]]['del'] = [rule(new_path[0], match, -1, clk-1, out_port[new_path[0]], table_id, prt)]
        return {'rule_set': rule_set, 'first_rule': first_rule}



def rule_construct_cu_twice(old_path, new_path, flow, state, prt, out_port, clk):
    rule_set = {}
    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    for i in range(1, len(new_path)):
        rule_set[new_path[i]] = {}
        rule_set[new_path[i]]['add'] = []
        rule_set[new_path[i]]['del'] = []
        if i == len(new_path)-1:
            rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, prt))
        else:
            if i == 0:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, 0))
            else:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, prt))

    first_rule = {}
    first_rule[new_path[0]] = {}
    first_rule[new_path[0]]['add'] = [rule(new_path[0], match, -1, clk, out_port[new_path[0]], table_id, prt)]
    first_rule[new_path[0]]['del'] = [rule(new_path[0], match, -1, clk-1, out_port[new_path[0]], table_id, prt)]
    #first_rule[new_path[0]]['del'].append(rule(new_path[0], match, -1, clk, out_port[new_path[0]], table_id, 0))
    return {'rule_set': rule_set, 'first_rule': first_rule}



def rule_construct_coco(old_path, new_path, flow, state, prt, out_port, clk):
    rule_set = {}
    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    if old_path:
        intersect_set = []
        for i in range(len(new_path)-1):
            if (new_path[i] in old_path) and (new_path[i+1] not in old_path):
                intersect_set.append(i)

        for i in range(len(new_path)):
            if i >= intersect_set[0]:
                rule_set[new_path[i]] = {}
                rule_set[new_path[i]]['add'] = []
                rule_set[new_path[i]]['del'] = []
                rext = state.get_table(new_path[i], table_id).get_rule(flow)
                if rext and rext.get_prt() == prt:
                    df = difference(rext.get_match_bin(), match_parse(flow))
                    if df:
                        for j in df:
                            rule_set[new_path[i]]['add'].append(rule(new_path[i], match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                    rule_set[new_path[i]]['del'].append(rule(new_path[i], rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                if i == 0:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, prt))
                else:
                    if i == len(new_path)-1:
                        rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, prt))
                    else:
                        rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, prt))

        for i in (set(old_path) - set(new_path)):
            if i not in rule_set.keys():
                rule_set[i] = {}
                rule_set[i]['add'] = []
                rule_set[i]['del'] = []
            rext = state.get_table(i, table_id).get_rule(flow)
            if rext.get_prt() == prt:
                df = difference(rext.get_match_bin(), match_parse(flow))
                if df:
                    for j in df:
                        rule_set[i]['add'].append(rule(i, match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                rule_set[i]['del'].append(rule(i, rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
            #rule_set[i]['del'].append(rule(i, {}, 1, 1, 0, table_id, 0))
            rule_set[i]['add'].append(rule(i, match, clk, clk, 0, table_id, prt))

    else:
        for i in range(len(new_path)):
            rule_set[new_path[i]] = {}
            rule_set[new_path[i]]['add'] = []
            rule_set[new_path[i]]['del'] = []
            if i == 0:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, prt))
            else:
                if i == len(new_path)-1:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, prt))
                else:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, prt))

    return rule_set


def rule_construct_coco_final(old_path, new_path, flow, state, prt, out_port_old, out_port_new, clk):

    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    if not old_path:
        rule_set = {}
        for i in range(len(new_path)):
            rule_set[new_path[i]] = {}
            rule_set[new_path[i]]['add'] = []
            rule_set[new_path[i]]['del'] = []
            if i == len(new_path)-1:
                rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port_new[new_path[i]], table_id, prt))
            else:
                if i == 0:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port_new[new_path[i]], table_id, prt))
                else:
                    rule_set[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port_new[new_path[i]], table_id, prt))
        return rule_set

    else:
        intersect_set = []
        for i in range(len(new_path)-1):
            if (new_path[i] in old_path) and (new_path[i+1] not in old_path):
                intersect_set.append(new_path[i])

        rule_set_first = {}
        rule_set_second = {}
        rule_set_third = {}
        rule_set_fourth = {}

        for j in range(new_path.index(intersect_set[0]), len(new_path)):
            i = new_path[j]
            rule_set_first[i] = {}
            rule_set_first[i]['add'] = []
            rule_set_first[i]['del'] = []
            rule_set_second[i] = {}
            rule_set_second[i]['add'] = []
            rule_set_second[i]['del'] = []
            rule_set_third[i] = {}
            rule_set_third[i]['add'] = []
            rule_set_third[i]['del'] = []
            rule_set_fourth[i] = {}
            rule_set_fourth[i]['add'] = []
            rule_set_fourth[i]['del'] = []
            if i == new_path[0]:
                rule_set_first[i]['add'].append(rule(i, match, -1, clk+1, out_port_new[i], table_id, prt-1))
                rule_set_second[i]['del'].append(rule(i, match, -1, clk+1, out_port_new[i], table_id, prt-1))
                rule_set_second[i]['add'].append(rule(i, match, -1, clk+1, out_port_new[i], table_id, prt+1))
                rule_set_third[i]['del'].append(rule(i, match, -1, clk+1, out_port_new[i], table_id, prt+1))
                rule_set_third[i]['add'].append(rule(i, match, -1, clk, out_port_new[i], table_id, prt+1))
                rule_set_fourth[i]['del'].append(rule(i, match, -1, clk, out_port_new[i], table_id, prt+1))
                rule_set_fourth[i]['add'].append(rule(i, match, -1, clk, out_port_new[i], table_id, prt))
            else:
                if i == new_path[len(new_path)-1]:
                    rule_set_first[i]['add'].append(rule(i, match, clk+1, -1, out_port_new[i], table_id, prt-1))
                    rule_set_second[i]['del'].append(rule(i, match, clk+1, -1, out_port_new[i], table_id, prt-1))
                    rule_set_second[i]['add'].append(rule(i, match, clk+1, -1, out_port_new[i], table_id, prt+1))
                    rule_set_fourth[i]['del'].append(rule(i, match, clk+1, -1, out_port_new[i], table_id, prt+1))
                    rule_set_fourth[i]['add'].append(rule(i, match, clk, -1, out_port_new[i], table_id, prt))
                else:
                    rule_set_first[i]['add'].append(rule(i, match, clk+1, clk+1, out_port_new[i], table_id, prt-1))
                    rule_set_second[i]['del'].append(rule(i, match, clk+1, clk+1, out_port_new[i], table_id, prt-1))
                    rule_set_second[i]['add'].append(rule(i, match, clk+1, clk+1, out_port_new[i], table_id, prt+1))
                    rule_set_third[i]['del'].append(rule(i, match, clk+1, clk+1, out_port_new[i], table_id, prt+1))
                    rule_set_third[i]['add'].append(rule(i, match, clk+1, clk, out_port_new[i], table_id, prt+1))
                    rule_set_fourth[i]['del'].append(rule(i, match, clk+1, clk, out_port_new[i], table_id, prt+1))
                    rule_set_fourth[i]['add'].append(rule(i, match, clk, clk, out_port_new[i], table_id, prt))

        for j in range(old_path.index(intersect_set[0]), len(old_path)):
            i = old_path[j]
            if i not in rule_set_third.keys():
                rule_set_third[i] = {}
                rule_set_third[i]['add'] = []
                rule_set_third[i]['del'] = []
            if i == old_path[0]:
                rule_set_third[i]['del'].append(rule(i, match, -1, clk, out_port_old[i], table_id, prt))
            else:
                if i == old_path[len(old_path)-1]:
                    rule_set_third[i]['del'].append(rule(i, match, clk, -1, out_port_old[i], table_id, prt))
                else:
                    rule_set_third[i]['del'].append(rule(i, match, clk, clk, out_port_old[i], table_id, prt))

        return {'rule_set_first': rule_set_first, 'rule_set_second': rule_set_second, 'rule_set_third': rule_set_third, 'rule_set_fourth': rule_set_fourth}




def rule_construct_coco_twice(old_path, new_path, flow, state, prt, out_port, clk):
    rule_set_first = {}
    rule_set_second = {}
    table_id = 0
    match = {}
    match['ipv4_dst'] = flow['ipv4_dst']
    match['ipv4_src'] = flow['ipv4_src']
    match["eth_type"] = 2048

    if old_path:
        intersect_set = []
        for i in range(len(new_path)-1):
            if (new_path[i] in old_path) and (new_path[i+1] not in old_path):
                intersect_set.append(i)

        for i in range(len(new_path)):
            if i >= intersect_set[0]:
                rule_set_first[new_path[i]] = {}
                rule_set_first[new_path[i]]['add'] = []
                rule_set_first[new_path[i]]['del'] = []
                rule_set_second[new_path[i]] = {}
                rule_set_second[new_path[i]]['add'] = []
                rule_set_second[new_path[i]]['del'] = []
                """
                rext = state.get_table(new_path[i], table_id).get_rule(flow)
                if rext and rext.get_prt() == prt:
                    df = difference(rext.get_match_bin(), match_parse(flow))
                    if df:
                        for j in df:
                            rule_set_first[new_path[i]]['add'].append(rule(new_path[i], match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                    rule_set_first[new_path[i]]['del'].append(rule(new_path[i], rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                """
                if i == 0:
                    rule_set_first[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, 0))
                    rule_set_second[new_path[i]]['del'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, 0))
                    rule_set_second[new_path[i]]['add'].append(rule(new_path[i], match, -1, clk, out_port[new_path[i]], table_id, prt+1))
                else:
                    if i == len(new_path)-1:
                        rule_set_first[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, 0))
                        rule_set_second[new_path[i]]['del'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, 0))
                        rule_set_second[new_path[i]]['add'].append(rule(new_path[i], match, clk, -1, out_port[new_path[i]], table_id, prt+1))
                    else:
                        rule_set_first[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, 0))
                        rule_set_second[new_path[i]]['del'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, 0))
                        rule_set_second[new_path[i]]['add'].append(rule(new_path[i], match, clk, clk, out_port[new_path[i]], table_id, prt+1))

        """
        for i in (set(old_path) - set(new_path)):
            if i not in rule_set.keys():
                rule_set_first[i] = {}
                rule_set_first[i]['add'] = []
                rule_set_first[i]['del'] = []
            rext = state.get_table(i, table_id).get_rule(flow)
            if rext.get_prt() == prt:
                df = difference(rext.get_match_bin(), match_parse(flow))
                if df:
                    for j in df:
                        rule_set_first[i]['add'].append(rule(i, match_reverse(j), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
                rule_set_first[i]['del'].append(rule(i, rext.get_match(), rext.get_rtmp(), rext.get_ttmp(), rext.get_action(), table_id, prt))
            #rule_set[i]['del'].append(rule(i, {}, 1, 1, 0, table_id, 0))
            rule_set_first[i]['add'].append(rule(i, match, clk, clk, 0, table_id, prt))
        """

    return {'rule_set_first': rule_set_first, 'rule_set_second': rule_set_second}



def state_update(rule_set, state_old):
    state = copy.deepcopy(state_old)
    table_id = 0
    for i in rule_set.keys():
        tb = state.get_table(i, table_id)
        for r in rule_set[i]['del']:
            tb.del_rule(r.get_match(), r.get_prt())
        for r in rule_set[i]['add']:
            tb.add_rule(r.get_match(), r.get_rtmp(), r.get_ttmp(), r.get_action(), r.get_prt())
    return state



if __name__ == '__main__':
    n = net()
    n.add_table(1,0)
    n.add_table(2,0)
    n.add_table(3,0)
    n.add_table(4,0)
    n.get_table(1,0).add_rule({}, 1, 1, 0, 1)
    n.get_table(2,0).add_rule({}, 1, 1, 0, 1)
    n.get_table(3,0).add_rule({}, 1, 1, 0, 1)
    n.get_table(4,0).add_rule({}, 1, 1, 0, 1)

    nnext = net()
    nnext = copy.deepcopy(n)

    match = {}
    match["ipv4_src"] = "10.0.0.1/255.255.255.255"
    match["ipv4_dst"] = "10.0.0.2/255.255.255.255"
    match["eth_type"] = 2048

    flow = {}
    flow["ipv4_src"] = "10.0.0.1/255.255.255.255"
    flow["ipv4_dst"] = "10.0.0.2/255.255.255.255"
    flow["eth_type"] = 2048

    prt = 2
    """
    n.get_table(1, 0).add_rule(match, 1, 2, 2, prt)
    n.get_table(2, 0).add_rule(match, 2, 4, 3, prt)
    n.get_table(4, 0).add_rule(match, 4, 5, 6, prt)

    nnext.get_table(1, 0).add_rule(match, 1, 2, 2, prt)
    nnext.get_table(2, 0).add_rule(match, 2, 4, 3, prt)
    nnext.get_table(4, 0).add_rule(match, 4, 5, 6, prt)
    """

    old_path = []
    print "\nold state:"
    n.print_state()

    new_path = [1, 2, 4]
    out_port = {}
    out_port[1] = 1
    out_port[2] = 2
    out_port[4] = 4

    clk = 8

    print "\nrule construct:"
    rset = rule_construct(old_path, new_path, flow, n, prt, out_port, clk)
    for i in rset.keys():
        print "add rule:"
        for j in rset[i]['add']:
            j.print_rule()

        print "del rule:"
        for j in rset[i]['del']:
            j.print_rule()

    sset = sb_rule_construct(old_path, new_path, flow, clk)
    print "\nsend back rules:"
    for i in sset:
        i.print_rule()

    print "\nstate update:"
    state_update(rset, nnext, clk)
    nnext.print_state()

    setTMP(old_path, new_path, flow, n, nnext, rset, clk)
    print "\nafter setTMP:"
    for i in rset.keys():
        print "add rule:"
        for j in rset[i]['add']:
            j.print_rule()

        print "del rule:"
        for j in rset[i]['del']:
            j.print_rule()
