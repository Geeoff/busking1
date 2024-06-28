# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
import time
import lifxlan
from more_math import *
from dmx_controller import DmxController
from generic_fixtures import ParDimRgb, ParDimRgbwStrobe
from color_math import ColorRGB
from metronome import Metronome
from dimmer_animators import *

####################################################################################################
class BackParState:
    def __init__(self):
        self.fixture = None

        #self.base_color = ColorRGB() #TODO
        self.base_dimmer = 1.0

        self.color = ColorRGB()
        self.strobe_speed = None

class FrontParState:
    def __init__(self):
        self.fixture = None
        self.color = ColorRGB()
        self.dimmer = 1.0

####################################################################################################
class ConduitAnimatorBase:
    def __init__(self):
        # Init par states.
        self.front_pars = FrontParState()
        self.back_par_list = [BackParState() for _ in range(7)]

        # Init master controls.
        self.back_pars_master_dimmer = 1.0
        self.back_pars_min_dim = 0.0

        # Init color
        self.base_color = ColorRGB(0.5, 0.0, 1.0)

        # Init dimmers
        self.cos_dimmer_animator = CosDimmerAnimator(0.25)
        self.quick_chase_dimmer_animator = QuickChaseDimmerAnimator(1.0)
        self.saw_dimmer_animator = SawDimmerAnimator(1.0)
        self.alt_saw_dimmer_animator = AltSawDimmerAnimator(1.0)
        self.double_pulse_dimmer_animator = DoublePulseDimmerAnimator(1.0)
        self.dimmer_animator = self.cos_dimmer_animator

        # Init flash state.
        self.flash_counter = 0

        # Init rainbow state.
        self.rainbow_hue = 0.0
        self.rainbow_speed = 0.1
        self.rainbow_is_enabled = False

        # Init strobe state.
        self.back_pars_strobe_enabled = False
        self.back_pars_strobe_speed = 1.0

        # Init blackout FX state.
        self.blackout_enabled = False

        # Init long flash state.
        self.long_flash_lifespan = 1.0
        self.long_flash_start_time = 0.0
        self.long_flash_col = ColorRGB(1.0, 1.0, 1.0)
        self.long_flash_blend = 0.0

    def set_static_color(self, col:ColorRGB) -> None:
        self.rainbow_is_enabled = False
        self.base_color = col

    def start_rainbow(self) -> None:
        self.rainbow_hue,_,_ = self.base_color.to_hsv()
        self.rainbow_is_enabled = True

    def start_long_flash(self) -> None:
        self.long_flash_start_time = time.perf_counter()

    def tick(self, metronome:Metronome) -> None:
        self._tick_dimmer_animator(metronome)
        self._tick_rainbow(metronome)
        #self._tick_flash(metronome)
        self._tick_long_flash()
        self._update_front_pars_color()
        self._update_back_pars_colors()

    def _tick_dimmer_animator(self, metronome:Metronome) -> None:
        dimmer_list = self.dimmer_animator.tick(metronome, len(self.back_par_list))
        for i, par in enumerate(self.back_par_list):
            par.base_dimmer = dimmer_list[i]

    def _tick_rainbow(self, metronome:Metronome) -> None:
        if self.rainbow_is_enabled:
            self.rainbow_hue = (self.rainbow_hue + self.rainbow_speed * metronome.dt) % 1.0

    def _tick_flash(self, metronome:Metronome) -> None:
        flash_beat = metronome.get_beat_info()
        if flash_beat.this_frame:
            self.flash_counter = 5
        else:
            self.flash_counter -= 1

    def _tick_long_flash(self) -> None:
        # Calc blend amount.
        age = time.perf_counter() - self.long_flash_start_time
        self.long_flash_blend = max(0.0, 1.0 -  age / self.long_flash_lifespan)

        # Calc color. Go from bright white to very warm as this effect dims.
        self.long_flash_col = ColorRGB().from_hsv(0.2, 1.0 - self.long_flash_blend, 1.0)

    def _update_front_pars_color(self) -> None:
        if self.blackout_enabled:
            col = ColorRGB() # black

        else:
            flash_val = 1.0 if self.flash_counter > 0 else 0
            col = ColorRGB(flash_val, flash_val, flash_val)

        # Apply long flash.
        self.front_pars.color = lerp(col, self.long_flash_col, self.long_flash_blend)

    def _update_back_pars_colors(self) -> ColorRGB:
        for par in self.back_par_list:
            if self.blackout_enabled:
                col = ColorRGB() # black

            else:
                # Calc color
                if self.rainbow_is_enabled:
                    col = ColorRGB.from_hsv(self.rainbow_hue, 1.0, 1.0)
                else:
                    col = self.base_color

                # Apply dimmer.
                dim = lerp(self.back_pars_min_dim, self.back_pars_master_dimmer, par.base_dimmer)
                dim = max(self.back_pars_min_dim, dim)
                col = col * dim

            # Apply long flash.
            par.color = lerp(col, self.long_flash_col, self.long_flash_blend)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        raise NotImplemented


####################################################################################################
class ConduitAnimator(ConduitAnimatorBase):
    def __init__(self):
        super().__init__()

        # Init fixtures.
        self.front_pars.fixture = ParDimRgb(1)
        for i, par in enumerate(self.back_par_list):
            par.fixture = ParDimRgbwStrobe(17 + i*ParDimRgbwStrobe.CHANNEL_COUNT)

        # global DMX settings
        self.back_pars_use_white = False

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self._update_front_par_dmx(self.front_pars, dmx_ctrl)
        for par in self.back_par_list:
            self._update_back_par_dmx(par, dmx_ctrl)

    def _update_front_par_dmx(self, par:FrontParState, dmx_ctrl:DmxController):
        col = par.color.clamp()
        par.fixture.dimmer = 1.0
        par.fixture.r = col.r
        par.fixture.g = col.g
        par.fixture.b = col.b
        par.fixture.update_dmx(dmx_ctrl)

    def _update_back_par_dmx(self, par:BackParState, dmx_ctrl:DmxController):
        col = par.color.clamp()

        if self.back_pars_use_white:
            # WARNING: This assume linear intensity!
            w = min(col.r, col.g, col.b)
            col.r = col.r - w
            col.g = col.g - w
            col.b = col.b - w

        else:
            w = 0.0

        par.fixture.dimmer = 1.0
        par.fixture.r = col.r
        par.fixture.g = col.g
        par.fixture.b = col.b
        par.fixture.w = w
        par.fixture.strobe_speed = self.back_pars_strobe_speed if self.back_pars_strobe_enabled else 0.0
        par.fixture.update_dmx(dmx_ctrl)


####################################################################################################
class UsherAsConduitAnimator(ConduitAnimatorBase):
    def __init__(self):
        super().__init__()
        print("Starting Conduit emulation with LIFX bulbs...")
        self.lifx_lan = lifxlan.LifxLAN()

        # FIXME: Sometimes get_lights fails. Keep trying until it works.
        while True:
            try:
                light_list = list(self.lifx_lan.get_lights())
                break
            except:
                print("  get_lights failed. Trying again...")
                pass

        # Only use the bar lights.
        # Trying to update all the lights is too laggy.
        front_par_label = "Bar Light 1"
        back_par_label = "Bar Light 2"

        for light in light_list:
            print(f"  Found '{light.get_label()}'.")

            label = light.get_label()
            if label in (front_par_label, back_par_label):
                # Init light
                light.set_power(True, 0, False)
                light.set_color((0,0,0,65000))

                # Sort front and back lights.
                if label == front_par_label:
                    self.front_pars.fixture = light
                elif label == back_par_label:
                    self.back_par_list[0].fixture = light

        if self.front_pars.fixture is None:
            print(f"  ERROR: Did not find '{front_par_label}' to use a front par.")
        if self.back_par_list[0].fixture is None:
            print(f"  ERROR: Did not find '{back_par_label}' to use a back par.")

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        def update_light(par:FrontParState|BackParState):
            if par.fixture is not None:
                color = par.color.clamp()
                h,s,v = color.to_hsv()
                lifx_color = (0xFFFF * h, 0xFFFF * s, 0xFFFF * v, 65000)
                par.fixture.set_color(lifx_color, 0, True)

        update_light(self.front_pars)
        for par in self.back_par_list:
            update_light(par)