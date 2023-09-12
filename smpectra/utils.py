def save_spectrum(filename, spectrum):
    wavelengths, intensities = spectrum
    with open(filename, 'w') as f:
        f.write("Wavelength\tIntensity\n")
        for i in range(len(wavelengths)):
            f.write(f"{wavelengths[i]}\t{intensities[i]}\n")
