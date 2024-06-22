# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
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
        # Init gentle sin state.
        self.gentle_sin_color = ColorRGB(0.5, 0.0, 1.0)
        self.gentle_sin_dimmer = 0.0

        # Init flash state.
        self.flash_counter = 0

        # Init rainbow state.
        self.rainbow_hue = 0.0
        self.rainbow_speed = 0.1
        self.rainbow_is_enabled = False

    def set_static_color(self, col:ColorRGB) -> None:
        self.rainbow_is_enabled = False
        self.gentle_sin_color = col

    def start_rainbow(self) -> None:
        self.rainbow_hue,_,_ = self.gentle_sin_color.to_hsv()
        self.rainbow_is_enabled = True

    def tick(self, metronome:Metronome) -> None:
        # Tick rainbow color
        self._tick_rainbow(metronome)

        # Update gentle sin wave
        sin_beat = metronome.get_beat_info(0.25)
        self.gentle_sin_dimmer = 0.5 * math.sin(2.0 * math.pi * sin_beat.t) + 0.5

        # Update flash
        flash_beat = metronome.get_beat_info()
        if flash_beat.this_frame:
            self.flash_counter = 5
        else:
            self.flash_counter -= 1

    def _tick_rainbow(self, metronome:Metronome) -> None:
        if self.rainbow_is_enabled:
            self.rainbow_hue = (self.rainbow_hue + self.rainbow_speed * metronome.dt) % 1.0

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
        print("Starting Conduit emulation with LIFX bulbs...")
        self.lifx_lan = lifxlan.LifxLAN()
        self.front_pars : lifxlan.Light | None = None
        self.back_pars : lifxlan.Light | None = None

        # FIXME: Sometimes get_lights fails. Keep trying until it works.
        while True:
            try:
                light_list = list(self.lifx_lan.get_lights())
                break
            except:
                print("get_lights failed...")
                pass

        # Only use the bar lights.
        # Trying to update all the lights is too laggy.
        front_par_label = "Bar Light 1"
        back_par_label = "Bar Light 2"

        for light in light_list:
            print(f"Found '{light.get_label()}'.")

            label = light.get_label()
            if label in (front_par_label, back_par_label):
                # Init light
                light.set_power(True, 0, False)
                light.set_color((0,0,0,65000))

                # Sort front and back lights.
                if label == front_par_label:
                    self.front_pars = light
                elif label == back_par_label:
                    self.back_pars = light

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        # Update front pars
        if self.flash_counter > 0:
            v = 0xFFFF
        else:
            v = 0
        lifx_col = (0,0,v,65000)
        self.front_pars.set_color(lifx_col, 0, True)

        # Update back pars
        if self.rainbow_is_enabled:
            lifx_col = (0xFFFF * self.rainbow_hue, 0xFFFF, 0xFFFF * self.gentle_sin_dimmer, 65000)
        else:
            dim_col = self.gentle_sin_color * self.gentle_sin_dimmer
            h,s,v = dim_col.to_hsv()
            lifx_col = (0xFFFF * h, 0xFFFF * s, 0xFFFF * v, 65000)

        self.back_pars.set_color(lifx_col, 0, True)