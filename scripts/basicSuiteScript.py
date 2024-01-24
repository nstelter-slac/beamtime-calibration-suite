import argparse
import numpy as np
import logging
from rixSuiteConfig import experimentHash
from psana2Base import PsanaBase

logger = logging.getLogger(__name__)


class BasicSuiteScript(PsanaBase):
    def __init__(self, analysisType="scan"):
        super().__init__()
        print("in BasicSuiteScript, inheriting from PsanaBase, type is psana%d" %(self.psanaType))
        logger.info("in BasicSuiteScript, inheriting from PsanaBase, type is psana%d" %(self.psanaType))
        self.gainModes = {"FH": 0, "FM": 1, "FL": 2, "AHL-H": 3, "AML-M": 4, "AHL-L": 5, "AML-L": 6}
        self.ePix10k_cameraTypes = {1: "Epix10ka", 4: "Epix10kaQuad", 16: "Epix10ka2M"}
        self.camera = 0
        self.outputDir = "../%s/" % (analysisType)

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
            self.ROIfileNames = experimentHash["ROIs"]
            self.ROIs = []
            for f in self.ROIfileNames:
                self.ROIs.append(np.load(f + ".npy"))
            try:  ## dumb code for compatibility or expectation
                self.ROI = self.ROIs[0]
            except Exception:
                pass

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

        parser = argparse.ArgumentParser(
            description="Configures calibration suite, overriding experimentHash",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        parser.add_argument("-e", "--exp", help="experiment")
        parser.add_argument("-l", "--location", help="hutch location, e.g. MfxEndstation or DetLab")
        parser.add_argument("-r", "--run", type=int, help="run")
        parser.add_argument("-R", "--runRange", help="run range, format ...")
        parser.add_argument("--fivePedestalRun", type=int, help="5 pedestal run")
        parser.add_argument("--fakePedestal", type=str, help="fake pedestal file")
        parser.add_argument("-c", "--camera", type=int, help="camera.n")
        parser.add_argument("-p", "--path", type=str, help="the base path to the output directory")
        parser.add_argument("-n", "--nModules", type=int, help="nModules")
        parser.add_argument(
            "-d", "--detType", type=str, default="", help="Epix100, Epix10ka, Epix10kaQuad, Epix10ka2M, ..."
        )
        parser.add_argument("--maxNevents", type=int, default="666666", help="max number of events to analyze")
        parser.add_argument(
            "--skipNevents", type=int, default=0, help="max number of events to skip at the start of each step"
        )
        parser.add_argument(
            "--configScript",
            type=str,
            default="experimentSuiteConfig.py",
            help="name of python config file to load if any",
        )
        parser.add_argument("--detObj", help='"raw", "calib", "image"')
        parser.add_argument("-f", "--file", type=str, help="run analysis only on file")
        parser.add_argument("-L", "--label", type=str, help="analysis label")
        parser.add_argument("-t", "--threshold", help="threshold (ADU or keV or wave8) depending on --detObj")
        parser.add_argument("--fluxCut", type=float, help="minimum flux to be included in analysis")
        parser.add_argument(
            "--special",
            type=str,
            help="comma-separated list of special behaviors - maybe this is too lazy.\
                E.g. positiveParity,doKazEvents,...",
        )
        args = parser.parse_args()

        ## for standalone analysis
        self.file = args.file
        self.label = ""
        if args.label is not None:
            self.label = args.label

        ## analyzing xtc
        if args.run is not None:
            self.run = args.run
        if args.camera is not None:
            self.camera = args.camera
        if args.exp is not None:
            self.exp = args.exp
        if args.location is not None:
            self.location = args.location
        if args.maxNevents is not None:
            self.maxNevents = args.maxNevents
        if args.skipNevents is not None:
            self.skipNevents = args.skipNevents
        if args.path is not None:
            self.outputDir = args.path
        self.detObj = args.detObj
        if args.threshold is not None:
            self.threshold = eval(args.threshold)
        else:
            self.threshold = None
        if args.fluxCut is not None:
            self.fluxCut = args.fluxCut
        try:
            self.runRange = eval(args.runRange)  ## in case needed
        except Exception:
            self.runRange = None

        self.fivePedestalRun = args.fivePedestalRun  ## in case needed
        self.fakePedestal = args.fakePedestal  ## in case needed
        if self.fakePedestal is not None:
            self.fakePedestalFrame = np.load(self.fakePedestal)  ##cast to uint32???

        if args.detType == "":
            ## assume epix10k for now
            if args.nModules is not None:
                self.detType = self.ePix10k_cameraTypes[args.nModules]
        else:
            self.detType = args.detType

        self.special = args.special
        ## done with configuration

        self.ds = None
        self.det = None  ## do we need multiple dets in an array? or self.secondDet?

        ##self.setupPsana()
        ##do this later or skip for -file

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
        for r in range(self.detRows):
            colOffset = 0
            for b in range(0, 2):
                try:
                    rowCM = np.median(
                        frame[r, colOffset : colOffset + self.detColsPerBank][
                            frame[r, colOffset : colOffset + self.detColsPerBank] < arbitraryCut
                        ]
                    )
                    frame[r, colOffset : colOffset + self.detColsPerBank] -= rowCM
                except Exception:
                    rowCM = -666
                    print("rowCM problem")
                    logger.error("rowCM problem")
                    print(frame[r, colOffset : colOffset + self.detColsPerBank])
                colOffset += self.detColsPerBank
        return frame