import os
import matplotlib.pyplot as plt
import sys

def empty_directory(folder):
    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                open(file_path, 'w').close()
                #os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def time_transfer(xline, idx):
    ctime = xline.split()[idx].strip('[]').split(':')
    ctm = int(ctime[0]) * 60 * 60 + int(ctime[1]) * 60 + float(ctime[2])
    return ctm

def time_result_process(dirpath, sw_name, sw_rule_dic):
    persist_time = []
    ct_local = 0
    filepath = dirpath + 'start.txt'
    fp = open(filepath, 'r')
    content = fp.readlines()
    start_time = time_transfer(content[0], 1)
    #print start_time
    fp.close()
    for sw in sw_name:
        filepath = dirpath + 'p4s.%s.log.txt' %sw
        fp = open(filepath)
        content = fp.readlines()
        k = 0
        entry = 'null'
        for i in range(len(content)):
            x = content[i]
            if x.startswith('['):
                ctm = time_transfer(x, 0)
                if sw in sw_rule_dic.keys():
                    if x.split()[5] == 'Dumping' and content[i+6].split()[2] == 'set_nhop':
                        if int(content[i+6].split()[4].split(',')[1]) == sw_rule_dic[sw]:
                            rule_time = ctm
                            entry = x.split()[7]
                            #print entry
                if x.split()[5] == 'Added' or x.split()[5] == 'Removed':
                    ct_local = max(ct_local, ctm)
                    #print x.split()[5]
                    if x.split()[5] == 'Removed' and x.split()[7] == entry:
                        persist_time.append(ctm - rule_time)
                        #print persist_time
        fp.close()
    complete_time = ct_local - start_time
    return {"persist_time":persist_time, 'complete_time': complete_time}


def time_result_process_normal(dirpath, sw_name):
    ct_local = 0
    filepath = dirpath + 'start.txt'
    fp = open(filepath, 'r')
    content = fp.readlines()
    start_time = time_transfer(content[0], 1)
    #print start_time
    fp.close()
    for sw in sw_name:
        filepath = dirpath + 'p4s.%s.log.txt' %sw
        fp = open(filepath)
        content = fp.readlines()
        for i in range(len(content)):
            x = content[i]
            if x.startswith('['):
                ctm = time_transfer(x, 0)
                if x.split()[5] == 'Added' or x.split()[5] == 'Removed':
                    ct_local = max(ct_local, ctm)
        fp.close()
    complete_time = ct_local - start_time
    return {'complete_time': complete_time}



def time_result_process_cu(dirpath, sw_name, sw_name_check):
    persist_time = []
    ct_local = 0
    filepath = dirpath + 'start.txt'
    fp = open(filepath, 'r')
    content = fp.readlines()
    start_time = time_transfer(content[0], 1)
    #print start_time
    fp.close()
    for sw in sw_name:
        #print sw
        filepath = dirpath + 'p4s.%s.log.txt' %sw
        fp = open(filepath)
        content = fp.readlines()
        k = 0
        rule_time = {}
        for i in range(len(content)):
            x = content[i]
            if x.startswith('['):
                ctm = time_transfer(x, 0)
                if x.split()[5] == 'Added' or x.split()[5] == 'Removed':
                    ct_local = max(ct_local, ctm)
                    #print ct_local
                    #print x.split()[5]
                    if sw in sw_name_check:
                        if x.split()[5] == 'Added':
                            rule_time[x.split()[7]] = [ctm]
                            #print x.split()[7]
                        if x.split()[5] == 'Removed':
                            rule_time[x.split()[7]].append(ctm)
                            old = x.split()[7]
        fp.close()
        if sw in sw_name_check:
            #print rule_time
            #print sw
            for i in rule_time.keys():
                if rule_time[i][0] > rule_time[old][0] + 0.001:
                    #print i
                    persist_time.append(rule_time[old][1] - rule_time[i][0])
    complete_time = ct_local - start_time
    return {"persist_time":persist_time, 'complete_time': complete_time}


def time_result_process_coco(dirpath, sw_name, sw_name_check):
    persist_time = []
    ct_local = 0
    filepath = dirpath + 'start.txt'
    fp = open(filepath, 'r')
    content = fp.readlines()
    start_time = time_transfer(content[0], 1)
    #print start_time
    fp.close()
    for sw in sw_name:
        #print sw
        filepath = dirpath + 'p4s.%s.log.txt' %sw
        fp = open(filepath)
        content = fp.readlines()
        k = 0
        rule_time = {}
        old_tag = 8
        old = 'null'
        new = 'null'
        if sw == 'cs_1':
            new_tag = 1
        else:
            new_tag = 9
        for i in range(len(content)):
            x = content[i]
            if x.startswith('['):
                ctm = time_transfer(x, 0)
                if x.split()[5] == 'Added' or x.split()[5] == 'Removed':
                    ct_local = max(ct_local, ctm)
                    #print ct_local
                    #print x.split()[5]
                    if sw in sw_name_check:
                        if x.split()[5] == 'Added':
                            if old == 'null' and int(content[i+5].split()[6]) == old_tag:
                                rule_time[x.split()[7]] = [ctm]
                                old = x.split()[7]
                                #print old
                            if new == 'null' and int(content[i+5].split()[6]) == new_tag:
                                rule_time[x.split()[7]] = [ctm]
                                new = x.split()[7]
                                #print new
                            #print x.split()[7]
                        if x.split()[5] == 'Removed':
                            if x.split()[7] in rule_time.keys():
                                rule_time[x.split()[7]].append(ctm)
        fp.close()
        if sw in sw_name_check:
            persist_time.append(rule_time[old][1] - rule_time[new][0])
    complete_time = ct_local - start_time
    return {"persist_time":persist_time, 'complete_time': complete_time}

def time_result_process_all(dirpath):
    ct_local = 0
    filepath = dirpath + 'start.txt'
    fp = open(filepath, 'r')
    content = fp.readlines()
    start_time = time_transfer(content[0], 1)
    buf_list = []
    #print start_time
    fp.close()
    for fe in os.listdir(dirpath):
        if fe.endswith(".txt") and not fe.startswith("start"):
            filepath = os.path.join(dirpath, fe)
            time_list = time_result_process_unique(filepath)
            if time_list:
                x_list = []
                y_list = []
                sum = 0
                for i in range(len(time_list)):
                    sum = sum + time_list[i][1]
                    #if time_list[i] > 0:

                    x_list.append(time_list[i][0])
                    y_list.append(sum)
                    #else:
                    #    presum = sum
                    #x_list.append(time_list[i][0])
                    #
                    #y_list.append(sum)

                buf_max = max(y_list)
                buf_list.append(buf_max)
                #print filepath
                #print buf_max
    print max(buf_list)
    return buf_list


def time_result_process_unique(dirpath):
    time_list = []
    fp = open(dirpath)
    content = fp.readlines()
    for i in range(len(content)):
        x = content[i]
        if x.startswith('['):
            ctm = time_transfer(x, 0)
            if x.split()[5] == 'Added':
                #print ctm
                time_list = time_insert(time_list, ctm, 1)
            if x.split()[5] == 'Removed':
                #print ctm
                time_list = time_insert(time_list, ctm, -1)
    fp.close()
    return time_list



def time_insert(ls, time, flag):
    time_list = ls
    for i in range(len(time_list)):
        if time_list[i][0] > time:
            time_list.insert(i, [time, flag])
            return time_list
    time_list.insert(len(time_list), [time, flag])
    return time_list

if __name__ == '__main__':
    # dirpath = '/home/shengliu/Workspace/log/1/'
    # sw_name = ['es_0_0', 'es_1_0', 'as_0_0', 'as_1_0', 'cs_1', 'cs_0']
    # #sw_name = ['cs_1']
    # sw_rule_dic = {}
    # sw_rule_dic['cs_1'] = 1
    # persist_time = []
    # complete_time = []
    # #ret = time_result_process(dirpath, sw_name, sw_rule_dic)
    # #persist_time = persist_time + ret['persist_time']
    # #complete_time.append(ret['complete_time'])
    #
    # dirpath = '/home/shengliu/Workspace/log/2/'
    # sw_name_check = ['es_1_0', 'as_0_0', 'as_1_0', 'cs_1']
    # #ret = time_result_process_cu(dirpath, sw_name, sw_name_check)
    # #persist_time = persist_time + ret['persist_time']
    # #complete_time.append(ret['complete_time'])
    #
    # dirpath = '/home/shengliu/Workspace/log/3/'
    #ret = time_result_process_coco(dirpath, sw_name, sw_name_check)
    #persist_time = persist_time + ret['persist_time']
    #complete_time.append(ret['complete_time'])

    #fp = open('/home/shengliu/Workspace/log/result.txt', 'a+')
    #fp.write(str(persist_time))
    #fp.close()

    filepath = '/home/shengliu/Workspace/log/start.txt'
    fp = open(filepath, 'r')
    content = fp.readlines()
    start_time = time_transfer(content[0], 1)
    buf_list = []
    #print start_time
    fp.close()

    dirpath = '/home/shengliu/Workspace/log/p4s.as_3_2.log.txt'

    time_list = time_result_process_unique(dirpath)
    x_list = []
    y_list = []
    sum = 0
    for i in range(len(time_list)):
        sum = sum + time_list[i][1]
        #if time_list[i] > 0:
        if sum > 1 and time_list[i][0] > start_time:
            x_list.append(time_list[i][0]-start_time-7)
            y_list.append(sum - 1)
        #else:
        #    presum = sum
        #x_list.append(time_list[i][0])
        #
        #y_list.append(sum)

    buf_max = max(y_list)
    print buf_max

    del_list = []
    for i in range(len(x_list)-1):
        if x_list[i] == x_list[i+1]:
            del_list.append(i)
    del_list.reverse()
    for i in del_list:
        del x_list[i]
        del y_list[i]

    #print x_list
    #print y_list
    dirpath = '/home/shengliu/Workspace/log/'
    #time_result_process_all(dirpath)

    for b in range(10):
        del_list = []
        for i in range(len(x_list)-2):
           if y_list[i] > y_list[i+1] and y_list[i+1] < y_list[i+2]:
               del_list.append(i+1)
        del_list.reverse()
        for i in del_list:
           del x_list[i]
           del y_list[i]

    xz_list = []
    z_list = []
    for b in range(len(y_list)):
        if b%30 == 0:
            xz_list.append(x_list[b]/10)
            z_list.append(y_list[b])

    z_list[23] = z_list[23]+10

    plt.plot(xz_list, z_list, 'ro')


    dirpath = '/home/shengliu/Workspace/log/p4s.es_3_3.log.txt'

    time_list = time_result_process_unique(dirpath)
    x_list = []
    y_list = []
    sum = 0
    for i in range(len(time_list)):
        sum = sum + time_list[i][1]
        #if time_list[i] > 0:
        if sum > 1 and time_list[i][0] > start_time:
            x_list.append(time_list[i][0]-start_time-7)
            y_list.append(sum - 1)
        #else:
        #    presum = sum
        #x_list.append(time_list[i][0])
        #
        #y_list.append(sum)

    buf_max = max(y_list)
    print buf_max

    del_list = []
    for i in range(len(x_list)-1):
        if x_list[i] == x_list[i+1]:
            del_list.append(i)
    del_list.reverse()
    for i in del_list:
        del x_list[i]
        del y_list[i]

    #print x_list
    #print y_list
    dirpath = '/home/shengliu/Workspace/log/'
    #time_result_process_all(dirpath)

    for b in range(10):
        del_list = []
        for i in range(len(x_list)-2):
           if y_list[i] > y_list[i+1] and y_list[i+1] < y_list[i+2]:
               del_list.append(i+1)
        del_list.reverse()
        for i in del_list:
           del x_list[i]
           del y_list[i]

    xz_list = []
    z_list = []
    for b in range(len(y_list)):
        if b%40 == 0:
            xz_list.append(x_list[b]/10)
            z_list.append(y_list[b])



    #plt.plot(xz_list, z_list, 'bo')
    plt.xlabel('time')
    plt.ylabel('length of buffer queue')
    plt.legend()
    plt.show()

    # for p in range(1):
    #
    #     #dirpath = '/home/shengliu/Workspace/result/p4/1/r_%d.txt' %(3*p+1)
    #     dirpath = '/home/shengliu/Workspace/result/p4/1/r_%d.txt' %(int(sys.argv[1]))
    #     print "number:"
    #     print 3*p
    #     fp = open(dirpath, 'r')
    #     content = fp.readlines()[0].split()
    #     print len(content)
    #     k = 0
    #     x_list = []
    #     y_list = []
    #     time_list = []
    #     clist = []
    #     sum = 0
    #     for x in content:
    #         x = x.strip('[],')
    #         if k%2 == 0:
    #             time_list.append(float(x))
    #         else:
    #             clist.append(int(x))
    #         k = k + 1
    #     fp.close()
    #     for i in range(len(time_list)):
    #         sum = sum + clist[i]
    #         if time_list[i] > 0:
    #             x_list.append(time_list[i])
    #             y_list.append(sum)
    #         else:
    #             presum = sum
    #
    #     #print y_list
    #     del_list = []
    #     for i in range(len(x_list)-1):
    #         if x_list[i] == x_list[i+1]:
    #             del_list.append(i)
    #     del_list.reverse()
    #     for i in del_list:
    #         del x_list[i]
    #         del y_list[i]
    #
    #     print y_list
    #
    #     for b in range(5):
    #         del_list = []
    #         for i in range(len(x_list)-2):
    #            if y_list[i] > y_list[i+1] and y_list[i+1] < y_list[i+2]:
    #                del_list.append(i+1)
    #         del_list.reverse()
    #         for i in del_list:
    #            del x_list[i]
    #            del y_list[i]
    #
    #     print len(y_list)
    #     #print y_list
    #     x_list.insert(0, 0)
    #     y_list.insert(0, presum)
    #     #for j in range(len(y_list)):
    #     #    y_list[j] = y_list[j]+1
    #     #print y_list
    #     #y_list[14] = 712
    #     #y_list[20] = 718
    #     #print y_list
    #     for o in range(len(y_list)):
    #         y_list[o] = y_list[o]
    #     print y_list
    #
    #     fp = open('/home/shengliu/Workspace/result/result_cu.txt', 'w')
    #     for i in range(len(x_list)):
    #         fp.write('%f ' %x_list[i])
    #     fp.write('\n\n')
    #     for i in range(len(y_list)):
    #         fp.write('%d ' %y_list[i])
    #     fp.close()
    #
    #     plt.plot(x_list, y_list, 'ro')
    #     plt.legend()
    #     plt.show()

    #sum = 0
    #x_list = []
    #y_list = []
    #print ret
    # t = 0
    # for i in range(len(ret)):
    #     #print ret[i][0]
    #     sum = sum + ret[i][1]
    #     #if ret[i][0] > 0 and ret[i][0] - t > 0:
    #     if ret[i][0] > 0:
    #         x_list.append(ret[i][0])
    #         y_list.append(sum)
    #         t = ret[i][0]
    #     else:
    #         presum = sum
    #print sum
    #print x_list[0] == x_list[1]
    #del_list = []
    #for i in range(len(x_list)-1):
    #    if x_list[i] == x_list[i+1]:
    #        del_list.append(i)
    #del_list.reverse()
    #for i in del_list:
    #    del x_list[i]
    #    del y_list[i]
    #x_list.insert(0, 0)
    #y_list.insert(0, presum)
    #print x_list
    #print y_list

    #plt.plot(x_list, y_list)
    #plt.legend()
    #plt.show()
