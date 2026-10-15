def save_spectrum(
    filename,
    normalised_spectrum,
    spectrum,
    dark_state,
    bright_state,
    dark_state_set,
    bright_state_set,
    transmittance,
):
    wavelengths, intensities = spectrum
    with open(filename, "w") as f:
        if dark_state_set and bright_state_set:
            f.write(
                "Wavelength\tNormalised Intensity\tIntensity\tDark State\tBright State\n"
            )
            if transmittance:
                f.writelines(
                    f"{wavelengths[i]}\t{normalised_spectrum[1][i]}\t{intensities[i]}\t{dark_state[1][i]}\t{bright_state[1][i]}\n"
                    for i in range(len(wavelengths))
                )
            else:
                f.writelines(
                    f"{wavelengths[i]}\t{1 - normalised_spectrum[1][i]}\t{intensities[i]}\t{dark_state[1][i]}\t{bright_state[1][i]}\n"
                    for i in range(len(wavelengths))
                )

        else:
            f.write("Wavelength\tIntensity\n")
            f.writelines(
                f"{wavelengths[i]}\t{intensities[i]}\n" for i in range(len(wavelengths))
            )
