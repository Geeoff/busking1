# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dmx_controller import *

class VenueRotatingLaser:
    CHANNEL_COUNT = 13

    def __init__(self, addr:int):
        self.addr : int = addr
        self.pan : int|float = 128
        self.tilt : int|float = 100
        self.tilt_spin : int|float = 0.0
        self.turn_speed : int|float = 255
        self.light_r : int|float = 0
        self.light_g : int|float = 0
        self.light_b : int|float = 0
        self.light_w : int|float = 0
        self.laser_dim : int|float = 0
        self.strobe_speed : int|float = 255
        self.open : int|float = 255
        self.dim_mode : int = 10 # Standard Mode - No delay
        self.multi_work_mode : int = 0

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        dmx_ctrl.set_chan(self.addr, 1, float_to_dmx(self.pan))
        dmx_ctrl.set_chan(self.addr, 2, float_to_dmx(self.tilt))
        dmx_ctrl.set_chan(self.addr, 3, self.tilt_spin)
        dmx_ctrl.set_chan(self.addr, 4, float_to_dmx(self.turn_speed))
        dmx_ctrl.set_chan(self.addr, 5, float_to_dmx(self.light_r))
        dmx_ctrl.set_chan(self.addr, 6, float_to_dmx(self.light_g))
        dmx_ctrl.set_chan(self.addr, 7, float_to_dmx(self.light_b))
        dmx_ctrl.set_chan(self.addr, 8, float_to_dmx(self.light_w))
        dmx_ctrl.set_chan(self.addr, 9, float_to_dmx(self.laser_dim))
        dmx_ctrl.set_chan(self.addr, 10, float_to_dmx(self.strobe_speed))
        dmx_ctrl.set_chan(self.addr, 11, float_to_dmx(self.open))
        dmx_ctrl.set_chan(self.addr, 12, self.dim_mode)
        dmx_ctrl.set_chan(self.addr, 13, self.multi_work_mode)
