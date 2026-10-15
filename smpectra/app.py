from pathlib import Path

import dearpygui.dearpygui as dpg

from smpectra.ui import DRAW_HEIGHT, VIEWPORT_WIDTH, SMPectraUI

# TODO: add ability to save 'd' values and average them
# TODO: fit the spectrum to find m...


def main():

    Path("../SMPectra_Data").mkdir(parents=True, exist_ok=True)
    dpg.create_context()
    font_path = Path("./assets/IosevkaNerdFont-Regular.ttf")
    with dpg.font_registry():
        default_font = dpg.add_font(font_path, 18)
    dpg.bind_font(default_font)
    dpg.create_viewport(title="SMPectra", width=VIEWPORT_WIDTH, height=DRAW_HEIGHT)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    ui = SMPectraUI()

    viewport_width = dpg.get_viewport_client_width()
    viewport_height = dpg.get_viewport_client_height()

    while dpg.is_dearpygui_running():
        if (
            viewport_width != dpg.get_viewport_client_width()
            or viewport_height != dpg.get_viewport_client_height()
        ):
            viewport_width = dpg.get_viewport_client_width()
            viewport_height = dpg.get_viewport_client_height()
            ui.draw_children(viewport_width, viewport_height)

        if ui.bright_state_set and ui.dark_state_set:
            ui.set_transmission_mode_button.show = True
        dpg.render_dearpygui_frame()
    dpg.destroy_context()

    if ui.spectrometer_attached:
        ui.stop_thread = True
        ui.get_spectra_thread.join()
        ui.spectrometer.close()


if __name__ == "__main__":
    main()
