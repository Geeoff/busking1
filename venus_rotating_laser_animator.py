# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from turtle import speed
from venue_rotating_laser import VenueRotatingLaser
from dmx_controller import *
from metronome import Metronome
from color_math import ColorRGB

class PingPongAnim:
    def __init__(self, speed):
        self.x = 0.0
        self.speed = speed

    def tick(self, delta_secs:float) -> None:
        self.x = (self.x + self.speed * delta_secs) % 1.0

    def get_val(self) -> float:
        if self.x <= 0.5:
            return 2.0 * self.x
        else:
            return 2.0 * (1.0 - self.x)

class VenueRotatingLaserAnimator:
    def __init__(self, addr : int = 1):
        self.device = VenueRotatingLaser(addr)

        self.master_dimmer = 1.0
        self.light_dimmer = 1.0
        self.light_color = ColorRGB()

        self.device.pan = 0.0 # convert to float
        self.pan_anim = PingPongAnim(0.005)
        self.tilt_anim = PingPongAnim(0.005)
        self.device.turn_speed = 255

        # 000�020 Stda(Standard)
        # 021�040 StGE(Stage)
        # 041�060 tv(TV)
        # 061�080 ArAL(Architectural)
        # 081�100 tHAL(Theatrical)
        # 101�255 Default setting
        self.device.dim_mode = 10 
        
    def tick(self, metronome:Metronome) -> None:
        self._tick_color()
        self._tick_rot(metronome.delta_secs)

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
        self.device.light_w = w

        #self.device.open = self.master_dimmer * self.light_dimmer
        self.device.laser_dim = self.master_dimmer

    def _tick_rot(self, delta_secs:float) -> None:
        self.pan_anim.tick(delta_secs)
        self.device.pan = self.pan_anim.get_val()
        self.tilt_anim.tick(delta_secs)
        self.device.tilt = self.tilt_anim.get_val()
        
    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.device.update_dmx(dmx_ctrl)
