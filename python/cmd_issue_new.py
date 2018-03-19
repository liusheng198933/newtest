import subprocess
import time


def addFlowRule(dpid, match, out_port, table_id=0, priority=2, flag="add"):
    # add normal rule
    dpid = str(int(dpid, 16))
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"table_id\": ' + str(table_id) + ",")
    cmd.append('\"priority\": ' + str(priority) + ",")

    match_para = ['\"match\":{ ']
    for key in match.keys():
        if "ip" in key:
            match_para.append('\"%s\":\"%s\"' %(key, str(match[key])))
        else:
            match_para.append('\"%s\":%s' %(key, str(match[key])))
        match_para.append(",")
    match_para.pop()
    match_para.append("},")


    if out_port == 'flood':
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"OUTPUT\",\"port\": \"FLOOD\"}]}]']
    else:
        if out_port == 'drop':
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[ ]}]']
        else:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(out_port))]

    if match:
        cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/flowentry/%s \n\n" %flag)
    return ''.join(cmd)


def addFlowRule_bdid(dpid, bdid, match, out_port, table_id=0, priority=2, flag="add"):
    # add normal rule
    #dpid = str(int(dpid, 16))
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"bdid\": ' + str(bdid) + ",")
    cmd.append('\"table_id\": ' + str(table_id) + ",")
    cmd.append('\"priority\": ' + str(priority) + ",")

    match_para = ['\"match\":{ ']
    for key in match.keys():
        if "ip" in key:
            match_para.append('\"%s\":\"%s\"' %(key, str(match[key])))
        else:
            match_para.append('\"%s\":%s' %(key, str(match[key])))
        match_para.append(",")
    match_para.pop()
    match_para.append("},")

    if out_port == 'flood':
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"OUTPUT\",\"port\": \"FLOOD\"}]}]']
    else:
        if out_port == 0:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[ ]}]']
        else:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/flowentry/%s \n\n" %flag)
    return ''.join(cmd)


def addTMPRule(dpid, match, rtmp, ttmp, out_port, table_id=0, priority=2, flag="add"):
    # add normal rule with timestamp
    dpid = str(int(dpid, 16))
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"table_id\": ' + str(table_id) + ",")
    cmd.append('\"priority\": ' + str(priority) + ",")

    match_para = ['\"match\":{ ']
    for key in match.keys():
        if "ip" in key:
            match_para.append('\"%s\":\"%s\"' %(key, str(match[key])))
        else:
            match_para.append('\"%s\":%s' %(key, str(match[key])))
        match_para.append(",")
    match_para.append('\"dl_vlan\":%s' % str(rtmp))
    match_para.append("},")

    if out_port == 0:
        # drop action
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[ ]}]']
    else:
        if out_port == -1:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": \"in_port\"}]}]' %(str(ttmp+4096))]
        else:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(ttmp+4096), str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/flowentry/%s \n\n" %flag)
    return ''.join(cmd)



def bundleAddMsg(dpid, bdid, match, rtmp, ttmp, out_port, table_id=0, priority=2, flag="add"):
    # bundle add rule with timestamp
    dpid = str(int(dpid, 16))
    if rtmp == -1 and ttmp == -1:
        return addFlowRule_bdid(dpid, bdid, match, out_port, table_id, priority, flag)

    if rtmp == -1:
        return pushTMP(dpid, bdid, match, ttmp, out_port, table_id, priority, flag)

    if ttmp == -1:
        return popTMP(dpid, bdid, match, rtmp, out_port, table_id, priority, flag)

    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"bdid\": ' + str(bdid) + ",")
    cmd.append('\"table_id\": ' + str(table_id) + ",")
    cmd.append('\"priority\": ' + str(priority) + ",")

    match_para = ['\"match\":{ ']
    for key in match.keys():
        if "ip" in key:
            match_para.append('\"%s\":\"%s\"' %(key, str(match[key])))
        else:
            match_para.append('\"%s\":%s' %(key, str(match[key])))
        match_para.append(",")
    match_para.append('\"dl_vlan\":%s' % str(rtmp))
    match_para.append("},")

    #if out_port == "in_port":
    if out_port == -1:
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"DEC_NW_TTL\"}, {\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": \"in_port\"}]}]' %(str(ttmp+4096))]
    else:
        #if out_port == "drop":
        if out_port == 0:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[]}]']
        else:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"DEC_NW_TTL\"}, {\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(ttmp+4096), str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/bundleadd/%s \n\n" %flag)
    return ''.join(cmd)


def bundleCtrlMsg(dpid, bdid, flag):
    dpid = str(int(dpid, 16))
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"bdid\": ' + str(bdid))
    cmd.append("}\' http://localhost:8080/stats/bundlectrl/%s \n\n" %flag)
    return ''.join(cmd)


def pushTMP(dpid, bdid, match, ttmp, out_port, table_id=0, priority=2, flag="add"):
    # add rule with timestamp to the first switch on path
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"bdid\": ' + str(bdid) + ",")
    cmd.append('\"table_id\": ' + str(table_id) + ",")
    cmd.append('\"priority\": ' + str(priority) + ",")

    match_para = ['\"match\":{ ']
    for key in match.keys():
        if "ip" in key:
            match_para.append('\"%s\":\"%s\"' %(key, str(match[key])))
        else:
            match_para.append('\"%s\":%s' %(key, str(match[key])))
        match_para.append(",")
    match_para.pop()
    match_para.append("},")

    instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"PUSH_VLAN\",\"ethertype\": 33024}, {\"type\": \"SET_NW_TTL\",\"nw_ttl\": 15}, {\"type\": \"DEC_NW_TTL\"}, {\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(ttmp+4096), str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/bundleadd/%s \n\n" %flag)
    return ''.join(cmd)



def popTMP(dpid, bdid, match, rtmp, out_port, table_id=0, priority=2, flag="add"):
    # add rule with timestamp to the last switch on path
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"bdid\": ' + str(bdid) + ",")
    cmd.append('\"table_id\": ' + str(table_id) + ",")
    cmd.append('\"priority\": ' + str(priority) + ",")

    match_para = ['\"match\":{ ']
    for key in match.keys():
        if "ip" in key:
            match_para.append('\"%s\":\"%s\"' %(key, str(match[key])))
        else:
            match_para.append('\"%s\":%s' %(key, str(match[key])))
        match_para.append(",")
    match_para.append('"dl_vlan":%s' % str(rtmp))
    match_para.append("},")

    if out_port == -1:
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"DEC_NW_TTL\"}, {\"type\": \"POP_VLAN\"},{\"type\": \"OUTPUT\",\"port\": \"in_port\"}]}]']
    else:
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"DEC_NW_TTL\"}, {\"type\": \"POP_VLAN\"}, {\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/bundleadd/%s \n\n" %flag)
    return ''.join(cmd)


def table_clear(dpid):
    dpid = str(int(dpid, 16))
    cmd = ["curl -X DELETE http://localhost:8080/stats/flowentry/clear/%s \n\n" %(str(dpid))]
    return ''.join(cmd)


def script_init(path):
    with open(path,"w+") as f:
        f.write("#!/bin/bash\n")
        f.close()


def script_write(path, str):
    with open(path,"a+") as f:
        f.write(str)
        f.close()

def switch_query(path, dpid):
    with open(path,"w+") as f:
        f.write("#!/bin/bash\n")
        f.write("curl -X GET http://localhost:8080/stats/flow/%s\n" % dpid)
        f.close()

def table_query(path, dpid):
    with open(path,"w+") as f:
        f.write("#!/bin/bash\n")
        f.write("curl -X GET http://localhost:8080/stats/table/%s\n" % dpid)
        f.close()

def parse_table_query(path, dpid):
    table_query(path, dpid)
    p = subprocess.Popen(path, stdout=subprocess.PIPE)
    ret = p.communicate()[0]
    num = int(ret.split()[8].strip('},'))
    return num

def network_clear(dp_range, filepath):
    for i in range(dp_range):
        script_write(filepath, table_clear(i+1))

def network_drop(dp_range, filepath):
    for i in range(dp_range):
        drop_rule_push(i+1, filepath, 1, 1, 0, 1)

def arp_rule_push(dpid, filepath, table_id=0, priority=1):
    match = {}
    match["eth_type"] = 0x0806
    script_write(filepath, addFlowRule(dpid, match, 'flood', table_id, priority, "add"))


def drop_rule_push(dpid, filepath, rtmp=1, ttmp=1, table_id=0, priority=0):
    script_write(filepath, addTMPRule(dpid, {}, rtmp, ttmp, 0, table_id, priority, "add"))

def path_deploy_test(old_path, new_path, flow, state, prt, out_port, clk):
    bdid = 0
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    for i in rule_set.keys():
        bdid = bdid + 1
        if i == new_path[0]:
            script_write(filepath, bundleCtrlMsg(i, bdid, "open"))
            for r in rule_set[i]['del']:
                script_write(filepath, pushTMP(i, bdid, r.get_match(), r.get_ttmp(), out_port[i], r.get_table_id(), r.get_prt(), "del"))
            for r in rule_set[i]['add']:
                script_write(filepath, pushTMP(i, bdid, r.get_match(), r.get_ttmp(), out_port[i], r.get_table_id(), r.get_prt(), "add"))

            script_write(filepath, bundleCtrlMsg(i, bdid, "commit"))
        else:
            if i == new_path[len(new_path)]:
                script_write(filepath, bundleCtrlMsg(i, bdid, "open"))
                for r in rule_set[i]['del']:
                    script_write(filepath, popTMP(i, bdid, r.get_match(), r.get_rtmp(), out_port[i], r.get_table_id(), r.get_prt(), "del"))
                for r in rule_set[i]['add']:
                    script_write(filepath, popTMP(i, bdid, r.get_match(), r.get_rtmp(), out_port[i], r.get_table_id(), r.get_prt(), "add"))

                script_write(filepath, bundleCtrlMsg(i, bdid, "commit"))
            else:
                script_write(filepath, bundleCtrlMsg(i, bdid, "open"))
                for r in rule_set[i]['del']:
                    script_write(filepath, bundleAddMsg(i, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), out_port[i], r.get_table_id(), r.get_prt(), "del"))
                for r in rule_set[i]['add']:
                    script_write(filepath, bundleAddMsg(i, bdid, r.get_match(), r.get_rtmp(), r.get_ttmp(), out_port[i], r.get_table_id(), r.get_prt(), "add"))
                script_write(filepath, bundleCtrlMsg(i, bdid, "commit"))
        subprocess.call("%s" %filepath)

if __name__ == '__main__':
    filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"
    node_num = 21

    script_init(filepath)
    network_clear(node_num, filepath)
    network_drop(node_num, filepath)
    #network_arp_push(node_num, filepath)
    match = {}
    match["eth_type"] = 0x0806
    for i in range(8):
        script_write(filepath, addFlowRule(i+1, match, 'flood', 0, 1, "add"))
    script_write(filepath, addFlowRule(21, match, 'flood', 0, 1, "add"))
    subprocess.call("%s" %filepath)


    match1 = {}
    match1["ipv4_src"] = "10.0.1.1/255.255.255.255"
    match1["ipv4_dst"] = "10.0.1.4/255.255.255.255"
    match1["eth_type"] = 2048

    match2 = {}
    match2["ipv4_src"] = "10.0.1.4/255.255.255.255"
    match2["ipv4_dst"] = "10.0.1.1/255.255.255.255"
    match2["eth_type"] = 2048

    dp = 1
    bdid = 1
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    script_write(filepath, pushTMP(dp, bdid, match1, 1, 3, 0, 2, "add"))
    script_write(filepath, popTMP(dp, bdid, match2, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))


    dp = 9
    bdid = 2
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 4, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 2, 2, 1, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match2, 4, 1, 0, 2, "add"))
    #script_write(filepath, pushTMP(dp, bdid, match1, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 18
    bdid = 3
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 2, 2, 1, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 'drop', 0, 1, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 1, 1, 'drop', 0, 1, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 11
    bdid = 4
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 1, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 2, 2, 4, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    #dp = 4
    #bdid = 4
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 3
    bdid = 5
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    script_write(filepath, popTMP(dp, bdid, match1, 1, 1, 0, 2, "add"))
    script_write(filepath, pushTMP(dp, bdid, match2, 2, 3, 0, 2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    subprocess.call("%s" %filepath)


    time.sleep(10)



    script_init(filepath)
    dp = 11
    bdid = 6
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 2, 2, 4, 0, 2, "delete_strict"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 3, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 5, 5, "in_port", 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "delete_strict"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 5, "in_port", 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
#    subprocess.call("%s" %filepath)

    dp = 17
    bdid = 7
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 2, 2, 0, 2, "delete_strict"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 5, 5, "in_port", 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 1, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 2, 1, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 5, "in_port", 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
#    subprocess.call("%s" %filepath)

    dp = 18
    bdid = 8
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 2, 0, 2, "delete_strict"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 3, -1, 0, 5, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 2, 2, 1, 0, 2, "delete_strict"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, -1, 0, 5, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
    subprocess.call("%s" %filepath)

    time.sleep(1)
    script_init(filepath)
    dp = 9
    bdid = 9
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
        #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 4, 0, 2, "delete_strict"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 3, 3, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    #subprocess.call("%s" %filepath)



    #dp = 3
    #bdid = 8
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "delete_strict"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 5, 2, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, 2, 4, 3, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    #dp = 4
    #bdid = 9
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 5, 2, 2, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 4, 1, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    #dp = 5
    #bdid = 10
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, 4, 2, 0, 2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    subprocess.call("%s" %filepath)
