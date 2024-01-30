import numpy as np
from scipy.stats import binned_statistic

def makeProfile(x, y, bins, range=None, spread=False):
    ## NaN for empty bins are suppressed
    ## using mean root(N) for non-empty bins to calculate 0 var weights
    ##
    ## spread=True to return standard deviation instead of standard error

    meansObj = binned_statistic(x, [y, y**2], bins=bins, range=range, statistic='mean')
    means, means2 = meansObj.statistic
    countsObj = binned_statistic(x, [y, y**2], bins=bins, range=(0,1), statistic='count')
    bin_N = countsObj.statistic
    yErr = np.sqrt(means2 - means**2)
    if not spread:
        root_N = np.sqrt(bin_N)
        root_N[root_N==0] = root_N[root_N>0].mean()
        yErr = yErr/root_N
        ##yErr = yErr.clip(0, 6666666.)
    bin_edges = means_result.bin_edges
    bin_centers = (bin_edges[:-1] + bin_edges[1:])/2.
    usefulBins = bin_N>0
    return bin_centers[usefulBins], means[usefulBins], yErr[usefulBins]

def plotProfile(x, y, yErr):
    plt.errorbar(x=x, y=y, yerr=yErr, linestyle='none', marker='.')

def selectedClusters(clusters, row, col, lowEnerygCut, highEnergyCut, nPixelCut=4, isSquare=1):
    pass

def goodClusters(clusters, row, col, nPixelCut=4, isSquare=None):
    ##print(clusters)
    pixelRowCol = np.bitwise_and((clusters[:,:,1] == row),
                                 (clusters[:,:,2] == col))
    if isSquare is None:
        small = clusters[:,:,3]<nPixelCut
    else:
        small = np.bitwise_and((clusters[:,:,3]<nPixelCut), (clusters[:,:,4]==isSquare))
    return clusters[np.bitwise_and(small, pixelRowCol)]

def getClusterEnergies(clusters):
    ##print(clusters)
    return clusters[:, 0]
