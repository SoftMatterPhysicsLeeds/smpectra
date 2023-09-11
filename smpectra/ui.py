import dearpygui.dearpygui as dpg
from seabreeze.spectrometers import Spectrometer

VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 800
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPectraUI:
    def __init__(self):
        self.setup_control_window()
        self.setup_graph_window()
#        self.spectrometer = Spectrometer.from_serial_number()

    def setup_control_window(self):
        with dpg.window(label="Control",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/2,
                        height=VIEWPORT_HEIGHT
                        ):
            with dpg.group(horizontal=True):
                self.get_spectra = dpg.add_button(
                    label="Get Spectrum",
                    callback=self._get_spectrum)

    def setup_graph_window(self):
        with dpg.window(label="Spectrum",
                        pos=[VIEWPORT_WIDTH/2, 0],
                        width=VIEWPORT_WIDTH/2,
                        height=VIEWPORT_HEIGHT):
            with dpg.plot(height=VIEWPORT_HEIGHT - 50,
                          width=VIEWPORT_WIDTH/2 - 10,
                          anti_aliased=True,
                          ):
                self.wavelength_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="wavelength (nm)")
                self.intensity_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="intensity")

                self.spectrum = dpg.add_line_series(
                    x=[], y=[], label="spectrum", parent=self.intensity_axis)

    def _get_spectrum(self):
        dpg.set_value(self.spectrum, [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]])
        dpg.fit_axis_data(self.intensity_axis)
        dpg.fit_axis_data(self.wavelength_axis)
