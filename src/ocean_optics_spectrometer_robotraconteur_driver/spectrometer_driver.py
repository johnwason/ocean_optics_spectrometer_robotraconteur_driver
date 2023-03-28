import time
import traceback
import RobotRaconteur as RR
RRN = RR.RobotRaconteurNode.s
import RobotRaconteurCompanion as RRC
from RobotRaconteurCompanion.Util.RobDef import register_service_types_from_resources

from RobotRaconteurCompanion.Util.InfoFileLoader import InfoFileLoader
from RobotRaconteurCompanion.Util.DateTimeUtil import DateTimeUtil
from RobotRaconteurCompanion.Util.SensorDataUtil import SensorDataUtil
from RobotRaconteurCompanion.Util.AttributesUtil import AttributesUtil

import argparse
import threading
from contextlib import suppress
import sys
import os
import jpype
from pathlib import Path

class SpectrometerImpl:
    def __init__(self, device_info):
        self.device_info = device_info

        self._spectro_wrapper = None
        self._spectro_device_number = 0
        self._lock = threading.Lock()
        self._spectrum_type = RRN.GetStructureType("experimental.ocean_optics.spectrometer.Spectrum")

    def _open_spectrometer(self, device_serial_number):
        assert self._spectro_wrapper is None
        import jpype
        import jpype.imports
        from com.oceanoptics.omnidriver.api.wrapper import Wrapper
        self._spectro_wrapper = Wrapper()
        num_spectro = self._spectro_wrapper.openAllSpectrometers()
        for i in range(num_spectro):
            if device_serial_number is None or self._spectro_wrapper.getSerialNumber(i) == device_serial_number:
                self._spectro_device_number = i
                return
        assert False, f"Could not find spectrometer. Detected {num_spectro} spectrometers"
            

    def capture_spectrum(self):
        ret = self._spectrum_type()
        wavelengths = self._spectro_wrapper.getWavelengths(self._spectro_device_number)
        spectrum = self._spectro_wrapper.getSpectrum(self._spectro_device_number)
        assert self._spectro_wrapper.getWrapperExtensions().isSpectrumValid(self._spectro_device_number), \
            "Captured spectrum is not valid"

        ret.wavelengths = wavelengths
        ret.spectrum_counts = spectrum

        return ret

    def getf_param(self, param_name):
        if param_name == "electric_dark":
            ret =  self._spectro_wrapper.getCorrectForElectricalDark(self._spectro_device_number) != 0
            return RR.VarValue(ret, "bool")
        if param_name == "integration_time":
            return RR.VarValue(self._spectro_wrapper.getIntegrationTime(self._spectro_device_number), "int32")
        if param_name == "scans_to_average":
            return RR.VarValue(self._spectro_wrapper.getScansToAverage(self._spectro_device_number), "int32")
        raise RR.InvalidArgumentException("Invalid parameter")

    def setf_param(self, param_name, value):
        if param_name == "electric_dark":
            return self._spectro_wrapper.setCorrectForElectricalDark(self._spectro_device_number, value.data[0])
        if param_name == "integration_time":
            return self._spectro_wrapper.setIntegrationTime(self._spectro_device_number, value.data[0])
        if param_name == "scans_to_average":
            return self._spectro_wrapper.setScansToAverage(self._spectro_device_number, value.data[0])
        raise RR.InvalidArgumentException("Invalid parameter")

def _start_jvm():
    if sys.platform == "win32":
        java_home = os.environ["JAVA_HOME"]
        jvmpath = str(next(Path(java_home).rglob("jvm.dll")))

        jpype.startJVM(
            classpath=[f"{os.environ['OOI_HOME']}/OmniDriver.jar"], 
            jvmpath = jvmpath)
    else:
        jpype.startJVM(classpath=[f"{os.environ['OOI_HOME']}/OmniDriver.jar"])

def _list_spectrometers():
    _start_jvm()
    
    import jpype
    import jpype.imports
    from com.oceanoptics.omnidriver.api.wrapper import Wrapper
    wrapper = Wrapper()
    num_spectro = wrapper.openAllSpectrometers()
    print("")
    print("Detected Spectrometers:")
    for i in range(num_spectro):
        print(f"{i}: {wrapper.getSerialNumber(i)}")

def main():
    parser = argparse.ArgumentParser(description="Ocean Optics Spectrometer Robot Raconteur Driver")

    parser.add_argument("--device-serial-number", type=str,default=None,required=False,help="Device serial number (optional)")
    parser.add_argument("--wait-signal",action='store_const',const=True,default=False, help="wait for SIGTERM or SIGINT (Linux only)")
    parser.add_argument("--list-spectrometers",action='store_true',default=False,help="List available spectrometers and exit")


    args, _ = parser.parse_known_args()

    if args.list_spectrometers:
        _list_spectrometers()
        return

    RRC.RegisterStdRobDefServiceTypes(RRN)

    register_service_types_from_resources(RRN, __package__, ["experimental.ocean_optics.spectrometer"])

    _start_jvm()

    spectrometer = SpectrometerImpl(None)

    spectrometer._open_spectrometer(args.device_serial_number)

    
    with RR.ServerNodeSetup("ocean_optics.spectrometer",60825):

        service_ctx = RRN.RegisterService("spectrometer","experimental.ocean_optics.spectrometer.Spectrometer",spectrometer)
        # service_ctx.SetServiceAttributes(welder_attributes)
        # welder._start()

        if args.wait_signal:  
            #Wait for shutdown signal if running in service mode          
            print("Press Ctrl-C to quit...")
            import signal
            signal.sigwait([signal.SIGTERM,signal.SIGINT])
        else:
            #Wait for the user to shutdown the service
            input("Server started, press enter to quit...")