# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from venue_rotating_laser import VenueRotatingLaser
from dmx_controller import *
from metronome import Metronome
from color_math import ColorRGB

class VenueRotatingLaserAnimator:
    def __init__(self, addr : int = 1):
        self.device = VenueRotatingLaser(addr)

        self.master_dimmer = 1.0
        self.light_dimmer = 1.0
        self.light_color = ColorRGB()

        self.device.pan = 0.0 # convert to float
        self.pan_speed = 0.01
        self.pan_dir = 1

        # Slow spin
        self.device.tilt_spin = 189

        # Test
        self.device.laser_dim = 255

        # 000–020 Stda(Standard)
        # 021–040 StGE(Stage)
        # 041–060 tv(TV)
        # 061–080 ArAL(Architectural)
        # 081–100 tHAL(Theatrical)
        # 101–255 Default setting
        self.device.dim_mode = 10 
        
    def tick(self, metronome:Metronome) -> None:
        self._tick_color()
        self._tick_pan(metronome)

    def _tick_color(self) -> None:
        dim = self.master_dimmer * self.light_dimmer
        r = dim * self.light_color.r
        g = dim * self.light_color.g
        b = dim * self.light_color.b

        w = min(r, g, b)
        r -= w
        g -= w
        b -= w

        self.device.light_r = r
        self.device.light_g = g
        self.device.light_b = b

        #self.device.open = self.master_dimmer * self.light_dimmer
        self.device.laser_dim = self.master_dimmer

    def _tick_pan(self, metronome:Metronome) -> None:
        delta_pan = self.pan_speed * metronome.delta_secs

        if self.pan_dir >= 0:
            self.device.pan += delta_pan
            if self.device.pan >= 1.0:
                self.device.pan = 2.0 - self.device.pan
                self.pan_dir = -1
        else:
            self.device.pan -= delta_pan
            if self.device.pan < 0.0:
                self.device.pan = -self.device.pan
                self.pan_dir = 1
        
    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.device.update_dmx(dmx_ctrl)
