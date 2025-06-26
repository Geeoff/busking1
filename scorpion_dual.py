# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import enum
import math
from dmx_controller import *

class ModeParam:
    def __init__(self, mode, param = 0):
        self.mode = mode
        self.param = param

    def to_dmx(self) -> int:
        return self.mode.to_dmx(self.param)

class ControlFunc(enum.IntEnum):
    RAW = 0
    DMX = enum.auto()
    AUTO_PROG = enum.auto()
    SOUND_ACTIVATED = enum.auto()
    
    def to_dmx(self, param:int) -> int:
        if self == ControlFunc.RAW:
            return param
        elif self == ControlFunc.DMX:
            return 0
        elif self == ControlFunc.AUTO_PROG:
            return 86
        elif self == ControlFunc.SOUND_ACTIVATED:
            return 171
        raise ValueError()

def strobe_to_dmx(hide:bool, strobe):
    if hide:
        return 0
    elif strobe is None:
        return 255
    else:
        return param_to_dmx(10, 249, strobe)

class Pattern(enum.IntEnum):
    RAW = 0
    CIRCLE = enum.auto()
    CIRCLE_WITH_DASHED_LINES = enum.auto()
    TRIANGLE = enum.auto()
    BOX = enum.auto()
    BOX_DONUT = enum.auto()
    DOUBLE_BOX = enum.auto()
    PLUS_SHAPE = enum.auto()
    SHURIKEN = enum.auto()
    L_SHAPE = enum.auto()
    BOWTIE = enum.auto()
    SPIRAL1 = enum.auto()
    TWO_PARTIAL_CIRCLES = enum.auto()
    SPIRAL2 = enum.auto()
    HINT_OF_CIRCLE = enum.auto()
    SUNGLASSES = enum.auto()
    ZIG_ZAG = enum.auto()
    V = enum.auto()
    M = enum.auto()
    SQUARE_WAVE = enum.auto()
    LINE = enum.auto()
    DASHED_LINES1 = enum.auto()
    LINE_WITH_DASHED_LINES = enum.auto()
    TWO_LINES_TOP_BOTTOM = enum.auto()
    PLUS_LINE = enum.auto()
    TWO_LINES_CORNERS = enum.auto()
    SCI_FI_CROSSHAIR = enum.auto()
    TWO_BOXES = enum.auto()
    FOUR_BOXES = enum.auto()
    SMALL_CIRCLE = enum.auto()
    DASHED_LINES2 = enum.auto()
    DASHED_HALF_CIRCLE = enum.auto()
    SPOTS = enum.auto()

    def to_dmx(self, param:int) -> int:
        if self == Pattern.RAW:
            return param
        elif self == Pattern.CIRCLE:
           return 0
        elif self == Pattern.CIRCLE_WITH_DASHED_LINES:
            return 8
        elif self == Pattern.TRIANGLE:
            return 16
        elif self == Pattern.BOX:
            return 24
        elif self == Pattern.BOX_DONUT:
            return 32
        elif self == Pattern.DOUBLE_BOX:
            return 40
        elif self == Pattern.PLUS_SHAPE:
            return 48
        elif self == Pattern.SHURIKEN:
            return 56
        elif self == Pattern.L_SHAPE:
            return 64
        elif self == Pattern.BOWTIE:
            return 72
        elif self == Pattern.SPIRAL1:
            return 80
        elif self == Pattern.TWO_PARTIAL_CIRCLES:
            return 88
        elif self == Pattern.SPIRAL2:
            return 96
        elif self == Pattern.HINT_OF_CIRCLE:
            return 104
        elif self == Pattern.SUNGLASSES:
            return 112
        elif self == Pattern.ZIG_ZAG:
            return 120
        elif self == Pattern.V:
            return 128
        elif self == Pattern.M:
            return 136
        elif self == Pattern.SQUARE_WAVE:
            return 144
        elif self == Pattern.LINE:
            return 152
        elif self == Pattern.DASHED_LINES1:
            return 160
        elif self == Pattern.LINE_WITH_DASHED_LINES:
            return 168
        elif self == Pattern.TWO_LINES_TOP_BOTTOM:
            return 176
        elif self == Pattern.PLUS_LINE:
            return 182
        elif self == Pattern.TWO_LINES_CORNERS:
            return 190
        elif self == Pattern.SCI_FI_CROSSHAIR:
            return 198
        elif self == Pattern.TWO_BOXES:
            return 206
        elif self == Pattern.FOUR_BOXES:
            return 214
        elif self == Pattern.SMALL_CIRCLE:
            return 222
        elif self == Pattern.DASHED_LINES2:
            return 230
        elif self == Pattern.DASHED_HALF_CIRCLE:
            return 238
        elif self == Pattern.SPOTS:
            return 246
        raise NotImplemented()

class ZoomMode(enum.IntEnum):
    RAW = 0
    PCT = enum.auto()
    ZOOM = enum.auto()
    ZOOM_BOUNCE = enum.auto()

    def to_dmx(self, param:int) -> int:
        if self == ZoomMode.RAW:
            return param
        elif self == ZoomMode.PCT:
            return 127 - param_to_dmx(0, 127, param)
        elif self == ZoomMode.ZOOM:
            if param < 0:
                return param_to_dmx(128, 169, -param)
            elif param > 0:
                return param_to_dmx(170, 209, param)
            else:
                return 0
        elif self == ZoomMode.ZOOM_BOUNCE:
            return param_to_dmx(210, 255, param)
        raise ValueError()

class RotMode(enum.IntEnum):
    RAW = 0
    POS = enum.auto()
    SPIN = enum.auto()

    def to_dmx(self, param:int) -> int:
        if self == RotMode.RAW:
            return param
        elif self == RotMode.POS:
            return param_to_dmx(0, 127, param)
        elif self == RotMode.SPIN:
            if param < 0:
                return param_to_dmx(128, 191, -param)
            elif param > 0:
                return param_to_dmx(192, 255, param)
            else:
                return 0
        raise ValueError()

class ScanMode(enum.IntEnum):
    RAW = 0
    SPEED = enum.auto()
    ACCEL = enum.auto()
    ACCEL_BOUNCE = enum.auto()

    def to_dmx(self, param:int) -> int:
        if self == ScanMode.RAW:
            return param
        elif self == ScanMode.SPEED:
            return 127 - param_to_dmx(0, 127, param)
        elif self == ScanMode.ACCEL:
            if param < 0:
                return param_to_dmx(128, 169, -param)
            elif param > 0:
                return param_to_dmx(170, 209, param)
            else:
                return 0
        elif self == ScanMode.ACCEL_BOUNCE:
            return param_to_dmx(210, 255, param)
        raise ValueError()


class ScorpionDual:
    """TBD"""

    CHANNEL_COUNT = 10

    def __init__(self, addr:int):
        self.addr = addr
        self.func = ModeParam(ControlFunc.DMX)
        self.hide = False
        self.strobe = None
        self.pattern = ModeParam(Pattern.L_SHAPE)
        self.zoom = ModeParam(ZoomMode.PCT, 1.0)
        self.rot_y = ModeParam(RotMode.POS)
        self.rot_x = ModeParam(RotMode.POS)
        self.rot_z = ModeParam(RotMode.POS)
        self.pan = ModeParam(RotMode.POS)
        self.tilt = ModeParam(RotMode.POS)
        self.scan = ModeParam(ScanMode.SPEED, 1.0)
        
    def update_dmx(self, dmx_ctrl:DmxController):
        dmx_ctrl.set_chan(self.addr, 1, self.func.to_dmx())
        dmx_ctrl.set_chan(self.addr, 2, strobe_to_dmx(self.hide, self.strobe))
        dmx_ctrl.set_chan(self.addr, 3, self.pattern.to_dmx())
        dmx_ctrl.set_chan(self.addr, 4, self.zoom.to_dmx())
        dmx_ctrl.set_chan(self.addr, 5, self.rot_y.to_dmx())
        dmx_ctrl.set_chan(self.addr, 6, self.rot_x.to_dmx())
        dmx_ctrl.set_chan(self.addr, 7, self.rot_z.to_dmx())
        dmx_ctrl.set_chan(self.addr, 8, self.pan.to_dmx())
        dmx_ctrl.set_chan(self.addr, 9, self.tilt.to_dmx())
        dmx_ctrl.set_chan(self.addr, 10, self.scan.to_dmx())
