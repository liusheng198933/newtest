from test_main import delay_generate

def get_delay(num):
    rule_set = {}
    for i in range(num):
        rule_set[i] = i
    c = 0
    for t in range(100000):
        delay_list = delay_generate(rule_set)
        ls = []
        for i in delay_list.keys():
            ls.append(delay_list[i])
        c = c + max(ls)
    return float(c)/100000

if __name__ == '__main__':
    rule_set = {}
    rule_set['1'] = 1
    rule_set['2'] = 2
    rule_set['3'] = 3
    rule_set['4'] = 4

    rule_set2 = {}
    rule_set2['1'] = 1
    rule_set2['2'] = 2
    rule_set2['3'] = 3
    rule_set2['4'] = 4
    rule_set2['5'] = 5


    print delay_generate(rule_set)

    c = 0
    for t in range(100000):
        delay_list = delay_generate(rule_set)
        ls = []
        for i in delay_list.keys():
            ls.append(delay_list[i])
        c = c + max(ls)
    print float(c)/100000


    c = 0
    for t in range(100000):
        delay_list = delay_generate(rule_set2)
        ls = []
        for i in delay_list.keys():
            ls.append(delay_list[i])
        c = c + max(ls)
    print float(c)/100000

    delay_coco = get_delay(2) * 2 + get_delay(3)
    delay_cu = get_delay(4)*2 + get_delay(1)
    delay_scc = get_delay(3) + get_delay(1)

    print delay_coco
    print delay_cu
    print delay_scc
