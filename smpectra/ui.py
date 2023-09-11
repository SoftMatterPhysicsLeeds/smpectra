import dearpygui.dearpygui as dpg
from seabreeze.spectrometers import Spectrometer

VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 800
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPectraUI:
    def __init__(self):
        self.setup_control_window()
        self.setup_graph_window()
        self.spectrometer = Spectrometer.from_serial_number("HR4C3262")
        self.spectrometer.integration_time_micros(100000)
    def setup_control_window(self):
        with dpg.window(label="Control",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/4,
                        height=VIEWPORT_HEIGHT
                        ):
            with dpg.group(horizontal=True):
                self.get_spectra = dpg.add_button(
                    label="Get Spectrum",
                    callback=self._get_spectrum)

            with dpg.group(horizontal=True):
                dpg.add_text("Integration\n time (us): ")
                self.int_time_input = dpg.add_input_int(default_value = 100000, width = 100)
                self.apply_int_time = dpg.add_button(
                    label="Apply",
                    callback=self._set_integration_time)

    def setup_graph_window(self):
        with dpg.window(label="Spectrum",
                        pos=[VIEWPORT_WIDTH/4, 0],
                        width=3*VIEWPORT_WIDTH/4 - 15,
                        height=VIEWPORT_HEIGHT):
            with dpg.plot(height=VIEWPORT_HEIGHT - 50,
                          width=3*VIEWPORT_WIDTH/4 - 10,
                          anti_aliased=True,
                          ):
                self.wavelength_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="wavelength (nm)")
                self.intensity_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="intensity")

                self.spectrum = dpg.add_line_series(
                    x=[], y=[], label="spectrum", parent=self.intensity_axis)

    def _get_spectrum(self):
        wavelengths, intensities = self.spectrometer.spectrum()
        dpg.set_value(self.spectrum, [wavelengths, intensities])
        dpg.fit_axis_data(self.intensity_axis)
        dpg.fit_axis_data(self.wavelength_axis)

    def _set_integration_time(self):
        integration_time = dpg.get_value(self.int_time_input)
        self.spectrometer.integration_time_micros(integration_time)
