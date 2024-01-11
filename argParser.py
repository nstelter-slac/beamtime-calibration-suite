import argparse
import numpy as np
from basicSuiteScript import BasicSuiteScript

def parseAndSetCmdlineArgs(eventObject):
    
    print ('!!A')
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
    eventObject.file = args.file
    eventObject.label = ""
    if args.label is not None:
        eventObject.label = args.label

    ## analyzing xtc
    if args.run is not None:
        eventObject.run = args.run
    if args.camera is not None:
        eventObject.camera = args.camera
    if args.exp is not None:
        eventObject.exp = args.exp
    if args.location is not None:
        eventObject.location = args.location
    if args.maxNevents is not None:
        eventObject.maxNevents = args.maxNevents
    if args.skipNevents is not None:
        eventObject.skipNevents = args.skipNevents
    if args.path is not None:
        eventObject.outputDir = args.path
    eventObject.detObj = args.detObj
    if args.threshold is not None:
        eventObject.threshold = eval(args.threshold)
    else:
        eventObject.threshold = None
    if args.fluxCut is not None:
        eventObject.fluxCut = args.fluxCut
    try:
        eventObject.runRange = eval(args.runRange)  ## in case needed
    except Exception:
        eventObject.runRange = None

    eventObject.fivePedestalRun = args.fivePedestalRun  ## in case needed
    eventObject.fakePedestal = args.fakePedestal  ## in case needed
    if eventObject.fakePedestal is not None:
        eventObject.fakePedestalFrame = np.load(eventObject.fakePedestal)  ##cast to uint32???

    if args.detType == "":
        ## assume epix10k for now
        if args.nModules is not None:
            eventObject.detType = eventObject.ePix10k_cameraTypes[args.nModules]
    else:
        eventObject.detType = args.detType

    eventObject.special = args.special

    print ("!!B ")
