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

        # Init vals from experimentHash
        self.location = experimentHash.get('location', None)
        self.exp = experimentHash.get("exp", None)
        self.singlePixels = experimentHash.get("singlePixels", None)

        self.ROIfileNames = experimentHash.get("ROIs", [])
        self.ROIs = []
        for f in self.ROIfileNames:
            self.ROIs.append(np.load(f + ".npy"))
        self.ROI = self.ROIs[0] if len(self.ROIs) > 0 else None 

        self.regionSlice = experimentHash.get("regionSlice", None)
        if self.regionSlice is not None:
            self.sliceCoordinates = [
                [self.regionSlice[0].start, self.regionSlice[0].stop],
                [self.regionSlice[1].start, self.regionSlice[1].stop],
            ]
            sc = self.sliceCoordinates
            self.sliceEdges = [sc[0][1] - sc[0][0], sc[1][1] - sc[1][0]]

        self.fluxSource = experimentHash.get("fluxSource", None)
        self.fluxChannels = experimentHash.get("fluxChannels", range(8, 16))
        self.fluxSign = experimentHash.get("fluxSign", 1)

        # Parse command-line arguments
        args_parser = ArgumentParser()
        args = args_parser.parse_args()

        # Handle cmdline arguments
        self.file = args.file
        self.label = args.label or ""

        self.run = args.run if args.run is not None else None
        self.camera = args.camera if args.camera is not None else self.camera
        self.exp = args.exp if args.exp is not None else self.exp
        self.location = args.location if args.location is not None else self.location
        self.maxNevents = args.maxNevents if args.maxNevents is not None else None
        self.skipNevents = args.skipNevents if args.skipNevents is not None else None
        self.outputDir = args.path if args.path is not None else self.outputDir
        self.detObj = args.detObj

        self.threshold = eval(args.threshold) if args.threshold is not None else None
        self.fluxCut = args.fluxCut if args.fluxCut is not None else None

        try:
            self.runRange = eval(args.runRange)  ## in case needed
        except Exception as e:
            print(f"An exception occurred: {e}")
            logging.error(f"An exception occurred: {e}")
            self.runRange = None

        self.fivePedestalRun = args.fivePedestalRun if args.fivePedestalRun is not None else None
        self.fakePedestal = args.fakePedestal if args.fakePedestal is not None else None
        self.fakePedestalFrame = np.load(self.fakePedestal) if self.fakePedestal is not None else None

        if args.detType == "":
             ## assume epix10k for now
            if args.nModules is not None:
                self.detType = self.e_pix_10k_camera_types[args.nModules]
        else:
            self.detType = args.detType

        self.special = args.special
        self.ds = None
        self.det = None  ## do we need multiple dets in an array? or self.secondDet?

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
                except Exception as e:
                    print(f"An exception occurred: {e}")
                    logging.error(f"An exception occurred: {e}")
                    rowCM = -666
                    print("rowCM problem")
                    logger.error("rowCM problem")
                    print(frame[r, colOffset : colOffset + self.detColsPerBank])

                colOffset += self.detColsPerBank
        return frame


class ArgumentParser:
    def __init__(self):
                # Get cmdline arguments
        self.parser = argparse.ArgumentParser(
            description="Configures calibration suite, overriding experimentHash",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )
        self.parser.add_argument("-e", "--exp", help="experiment")
        self.parser.add_argument("-l", "--location", help="hutch location, e.g. MfxEndstation or DetLab")
        self.parser.add_argument("-r", "--run", type=int, help="run")
        self.parser.add_argument("-R", "--runRange", help="run range, format ...")
        self.parser.add_argument("--fivePedestalRun", type=int, help="5 pedestal run")
        self.parser.add_argument("--fakePedestal", type=str, help="fake pedestal file")
        self.parser.add_argument("-c", "--camera", type=int, help="camera.n")
        self.parser.add_argument("-p", "--path", type=str, help="the base path to the output directory")
        self.parser.add_argument("-n", "--nModules", type=int, help="nModules")
        self.parser.add_argument(
            "-d", "--detType", type=str, default="", help="Epix100, Epix10ka, Epix10kaQuad, Epix10ka2M, ..."
        )
        self.parser.add_argument("--maxNevents", type=int, default="666666", help="max number of events to analyze")
        self.parser.add_argument(
            "--skipNevents", type=int, default=0, help="max number of events to skip at the start of each step"
        )
        self.parser.add_argument(
            "--configScript",
            type=str,
            default="experimentSuiteConfig.py",
            help="name of python config file to load if any",
        )
        self.parser.add_argument("--detObj", help='"raw", "calib", "image"')
        self.parser.add_argument("-f", "--file", type=str, help="run analysis only on file")
        self.parser.add_argument("-L", "--label", type=str, help="analysis label")
        self.parser.add_argument("-t", "--threshold", help="threshold (ADU or keV or wave8) depending on --detObj")
        self.parser.add_argument("--fluxCut", type=float, help="minimum flux to be included in analysis")
        self.parser.add_argument(
            "--special",
            type=str,
            help="comma-separated list of special behaviors - maybe this is too lazy.\
                E.g. positiveParity,doKazEvents,...",
        )

    def parse_args(self):
        return self.parser.parse_args()