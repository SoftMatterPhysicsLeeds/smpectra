import dearpygui.dearpygui as dpg
from smpectra.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPectraUI
import time
import threading


def get_spectrum(ui):
    first_time = True
    start = time.time()
    while True:
        if ui.stop_thread:
            print("Stopping acquisition thread...")
            break
        integration_time_in_seconds = ui.integration_time*1e-6
        if time.time() - start > integration_time_in_seconds + 0.1*integration_time_in_seconds:
            ui._get_spectrum()
            if first_time:
                ui.scale_axes()
                first_time = False
            start = time.time()


def main():
    dpg.create_context()

    dpg.create_viewport(
        title="SMPectra",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    ui = SMPectraUI()
    get_spectra_thread = threading.Thread(target=get_spectrum, args=(ui,))
    get_spectra_thread.daemon = True
    get_spectra_thread.start()

    while dpg.is_dearpygui_running():

        dpg.render_dearpygui_frame()
    ui.stop_thread = True
    get_spectra_thread.join()
    dpg.destroy_context()
    ui.spectrometer.close()


if __name__ == "__main__":
    main()
