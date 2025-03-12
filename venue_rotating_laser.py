# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import enum
from dmx_controller import *

class StrobeMode(enum.IntEnum):
    RAW = 0
    CLOSED = enum.auto()
    OPEN = enum.auto()
    STROBE = enum.auto()
    INV_SAW = enum.auto()
    SAW = enum.auto()
    RAND = enum.auto()

    def to_dmx(self, param:int) -> int:
        # 000 to 007 -> OFF
        # 008 to 015 -> Open
        # 016 to 131 -> Strobe from slow to fast
        # 132 to 139 -> Open
        # 140 to 181 -> OFF fast and slow-open
        # 182 to 189 -> Open
        # 190 to 231 -> ON fast and slow OFF
        # 232 to 239 -> Open
        # 240 to 247 -> Random strobe
        # 248 to 255 -> Open
        if self == StrobeMode.RAW:
            raw = param
        elif self == StrobeMode.CLOSED:
            raw = 0
        elif self == StrobeMode.OPEN:
            raw = 255
        elif self == StrobeMode.STROBE:
            raw = param_to_dmx(16, 131, param)
        elif self == StrobeMode.INV_SAW:
            raw = param_to_dmx(140, 181, param)
        elif self == StrobeMode.SAW:
            raw = param_to_dmx(231, 190, param)
        elif self == StrobeMode.RAND:
            raw = 240

        return raw

class VenueRotatingLaser:
    CHANNEL_COUNT = 13

    def __init__(self, addr:int):
        self.addr : int = addr
        self.pan : int|float = 128
        self.tilt : int|float = 100
        self.tilt_spin : int = 0
        self.turn_speed : int|float = 0
        self.light_r : int|float = 0
        self.light_g : int|float = 0
        self.light_b : int|float = 0
        self.light_w : int|float = 0
        self.laser_dim : int|float = 0
        self.strobe : StrobeMode.OPEN
        self.strobe_param : int|float = 0
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
        dmx_ctrl.set_chan(self.addr, 10, self.strobe.to_dmx(self.strobe_param))
        dmx_ctrl.set_chan(self.addr, 11, float_to_dmx(self.open))
        dmx_ctrl.set_chan(self.addr, 12, self.dim_mode)
        dmx_ctrl.set_chan(self.addr, 13, self.multi_work_mode)
