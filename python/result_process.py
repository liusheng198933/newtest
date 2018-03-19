import sys
import os

if __name__ == '__main__':
    cwd = os.getcwd()
    pattern = 'normal'
    #pattern = 'link'
    filepath = cwd + '/result/%s/run_result_%d.txt' %(pattern, int(sys.argv[1]))

    #filepath = '/home/shengliu/Workspace/mininet/haha/API/result.txt'
    fp = open(filepath)
    content = fp.readlines()

    result_dic = {}
    for x in content:
        if x:
            t = x.strip().split()
            pkt_rate = int(t[3])
            sent_num = int(t[5])
            recv_num = int(t[7])
            if pkt_rate not in result_dic.keys():
                result_dic[pkt_rate] = {}
                result_dic[pkt_rate]['sent'] = [sent_num]
                result_dic[pkt_rate]['recv'] = [recv_num]
                #result_dic[pkt_rate]['loss'] = [1 - float(recv_num) / sent_num]
                result_dic[pkt_rate]['loss'] = [(sent_num - recv_num)]
            else:
                result_dic[pkt_rate]['sent'].append(sent_num)
                result_dic[pkt_rate]['recv'].append(recv_num)
                #result_dic[pkt_rate]['loss'].append(1 - float(recv_num) / sent_num)
                result_dic[pkt_rate]['loss'].append((sent_num - recv_num))

    for i in result_dic.keys():
        print 'pkt rate: %d' %i
        print float(sum(result_dic[i]['loss'])) / len(result_dic[i]['loss'])

    fp.close()

    xline = [600, 700, 800, 900, 1000]
    #xline = [1000]
    filepath = cwd + '/result/%s/result.txt' %pattern
    fp = open(filepath, 'a+')
    for i in range(len(xline)):
        fp.write('%f ' %(float(sum(result_dic[xline[i]]['loss'])) / len(result_dic[xline[i]]['loss'])))
    fp.write('\n')
    fp.close()

    #print float(recv_sum)/sent_sum
