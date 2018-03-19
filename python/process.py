import networkx as nx
import sys
from random import randint
def getShortPaths(g):
    paths=dict(nx.all_pairs_shortest_path(g))
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
def gen(filename):
    g=(nx.read_graphml(filename))
    nnode=len(list(g.nodes))
    nedge=len(list(g.edges))
    #print len(list(g.edges))
    #g=g.to_directed()
    [out,maxlen]=getShortPaths(g)
    filename=filename.replace(".graphml","")
    outname=filename+"_"+str(nnode)+"_"+str(nedge)+"_"+str(maxlen)
    f=open(outname+".old","w")
    f.write(out)
    f.close()
    edges=list(g.edges)
    edge=edges[randint(0,len(edges)-1)]
    g.remove_edge(*edge)
    [out,maxlen]=getShortPaths(g)
    f=open(outname+".new","w")
    f.write(out)
    f.close()


gen(sys.argv[1])
