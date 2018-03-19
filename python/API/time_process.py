import matplotlib.pyplot as plt
from lmfit import  Model
from numpy import sqrt, pi, exp

def draw_plot(filepath, labels, ampi, ceni, widi, color=None, marks=None):
    flow_num = 30

    fp = open(filepath, 'r')
    cxt = fp.readlines()
    bid_list = {}
    time_point = {}
    time_point[0] = 80 + 32 + flow_num * 5
    rule_num = 0
    for ln in cxt:
        if 'bundle add' in ln:
            bid = int(ln.split()[3])
            cmd = int(ln.split()[5])
            if cmd == 0:
                if bid not in bid_list.keys():
                    bid_list[bid] = 1
                else:
                    bid_list[bid] = bid_list[bid] + 1
            if cmd == 4:
                if bid not in bid_list.keys():
                    bid_list[bid] = -1
                else:
                    bid_list[bid] = bid_list[bid] - 1


    ct = 0
    for ln in cxt:
        if ln.startswith('begin time'):
            sec = float(ln.split()[2])
            micro = float(ln.split()[3])
            basic_time = sec + micro/1000000
        if 'rules commit' in ln:
            sec = float(ln.split()[5])
            micro = float(ln.split()[6])
            bid = int(ln.split()[1])
            cur_time = sec + micro/1000000 - basic_time
            if bid not in bid_list:
                print bid
            else:
                if cur_time > 0:
                    time_point[cur_time] = bid_list[bid]
                else:
                    ct = ct + 1
        if 'del prt' in ln:
            sec = float(ln.split()[12])
            micro = float(ln.split()[13])
            cur_time = sec + micro/1000000 - basic_time
            time_point[cur_time] = -1

    print ct
    print time_point
    x_list = []
    y_list = []
    for i in time_point.keys():
        x_list.append(i)
    x_list.sort()
    for i in x_list:
        rule_num = rule_num + time_point[i]
        y_list.append(rule_num)
    print max(x_list)
    print max(y_list)

    gmodel = Model(gaussian)
    result = gmodel.fit(y_list, x=x_list, amp=ampi, cen=ceni, wid=widi)
    plt.plot(x_list, y_list, color+marks, label=labels, markersize=10, linewidth=8)
    #plt.plot(x_list, result.best_fit, color+marks, label=labels, markersize=10, linewidth=8)

def gaussian(x, amp, cen, wid):
    "1-d gaussian: gaussian(x, amp, cen, wid)"
    return (amp/(sqrt(2*pi)*wid)) * exp(-(x-cen)**2 /(2*wid**2)) + 262



if __name__ == '__main__':
    filepath = "/home/shengliu/Workspace/mininet/haha/API/result/snapshot/debug_scc_30.txt"
    draw_plot(filepath, 'SCC', 25, 1.8, 0.2, 'r', 'D')
    filepath = "/home/shengliu/Workspace/mininet/haha/API/result/snapshot/debug_cu_30.txt"
    draw_plot(filepath, 'CU', 120, 1.8, 0.1, 'b', 'o')
    filepath = "/home/shengliu/Workspace/mininet/haha/API/result/snapshot/debug_coco_30.txt"
    draw_plot(filepath, 'COCO', 100, 5, 4.5, 'g', '*')
    plt.xlabel("time [s]", fontsize=20)
    plt.ylabel("the total number of rules", fontsize=20)
    plt.legend()
    plt.show()
