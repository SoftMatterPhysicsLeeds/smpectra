import threading
import dearpygui.dearpygui as dpg
import time
import numpy as np
from seabreeze.spectrometers import Spectrometer
from seabreeze.cseabreeze._wrapper import SeaBreezeError
from smpectra.utils import save_spectrum
VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 800
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPectraUI:
    def __init__(self):
        self.setup_control_windows()
        self.setup_graph_window()
        self.setup_device_thickness_calculator_window()

        self.continuous_measurement = False
        self.stop_thread = False
        self.spectrometer_attached = False
        self.dark_state_set = False
        self.bright_state_set = False
        self.integration_time = 100000
        try:
            self.spectrometer = Spectrometer.from_serial_number("HR4C3262")
            self.spectrometer_attached = True
            self.spectrometer.integration_time_micros(self.integration_time)
            self.start_continuous_measurement()
        except SeaBreezeError:
            print("Could not find spectrometer")

    def setup_control_windows(self):
        with dpg.window(label="Spectrometer Control",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/4,
                        height=VIEWPORT_HEIGHT/4
                        ):
            self.continuous_measurement_button = dpg.add_button(
                label="Stop Continuous Measurements", callback=self.stop_continuous_measurement)
            with dpg.group(horizontal=True):
                dpg.add_text("Integration\n time (us): ")
                self.int_time_input = dpg.add_input_int(
                    default_value=100000, width=100)
                self.apply_int_time = dpg.add_button(
                    label="Apply",
                    callback=self._set_integration_time)
            with dpg.group(horizontal=True):
                dpg.add_text("Number of averages: ")
                self.number_of_averages_input = dpg.add_input_int(
                    default_value=10, width=100)
            self.get_average_spectrum_button = dpg.add_button(
                label="Get Spectrum", callback=self.get_average_spectrum)
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

        with dpg.window(
                label="Graph Control",
                pos=[0, VIEWPORT_HEIGHT/4],
                width=VIEWPORT_WIDTH/4,
                height=VIEWPORT_HEIGHT/4
        ):
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

    def setup_device_thickness_calculator_window(self):
        with dpg.window(label="Device Thickness Calculator",
                        pos=[0, VIEWPORT_HEIGHT/2],
                        width=VIEWPORT_WIDTH/4,
                        height=VIEWPORT_HEIGHT/2):
            with dpg.group(horizontal=True):
                dpg.add_text("lambda 1 (nm): ")
                self.lambda1_input = dpg.add_input_float(default_value=400)
            with dpg.group(horizontal=True):
                dpg.add_text("lambda 2 (nm): ")
                self.lambda2_input = dpg.add_input_float(default_value=800)
            with dpg.group(horizontal=True):
                dpg.add_text("n: ")
                self.n_input = dpg.add_input_float(default_value=1)
            with dpg.group(horizontal=True):
                dpg.add_text("m: ")
                self.m_input = dpg.add_input_int(default_value=1)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Calculate",
                               callback=self.calculate_thickness)
            with dpg.group(horizontal=True):
                dpg.add_text("d (nm): ")
                self.d_result_label = dpg.add_text("0")

    def calculate_thickness(self):
        lambda1 = dpg.get_value(self.lambda1_input)
        lambda2 = dpg.get_value(self.lambda2_input)
        n = dpg.get_value(self.n_input)
        m = dpg.get_value(self.m_input)
        result = (m * lambda1 * lambda2)/(2 * n * (lambda2 - lambda1))
        dpg.set_value(self.d_result_label, result)

    def normalise_spectrum(self):
        if self.dark_state_set and self.bright_state_set:
            bright_bg_removed = self.bright_state[1] - self.dark_state[1]
            spec_bg_removed = self.spectrum[1] - self.dark_state[1]
            normalised_spectrum = np.divide(spec_bg_removed, bright_bg_removed, out=np.zeros_like(
                spec_bg_removed), where=bright_bg_removed != 0)
            self.spectrum[1] = normalised_spectrum

    def set_dark_state(self):
        self.dark_state = self.spectrum
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
        self.bright_state = self.spectrum
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
        if not self.continuous_measurement:
            print("drawing Spectrum")
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

    def start_continuous_measurement(self):
        self.stop_thread = False
        self.get_spectra_thread = threading.Thread(
            target=get_spectrum, args=(self,))
        self.get_spectra_thread.daemon = True
        self.get_spectra_thread.start()
        self.continuous_measurement = True
        dpg.configure_item(self.continuous_measurement_button,
                           label="Stop Continuous Measurements", callback=self.stop_continuous_measurement)

    def stop_continuous_measurement(self):
        self.stop_thread = True
        self.get_spectra_thread.join()
        self.continuous_measurement = False
        dpg.configure_item(self.continuous_measurement_button,
                           label="Start Continuous Measurements", callback=self.start_continuous_measurement)

    def get_average_spectrum(self):
        sum_spectrum = np.zeros_like(self.spectrum[1])
        wavelengths = self.spectrum[0]
        num_of_averages = dpg.get_value(self.number_of_averages_input)
        for i in range(num_of_averages):
            print(i)
            sum_spectrum += self.spectrometer.spectrum()[1]
        self.average_spectrum = [wavelengths, sum_spectrum/num_of_averages]
        print(self.average_spectrum)

        self.draw_spectrum(self.average_spectrum)


def _file_saveas_callback(sender, app_data, output_file_path):
    dpg.set_value(output_file_path, app_data["file_path_name"])


def get_spectrum(ui):
    first_time = True
    start = time.time()
    print("Starting acquisition thread...")
    while True:
        if ui.stop_thread:
            print("Stopping acquisition thread...")
            break
        integration_time_in_seconds = ui.integration_time*1e-6
        if time.time() - start > integration_time_in_seconds + 0.01*integration_time_in_seconds:
            ui._get_spectrum()
            if first_time:
                ui.scale_axes()
                first_time = False
            start = time.time()
