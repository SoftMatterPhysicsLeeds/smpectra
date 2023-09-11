from seabreeze.spectrometers import Spectrometer
import matplotlib.pyplot as plt


spec = Spectrometer.from_serial_number("HR4C3262")

fig, ax = plt.subplots()

ax.plot(spec.wavelengths(), spec.intensities())

plt.show()
