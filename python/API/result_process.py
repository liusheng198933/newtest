import sys

if __name__ == '__main__':
    filepath = '/home/shengliu/Workspace/mininet/haha/API/ping_result_%d.txt' %(int(sys.argv[1]))
    #filepath = '/home/shengliu/Workspace/mininet/haha/API/result.txt'
    fp = open(filepath)
    content = fp.readlines()
    result_dic = {}
    for x in content:
        if x:
            t = x.strip().split()
            pkt_rate = int(t[3].strip(','))
            sent_num = int(t[5].strip(','))
            recv_num = int(t[7].strip(','))
            if pkt_rate not in result_dic.keys():
                result_dic[pkt_rate] = {}
                result_dic[pkt_rate]['sent'] = [sent_num]
                result_dic[pkt_rate]['recv'] = [recv_num]
                result_dic[pkt_rate]['loss'] = [1 - float(recv_num) / sent_num]
            else:
                result_dic[pkt_rate]['sent'].append(sent_num)
                result_dic[pkt_rate]['recv'].append(recv_num)
                result_dic[pkt_rate]['loss'].append(1 - float(recv_num) / sent_num)

    for i in result_dic.keys():
        print 'pkt rate: %d' %i
        print sum(result_dic[i]['loss']) / len(result_dic[i]['loss'])

    fp.close()

    xline = [4000, 5000, 6000, 7000, 8000, 9000, 10000, 11000]
    filepath = '/home/shengliu/Workspace/mininet/haha/API/result.txt'
    fp = open(filepath, 'a+')
    for i in range(len(xline)):
        fp.write('%f ' %(sum(result_dic[xline[i]]['loss']) / len(result_dic[xline[i]]['loss'])))
    fp.write('\n')
    fp.close()

    #print float(recv_sum)/sent_sum
