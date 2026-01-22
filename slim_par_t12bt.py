# Copyright 2026, Geoffrey Caagle (geoff.v.cagle@gmail.com)
from dmx_controller import DmxController, float_to_dmx

class SlimPar_T12BT_7Ch:
    CHANNEL_COUNT = 7

    def __init__(self, addr:int):
        self.addr : int = addr
        self.r : int|float = 0
        self.g : int|float = 0
        self.b : int|float = 0
        self.strobe_speed : int|float = 0  # "0-20 Hz, slow to fast"
        self.prog_raw : int = 0
        self.prog_speed_raw : int|float = 0  # "Slow to fast"
        self.dimmer : int|float = 0  # Doc says "Auto and sound programs".

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        dmx_ctrl.set_chan(self.addr, 1, float_to_dmx(self.r))
        dmx_ctrl.set_chan(self.addr, 2, float_to_dmx(self.g))
        dmx_ctrl.set_chan(self.addr, 3, float_to_dmx(self.b))
        dmx_ctrl.set_chan(self.addr, 4, float_to_dmx(self.strobe_speed))
        dmx_ctrl.set_chan(self.addr, 5, self.prog_raw)
        dmx_ctrl.set_chan(self.addr, 6, float_to_dmx(self.prog_speed_raw))
        dmx_ctrl.set_chan(self.addr, 7, float_to_dmx(self.dimmer))