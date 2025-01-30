# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dmx_controller import *

class ParDimRgb:
    CHANNEL_COUNT = 4

    def __init__(self, addr:int):
        self.addr : int = addr
        self.dimmer : int|float = 0
        self.r : int|float = 0
        self.g : int|float = 0
        self.b : int|float = 0

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        dmx_ctrl.set_chan(self.addr, 1, float_to_dmx(self.dimmer))
        dmx_ctrl.set_chan(self.addr, 2, float_to_dmx(self.r))
        dmx_ctrl.set_chan(self.addr, 3, float_to_dmx(self.g))
        dmx_ctrl.set_chan(self.addr, 4, float_to_dmx(self.b))

class ParDimRgbwStrobe:
    CHANNEL_COUNT = 8

    def __init__(self, addr:int):
        self.addr : int = addr
        self.dimmer : int|float = 0
        self.r : int|float = 0
        self.g : int|float = 0
        self.b : int|float = 0
        self.w : int|float = 0
        self.strobe_speed : int|float = 0 # Seems to just go from slow to fast.
        self.color_cycle_raw : int = 0
        self.control_mode_raw : int = 0

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        dmx_ctrl.set_chan(self.addr, 1, float_to_dmx(self.dimmer))
        dmx_ctrl.set_chan(self.addr, 2, float_to_dmx(self.r))
        dmx_ctrl.set_chan(self.addr, 3, float_to_dmx(self.g))
        dmx_ctrl.set_chan(self.addr, 4, float_to_dmx(self.b))
        dmx_ctrl.set_chan(self.addr, 5, float_to_dmx(self.w))
        dmx_ctrl.set_chan(self.addr, 6, float_to_dmx(self.strobe_speed))
        dmx_ctrl.set_chan(self.addr, 7, self.color_cycle_raw)
        dmx_ctrl.set_chan(self.addr, 8, self.control_mode_raw)