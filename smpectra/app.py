import dearpygui.dearpygui as dpg
from smpectra.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPectraUI
from pathlib import Path

def main():
    dpg.create_context()
    font_path = Path("./assets/IosevkaNerdFont-Regular.ttf")
    with dpg.font_registry():
        default_font = dpg.add_font(
            font_path, 18)

    dpg.bind_font(default_font)
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
