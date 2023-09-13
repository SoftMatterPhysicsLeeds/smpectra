import dearpygui.dearpygui as dpg
import numpy as np
from seabreeze.spectrometers import Spectrometer
from seabreeze.cseabreeze._wrapper import SeaBreezeError
from smpectra.utils import save_spectrum
VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 800
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPectraUI:
    def __init__(self):
        self.setup_control_window()
        self.setup_graph_window()
        self.spectrometer_attached = False
        self.dark_state_set = False
        self.bright_state_set = False
        self.integration_time = 100000
        try:
            self.spectrometer = Spectrometer.from_serial_number("HR4C3262")
            self.spectrometer_attached = True
            self.spectrometer.integration_time_micros(self.integration_time)
        except SeaBreezeError:
            print("Could not find spectrometer")

    def setup_control_window(self):
        with dpg.window(label="Control",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/4,
                        height=VIEWPORT_HEIGHT
                        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Integration\n time (us): ")
                self.int_time_input = dpg.add_input_int(
                    default_value=100000, width=100)
                self.apply_int_time = dpg.add_button(
                    label="Apply",
                    callback=self._set_integration_time)
            with dpg.group(horizontal=True):
                self.set_dark_state_button = dpg.add_button(
                    label="Set Dark State",
                    callback=self.set_dark_state)
                self.dark_state_label = dpg.add_text("Dark State not set")
            with dpg.group(horizontal=True):
                self.set_bright_state_button = dpg.add_button(
                    label="Set Bright State",
                    callback=self.set_bright_state)
                self.bright_state_label = dpg.add_text("Bright State not set")
            with dpg.group(horizontal=True):
                self.scale_axes_button = dpg.add_button(
                    label="Auto-scale axes",
                    callback=self.scale_axes)

            with dpg.group(horizontal=True):
                self.save_spectra_button = dpg.add_button(
                    label="Save Spectrum",
                    callback=self._save_spectrum)

            with dpg.group(horizontal=True):
                self.output_file_path = dpg.add_input_text(
                    default_value="results.txt"
                )
                self.browse_button = dpg.add_button(
                    label="Browse", callback=lambda: dpg.show_item("file_dialog_id")
                )

            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                callback=_file_saveas_callback,
                user_data=self.output_file_path,
                id="file_dialog_id",
                width=700,
                height=400,
            ):
                dpg.add_file_extension(".txt")

    def setup_graph_window(self):
        with dpg.window(label="Spectrum",
                        pos=[VIEWPORT_WIDTH/4, 0],
                        width=3*VIEWPORT_WIDTH/4 - 15,
                        height=VIEWPORT_HEIGHT):
            with dpg.plot(height=VIEWPORT_HEIGHT - 50,
                          width=3*VIEWPORT_WIDTH/4 - 10,
                          anti_aliased=True,
                          crosshairs=True 
                          ):
                self.wavelength_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="wavelength (nm)")
                self.intensity_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="intensity")

                self.spectrum_graph = dpg.add_line_series(
                    x=[], y=[], label="spectrum", parent=self.intensity_axis)

    def normalise_spectrum(self):
        if self.dark_state_set and self.bright_state_set:
            bright_bg_removed = self.bright_state[1] - self.dark_state[1]
            spec_bg_removed = self.spectrum[1] - self.dark_state[1]
            normalised_spectrum = np.divide(spec_bg_removed, bright_bg_removed, out=np.zeros_like(
                spec_bg_removed), where=bright_bg_removed != 0)
            self.spectrum[1] = normalised_spectrum

    def set_dark_state(self):
        self.dark_state = self.spectrometer.spectrum()
        self.dark_state_set = True
        dpg.set_value(self.dark_state_label, "Dark State set")
        dpg.configure_item(self.set_dark_state_button,
                           label="Unset Dark State", callback=self.unset_dark_state)

    def unset_dark_state(self):
        self.dark_state_set = False
        dpg.set_value(self.dark_state_label, "Dark State not set")
        dpg.configure_item(self.set_dark_state_button,
                           label="Set Dark State", callback=self.set_dark_state)

    def set_bright_state(self):
        self.bright_state = self.spectrometer.spectrum()
        self.bright_state_set = True
        dpg.set_value(self.bright_state_label, "Bright State set")
        dpg.configure_item(self.set_bright_state_button,
                           label="Unset Bright State", callback=self.unset_bright_state)

    def unset_bright_state(self):
        self.dark_state_set = False
        dpg.set_value(self.bright_state_label, "Bright State not set")
        dpg.configure_item(self.set_bright_state_button,
                           label="Set Bright State", callback=self.set_bright_state)

    def _get_spectrum(self):
        self.spectrum = self.spectrometer.spectrum()
        if self.bright_state_set and self.dark_state_set:
            self.normalise_spectrum()

        self.draw_spectrum(self.spectrum)

    def draw_spectrum(self, spectrum):
        dpg.set_value(self.spectrum_graph, [
                      self.spectrum[0], self.spectrum[1]])

    def scale_axes(self):
        dpg.fit_axis_data(self.intensity_axis)
        dpg.fit_axis_data(self.wavelength_axis)

    def _save_spectrum(self):
        save_path = dpg.get_value(self.output_file_path)
        save_spectrum(save_path, self.spectrum)

    def _set_integration_time(self):
        if self.spectrometer_attached:
            integration_time = dpg.get_value(self.int_time_input)
            self.spectrometer.integration_time_micros(integration_time)
            self.integration_time = integration_time
        else:
            print("ERROR: No spectrometer attached, cannot set integration time")


def _file_saveas_callback(sender, app_data, output_file_path):
    dpg.set_value(output_file_path, app_data["file_path_name"])
