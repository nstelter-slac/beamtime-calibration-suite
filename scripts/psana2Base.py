# ignoring from ruff for now, need sort out later along
# with other noqa in this file
from psana import * # noqa: F403
# standard
from mpi4py import MPI
# for parallelism
import os
import logging

logger = logging.getLogger(__name__)

# psana2 only
os.environ["PS_SMD_N_EVENTS"] = "50"
os.environ["PS_SRV_NODES"] = "1"


class PsanaBase(object):
    def __init__(self, analysisType="scan"):
        self.psanaType = 2
        print("in psana2Base")
        logger.info("in psana2Base")
        self.gainModes = {"FH": 0, "FM": 1, "FL": 2, "AHL-H": 3, "AML-M": 4, "AHL-L": 5, "AML-L": 6}
        self.ePix10k_cameraTypes = {1: "Epix10ka", 4: "Epix10kaQuad", 16: "Epix10ka2M"}
        self.g0cut = 1 << 14  # 2023
        self.gainBitsMask = self.g0cut - 1

        self.allowed_timestamp_mismatch = 1000

    def get_ds(self, run=None):
        if run is None:
            run = self.run
        return DataSource(exp=self.exp, run=run, intg_det="epixhr", max_events=self.maxNevents) # noqa: F405

    def setupPsana(self):
        print("have built basic script class, exp %s run %d" %(self.exp, self.run))
        logger.info("have built basic script class, exp %s run %d" %(self.exp, self.run))
        if self.runRange is None:
            self.ds = self.get_ds(self.run)
        else:
            self.run = self.runRange[0]
            self.ds = self.get_ds()

        self.myrun = next(self.ds.runs())
        try:
            self.step_value = self.myrun.Detector("step_value")
            self.step_docstring = self.myrun.Detector("step_docstring")
        except Exception:
            self.step_value = self.step_docstring = None

        # make this less dumb to accommodate epixM etc, use a dict etc.
        self.det = self.myrun.Detector("epixhr")
        # could set to None and reset with first frame I guess, or does the det object know?
        self.detRows = 288
        self.detCols = 384
        self.detColsPerBank = 96
        self.detNbanks = int(384 / self.detColsPerBank)

        self.timing = self.myrun.Detector("timing")
        self.desiredCodes = {"120Hz": 272, "4kHz": 273, "5kHz": 274}

        try:
            self.mfxDg1 = self.myrun.Detector("MfxDg1BmMon")
        except Exception as e:
            print(f"An exception occurred: {e}")
            logging.exception(f"An exception occurred: {e}")
            self.mfxDg1 = None
            print("No flux source found")
            logger.info("No flux source found")
        try:
            self.mfxDg2 = self.myrun.Detector("MfxDg2BmMon")
        except Exception:
            self.mfxDg2 = None
        # fix hardcoding in the fullness of time
        self.detEvts = 0
        self.flux = None

        self.evrs = None
        try:
            self.wave8 = Detector(self.fluxSource, self.ds.env()) # noqa: F405
        except Exception:
            self.wave8 = None
        self.config = None
        try:
            self.controlData = Detector("ControlData") # noqa: F405
        except Exception:
            self.controlData = None

    def getFivePedestalRunInfo(self):
        # could do load_txt but would require full path so
        if self.det is None:
            self.setupPsana()

        evt = self.getEvt(self.fivePedestalRun)
        self.fpGains = self.det.gain(evt)
        self.fpPedestals = self.det.pedestals(evt)
        self.fpStatus = self.det.status(evt)  ## does this work?
        self.fpRMS = self.det.rms(evt)  ## does this work?

    def getEvtOld(self, run=None):
        oldDs = self.ds
        if run is not None:
            self.ds = self.get_ds(run)
        try:  ## or just yield evt I think
            evt = next(self.ds.events())
        except StopIteration:
            self.ds = oldDs
            return None
        self.ds = oldDs
        return evt

    def getNextEvtFromGen(self, gen):
        # this is needed to get flux information out of phase with detector
        # information in mixed lcls1/2 mode
        for nevt, evt in enumerate(gen):
            try:
                self.flux = self._getFlux(evt)
            except Exception:
                pass
            if self.det.raw.raw(evt) is None:
                continue
            self.detEvts += 1
            # should check for beam code here to be smarter
            return self.detEvts, evt

    def matchedDetEvt(self):
        self.fluxTS = 0
        for nevt, evt in enumerate(self.myrun.events()):
            ec = self.getEventCodes(evt)
            if ec[137]:
                self.flux = self._getFlux(evt)  ## fix this
                self.fluxTS = self.getTimestamp(evt)
                continue
            elif ec[281]:
                self.framesTS = self.getTimestamp(evt)
                if self.framesTS - self.fluxTS > self.allowed_timestamp_mismatch:
                    continue
                yield evt
            else:
                continue

    def getEvtFromRunsTooSmartForMyOwnGood(self):
        for r in self.runRange:
            self.run = r
            self.ds = self.get_ds()
            try:
                evt = next(self.ds.events())
                yield evt
            except Exception:
                continue

    def getEvtFromRuns(self):
        try:  ## can't get yield to work
            evt = next(self.ds.events())
            return evt
        except StopIteration:
            i = self.runRange.index(self.run)
            try:
                self.run = self.runRange[i + 1]
                print("switching to run %d" % (self.run))
                logger.info("switching to run %d" % (self.run))
                self.ds = self.get_ds(self.run)
            except Exception:
                print("have run out of new runs")
                logger.info("have run out of new runs")
                return None
            print("get event from new run")
            logger.info("get event from new run")
            evt = next(self.ds.events())
            return evt

    def getAllFluxes(self, evt):
        if evt is None:
            return None
        try:
            return self.mfxDg1.raw.peakAmplitude(evt)
        except Exception:
            return None

    def _getFlux(self, evt):
        if self.mfxDg1 is None:
            return None

        try:
            f = self.mfxDg1.raw.peakAmplitude(evt)[self.fluxChannels].mean() * self.fluxSign
        except Exception:
            return None
        try:
            if f < self.fluxCut:
                return None
        except Exception:
            pass
        return f

    def getFlux(self, evt):
        return self.flux

    def get_evrs(self):
        if self.config is None:
            self.get_config()

        self.evrs = []
        for key in list(self.config.keys()):
            if key.type() == EvrData.ConfigV7: # noqa: F405
                self.evrs.append(key.src())

    def getEventCodes(self, evt):
        return self.timing.raw.eventcodes(evt)

    def getPulseId(self, evt):
        return self.timing.raw.pulseId(evt)

    def isKicked(self, evt):
        allcodes = self.getEventCodes(evt)
        return allcodes[self.desiredCodes["120Hz"]]

    def get_config(self):
        self.config = self.ds.env().configStore()

    def getStepGen(self):
        return self.myrun.steps()

    def getRunGen(self):
        return self.ds.runs()

    def getEvt(self):
        try:
            evt = next(self.myrun.events())
        except StopIteration:
            return None
        return evt

    def getScanValue(self, step, useStringInfo=False):
        #print(self.step_value(step),self.step_docstring(step),useStringInfo)
        if useStringInfo:
            payload = self.step_docstring(step)
            sv = eval(payload.split()[-1][:-1])
            #print("step", int(self.step_value(step)), sv)
            return sv
        return self.step_value(step)

    def getRawData(self, evt, gainBitsMasked=True):
        frames = self.det.raw.raw(evt)
        if frames is None:
            return None
        if gainBitsMasked:
            return frames & self.gainBitsMask
        return frames

    def getCalibData(self, evt):
        frames = self.det.raw.calib(evt)
        return frames

    def getImage(self, evt, data=None):
        return self.raw.image(evt, data)

    def getTimestamp(self, evt):
        return evt.timestamp

    def getPingPongParity(self, frameRegion):
        evensEvenRowsOddsOddRows = frameRegion[::2, ::2] + frameRegion[1::2, 1::2]
        oddsEvenRowsEvensOddRows = frameRegion[1::2, ::2] + frameRegion[::2, 1::2]
        delta = evensEvenRowsOddsOddRows.mean() - oddsEvenRowsEvensOddRows.mean()
        return delta > 0