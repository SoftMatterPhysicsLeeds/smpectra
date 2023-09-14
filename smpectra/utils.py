def save_spectrum(filename, normalised_spectrum, spectrum, dark_state, bright_state):
    wavelengths, intensities = spectrum
    with open(filename, 'w') as f:
        if dark_state.any():
            f.write(
                "Wavelength\tNormalised Intensity\tIntensity\tDark State\tBright State\n")
            for i in range(len(wavelengths)):
                f.write(
                    f"{wavelengths[i]}\t{normalised_spectrum[1][i]}\t{intensities[i]}\t{dark_state[1][i]}\t{bright_state[1][i]}\n")

        else:
            f.write("Wavelength\tIntensity\n")
            for i in range(len(wavelengths)):
                f.write(f"{wavelengths[i]}\t{intensities[i]}\n")
