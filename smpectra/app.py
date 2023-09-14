import dearpygui.dearpygui as dpg
from smpectra.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPectraUI


def main():
    dpg.create_context()

    dpg.create_viewport(
        title="SMPectra",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    ui = SMPectraUI()

    while dpg.is_dearpygui_running():

        dpg.render_dearpygui_frame()
    dpg.destroy_context()

    if ui.spectrometer_attached:
        ui.stop_thread = True
        ui.get_spectra_thread.join()
        ui.spectrometer.close()


if __name__ == "__main__":
    main()
