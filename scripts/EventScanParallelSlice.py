from basicSuiteScript import BasicSuiteScript
from matplotlib.ticker import AutoMinorLocator
from mpi4py import MPI
import numpy as np
import matplotlib.pyplot as plt
import sys
import h5py
import logging

# Setup logging.
# Log file gets appended to each new run, can manually delete for fresh log.
# Could change so makes new unique log each run or overwrites existing log.
logging.basicConfig(
    filename='scan_parallel_slice.log',
    level=logging.INFO, # For full logging set to INFO which includes ERROR logging too
    format='%(asctime)s - %(levelname)s - %(message)s' # levelname is log severity (ERROR, INFO, etc)
)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def sortArrayByList(a, data):
    return [x for _, x in sorted(zip(a, data), key=lambda pair: pair[0])]


class EventScanParallel(BasicSuiteScript):
    def __init__(self):
        super().__init__()

    def plotData(self, data, pixels, eventNumbers, dPulseId, label):
        if "timestamp" in label:
            xlabel = "Timestamp (s)"
        else:
            xlabel = "Event number"

        for i, roi in enumerate(self.ROIs):
            ax = plt.subplot()
            ax.scatter(eventNumbers, data[i], label=self.ROIfileNames[i])
            plt.grid(which="major", linewidth=0.5)
            minor_locator = AutoMinorLocator(5)
            ax.xaxis.set_minor_locator(minor_locator)
            plt.grid(which="minor", linewidth=0.5)
            plt.xlabel(xlabel)
            plt.ylabel("Mean (ADU)")
            plt.grid(which="major", linewidth=0.75)
            minor_locator = AutoMinorLocator(5)
            ax.xaxis.set_minor_locator(minor_locator)
            plt.grid(which="minor", linewidth=0.5)
            fileName = "%s/%s_r%d_c%d_%s_ROI%d.png" % (self.outputDir, self.__class__.__name__, self.run, self.camera, label, i)
            logging.info("Writing plot: " + fileName)
            plt.savefig(fileName)
            plt.clf()

        for i, roi in enumerate(self.ROIs):
            ax = plt.subplot()
            ax.scatter(eventNumbers, data[i], label=self.ROIfileNames[i])
            plt.grid(which="major", linewidth=0.75)
            minor_locator = AutoMinorLocator(5)
            ax.xaxis.set_minor_locator(minor_locator)
            plt.grid(which="minor", linewidth=0.5)
            plt.xlabel(xlabel)
            plt.ylabel("Mean (ADU)")
            plt.legend(loc="upper right")
        fileName = "%s/%s_r%d_c%d_%s_All%d.png" % (self.outputDir, self.__class__.__name__, self.run, self.camera, label, i)
        logging.info("Writing plot: " + fileName)
        plt.savefig(fileName)
        plt.clf()

        for i, p in enumerate(self.singlePixels):
            ax = plt.subplot()
            ax.plot(eventNumbers, pixels[i], ".", ms=1, label=str(p))
            ax.plot(eventNumbers[:-1][dPulseId < 7740], pixels[i][:-1][dPulseId < 7740], "r.", ms=1, label=str(p))
            plt.xlabel(xlabel)
            plt.ylabel("Pixel ADU")
            fileName = "%s/%s_r%d_c%d_%s_pixel%d.png" % (self.outputDir, self.__class__.__name__, self.run, self.camera, label, i)
            logging.info("Writing plot: " + fileName)
            plt.savefig(fileName)
            plt.close()

            ax = plt.subplot()
            ax.hist(pixels[i], 100)
            plt.xlabel("Pixel ADU")
            plt.title("Event scan projection of pixel %d" % (i))
            fileName = "%s/%s_r%d_c%d_%s_pixel%d_hist.png" % (self.outputDir, self.__class__.__name__, self.run, self.camera, label, i)
            logging.info("Writing plot: " + fileName)
            plt.savefig(fileName)
            plt.close()

    # Doesn't work atm b/c undefined functions
    '''
    def analyzeData(self, delays, data, label):
        edge = np.zeros(data.shape[0])
        for m in range(data.shape[1]):
            for r in range(data.shape[2]):
                for c in range(data.shape[3]):
                    d = data[:, m, r, c]
                    # where are these funcs defined?, ignoring from ruff for now
                    p0 = estimateFineScanPars(delays, d) # noqa: F821
                    f = fineScanFunc # noqa: F821
                    coeff, var = curve_fit(f, delays, d, p0=p0) # noqa: F821
                    edge[m, r, c] = coeff[1]
        return edge
    '''

    def analyze_h5(self, dataFile, label):
        data = h5py.File(dataFile)
        ts = data["timestamps"][()]
        pulseIds = data["pulseIds"][()]
        pixels = data["pixels"][()]
        rois = data["rois"][()]

        try:
            bitSlice = data["summedBitSlice"][()]
            fileName = "%s/bitSlice_c%d_r%d_%s.npy" % (self.outputDir, self.camera, self.run, self.exp), np.array(bitSlice)
            logging.info("Writing plot: " + fileName)
            np.save(fileName)
        except Exception as e:
            print(f"An exception occurred: {e}")
            logging.exception(f"An exception occurred: {e}")
            pass

        pulseIds.sort()
        fileName = "%s/pulseIds_c%d_r%d_%s.npy" % (self.outputDir, self.camera, self.run, self.exp)
        logging.info("Writing npy: " + fileName)
        np.save(fileName, np.array(pulseIds))
        dPulseId = pulseIds[1:] - pulseIds[0:-1]

        pixels = sortArrayByList(ts, pixels)
        rois = sortArrayByList(ts, rois)
        ts.sort()
        ts = ts - ts[0]

        self.plotData(np.array(rois).T, np.array(pixels).T, ts, dPulseId, "timestamps" + label)


if __name__ == "__main__":
    esp = EventScanParallel()
    print("have built a" + esp.className + "class")
    logging.info("have built a" + esp.className + "class")

    # Standalone analysis
    if esp.file is not None:
        esp.analyze_h5(esp.file, esp.label)
        print("done with standalone analysis of %s, exiting" % (esp.file))
        logging.info("done with standalone analysis of %s, exiting" % (esp.file))
        sys.exit(0)

    # Parallel processing
    esp.setupPsana()
    fileNameSmallData = "%s/%s_c%d_r%d_n%d.h5" % (esp.outputDir, esp.className, esp.camera, esp.run, size)
    logging.info("Reading in smalldata: " + fileNameSmallData)
    smd = esp.ds.smalldata(filename=fileNameSmallData)

    esp.nGoodEvents = 0
    roiMeans = [[] for i in esp.ROIs]
    pixelValues = [[] for i in esp.singlePixels]
    eventNumbers = []
    bitSliceSum = None
    evtGen = esp.myrun.events()

    # Analyze events
    for nevt, evt in enumerate(evtGen):
        if evt is None:
            continue

        frames = esp.getRawData(evt, gainBitsMasked=True)
        if frames is None:
            continue

        if esp.fakePedestal is not None:
            frames = frames.astype("float") - esp.fakePedestalFrame
            if esp.special is not None and "commonMode" in esp.special:
                frames = np.array([esp.commonModeCorrection(frames[0])])

        eventNumbers.append(nevt)
        for i, roi in enumerate(esp.ROIs):
            m = frames[roi == 1].mean()
            roiMeans[i].append(m)

        for i, roi in enumerate(esp.singlePixels):
            pixelValues[i].append(frames[tuple(esp.singlePixels[i])])

        if esp.fakePedestal is None:
            slice = frames[0][esp.regionSlice]
            sliceView = slice.view(np.uint8).reshape(slice.size, 2)
            r = np.unpackbits(sliceView, axis=1, bitorder="little")[:, ::-1]

            try:
                bitSliceSum += r
            except Exception as e:
                print(f"An exception occurred: {e}")
                logging.exception(f"An exception occurred: {e}")
                bitSliceSum = r.astype(np.uint32)

        smd.event(
            evt,
            timestamps=evt.datetime().timestamp(),
            pulseIds=esp.getPulseId(evt),
            rois=np.array([roiMeans[i][-1] for i in range(len(esp.ROIs))]),
            pixels=np.array([pixelValues[i][-1] for i in range(len(esp.singlePixels))])
        )

        esp.nGoodEvents += 1
        if esp.nGoodEvents % 100 == 0:
            print("n good events analyzed: %d" % (esp.nGoodEvents))
            logging.info("n good events analyzed: %d" % (esp.nGoodEvents))

        if esp.nGoodEvents > esp.maxNevents:
            break

    fileNameMeans = "%s/means_c%d_r%d_%s.npy" % (esp.outputDir, esp.camera, esp.run, esp.exp)
    fileNameEventNumbers = "%s/eventNumbers_c%d_r%d_%s.npy" % (esp.outputDir, esp.camera, esp.run, esp.exp)
    logging.info("Saving npy: " + fileNameMeans)
    logging.info("Saving npy: " + fileNameEventNumbers)
    np.save(fileNameMeans, np.array(roiMeans))
    np.save(fileNameEventNumbers, np.array(eventNumbers))

    if smd.summary and esp.fakePedestal is None:
        allSum = smd.sum(bitSliceSum)
        smd.save_summary({"summedBitSlice": allSum})
    smd.done()
