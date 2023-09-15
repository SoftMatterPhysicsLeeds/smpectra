import threading
import dearpygui.dearpygui as dpg
import time
import numpy as np
from seabreeze.spectrometers import Spectrometer
from seabreeze.cseabreeze._wrapper import SeaBreezeError
from smpectra.utils import save_spectrum
VIEWPORT_WIDTH = 1280
DRAW_HEIGHT = 850
VIEWPORT_HEIGHT = DRAW_HEIGHT - 40


class SMPectraUI:
    def __init__(self):
        self.setup_control_windows()
        self.setup_graph_window()
        self.setup_device_thickness_calculator_window()

        self.first_time_normalising = True
        self.dark_state = None
        self.bright_state = None
        self.continuous_measurement = False
        self.stop_thread = False
        self.spectrometer_attached = False
        self.dark_state_set = False
        self.bright_state_set = False
        self.integration_time = 100000
        try:
            # connect to specific serial number - probably not necessary
            # self.spectrometer = Spectrometer.from_serial_number("HR4C3262")
            self.spectrometer = Spectrometer.from_first_available()
            self.spectrometer_attached = True
            self.spectrometer.integration_time_micros(self.integration_time)
            self.start_continuous_measurement()
        except SeaBreezeError:
            print("Could not find spectrometer")

    def setup_control_windows(self):
        with dpg.window(label="Spectrometer Control",
                        pos=[0, 0],
                        width=VIEWPORT_WIDTH/4,
                        height=2*(2*VIEWPORT_HEIGHT/3)/3
                        ):
            with dpg.group(horizontal=True):
                dpg.add_text("Status: ")
                self.status = dpg.add_text("Continuous Measurement")
            self.continuous_measurement_button = dpg.add_button(
                label="Stop Continuous Measurements",
                callback=self.stop_continuous_measurement, width=300, height=50)

            self.get_average_spectrum_button = dpg.add_button(
                label="Get Averaged Spectrum", callback=self.get_average_spectrum, width=300, height=50)
            with dpg.group(horizontal=True):
                self.set_dark_state_button = dpg.add_button(
                    label="Set Dark State",
                    callback=self.set_dark_state,
                    width=150,
                    height=25)
                self.dark_state_label = dpg.add_text("Dark State not set")
            with dpg.group(horizontal=True):
                self.set_bright_state_button = dpg.add_button(
                    label="Set Bright State",
                    callback=self.set_bright_state,
                    width=150,
                    height=25)
                self.bright_state_label = dpg.add_text("Bright State not set")
            with dpg.group(horizontal=True):
                dpg.add_text("Number of averages: ")
                self.number_of_averages_input = dpg.add_input_int(
                    default_value=10, width=100)
            with dpg.group(horizontal=True):
                dpg.add_text("Integration\n time (us): ")
                self.int_time_input = dpg.add_input_int(
                    default_value=100000, width=150)
                self.apply_int_time = dpg.add_button(
                    label="Apply",
                    callback=self._set_integration_time)
        with dpg.window(
                label="Graph Control",
                pos=[0, 2*(2*VIEWPORT_HEIGHT/3)/3],
                width=VIEWPORT_WIDTH/4,
                height=(2*VIEWPORT_HEIGHT/3)/3
        ):
            with dpg.group(horizontal=True):
                self.scale_axes_button = dpg.add_button(
                    label="Auto-scale x-axis",
                    callback=self.scale_x_axis)
                self.scale_axes_button = dpg.add_button(
                    label="Auto-scale y-axis",
                    callback=self.scale_y_axis)

            with dpg.group(horizontal=True):
                self.scale_axes_button = dpg.add_button(
                    label="Auto-scale axes",
                    callback=self.scale_axes)
            with dpg.group(horizontal=True):
                dpg.add_text("Folder:")
                self.output_folder = dpg.add_input_text(
                    default_value="..\\SMPectra_Data",
                    width=150
                )
                self.browse_button = dpg.add_button(
                    label="Browse",
                    callback=lambda: dpg.show_item("file_dialog_id")
                )
            with dpg.group(horizontal=True):
                dpg.add_text("Filename:")
                self.output_file = dpg.add_input_text(
                    default_value="data.txt"
                )

            with dpg.group(horizontal=True):
                self.save_spectra_button = dpg.add_button(
                    label="Save Spectrum",
                    callback=self._save_spectrum,
                    width=300,
                    height=25)

            with dpg.file_dialog(
                directory_selector=True,
                show=False,
                callback=_file_saveas_callback,
                user_data=self.output_folder,
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
                          crosshairs=True,
                          ):

                self.wavelength_axis = dpg.add_plot_axis(
                    dpg.mvXAxis, label="wavelength (nm)")
                self.intensity_axis = dpg.add_plot_axis(
                    dpg.mvYAxis, label="intensity")

                self.spectrum_graph = dpg.add_line_series(
                    x=[], y=[], label="spectrum", parent=self.intensity_axis)

                self.lambda1_line = dpg.add_drag_line(
                    label="lambda1",
                    color=[255, 0, 0, 255],
                    default_value=400,
                    callback=self.lambda1_line_changed
                )

                self.lambda2_line = dpg.add_drag_line(
                    label="lambda2",
                    color=[0, 0, 255, 255],
                    default_value=800,
                    callback=self.lambda2_line_changed
                )

    def lambda1_line_changed(self):
        val = dpg.get_value(self.lambda1_line)
        dpg.set_value(self.lambda1_input, val)

    def lambda2_line_changed(self):
        val = dpg.get_value(self.lambda2_line)
        dpg.set_value(self.lambda2_input, val)

    def setup_device_thickness_calculator_window(self):
        with dpg.window(label="Device Thickness Calculator",
                        pos=[0, 2*VIEWPORT_HEIGHT/3],
                        width=VIEWPORT_WIDTH/4,
                        height=VIEWPORT_HEIGHT/3):
            self.find_lambda_lines_button = dpg.add_button(
                    label="Find lambda lines",
                    callback=self.find_lambda_lines,
                    width=300
                    )
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'lambda 1 (nm):':>14} ")
                self.lambda1_input = dpg.add_input_float(
                    default_value=400, width=150, callback=self.lambda1_input_changed)
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'lambda 2 (nm):':>14} ")
                self.lambda2_input = dpg.add_input_float(
                    default_value=800, width=150, callback=self.lambda2_input_changed)
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'n:':>14} ")
                self.n_input = dpg.add_input_float(default_value=1, width=150)
            with dpg.group(horizontal=True):
                dpg.add_text(f"{'m:':>14} ")
                self.m_input = dpg.add_input_int(default_value=1, width=150)
            with dpg.group(horizontal=True):
                dpg.add_button(label="Calculate",
                               callback=self.calculate_thickness,
                               width=300,
                               height=50)
            with dpg.group(horizontal=True):
                dpg.add_text("d (nm): ")
                self.d_result_label = dpg.add_text("0")

    def find_lambda_lines(self):
        lims = dpg.get_axis_limits(self.wavelength_axis)
        dpg.set_value(self.lambda1_line, lims[0]+10)
        dpg.set_value(self.lambda2_line, lims[1]-10)

    def lambda1_input_changed(self):
        val = dpg.get_value(self.lambda1_input)
        dpg.set_value(self.lambda1_line, val)

    def lambda2_input_changed(self):
        val = dpg.get_value(self.lambda2_input)
        dpg.set_value(self.lambda2_line, val)

    def calculate_thickness(self):
        lambda1 = dpg.get_value(self.lambda1_input)
        lambda2 = dpg.get_value(self.lambda2_input)
        n = dpg.get_value(self.n_input)
        m = dpg.get_value(self.m_input)
        result = (m * lambda1 * lambda2)/(2 * n * (lambda2 - lambda1))
        dpg.set_value(self.d_result_label, result)

    def normalise_spectrum(self, spectrum):
        if self.dark_state_set and self.bright_state_set:
            bright_bg_removed = self.bright_state[1] - self.dark_state[1]
            spec_bg_removed = spectrum[1] - self.dark_state[1]
            normalised_spectrum = np.divide(spec_bg_removed, bright_bg_removed, out=np.zeros_like(
                spec_bg_removed), where=bright_bg_removed != 0)
            normalised_spectrum = [spectrum[0], normalised_spectrum]
            return normalised_spectrum

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
        self.draw_spectrum(self.spectrum)

    def draw_spectrum(self, spectrum):
        if self.bright_state_set and self.dark_state_set:
            spectrum = self.normalise_spectrum(spectrum)
            if self.first_time_normalising:
                self.scale_axes()
                self.first_time_normalising = False

        dpg.set_value(self.spectrum_graph, [
                      spectrum[0], spectrum[1]])

    def scale_axes(self):
        dpg.fit_axis_data(self.intensity_axis)
        dpg.fit_axis_data(self.wavelength_axis)

    def scale_x_axis(self):
        dpg.fit_axis_data(self.wavelength_axis)

    def scale_y_axis(self):
        dpg.fit_axis_data(self.intensity_axis)

    def _save_spectrum(self):
        save_path = dpg.get_value(self.output_folder) + \
            "\\" + dpg.get_value(self.output_file)
        print(f"Saving spectrum to {save_path}")
        normalised_spectrum = self.normalise_spectrum(self.spectrum)
        save_spectrum(save_path, normalised_spectrum,
                      self.spectrum, self.dark_state, self.bright_state, self.dark_state_set)

    def _set_integration_time(self):
        if self.spectrometer_attached:
            integration_time = dpg.get_value(self.int_time_input)
            self.spectrometer.integration_time_micros(integration_time)
            self.integration_time = integration_time
        else:
            print("ERROR: No spectrometer attached, cannot set integration time")

    def start_continuous_measurement(self):
        dpg.set_value(self.status, "Continuous Measurement")
        self.stop_thread = False
        self.get_spectra_thread = threading.Thread(
            target=get_spectrum, args=(self,))
        self.get_spectra_thread.daemon = True
        self.get_spectra_thread.start()
        self.continuous_measurement = True
        dpg.configure_item(self.continuous_measurement_button,
                           label="Stop Continuous Measurements", callback=self.stop_continuous_measurement)

    def stop_continuous_measurement(self):
        dpg.set_value(self.status, "Averaging Measurement: Idle")
        self.stop_thread = True
        self.get_spectra_thread.join()
        self.continuous_measurement = False
        dpg.configure_item(self.continuous_measurement_button,
                           label="Start Continuous Measurements", callback=self.start_continuous_measurement)

    def get_average_spectrum(self):
        self.stop_continuous_measurement()
        sum_spectrum = np.zeros_like(self.spectrum[1])
        wavelengths = self.spectrum[0]
        num_of_averages = dpg.get_value(self.number_of_averages_input)
        for i in range(num_of_averages):
            dpg.set_value(self.status, f"Averaging Measurement: #{i+1}")
            sum_spectrum += self.spectrometer.spectrum()[1]
        self.spectrum = [wavelengths, sum_spectrum/num_of_averages]
        dpg.set_value(self.status, "Averaging Measurement: Idle")
        self.draw_spectrum(self.spectrum)


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
