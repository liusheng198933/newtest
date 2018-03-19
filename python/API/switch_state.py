from util import *
import copy

class rule:
    def __init__(self, dpid, match, rtmp, ttmp, action, table_id=0, priority=0):
        # self.next_sid is the identifier of the switch
        # match is a list, each element of which is a src-dst ip addresses pair
        self.dpid = dpid
        self.match = match
        self.action = action
        # action = 0: drop;  action = -1: send back
        self.priority = priority
        self.table_id = table_id
        self.rtmp = rtmp
        self.ttmp = ttmp
        self.match_bin = match_parse(self.match)

    def get_exact_match(self, flow_table):
        # return a list
        exact = [self.match_bin]
        for r in flow_table.get_all_rules():
            if r.get_prt() <= self.priority:
                return exact
            else:
                tmp = []
                for i in exact:
                    tmp = tmp + difference(i, r.get_match_bin())
                exact = tmp
        return exact

    def print_rule(self):
        printstr = []
        printstr.append("rule dpid: %s, prt: %d, action: %d, rtmp: %d, ttmp: %d, table_id: %d\n" % (str(self.dpid), self.priority, self.action, self.rtmp, self.ttmp, self.table_id))
        printstr.append("match: %s" % str(self.match))
        print "".join(printstr)


    def get_rule(self):
        return {'dpid': self.dpid, 'match': self.match, 'action': self.action, 'priority':self.priority, 'rtmp': self.rtmp, 'ttmp': self.ttmp, 'table_id': self.table_id}

    def if_match(self, flow):
        # match field only includes ipv4_src(optional) and ipv4_dst
        flow_bin = match_parse(flow)
        if intersection(self.match_bin, flow_bin) == flow_bin:
            return True
        else:
            return False

    def if_overlap(self, match_cmp, prt_cmp):
        if prt_cmp != self.priority:
            return False
        match_cmp_bin = match_parse(match_cmp)
        if intersection(self.match_bin, match_cmp_bin):
            return True
        else:
            return False

    def if_equal(self, match_cmp, prt_cmp):
        if cmp(self.match, match_cmp) == 0 and prt_cmp == self.priority:
            return True
        else:
            return False

    def get_dpid(self):
        return self.dpid

    def get_table_id(self):
        return self.table_id

    def get_match(self):
        return self.match

    def get_match_bin(self):
        return self.match_bin

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
                return False

        for i in range(len(self.tb)):
            if self.tb[i].get_prt() <= priority:
                self.tb.insert(i, rule(self.dpid, match, rtmp, ttmp, action, self.table_id, priority))
                return True

        self.tb.append(rule(self.dpid, match, rtmp, ttmp, action, self.table_id, priority))
        return True

    def del_rule(self, match, priority):
        for i in range(len(self.tb)):
            if self.tb[i].if_equal(match, priority):
                del self.tb[i]
                return True
        return False

    def get_rule(self, flow):
        rprt = 0
        rule = -1
        for i in range(len(self.tb)):
            if self.tb[i].get_prt() > rprt and self.tb[i].if_match(flow):
                rprt = self.tb[i].get_prt()
                rule = i
        if rule < 0:
            return 0
        else:
            return self.tb[rule]

    def get_all_rules(self):
        return self.tb

    def get_dpid(self):
        return self.dpid

    def get_rule_num(self):
        return len(self.tb)

    def set_table(self, flowTable):
        self.tb = []
        for i in range(len(flowTable)):
            self.add_rule(flowTable[i].get_match(), flowTable[i].get_rtmp(), flowTable[i].get_ttmp(), flowTable[i].get_action(), flowTable[i].get_prt())

    def print_table(self):
        if self.tb:
            for i in self.tb:
                i.print_rule()

class net():
    def __init__(self):
        self.state = {}

    def add_switch(self, dpid):
        self.state[dpid] = {}

    def del_switch(self, dpid):
        del self.state[dpid]

    def add_table(self, dpid, table_id):
        if dpid not in self.state.keys():
            self.add_switch(dpid)
        self.state[dpid][table_id] = table(dpid, table_id)

    def get_state(self):
        return self.state

    def get_switch(self, dpid):
        return self.state[dpid]

    def get_table(self, dpid, table_id):
        return self.state[dpid][table_id]

    def copy_state(self, state_copy):
        self.state = copy.deepcopy(state_copy.get_state())

    def print_state(self):
        for i in self.state.keys():
            for j in self.state[i].keys():
                print i
                print j
                self.state[i][j].print_table()



def switch_query(path, dpid):
    with open(path,"w+") as f:
        f.write("#!/bin/bash\n")
        f.write("curl -X GET http://localhost:8080/stats/flow/%s\n" % dpid)
        f.close()


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
    #filepath = "/home/shengliu/Workspace/mininet/haha/cmd_test.sh"

    #switch_query(filepath, 3)
    #process = subprocess.Popen('%s' %filepath, stdout=subprocess.PIPE)
    #output, error = process.communicate()

    #rule_list = parse_query(output)
    #for r in rule_list:
    #    r.print_rule()

    n = net()
    n.add_table(1,0)
    n.add_table(2,0)
    n.add_table(3,0)

    match = {}
    match["ipv4_src"] = "10.0.0.1/255.255.255.255"
    match["ipv4_dst"] = "10.0.0.2/255.255.255.255"
    match["eth_type"] = 2048

    flow = {}
    flow["ipv4_src"] = "10.0.0.1/255.255.255.255"
    flow["ipv4_dst"] = "10.0.0.2/255.255.255.255"
    flow["eth_type"] = 2048

    n.get_table(1, 0).add_rule(match, 1, 2, 2, 1)
    n.get_table(1, 0).add_rule(match, 1, 3, 3, 2)
    n.get_table(2, 0).add_rule(match, 2, 3, 3, 1)

    n.get_table(1, 0).print_table()
    #print n.get_table(1, 0).get_rule(flow).get_action()
    #print n.get_table(3, 0).get_rule(flow).get_action()
    #print n.get_table(1, 0).get_rule(flow).get_rtmp()
    #print n.get_table(1, 0).get_rule(flow).get_ttmp()
    #print n.get_table(2, 0).get_rule(flow).get_action()
    #print n.get_table(2, 0).get_rule(flow).get_rtmp()
    #print n.get_table(2, 0).get_rule(flow).get_ttmp()
