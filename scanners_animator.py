# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
from dmx_controller import *
import intimidator_scan_305_irc as scan_305_irc
from metronome import Metronome
from rotation_math import *

####################################################################################################
class ScannerState:
    def __init__(self, dmx_offset:int):
        self.color = scan_305_irc.ColorMode.WHITE
        self.dimmer = 1.0
        self.rot = EulerAngles()
        self.use_roll = True
        self.strobe_speed = None
        self.fixture = scan_305_irc.Mode1(dmx_offset)
        
    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        # Update dimmer and color.
        self.fixture.color = self.color
        self.fixture.dimmer = self.dimmer

        # Update rotation.
        rot = self.rot.roll_over_signed()
        self.fixture.pan = rot.yaw
        self.fixture.tilt = rot.pitch
        
        if self.use_roll:
            self.fixture.gobo_rot = scan_305_irc.GoboRotMode.ANGLE
            self.fixture.gobo_rot_param = rot.roll
            
        # Update strobe.
        if self.strobe_speed is None:
            self.fixture.shutter = scan_305_irc.ShutterMode.OPEN
        else:
            self.fixture.shutter = scan_305_irc.ShutterMode.PULSE
            self.fixture.shutter_param = self.strobe_speed

        # Sync with DMX controller.
        self.fixture.update_dmx(dmx_ctrl)
        
####################################################################################################
class ScannersAnimator:
    def __init__(self, start_addr=101):
        self.scanner_list = [ScannerState(start_addr + i*scan_305_irc.Mode1.CHANNEL_COUNT) \
                             for i in range(4)]
        
    def tick(self, metronome:Metronome) -> None:
        pass
        
    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        for scanner in self.scanner_list:
            scanner.update_dmx(dmx_ctrl)