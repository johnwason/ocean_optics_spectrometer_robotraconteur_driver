# Ocean Optics Spectrometer Robot Raconteur Driver

This is a Robot Raconteur driver for Ocean Optics spectrometers. It is based on the "Ocean Optics OmniDriver". This driver is very simple: it allows for setting basic capture parameters, and capture the spectrometer counts at each frequency pixel. It does not support any of the advanced features of the spectrometer.

OceanOptics spectrometers work by splitting a light input into a spectrum using a diffraction grating, and then projecting the spectrum onto a single dimensional CCD. Each pixel in the CCD is then sampled to read the "counts" at that pixel. The counts are proportional to the intensity of the light at that wavelength, but do not have any direct physical meaning without some calibration method. Various parameters such as the "integration time" and "samples to average" can be set to control the capture process.

The OmniDriver is a Java library that communicates with the scanner. Using Java for this purpose introduces some complexities in the installation process. Be sure to carefully follow the installation instructions.

This driver has been tested with the HR4000CG-UV-NIR USB spectrometer.

## Installation

### Java

The OmniDriver is a Java library. Java must be installed on the system to use this driver. The Java Runtime Environment (JRE) is sufficient, but the Java Development Kit (JDK) is also acceptable. The Java version must be 1.8 or higher. See the [Java website](https://www.java.com/en/download/) for more information.

The `JAVA_HOME` environment variable must be set to the Java installation directory. For example, on Windows the `JAVA_HOME` environment variable should be set to something like
 `C:\Program Files\Java\jre1.8.0_181`, with the exact version number depending on the installation.

### OmniDriver

The OmniDriver runtime can be downloaded from the https://www.oceaninsight.com/support/software-downloads/omnidriver-and-spam. Install the redistributable driver. It should not require a password.

The `OOI_HOME` environment variable must be set to the OmniDriver installation directory. This should be set by the installer.

### Driver

The driver can be installed using pip:

```
python -m pip install --user git+https://github.com/johnwason/ocean_optics_spectrometer_robotraconteur_driver.git
```

## Running the Driver

A config file for the driver must be specified on the command line. A config file for the HR4000CG_UV_NIR spectrometer is available. Retrieve the file using curl:

```
curl -L -o HR4000CG_UV_NIR_spectrometer_default_config.yaml https://raw.githubusercontent.com/johnwason/ocean_optics_spectrometer_robotraconteur_driver/main/config/HR4000CG_UV_NIR_spectrometer_default_config.yaml
```

The driver can be run from the command line using the following command:

```
python -m ocean_optics_spectrometer_robotraconteur_driver --spectrometer-config-file=HR4000CG_UV_NIR_spectrometer_default_config.yaml
```

By default the driver can be connected using the following url: 'rr+tcp://localhost:60825?service=spectrometer'

The standard Robot Raconteur command line configuration flags are supported. See https://github.com/robotraconteur/robotraconteur/wiki/Command-Line-Options

## Example Client

```python
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
```