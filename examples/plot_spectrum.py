# Simple example to capture and display spectrum
from RobotRaconteur.Client import *

c = RRN.ConnectService('rr+tcp://localhost:60825?service=spectrometer')

print(f"Device serial number: {c.device_info.serial_number}")

print(c.getf_param("electric_dark").data[0])
print(c.getf_param("integration_time").data[0])
print(c.getf_param("scans_to_average").data[0])

c.setf_param("electric_dark", RR.VarValue(True, "bool"))
c.setf_param("integration_time", RR.VarValue(6000,"int32"))
c.setf_param("scans_to_average", RR.VarValue(5, "int32"))

spectrum = c.capture_spectrum()

import matplotlib.pyplot as plt
plt.plot(spectrum.wavelengths, spectrum.spectrum_counts)
plt.show()