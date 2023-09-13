import dearpygui.dearpygui as dpg
from smpectra.ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPectraUI
import time


def main():
    dpg.create_context()

    dpg.create_viewport(
        title="SMPectra",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    ui = SMPectraUI()
    start = time.time()
    while dpg.is_dearpygui_running():
        integration_time_in_seconds = ui.integration_time*1e-6
        if time.time() - start > integration_time_in_seconds + 0.1*integration_time_in_seconds:
            ui._get_spectrum()
            start = time.time()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


if __name__ == "__main__":
    main()
