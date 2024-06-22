# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import lifxlan
from dmx_controller import DmxController
from generic_fixtures import ParDimRgb, ParDimRgbwStrobe
from color_math import ColorRGB
from metronome import Metronome

####################################################################################################
class BackParState:
    def __init__(self, addr:int):
        self.use_white = False
        self.color = ColorRGB(1.0, 1.0, 1.0)
        self.fixture = ParDimRgbwStrobe(addr)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        col = self.color.clamp()

        if self.use_white:
            # WARNING: This assume linear intensity!
            w = min(col.r, col.g, col.b)
            col.r = col.r - w
            col.g = col.g - w
            col.b = col.b - w

        else:
            w = 0.0

        self.fixture.r = col.r
        self.fixture.g = col.g
        self.fixture.b = col.b
        self.fixture.w = w

        self.fixture.update_dmx(dmx_ctrl)

class FrontParState:
    def __init__(self, addr:int):
        self.color = ColorRGB(1.0, 1.0, 1.0)
        self.fixture = ParDimRgb(addr)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        col = self.color.clamp()
        self.fixture.r = col.r
        self.fixture.g = col.g
        self.fixture.b = col.b
        self.fixture.update_dmx(dmx_ctrl)


####################################################################################################
class ConduitAnimatorBase:
    def __init__(self):
        self.gentle_sin_color = ColorRGB(0.5, 0.0, 1.0)

    def tick(self, metronome:Metronome) -> None:
        pass

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        raise NotImplemented


####################################################################################################
class ConduitAnimator(ConduitAnimatorBase):
    def __init__(self):
        super().__init__()
        self.back_par_list = [BackParState(17 + i*8) for i in range(7)]
        self.front_pars = BackParState(1)

    def tick(self, metronome:Metronome) -> None:
        # Update base state.
        super().tick(metronome)

        # Update back pars.
        for par in self.back_par_list:
            par.color = self.gentle_sin_color

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        for par in self.back_par_list:
            par.update_dmx(dmx_ctrl)
        self.front_pars.update_dmx(dmx_ctrl)


####################################################################################################
class UsherAsConduitAnimator(ConduitAnimatorBase):
    def __init__(self):
        super().__init__()
        self.lifx_lan = lifxlan.LifxLAN(5+2+2)
        self.bulb_list = list(self.lifx_lan.get_lights())

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        # Just kidding, update LIFX
        for bulb in self.bulb_list:
            h,s,v = self.gentle_sin_color.to_hsv()
            h = int(0xFFFF * h)
            s = int(0xFFFF * s)
            v = int(0xFFFF * v)
            bulb.set_color((h,s,v,65000))