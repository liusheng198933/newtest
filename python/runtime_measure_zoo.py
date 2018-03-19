from util import *
#from cmd_p4 import *
from timestamp import setTMP, rule_construct, state_update
#from readFile import *
from switch_state import rule, net, table
import copy
import subprocess
import time
import random
from datetime import datetime
#from time_process import
from test_main import out_port_construct
from test_main_all import get_flow_list_new
import networkx as nx
import sys
from random import randint
import os


def path_deploy_runtime(old_path, new_path, flow, state_cur, prt, in_port, out_port_old, out_port_new, clock):

    start_time = time.time()

    clk = clock

    #time1 = time.time()

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


def state_init(num, state_cur):
    #state_cur = copy.deepcopy(state)
    table_id = 0
    #sw_num = pow((K/2),2) + ((K/2)*K) + ((K/2)*K)
    dp_set = [i for i in range(num)]


    for i in dp_set:
        state_cur.add_table(i, 0)
        #state_cur.get_table(i, 0).add_rule({}, 0, 0, 0, 0)

    return True
    #return state_cur


def test_measure(filename, i):
    #K = 8
    #filepath = os.getcwd() + '/flow_update_%d.tsv' %K
    #flow_list = get_flow_list_new(filepath, K, 0, 100)
    ret = gen(filename, i)

    flow_list = ret['flow_list']
    nnode = ret['nnode']
    nedge = ret['nedge']
    state_cur = net()
    state_init(ret['nnode'], state_cur)

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
    gentime_list = []

    #flow_list = get_flow_list_new(filepath, K, 0, num)
    #flow_list = {}
    # k = 0
    # for i in flow_list1.keys():
    #     k = k + 1
    #     flow_list[i] = flow_list1[i]
    #     if k >= num:
    #         break
    m = 0
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
            #print old_path
            #print new_path
            deploy_ret = path_deploy_runtime(old_path, new_path, flow, state_cur, priority, in_port_old, out_port_old, out_port_new, clk)
            #state_cur = deploy_ret['state']
            #clk = deploy_ret['clk']
            runtime_list.append(deploy_ret['runtime'])
            gentime_list.append(deploy_ret['runtime_rule'])
            #print deploy_ret['time']
            m = m + 1
    #print "path"
    print m
    #print runtime_list
    print sum(runtime_list)

    #retpath = '/home/shengliu/Workspace/result/result_%s_%d_%d.txt' %(filename, nnode, nedge)
    retpath = os.getcwd() + '/result_%s_%d_%d_all.txt' %(filename, nnode, nedge)
    fp = open(retpath, 'a+')
    fp.write('%f ' %(sum(runtime_list)))
    fp.close()
    retpath = os.getcwd() + '/result_%s_%d_%d_gen.txt' %(filename, nnode, nedge)
    fp = open(retpath, 'a+')
    fp.write('%f ' %(sum(gentime_list)))
    fp.close()



    #state_cur.print_state()
    # print runtime_list
    # print "max runtime"
    # print max(runtime_list)
    # print "total runtime"
    # print sum(runtime_list)
    # print "average runtime"
    # print float(sum(runtime_list)) / len(runtime_list)

def getShortPaths(g):
    paths=dict(nx.all_pairs_shortest_path(g))
    print paths
    minlen=1+len(g.nodes)
    maxlen=0
    out=""
    for src in paths:
        p=paths[src]
        for dst in p:
            path=paths[src][dst]
            out=out+','.join(path)+"\n"
            pl=len(path)
            #print paths[src][dst],len(path)
            if minlen> pl:
                minlen=pl
            if maxlen< pl:
                maxlen=pl

    return [out,maxlen]
    #print minlen,maxlen

def gen(filename, i):
    flow_list = {}
    g=(nx.read_graphml(filename))
    nnode=len(list(g.nodes))
    nedge=len(list(g.edges))
    #print len(list(g.edges))
    #g=g.to_directed()
    oldpaths=dict(nx.all_pairs_shortest_path(g))
    #[out,maxlen]=getShortPaths(g)

    #path_translate(out, flow_list)

    filename=filename.replace(".graphml","")
    #outname=filename+"_"+str(nnode)+"_"+str(nedge)+"_"+str(maxlen)
    #f=open(outname+".old","w")
    #f.write(out)
    #f.close()
    edges=list(g.edges)
    #if i < len(edges):
    edge = edges[i]
    #for edge in edges:
    g.remove_edge(*edge)
    newpaths=dict(nx.all_pairs_shortest_path(g))
    #edge=edges[randint(0,len(edges)-1)]
    #print edge
    #edge = ('17','31')


    retpath = os.getcwd() + '/result_%s_%d_%d_edge.txt' %(filename, nnode, nedge)
    fp = open(retpath, 'a+')
    fp.write('%s ' %(str(edge)))
    fp.close()


    flow_list = {}

    for src in newpaths.keys():
        p=newpaths[src]
        for dst in p.keys():
            if src in oldpaths.keys() and dst in oldpaths[src].keys():
                old_path = oldpaths[src][dst]
                new_path = newpaths[src][dst]

                for e in range(len(old_path)):
                    old_path[e] = int(old_path[e])
                for e in range(len(new_path)):
                    new_path[e] = int(new_path[e])
                if len(old_path) > 1:
                    flow = {}
                    flow['ipv4_dst'] = '10.0.0.%d' %old_path[len(old_path)-1]
                    flow['ipv4_src'] = '10.0.0.%d' %old_path[0]
                    f = match_parse(flow)
                    if f not in flow_list.keys():
                        flow_list[f] = {}
                        flow_list[f]['flow'] = flow
                        flow_list[f]['old_path'] = old_path
                        flow_list[f]['out_port_old'] = out_port_construct(old_path, len(old_path)*[1])
                        flow_list[f]['in_port_old'] = out_port_construct(old_path, len(old_path)*[2])
                        flow_list[f]['new_path'] = new_path
                        flow_list[f]['out_port_new'] = out_port_construct(new_path, len(new_path)*[1])
                        flow_list[f]['in_port_new'] = out_port_construct(new_path, len(new_path)*[2])


    #[out,maxlen]=getShortPaths(g)
    #path_translate(out, flow_list)
    #f=open(outname+".new","w")
    #f.write(out)
    #f.close()
    return {'flow_list': flow_list, 'nnode': nnode, 'nedge': nedge}


def path_translate(out, flow_list):
    #flow_list = copy.deepcopy(flow_list_org)

    for x in out.split():
        path = x.split(',')
        for i in range(len(path)):
            path[i] = int(path[i])
        if len(path) > 1:
            flow = {}
            flow['ipv4_dst'] = '10.0.0.%d' %path[len(path)-1]
            flow['ipv4_src'] = '10.0.0.%d' %path[0]
            f = match_parse(flow)
            if f not in flow_list.keys():
                flow_list[f] = {}
                flow_list[f]['flow'] = flow
                flow_list[f]['old_path'] = path
                flow_list[f]['out_port_old'] = out_port_construct(path, len(path)*[1])
                flow_list[f]['in_port_old'] = out_port_construct(path, len(path)*[2])
                flow_list[f]['new_path'] = path
                flow_list[f]['out_port_new'] = out_port_construct(path, len(path)*[1])
                flow_list[f]['in_port_new'] = out_port_construct(path, len(path)*[2])

            else:
                flow_list[f]['new_path'] = path
                flow_list[f]['out_port_new'] = out_port_construct(path, len(path)*[3])
                flow_list[f]['in_port_new'] = out_port_construct(path, len(path)*[4])


    return True





if __name__ == '__main__':
    K = 6
    filepath = os.getcwd() + '/flow_update_%d.tsv' %K

    #for i in range(100):
        #test_measure('Abilene.graphml')
    #for i in range(100):
        #test_measure('Quest.graphml')
    #for i in range(100):

        #test_measure('Geant2012.graphml')
    #for i in range(100):
        #test_measure('Bellcanada.graphml')
    #for i in range(100):
        #test_measure('Internode.graphml')
    #for i in range(100):
    test_measure('Dfn.graphml', int(sys.argv[1]))
        #test_measure('Arnes.graphml')




    # flow_list = gen('Abilene.graphml')
    #
    #
    #
    # state_cur = net()
    # state_cur = state_init(20, state_cur)
    #
    # #proto = 3
    # clk = 8 # > 1
    # priority = 8
    # #CLI(fat_tree_net)
    #
    # for i in flow_list.keys():
    #     flow = flow_list[i]['flow']
    #     old_path = flow_list[i]['old_path']
    #     new_path = flow_list[i]['new_path']
    #     out_port_old = flow_list[i]['out_port_old']
    #     out_port_new = flow_list[i]['out_port_new']
    #     in_port_old = flow_list[i]['in_port_old']
    #     in_port_new = flow_list[i]['in_port_new']
    #
    #     #path_deploy_runtime(K, old_path, new_path, flow, state_cur, prt, in_port, out_port, clock)
    #     deploy_ret = path_deploy_runtime([], old_path, flow, state_cur, priority, {}, {}, out_port_old, clk)
    #
    #     state_cur = deploy_ret['state']
    #     clk = deploy_ret['clk']

    #flow_list1 = get_flow_list_new(filepath, K, 0, 100)
    #flow_list2 = get_flow_list_new(filepath, K, 0, 20)

    #test_measure(K, 20, flow_list1)
    #flow_list1 = get_flow_list_new(filepath, K, 0, 100)
    #for i in range(5):
    #    num = (i+1)*20
        #flow_list2 = get_flow_list_new(filepath, K, 0, num)
    #    for j in range(100):
    #        test_measure(K, num, flow_list1)
