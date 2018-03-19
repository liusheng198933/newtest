import copy

def rule_set_merge(rule_set_all, rule_set):
    rule_set_final = rule_set_all
    for i in rule_set.keys():
        if i not in rule_set_all.keys():
            rule_set_final[i] = copy.deepcopy(rule_set[i])
        else:
            for j in rule_set[i].keys():
                if j in rule_set_final[i].keys():
                    rule_set_final[i][j]['add'] = rule_set_all[i][j]['add'] + rule_set[i][j]['add']
                    rule_set_final[i][j]['del'] = rule_set_all[i][j]['del'] + rule_set[i][j]['del']
                else:
                    rule_set_final[i][j] = copy.deepcopy(rule_set[i][j])

    return rule_set_final

def set_clean(rset):
    rule_set = copy.deepcopy(rset)
    for i in rule_set.keys():
        if not rule_set[i]:
            del rule_set[i]
        else:
            if (not rule_set[i]['add']) and (not rule_set[i]['del']):
                del rule_set[i]
    return rule_set


def int2dpid(kind, swNum, podNum=0):
    # kind = 1 indicates the core switches, 2 for aggrSwitch and 3 for edgeSwitch
    # the format of switch dpid is 1-bit for switch classification, 3-bit for pod number and 3-bit for aggr or edge number

    if kind == 1:
        dpid = hex(swNum)[2:]
        dpid = '0' * ( 6 - len( dpid ) ) + dpid
    else:
        dpid1 = hex(podNum)[2:]
        dpid1 = '0' * ( 3 - len( dpid1 ) ) + dpid1
        dpid2 = hex(swNum)[2:]
        dpid2 = '0' * ( 3 - len( dpid2 ) ) + dpid2
        dpid = dpid1 + dpid2
    return str(kind)+dpid


def reverse_flow(flow):
    flow_reverse = {}
    flow_reverse['ipv4_src'] = flow['ipv4_dst']
    flow_reverse['ipv4_dst'] = flow['ipv4_src']
    return flow_reverse


def ip_parse(ip):
# parse ip addres "10.0.0.1/255.255.255.254"
    ip_str = []
    ip_ret = ip.strip("\'\"")
    if "/" in ip:
        ip_addr = ip_ret.split('/')[0]
        ip_mask = ip_ret.split('/')[1]
    else:
        ip_addr = ip_ret
        ip_mask = 0
    if ip_mask:
        for i in range(4):
            bnum = '{:b}'.format(int(ip_addr.split('.')[i])).zfill(8)
            bmask = '{:b}'.format(int(ip_mask.split('.')[i])).zfill(8)
            bret = []
            for j in range(8):
                if bmask[j] == '0':
                    bret.append('x')
                else:
                    bret.append(bnum[j])
            ip_str = ip_str + bret
    else:
        for i in ip_addr.split('.'):
            bnum = '{:b}'.format(int(i)).zfill(8)
            ip_str.append(bnum)
    return "".join(ip_str)


def match_parse(flow):
    # flow = {}, flow['ipv4_dst'] = '10.0.0.1/255.255.255.255', flow['ipv4_src'] = '10.0.0.2/255.255.255.255'
    if not flow:
        return 'x'*64
    mt = []
    #if 'in_port' in flow.keys():
    #    mt.append('{:b}'.format(flow['in_port']).zfill(16))
    #else:
    #    mt.append('x' * 16)
    mt.append(ip_parse(flow['ipv4_dst']))
    if 'ipv4_src' in flow.keys():
        mt.append(ip_parse(flow['ipv4_src']))
    else:
        mt.append('x'*32)
    return ''.join(mt)

def match_reverse(match_str):
    mt = {}
    mt['ipv4_dst']= ip_reverse(match_str[0:32])
    mt['ipv4_src']= ip_reverse(match_str[32:64])
    return mt


def ip_reverse(ip_str):
    #return string without ""
    ip = []
    ip_mask = []
    for i in range(4):
        num = ip_str[i*8:i*8+8]
        bnum = []
        bmask = []
        for j in range(8):
            if num[j] == 'x':
                bmask.append('0')
                bnum.append('0')
            else:
                bmask.append('1')
                bnum.append(num[j])
        ip.append(str(int("".join(bnum), 2)))
        ip.append('.')
        ip_mask.append(str(int("".join(bmask), 2)))
        ip_mask.append('.')
    ip.pop()
    ip_mask.pop()
    return "".join(ip) + '/' + "".join(ip_mask)


def intersection(match1, match2):
    # match1 and match2 are strings of the same length
    # return string
    result = []
    for i in range(len(match2)):
        if match2[i] == 'x':
            result.append(match1[i])
        if match2[i] == '1':
            if match1[i] == '0':
                result.append('z')
                return False
            else:
                result.append('1')
        if match2[i] == '0':
            if match1[i] == '1':
                result.append('z')
                return False
            else:
                result.append('0')
    return "".join(result)


def union(match1, match2):
    # merge match1 and match2, return string
    count = 0
    result = []
    for i in range(len(match1)):
        if (match1[i] != match2[i]):
            count += 1
            result.append('x')
        else:
            result.append(match1[i])
        if count > 1:
            return False
    return "".join(result)

def union_set(st, ele):
    # merge string ele with list st, return list
    listcopy = copy.deepcopy(st)
    i = 0
    while (i < len(listcopy)):
        t = union(listcopy[i], ele)
        if t:
            ele = t
            del listcopy[i]
            i = 0
        else:
            i += 1
    listcopy.append(ele)
    return listcopy

def complement(match1):
    # return list
    result = []
    for i in range(len(match1)):
        if match1[i] != 'x':
            tmp = []
            for j in range(len(match1)):
                if j < i:
                    tmp.append(match1[j])
                if j == i:
                    if match1[i] == '1':
                        tmp.append('0')
                    else:
                        tmp.append('1')
                if j > i:
                    tmp.append('x')
            result = union_set(result, "".join(tmp))
    return result

def difference(match1, match2):
    # return list
    result = []
    elec = complement(match2)
    #print elec
    for i in range(len(elec)):
        t = intersection(match1, elec[i])
        if t:
            result = union_set(result, t)
    return result


def match_generate(bitnum):
    match = []
    for i in range(bitnum):
        r = random.randint(1,3)
        if r == 1:
            match.append('0')
        if r == 2:
            match.append('1')
        if r == 3:
            match.append('x')
    return "".join(match)

def path_generate(path_length, node_set):
    path = []
    i = 0
    while (i < path_length):
        r = random.randint(1, len(node_set))
        if node_set[r-1] not in path:
            path.append(node_set[r-1])
            i += 1
    return path


if __name__ == '__main__':
    print ip_parse("10.0.0.1/255.255.255.254")
