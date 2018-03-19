import numpy as np
import matplotlib.pyplot as plt

"""
# some fake data
data = np.random.normal(150, 50, 1000)
# evaluate the histogram
values, base = np.histogram(data, bins=40)
#evaluate the cumulative
cumulative = np.cumsum(values)
# plot the cumulative function
plt.plot(base[:-1], cumulative, c='blue')

plt.show()
"""
def cdfplot(path):
    data = np.loadtxt(path)

# Choose how many bins you want here
    data_size=len(data)

    # Set bins edges
    data_set=sorted(set(data))
    bins=np.append(data_set, data_set[-1]+1)

    # Use the histogram function to bin the data
    counts, bin_edges = np.histogram(data, bins=bins, density=False)

    counts=counts.astype(float)/data_size

    # Find the cdf
    cdf = np.cumsum(counts)
    return {'cdf': cdf, 'bin': bin_edges[0:-1]}


if __name__ == '__main__':
    # Plot the cdf
    gf = 'matu'
    scc, = plt.plot(cdfplot('%s_scc.txt' %gf)['bin'], cdfplot('%s_scc.txt' %gf)['cdf'], linestyle='--', marker="o", color='b', label='SCC')
    cu, = plt.plot(cdfplot('%s_cu.txt' %gf)['bin'], cdfplot('%s_cu.txt' %gf)['cdf'], linestyle='--', marker="o", color='r', label='CU')
    coco, = plt.plot(cdfplot('%s_coco.txt' %gf)['bin'], cdfplot('%s_coco.txt' %gf)['cdf'], linestyle='--', marker="o", color='g', label='COCONUT')
    plt.legend(handles=[scc, cu, coco], loc=2)
    plt.ylim((0,1))
    plt.ylabel("CDF")
    plt.xlabel("Time (ms)")
    plt.grid(True)

    plt.show()
