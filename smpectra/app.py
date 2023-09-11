import seabreeze
# pyseabreeze backend doesn't work - not sure why. Doesn't matter yet... 
from seabreeze.spectrometers import Spectrometer, list_devices
import dearpygui.dearpygui as dpg
from ui import VIEWPORT_WIDTH, DRAW_HEIGHT, SMPectraUI

if __name__ == "__main__":

    dpg.create_context()

    dpg.create_viewport(
        title = "SMPectra",
        width=VIEWPORT_WIDTH,
        height=DRAW_HEIGHT)
    
    dpg.setup_dearpygui()
    dpg.show_viewport()
    ui = SMPectraUI()
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()

    dpg.destroy_context()





