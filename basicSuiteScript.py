import numpy as np
import os   
from rixSuiteConfig import experimentHash

##from mfxRixSuiteConfig import *

if os.getenv("foo") == "1":
    print("psana1")
    from psana1Base import PsanaBase
else:
    print("psana2")
    from psana2Base import PsanaBase

def sortArrayByList(a, data):
    return [x for _, x in sorted(zip(a, data), key=lambda pair: pair[0])]

class BasicSuiteScript(PsanaBase):
    def __init__(self, analysisType="scan"):
        super().__init__()
        ##print("in BasicSuiteScript, inheriting from PsanaBase, type is psana%d" %(self.psanaType))

        self.gainModes = {"FH": 0, "FM": 1, "FL": 2, "AHL-H": 3, "AML-M": 4, "AHL-L": 5, "AML-L": 6}
        self.ePix10k_cameraTypes = {1: "Epix10ka", 4: "Epix10kaQuad", 16: "Epix10ka2M"}
        self.camera = 0
        ##self.outputDir = '/sdf/data/lcls/ds/rix/rixx1003721/results/%s/' %(analysisType)
        self.outputDir = "../%s/" % (analysisType)
        ##self.outputDir = '/tmp'

        self.className = self.__class__.__name__

        try:
            self.location = experimentHash["location"]
        except Exception:
            pass
        try:
            self.exp = experimentHash["exp"]
        except Exception:
            pass
        try:
            ##if True:
            self.ROIfileNames = experimentHash["ROIs"]
            self.ROIs = []
            for f in self.ROIfileNames:
                self.ROIs.append(np.load(f + ".npy"))
            try:  ## dumb code for compatibility or expectation
                self.ROI = self.ROIs[0]
            except Exception:
                pass
        ##if False:
        except Exception:
            print("had trouble finding", self.ROIfileNames)
            self.ROI = None
            self.ROIs = None
        try:
            self.singlePixels = experimentHash["singlePixels"]
        except Exception:
            self.singlePixels = None
        try:
            self.regionSlice = experimentHash["regionSlice"]
        except Exception:
            self.regionSlice = None
        if self.regionSlice is not None:
            self.sliceCoordinates = [
                [self.regionSlice[0].start, self.regionSlice[0].stop],
                [self.regionSlice[1].start, self.regionSlice[1].stop],
            ]
            sc = self.sliceCoordinates
            self.sliceEdges = [sc[0][1] - sc[0][0], sc[1][1] - sc[1][0]]

        try:
            self.fluxSource = experimentHash["fluxSource"]
            try:
                self.fluxChannels = experimentHash["fluxChannels"]
            except Exception:
                self.fluxChannels = range(8, 16)  ## wave8
            try:
                self.fluxSign = experimentHash["fluxSign"]
            except Exception:
                self.fluxSign = 1
        except Exception:
            self.fluxSource = None

    def setROI(self, roiFile=None, roi=None):
        """Call with both file name and roi to save roi to file and use,
        just name to load,
        just roi to set for current job"""
        if roiFile is not None:
            if roi is None:
                self.ROIfile = roiFile
                self.ROI = np.load(roiFile)
                return
            else:
                np.save(roiFile, roi)
        self.ROI = roi

    def commonModeCorrection(self, frame, arbitraryCut=1000):
        ## this takes a 2d frame
        ## cut keeps photons in common mode - e.g. set to <<1 photon

        ##rand = np.random.random()
        for r in range(self.detRows):
            colOffset = 0
            ##for b in range(0, self.detNbanks):
            for b in range(0, 2):
                try:
                    rowCM = np.median(
                        frame[r, colOffset : colOffset + self.detColsPerBank][
                            frame[r, colOffset : colOffset + self.detColsPerBank] < arbitraryCut
                        ]
                    )
                    ##if r == 280 and rand > 0.999:
                    ##print(b, frame[r, colOffset:colOffset + self.detColsPerBank], \
                    # rowCM, rowCM<arbitraryCut-1, rowCM*(rowCM<arbitraryCut-1))
                    ##frame[r, colOffset:colOffset + self.detColsPerBank] -= rowCM*(rowCM<arbitraryCut-1)
                    frame[r, colOffset : colOffset + self.detColsPerBank] -= rowCM
                    ##if r == 280 and rand > 0.999:
                    ##print(frame[r, colOffset:colOffset + self.detColsPerBank], \
                    # np.median(frame[r, colOffset:colOffset + self.detColsPerBank]))
                except Exception:
                    rowCM = -666
                    print("rowCM problem")
                    print(frame[r, colOffset : colOffset + self.detColsPerBank])
                colOffset += self.detColsPerBank
        return frame


if __name__ == "__main__":
    bSS = BasicSuiteScript()
    print("have built a BasicSuiteScript")
    bSS.setupPsana()
    evt = bSS.getEvt()
    print(dir(evt))
