# Copyright 2024-2026, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import enum
import math
import time
import lifxlan
from more_math import *
from dmx_controller import DmxController
from generic_fixtures import ParDimRgb, ParDimRgbwStrobe
from slim_par_t12bt import SlimPar_T12BT_7Ch
from color_math import ColorRGB
from metronome import Metronome
from dimmer_animators import *

####################################################################################################
class ParState:
    def __init__(self):
        self.fixture = None
        self.base_dimmer = 1.0
        self.color = ColorRGB()
        self.strobe_speed = None
        self.enabled = True

####################################################################################################
class ConduitAnimatorBase:
    def __init__(self):
        # Init par states.
        self.front_par_list = [ParState() for _ in range(10)]
        self.mid_par_list = [ParState() for _ in range(4)]
        self.back_par_list = [ParState() for _ in range(10)]

        # Disable back pars over the projector.
        for i in range(3,7):
            self.back_par_list[i].enabled = False
            self.front_par_list[i].enabled = False

        # Init master controls.
        self.pars_master_dimmer = 1.0
        self.pars_master_dimmer = 1.0

        # Init color
        self.base_color = ColorRGB(0.5, 0.0, 1.0) # Purple

        # Init dimmers
        self.cos_dimmer_animator = CosDimmerAnimator(0.25)
        self.quick_chase_dimmer_animator = QuickChaseDimmerAnimator(1.0)
        self.saw_dimmer_animator = SawDimmerAnimator(1.0)
        self.alt_saw_dimmer_animator = AltSawDimmerAnimator(1.0)
        self.double_pulse_dimmer_animator = DoublePulseDimmerAnimator(1.0)
        self.dimmer_animator = self.cos_dimmer_animator

        # Init flash state.
        self.beat_flash_enabled = False
        self.beat_flash_speed = 2
        self.flash_counter = 0

        # Init rainbow state.
        self.rainbow_hue = 0.0
        self.rainbow_speed = 0.1
        self.rainbow_is_enabled = False
        self.rainbow_spread = 0.0

        # Init strobe state.
        self.pars_strobe_enabled = False
        self.pars_strobe_speed = 1.0

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

    def is_static_color(self) -> bool:
        return not self.rainbow_is_enabled

    def get_static_color(self) -> None | ColorRGB:
        if self.is_static_color():
            return self.base_color
        else:
            return None

    def set_rainbow_color(self) -> None:
        #self.rainbow_hue,_,_ = self.base_color.to_hsv()
        self.rainbow_is_enabled = True

    def is_rainbow_color(self) -> bool:
        return self.rainbow_is_enabled

    def start_long_flash(self) -> None:
        self.long_flash_start_time = time.perf_counter()

    def start_quick_flash(self) -> None:
        self.flash_counter = 3

    def tick(self, metronome:Metronome) -> None:
        self._tick_dimmer_animator(metronome)
        self._tick_rainbow(metronome)
        self._tick_flash(metronome)
        self._tick_long_flash()
        self._update_front_and_back_par_colors()
        self._update_mid_par_colors()

    def _tick_dimmer_animator(self, metronome:Metronome) -> None:
        if self.dimmer_animator == self.quick_chase_dimmer_animator:
            # HACK: Just chase on enabled pars and mirror front and back.
            dimmer_list = self.dimmer_animator.tick(metronome, 3)
            # Reverse dimmer_list so we go from the inside out.
            dimmer_list = reversed(dimmer_list)
            for i, base_dimmer in enumerate(dimmer_list):
                # Left side
                par = self.front_par_list[i]
                par.base_dimmer = base_dimmer
                par = self.back_par_list[i]
                par.base_dimmer = base_dimmer
                # Right side
                j = -1-i
                par = self.front_par_list[j]
                par.base_dimmer = base_dimmer
                par = self.back_par_list[j]
                par.base_dimmer = base_dimmer
        else:
            dimmer_list = self.dimmer_animator.tick(metronome, len(self.front_par_list))
            for i, base_dimmer in enumerate(dimmer_list):
                # Mirror the dimmer values on front and back pars.
                front_par = self.front_par_list[i]
                front_par.base_dimmer = base_dimmer
                # Reverse order on  the front pars, so that AltSawDimmerAnimator alternates front to back, as well as
                # left to right.
                back_par = self.back_par_list[len(self.front_par_list)-1-i]
                back_par.base_dimmer = base_dimmer

    def _tick_rainbow(self, metronome:Metronome) -> None:
        self.rainbow_hue = (self.rainbow_hue + self.rainbow_speed * metronome.delta_secs) % 1.0

    def _tick_flash(self, metronome:Metronome) -> None:
        if self.beat_flash_enabled:
            flash_beat = metronome.get_beat_info()
            if flash_beat.this_frame:
                if self.beat_flash_speed == 4:
                    flash_this_beat = True
                else:
                    is_odd = (flash_beat.count & 1) != 0
                    flash_this_beat = is_odd
                    
                if flash_this_beat:
                    self.start_quick_flash()  
                    
        self.flash_counter -= 1

    def _tick_long_flash(self) -> None:
        # Calc blend amount.
        age = time.perf_counter() - self.long_flash_start_time
        self.long_flash_blend = max(0.0, 1.0 -  age / self.long_flash_lifespan)

        # Calc color. Go from bright white to very warm as this effect dims.
        self.long_flash_col = ColorRGB().from_hsv(0.2, 1.0 - self.long_flash_blend, 1.0)

    def _update_front_and_back_par_colors(self) -> None:
        # Iterate front and back pars together. Color will be mirrored between them, but flashes and dimmer values may
        # be different.
        for i, front_par in enumerate(self.front_par_list):
            back_par = self.back_par_list[i]

            # Calculate a base color.
            if self.blackout_enabled:
                base_color = ColorRGB() # black
            elif self.rainbow_is_enabled:
                t = i / (len(self.front_par_list) - 1)
                hue = self.rainbow_hue + t * self.rainbow_spread
                base_color = ColorRGB.from_hsv(hue, 1.0, 1.0)
            else:
                base_color = self.base_color

            # Update front par.
            front_dim = front_par.base_dimmer * self.pars_master_dimmer
            front_par.color = base_color * front_dim

            # Update back par.
            if self.flash_counter > 0:
                back_color = ColorRGB(1.0, 1.0, 1.0) # white
            else:
                back_dim = back_par.base_dimmer * self.pars_master_dimmer
                back_color = base_color * back_dim
                back_color = lerp(back_color, self.long_flash_col, self.long_flash_blend)
            back_par.color = back_color

    def _update_mid_par_colors(self) -> None:
        # Just update the outside pars, because in the inside pars face the screen.
        if self.flash_counter > 0:
            mid_color = ColorRGB(1.0, 1.0, 1.0) # white
        else:
            mid_color = self.long_flash_col * self.long_flash_blend

        self.mid_par_list[0].color = mid_color
        self.mid_par_list[-1].color = mid_color

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        raise NotImplemented


####################################################################################################
class ConduitAnimator(ConduitAnimatorBase):
    def __init__(self):
        super().__init__()

        self.old_pars_use_white = False

        # Init fixtures.
        for i, front_par in enumerate(self.front_par_list):
            front_par.fixture = ParDimRgbwStrobe(1 + i*ParDimRgbwStrobe.CHANNEL_COUNT)
        for i, mid_par in enumerate(self.mid_par_list):
            mid_par.fixture = ParDimRgbwStrobe(151 + i*ParDimRgbwStrobe.CHANNEL_COUNT)
        for i, back_par in enumerate(self.back_par_list):
            # Add in reverse so they mirror the order of the front pars.
            j = len(self.back_par_list) - i - 1
            back_par.fixture = SlimPar_T12BT_7Ch(81 + j*SlimPar_T12BT_7Ch.CHANNEL_COUNT)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        for par in self.front_par_list:
            self._update_old_par_dmx(par, dmx_ctrl)
        for par in self.mid_par_list:
            self._update_old_par_dmx(par, dmx_ctrl)
        for par in self.back_par_list:
            self._update_new_par_dmx(par, dmx_ctrl)

    def _update_old_par_dmx(self, par:ParState, dmx_ctrl:DmxController):
        if not par.enabled:
            return

        col = par.color.clamp()

        if self.old_pars_use_white:
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
        par.fixture.strobe_speed = self.pars_strobe_speed if self.pars_strobe_enabled else 1.0
        par.fixture.update_dmx(dmx_ctrl)

    def _update_new_par_dmx(self, par:ParState, dmx_ctrl:DmxController):
        if not par.enabled:
            return

        col = par.color.clamp()
        par.fixture.r = col.r
        par.fixture.g = col.g
        par.fixture.b = col.b
        par.fixture.strobe_speed = self.pars_strobe_speed if self.pars_strobe_enabled else 1.0
        par.fixture.prog_raw = 0
        par.fixture.prog_speed_raw = 0
        par.fixture.dimmer = 1.0
        par.fixture.update_dmx(dmx_ctrl)

#####################################################################################################
#class UsherAsConduitAnimator(ConduitAnimatorBase):
#    def __init__(self):
#        super().__init__()
#        print("Starting Conduit emulation with LIFX bulbs...")
#        self.lifx_lan = lifxlan.LifxLAN()
#
#        # FIXME: Sometimes get_lights fails. Keep trying until it works.
#        while True:
#            try:
#                light_list = list(self.lifx_lan.get_lights())
#                break
#            except:
#                print("  get_lights failed. Trying again...")
#                pass
#
#        # Only use the bar lights.
#        # Trying to update all the lights is too laggy.
#        front_par_label = "Bar Light 1"
#        back_par_label = "Bar Light 2"
#
#        for light in light_list:
#            print(f"  Found '{light.get_label()}'.")
#
#            label = light.get_label()
#            if label in (front_par_label, back_par_label):
#                # Init light
#                light.set_power(True, 0, False)
#                light.set_color((0,0,0,65000))
#
#                # Sort front and back lights.
#                if label == front_par_label:
#                    self.front_pars.fixture = light
#                elif label == back_par_label:
#                    self.back_par_list[0].fixture = light
#
#        if self.front_pars.fixture is None:
#            print(f"  ERROR: Did not find '{front_par_label}' to use a front par.")
#        if self.back_par_list[0].fixture is None:
#            print(f"  ERROR: Did not find '{back_par_label}' to use a back par.")
#
#    def update_dmx(self, dmx_ctrl:DmxController) -> None:
#        def update_light(par:FrontParState|BackParState):
#            if par.fixture is not None:
#                color = par.color.clamp()
#                h,s,v = color.to_hsv()
#                lifx_color = (0xFFFF * h, 0xFFFF * s, 0xFFFF * v, 65000)
#                par.fixture.set_color(lifx_color, 0, True)
#
#        update_light(self.front_pars)
#        for par in self.back_par_list:
#            update_light(par)