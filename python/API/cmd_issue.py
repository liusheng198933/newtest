import subprocess
import time


def addFlowRule(dpid, match, out_port, table_id=0, priority=2, flag="add"):
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

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/flowentry/%s \n\n" %flag)
    return ''.join(cmd)


def addTMPRule(dpid, match, rtmp, ttmp, out_port, table_id=0, priority=2, flag="add"):
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

    if out_port == "drop":
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[ ]}]']
    else:
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(ttmp+4096), str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/flowentry/%s \n\n" %flag)
    return ''.join(cmd)



def bundleAddMsg(dpid, bdid, match, rtmp, ttmp, out_port, table_id=0, priority=2, flag="add"):
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
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": \"in_port\"}]}]' %(str(ttmp+4096))]
    else:
        #if out_port == "drop":
        if out_port == 0:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[]}]']
        else:
            instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(ttmp+4096), str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/bundleadd/%s \n\n" %flag)
    return ''.join(cmd)


def bundleCtrlMsg(dpid, bdid, flag):
    cmd = ["curl -X POST -d \'{ "]
    cmd.append('\"dpid\": ' + str(dpid) + ",")
    cmd.append('\"bdid\": ' + str(bdid))
    cmd.append("}\' http://localhost:8080/stats/bundlectrl/%s \n\n" %flag)
    return ''.join(cmd)


def pushTMP(dpid, bdid, match, ttmp, out_port, table_id=0, priority=2, flag="add"):
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

    instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"PUSH_VLAN\",\"ethertype\": 33024}, {\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(ttmp+4096), str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/bundleadd/%s \n\n" %flag)
    return ''.join(cmd)



def popTMP(dpid, bdid, match, rtmp, out_port, table_id=0, priority=2, flag="add"):
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

    instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\": \"POP_VLAN\"}, {\"type\": \"OUTPUT\",\"port\": %s}]}]' %(str(out_port))]

    cmd = cmd + match_para
    cmd = cmd + instructions
    cmd.append("}\' http://localhost:8080/stats/bundleadd/%s \n\n" %flag)
    return ''.join(cmd)


def table_clear(dpid):
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


def network_clear(dp_range, filepath):
    for i in range(dp_range):
        script_write(filepath, table_clear(i+1))


def network_arp_push(dp_range, filepath):
    match = {}
    match["eth_type"] = 0x0806
    for i in range(dp_range):
        script_write(filepath, addFlowRule(i+1, match, 'flood', 0, 1, "add"))


def network_drop(dp_range, filepath):
    for i in range(dp_range):
        script_write(filepath, addTMPRule(i+1, {}, 1, 1, 'drop', 0, 0, "add"))

def path_deploy(rule_set, new_path, out_port):
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
    node_num = 6

    script_init(filepath)
    network_clear(node_num, filepath)
    network_drop(node_num, filepath)
    #network_arp_push(node_num, filepath)
    match = {}
    match["eth_type"] = 0x0806
    match["in_port"] = 1
    script_write(filepath, addFlowRule(1, match, 2, 0, 1, "add"))
    match = {}
    match["eth_type"] = 0x0806
    match["in_port"] = 2
    script_write(filepath, addFlowRule(1, match, 1, 0, 1, "add"))
    match = {}
    match["eth_type"] = 0x0806
    script_write(filepath, addFlowRule(2, match, 'flood', 0, 1, "add"))
    script_write(filepath, addFlowRule(3, match, 'flood', 0, 1, "add"))
    match = {}
    match["eth_type"] = 0x0806
    script_write(filepath, addFlowRule(4, match, 2, 0, 1, "add"))
    script_write(filepath, addFlowRule(5, match, 'flood', 0, 1, "add"))
    script_write(filepath, addFlowRule(6, match, 'flood', 0, 1, "add"))


    match1 = {}
    match1["ipv4_src"] = "10.0.0.1/255.255.255.255"
    match1["ipv4_dst"] = "10.0.0.2/255.255.255.255"
    match1["eth_type"] = 2048

    match2 = {}
    match2["ipv4_src"] = "10.0.0.2/255.255.255.255"
    match2["ipv4_dst"] = "10.0.0.1/255.255.255.255"
    match2["eth_type"] = 2048

    dp = 6
    bdid = 11
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    script_write(filepath, pushTMP(dp, bdid, match1, 2, 2, 0, 2, "add"))
    script_write(filepath, popTMP(dp, bdid, match2, 4, 1, 0, 2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 1
    bdid = 1
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 2, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match2, 4, 1, 0, 2, "add"))
    #script_write(filepath, pushTMP(dp, bdid, match1, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 2
    bdid = 2
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 1, 1, 'drop', 0, 1, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 1, 1, 'drop', 0, 1, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 3
    bdid = 3
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 2, 4, 3, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "add"))
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

    dp = 5
    bdid = 5
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    script_write(filepath, popTMP(dp, bdid, match1, 4, 2, 0, 2, "add"))
    script_write(filepath, pushTMP(dp, bdid, match2, 4, 1, 0, 2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    subprocess.call("%s" %filepath)


    #time.sleep(10)



    script_init(filepath)
    dp = 2
    bdid = 7
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 3, 2, 2, 0, 2, "delete_strict"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match1, 5, 5, "in_port", 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "delete_strict"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 5, "in_port", 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))
    subprocess.call("%s" %filepath)

    time.sleep(1)
    script_init(filepath)
    dp = 1
    bdid = 6
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
        #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 2, 2, 2, 0, 2, "delete_strict"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 5, 5, 3, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    #subprocess.call("%s" %filepath)



    dp = 3
    bdid = 8
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 4, 4, 1, 0, 2, "delete_strict"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 5, 2, 0, 2, "add"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, 2, 4, 3, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    dp = 4
    bdid = 9
    script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    script_write(filepath, bundleAddMsg(dp, bdid, match1, 5, 2, 2, 0, 2, "add"))
    script_write(filepath, bundleAddMsg(dp, bdid, match2, 5, 4, 1, 0, 2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, rtmp, out_port, 0, priority=2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    #dp = 5
    #bdid = 10
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "open"))
    #script_write(filepath, bundleAddMsg(dp, bdid, match, rtmp, ttmp, out_port, 0, priority=2, "add"))
    #script_write(filepath, popTMP(dp, bdid, match, 4, 2, 0, 2))
    #script_write(filepath, pushTMP(dp, bdid, match, ttmp, out_port, 0, priority=2))
    #script_write(filepath, bundleCtrlMsg(dp, bdid, "commit"))

    subprocess.call("%s" %filepath)
