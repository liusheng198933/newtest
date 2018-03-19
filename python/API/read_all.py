def merge_file():
    all_cxt = []
    for i in range(200):
        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug_%d.txt" %i
        f = open(filepath, 'r')
        cxt = f.readlines()
        all_cxt = all_cxt + cxt
        f.close()

    #print len(all_cxt)

    filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug.txt"
    f = open(filepath, 'a+')
    for i in all_cxt:
        f.write(i)
    f.close()


if __name__ == '__main__':

    all_cxt = []
    for i in range(200):
        filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug_%d.txt" %i
        #filepath = "/home/shengliu/Workspace/mininet/haha/API/result/snapshot/coco_370/debug_%d.txt" %i
        f = open(filepath, 'r')
        cxt = f.readlines()
        all_cxt = all_cxt + cxt
        f.close()

    print len(all_cxt)

    filepath = "/home/shengliu/Workspace/mininet/haha/API/time/debug.txt"
    #filepath = "/home/shengliu/Workspace/mininet/haha/API/result/snapshot/coco_370/debug.txt"
    f = open(filepath, 'a+')
    for i in all_cxt:
        f.write(i)
    f.close()
