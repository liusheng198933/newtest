import subprocess
import time


class rule:
    def __init__(self, dpid, match, rtmp, ttmp, action, table_id=0, priority=0):
        # self.next_sid is the identifier of the switch
        # match is a list, each element of which is a src-dst ip addresses pair
        self.dpid = dpid
        self.match = match
        self.action = action
        self.priority = priority
        self.table_id = table_id
        self.rtmp = rtmp
        self.ttmp = ttmp

    def print_rule(self):
        printstr = []
        printstr.append("rule dpid: %i, prt: %i, action: %s, rtmp: %i, ttmp: %i, table_id: %i\n" % (self.dpid, self.priority, self.action, self.rtmp, self.ttmp, self.table_id))
        printstr.append("match: %s" % str(self.match))
        print "".join(printstr)

    def get_rule(self):
        return {'dpid': self.dpid, 'match': self.match, 'action': self.action, 'priority':self.priority, 'rtmp': self.rtmp, 'ttmp': self.ttmp, 'table_id': self.table_id}

    def if_match(self, flow):
        pass

    def if_overlap(self, match, priority):
        pass

    def if_equal(self, match, priority):
        pass

    def get_dpid(self):
        return self.dpid

    def get_table_id(self):
        return self.table_id

    def get_match(self):
        return self.match

    def get_rtmp(self):
        return self.rtmp

    def get_ttmp(self):
        return self.ttmp

    def get_prt(self):
        return self.priority

    def get_action(self):
        return self.action

    def set_dpid(self, value):
        self.dpid = value

    def set_prt(self, value):
        self.priority = value

    def set_rtmp(self, value):
        self.rtmp = value

    def set_ttmp(self, value):
        self.ttmp = value

    def set_match(self, value):
        self.match = value

    def set_table_id(self, value):
        self.table_id = value

    def set_action(self, value):
        self.action = value




class table:
    # create an image of the switch flow table
    def __init__(self, dpid, table_id):
        self.tb = []
        self.dpid = dpid
        self.table_id = table_id

    def clear(self):
        self.tb = []

    def add_rule(self, match, rtmp, ttmp, action, priority):
        for i in range(len(self.tb)):
            if self.tb[i].if_overlap(match, priority):
                return
        self.tb.append(rule(self.dpid, match, rtmp, ttmp, action, self.table_id, priority))

    def del_rule(self, match, priority):
        for i in range(len(self.tb)):
            if self.tb[i].if_equal(self.sid, match, priority):
                del self.tb[i]
                return

    def get_rule(self, flow):
        rprt = 0
        rule = -1
        for i in range(len(self.tb)):
            if (self.tb[i].if_match(flow)) & (self.tb[i].get_prt() > rprt):
                rprt = self.tb[i].get_prt()
                rule = i
        if rule < 0:
            return 0
        else:
            return self.tb[rule]


    def get_dpid(self):
        return self.dpid

    def get_rule_num(self):
        return len(self.tb)

    def set_table(self, flowTable):
        self.tb = []
        for i in range(len(flowTable)):
            self.add_rule(flowTable[i].get_match(), flowTable[i].get_rtmp(), flowTable[i].get_ttmp(), flowTable[i].get_action(), flowTable[i].get_prt())



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

    if out_port == "in_port":
        instructions = ['\"instructions\":[{\"type\":\"APPLY_ACTIONS\",\"actions\":[{\"type\":\"SET_FIELD\",\"field\":\"vlan_vid\",\"value\": %s},{\"type\": \"OUTPUT\",\"port\": \"in_port\"}]}]' %(str(ttmp+4096))]
    else:
        if out_port == "drop":
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

def parse_query(output):
    strret = output.split()
    rule_list = []
    j = -1
    rmchars = '\"\':{}[],'
    dpid = int(strret[0].strip(rmchars))
    for i in range(len(strret)):
        if "priority" in strret[i]:
            rule_list.append(rule(dpid, {}, 0, 0, 0, 0, 0))
            j = j + 1
            rule_list[j].set_prt(int(strret[i+1].strip(rmchars)))

        if "table_id" in strret[i]:
            rule_list[j].set_table_id(int(strret[i+1].strip(rmchars)))

        if "match" in strret[i]:
            mt = {}
            k = i + 1
            while "instructions" not in strret[k]:
                if (k-i) % 2 == 1:
                    key = strret[k].strip(rmchars)
                    value = strret[k+1].strip(rmchars)
                    if key == 'vlan_vid':
                        rule_list[j].set_rtmp(int(value))
                    else:
                        if key != 'ipv4_dst' and key != 'ipv4_src':
                            value = int(value)
                        mt[key] = value
                k = k + 1
            rule_list[j].set_match(mt)

        if "action" in strret[i]:
            k = i + 1
            while ("priority" not in strret[k]) and (k < len(strret)):
                if strret[k].strip(rmchars) == 'vlan_vid':
                    rule_list[j].set_ttmp(int(strret[k+2].strip(rmchars)))
                if strret[k].strip(rmchars) == 'OUTPUT':
                    rule_list[j].set_action(strret[k+2].strip(rmchars))
                k = k + 1
    return rule_list

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
    print "haha"
    switch_query(filepath, 3)
    process = subprocess.Popen('%s' %filepath, stdout=subprocess.PIPE)
    output, error = process.communicate()

    rule_list = parse_query(output)
    for r in rule_list:
        r.print_rule()
