# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import enum
import math
from dmx_controller import *
import more_math
from color_math import *

# Extent from center for pan and tilt as a float.
# pan range = [-PAN_EXTENT, PAN_EXTENT]
# tilt range = [-TILT_EXTENT, TILT_EXTENT]
PAN_FLOAT_EXTENT = 0.5 * math.pi
TILT_FLOAT_EXTENT = 0.25 * math.pi

class ColorMode(enum.IntEnum):
    RAW = 0

    # Solid colors
    WHITE       = enum.auto()
    YELLOW      = enum.auto()
    PURPLE      = enum.auto()
    GREEN       = enum.auto()
    RED         = enum.auto()
    LIGHT_BLUE  = enum.auto()
    KELLY_GREEN = enum.auto()
    ORANGE      = enum.auto()
    DARK_BLUE   = enum.auto()

    # Split Colors
    WHITE_AND_YELLOW           = enum.auto()
    YELLOW_AND_PURPLE          = enum.auto()
    PURPLE_AND_GREEN           = enum.auto()
    GREEN_AND_RED              = enum.auto()
    RED_AND_LIGHT_BLUE         = enum.auto()
    LIGHT_BLUE_AND_KELLY_GREEN = enum.auto()
    KELLY_GREEN_AND_ORANGE     = enum.auto()
    ORANGE_AND_DARK_BLUE       = enum.auto()
    DARK_BLUE_AND_WHITE        = enum.auto()

    # Scrolling
    SCROLL = enum.auto()

    @staticmethod
    def from_color_rgb(col:ColorRGB):
        mode_to_col = [
            (ColorMode.WHITE,  ColorRGB(1.0, 1.0, 1.0)),
            (ColorMode.YELLOW, ColorRGB(1.0, 1.0, 0.0)),
            (ColorMode.PURPLE, ColorRGB(0.75, 0.0, 1.0)),
            (ColorMode.GREEN,  ColorRGB(0.0, 1.0, 0.0)),
            (ColorMode.RED, ColorRGB(1.0, 0.0, 0.0)),
            (ColorMode.LIGHT_BLUE, ColorRGB(0.5, 0.5, 1.0)),
            #(ColorMode.KELLY_GREEN, ColorRGB().from_hex(0x4CBB17)), # This is barly different than green.
            (ColorMode.ORANGE, ColorRGB(1.0, 0.5, 0.0)),
            (ColorMode.DARK_BLUE, ColorRGB(0.0, 0.0, 1.0)),
        ]

        # Find the best color:
        best_mode = None
        best_col = None
        best_dist_sq = math.inf

        for test_mode, test_col in mode_to_col:
            test_dist_sq = (test_col - col).length_sq
            if test_dist_sq < best_dist_sq:
                best_mode = test_mode
                best_dist_sq = test_dist_sq

        return best_mode

    def to_dmx(self, param:int):
        # 000 to 006 -> white
        # 007 to 013 -> yellow
        # 014 to 020 -> purple
        # 021 to 027 -> green
        # 028 to 034 -> red
        # 035 to 041 -> light blue
        # 043 to 048 -> kelly green
        # 049 to 055 -> orange
        # 056 to 063 -> dark blue
        # 064 to 070 -> split color: while + yellow
        # 071 to 077 -> split color: yellow + purple
        # 078 to 084 -> split color: purple + green
        # 085 to 091 -> split color: green + red
        # 092 to 098 -> split color: red + light blue
        # 099 to 105 -> split color: light blue + kelly green
        # 106 to 112 -> split color: kelly green + orange
        # 113 to 119 -> split color: orange + dark blue
        # 120 to 127 -> split color: dark blue + white
        # 128 to 191 -> scroll CCW (slow to fast)
        # 192 to 255 -> scroll CW (slow to fast)
        if self == ColorMode.RAW:
            color = param

        elif self == ColorMode.SCROLL:
            if param < 0:
                # CCW
                color = param_to_dmx(192, 255, -param)
            else:
                # CW
                color = param_to_dmx(128, 192, param)

        else:
            color_map = {
                ColorMode.WHITE                      : 0,
                ColorMode.YELLOW                     : 7,
                ColorMode.PURPLE                     : 14,
                ColorMode.GREEN                      : 21,
                ColorMode.RED                        : 28,
                ColorMode.LIGHT_BLUE                 : 35,
                ColorMode.KELLY_GREEN                : 43,
                ColorMode.ORANGE                     : 49,
                ColorMode.DARK_BLUE                  : 56,
                ColorMode.WHITE_AND_YELLOW           : 64,
                ColorMode.YELLOW_AND_PURPLE          : 71,
                ColorMode.PURPLE_AND_GREEN           : 78,
                ColorMode.GREEN_AND_RED              : 85,
                ColorMode.RED_AND_LIGHT_BLUE         : 92,
                ColorMode.LIGHT_BLUE_AND_KELLY_GREEN : 99,
                ColorMode.KELLY_GREEN_AND_ORANGE     : 106,
                ColorMode.ORANGE_AND_DARK_BLUE       : 113,
                ColorMode.DARK_BLUE_AND_WHITE        : 120,
            }
            color = color_map[self]

        return color

class GoboMode(enum.IntEnum):
    RAW     = 0
    OPEN    = enum.auto()
    GOBO1   = enum.auto()
    GOBO2   = enum.auto()
    GOBO3   = enum.auto()
    GOBO4   = enum.auto()
    GOBO5   = enum.auto()
    GOBO6   = enum.auto()
    GOBO7   = enum.auto()
    SCROLL  = enum.auto()

    def to_dmx(self, param:int):
        # 000 to 007 -> open
        # 008 to 015 -> gobo 1 (glass)
        # 016 to 023 -> gogo 2 (glass)
        # 024 to 031 -> gogo 3
        # 032 to 039 -> gogo 4
        # 040 to 047 -> gogo 5
        # 048 to 055 -> gogo 6
        # 056 to 063 -> gogo 7
        # 064 to 071 -> gogo 7, shaking fast to slow
        # 072 to 079 -> gogo 6, shaking fast to slow
        # 080 to 087 -> gogo 5, shaking fast to slow
        # 088 to 095 -> gogo 4, shaking fast to slow
        # 096 to 103 -> gogo 3, shaking fast to slow
        # 104 to 111 -> gogo 2 (glass), shaking fast to slow
        # 112 to 119 -> gogo 1 (glass), shaking fast to slow
        # 120 to 127 -> open, shaking fast to slow
        # 128 to 191 -> scroll CCW
        # 192 to 255 -> scroll CW
        if self == GoboMode.RAW:
            gobo = param

        elif self == GoboMode.SCROLL:
            assert param != 0
            if param < 0:
                gobo = param_to_dmx(128, 191, -param)
            else:
                gobo = param_to_dmx(192, 255, param)

        elif param > 0:
            if type(param) is float:
                assert param <= 1.0
                speed = int(7 * param)
            else:
                assert param < 8
                speed = param - 7

            gobo_map = {
                GoboMode.OPEN: 120,
                GoboMode.GOBO1: 112,
                GoboMode.GOBO2: 104,
                GoboMode.GOBO3: 96,
                GoboMode.GOBO4: 88,
                GoboMode.GOBO5: 80,
                GoboMode.GOBO6: 72,
                GoboMode.GOBO7: 64,
            }
            gobo = gobo_map[self] + speed

        else:
            assert param == 0
            gobo_map = {
                GoboMode.OPEN: 0,
                GoboMode.GOBO1: 8,
                GoboMode.GOBO2: 16,
                GoboMode.GOBO3: 24,
                GoboMode.GOBO4: 32,
                GoboMode.GOBO5: 40,
                GoboMode.GOBO6: 48,
                GoboMode.GOBO7: 56,
            }
            gobo = gobo_map[self]

        return gobo

# FIXME!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
class GoboRotMode(enum.IntEnum):
    RAW = 0
    ANGLE = enum.auto()
    SPIN = enum.auto()
    BOUNCE = enum.auto()

    def to_dmx(self, param:int):
        # 000 to 063 -> indexing CCW
        # 064 to 147 -> rotate (slow to fast)
        # 148 to 191 -> rotate opposite (slow to fast)
        # 192 to 255 -> bounce
        if self == GoboRotMode.RAW:
            rot = param
        elif self == GoboRotMode.ANGLE:
            if type(param) is float:
                param = more_math.roll_over_unsigned(param)
                rot = int(63 * param / (2.0 * math.pi))
            else:
                rot = param_to_dmx(0, 63, param)
        elif self == GoboRotMode.SPIN:
            if param == 0:
                rot = 0
            elif param < 0:
                # CCW
                rot = param_to_dmx(148, 191, -param)
            else:
                # CW
                rot = param_to_dmx(64, 147, param)
        else:
            raise ValueError(f"Unexpected GoboRotMode value, {self}.")

        return rot

class ShutterMode(enum.IntEnum):
    RAW = 0
    CLOSED = enum.auto()
    OPEN = enum.auto()
    SYNC = enum.auto()
    PULSE = enum.auto()
    RAND = enum.auto()

    def to_dmx(self, param:int) -> int:
        # 000 to 003 -> closed
        # 004 to 007 -> open
        # 008 to 076 -> synchronized (slow to fast)
        # 077 to 145 -> pulse (slow to fast)
        # 146 to 215 -> random (slow to fast)
        # 216 to 255 -> open
        if self == ShutterMode.RAW:
            shutter = param
        elif self == ShutterMode.CLOSED:
            shutter = 0
        elif self == ShutterMode.OPEN:
            shutter = 255
        elif self == ShutterMode.SYNC:
            shutter = param_to_dmx(8, 76, param)
        elif self == ShutterMode.PULSE:
            shutter = param_to_dmx(77, 145, param)
        elif self == ShutterMode.RAND:
            shutter = param_to_dmx(146, 215, param)
        else:
            raise ValueError(f"Unexpected BarrelRotMode value, {self}.")

        return shutter

class Mode1:
    """This class is used to set the DMX channels for a Intimidator Scan/Barrel 305 IRC using
       Mode 1 (11-channel).  We need 11-channels if we want access to the dimmer.

       The class itself will not update a Intimidator on it's own.  Use the apply function to copy
       its state an FtdiDevice.  Then tell the FtdiDevice to send the new DMX state.

       This class is similar to the spec, but some settings are designed a little differently to
       make them easier to work work.  For these settings, a RAW mode is provided as back up, in
       case there are issues with the current design."""

    CHANNEL_COUNT = 11

    def __init__(self, addr:int):
        self.addr = addr
        self.pan = 128 # or -PI to PI
        self.tilt = 128 # or -PI to PI
        self.move_speed_raw = 0 # Fastest.  Shouldn't need to touch this?
        self.color = ColorMode.WHITE
        self.color_param = 0
        self.shutter = ShutterMode.OPEN
        self.shutter_param = 0
        self.dimmer = 255
        self.gobo = GoboMode.OPEN
        self.gobo_param = 0
        self.gobo_rot = GoboRotMode.SPIN
        self.gobo_rot_param = 0
        self.prism_raw = 0
        self.op_mode_raw = 0 # No Func
        self.move_macro_raw = 0 # No Func

    def update_dmx(self, dmx_ctrl:DmxController):
        dmx_ctrl.set_chan(self.addr, 1, angle_to_dmx(self.pan, PAN_FLOAT_EXTENT))
        dmx_ctrl.set_chan(self.addr, 2, angle_to_dmx(self.tilt, TILT_FLOAT_EXTENT))
        dmx_ctrl.set_chan(self.addr, 3, self.move_speed_raw)
        dmx_ctrl.set_chan(self.addr, 4, self.color.to_dmx(self.color_param))
        dmx_ctrl.set_chan(self.addr, 5, self.shutter.to_dmx(self.shutter_param))
        dmx_ctrl.set_chan(self.addr, 6, float_to_dmx(self.dimmer))
        dmx_ctrl.set_chan(self.addr, 7, self.gobo.to_dmx(self.gobo_param))
        dmx_ctrl.set_chan(self.addr, 8, self.gobo_rot.to_dmx(self.gobo_rot_param))
        dmx_ctrl.set_chan(self.addr, 9, self.prism_raw)
        dmx_ctrl.set_chan(self.addr, 10, self.op_mode_raw)
        dmx_ctrl.set_chan(self.addr, 11, self.move_macro_raw)
