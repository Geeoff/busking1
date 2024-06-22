# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
"""This script controls the lights at Conduit in Winter Park, FL."""
import enum
from metronome import Metronome
from dmx_controller import DmxController
from scanners_animator import ScannerState, ScannersAnimator
from conduit_animator import ConduitAnimator, UsherAsConduitAnimator
from color_math import *

####################################################################################################
class ConduitAnimatorMode(enum.IntEnum):
    NONE = 0
    CONDUIT = enum.auto()
    USHER = enum.auto()

class ColorSyncMode(enum.IntEnum):
    NONE = 0
    COMPLEMENT = enum.auto()
    TRIADIC = enum.auto()
    RAINBOW = enum.auto()

class VoidTerrorSilenceBusking:
    def __init__(self, conduit_animator_mode:ConduitAnimatorMode):
        super().__init__()

        # Init scanners.
        self.scanners_animator = ScannersAnimator()

        # Init conduit par.
        if conduit_animator_mode == ConduitAnimatorMode.NONE:
            self.conduit_animator = None
        elif conduit_animator_mode == ConduitAnimatorMode.CONDUIT:
            self.conduit_animator = ConduitAnimator()
        elif conduit_animator_mode == ConduitAnimatorMode.USHER:
            self.conduit_animator = UsherAsConduitAnimator()
        else:
            raise ValueError(f"Bad conduit_animator_mode '{conduit_animator_mode}'.")

        # Init color sync state.
        self.color_sync_mode = ColorSyncMode.NONE

    def tick(self, metronome:Metronome) -> None:
        # Update my own state.
        self._tick_color_sync()

        # Update animators.
        self.scanners_animator.tick(metronome)
        if self.conduit_animator is not None:
            self.conduit_animator.tick(metronome)

    def _tick_color_sync(self) -> None:
        if self.color_sync_mode != ColorSyncMode.NONE:
            # Get hue of the back pars.
            if self.conduit_animator.rainbow_is_enabled:
                par_hue = self.conduit_animator.rainbow_hue
            else:
                par_hue, _, _ = self.conduit_animator.gentle_sin_color.to_hsv()

            # Set scanner colors.
            if self.color_sync_mode == ColorSyncMode.COMPLEMENT:
                self.scanners_animator.set_comp_color(par_hue)
            elif self.color_sync_mode == ColorSyncMode.TRIADIC:
                self.scanners_animator.set_triadic_colors(par_hue)
            elif self.color_sync_mode == ColorSyncMode.RAINBOW:
                self.scanners_animator.set_rainbow(par_hue)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.scanners_animator.update_dmx(dmx_ctrl)
        if self.conduit_animator is not None:
            self.conduit_animator.update_dmx(dmx_ctrl)

####################################################################################################
if __name__ == "__main__":
    import argparse
    from busking_app import *
    from mpd218_input import *
    import scanners_animator
    import intimidator_scan_305_irc as scan_305_irc
    from more_math import *

    def busk(conduit_mode:ConduitAnimatorMode) -> None:
        with create_busking_app() as app:
            with Mpd218Input() as midi_input:
                busking = VoidTerrorSilenceBusking(conduit_mode)

                def tick_midi():
                    for evt in midi_input.poll():
                        # Handle pad events.
                        if type(evt) is PadTapEvent:
                            # Handle bank A of pads.
                            # This is the main page for actual busking.
                            if evt.bank == BANK_A:
                                # Get shift pad state.
                                is_shift_enabled = midi_input.pad_mtx(0,0,BANK_A).is_touched

                                # Row 3 has the SHIFT pad, but also handles scanner movements.
                                if evt.row == 0:
                                    if evt.col == 1:
                                        if is_shift_enabled:
                                            print("Straight Ahead")
                                            busking.scanners_animator.move_func = scanners_animator.straight_ahead_movement
                                        else:
                                            print("Wander")
                                            busking.scanners_animator.move_func = scanners_animator.WanderMovement()
                                    if evt.col == 2:
                                        if is_shift_enabled:
                                            print("Disco")
                                            busking.scanners_animator.move_func = scanners_animator.disco_movement
                                        else:
                                            print("SinCos")
                                            busking.scanners_animator.move_func = scanners_animator.nice_sincos_movement
                                    if evt.col == 3:
                                        if is_shift_enabled:
                                            print("Fig8")
                                            busking.scanners_animator.move_func = scanners_animator.fix8_movement
                                        else:
                                            print("Pendulum")
                                            busking.scanners_animator.move_func = scanners_animator.pendulum_movement

                            # Handle bank B of pads.
                            # This bank controls the color of the pars and scanners.
                            if evt.bank == BANK_B:
                                # Rows 0 and 1 control scanner colors.
                                if evt.row == 0:
                                    if evt.col == 3:
                                        busking.color_sync_mode = ColorSyncMode.TRIADIC
                                    else:
                                        colors = [
                                            scan_305_irc.ColorMode.ORANGE,
                                            scan_305_irc.ColorMode.PURPLE,
                                            scan_305_irc.ColorMode.WHITE]
                                        busking.scanners_animator.set_color(colors[evt.col])
                                        busking.color_sync_mode = ColorSyncMode.NONE
                                elif evt.row == 1:
                                    colors = [
                                        scan_305_irc.ColorMode.RED,
                                        scan_305_irc.ColorMode.GREEN,
                                        scan_305_irc.ColorMode.DARK_BLUE,
                                        scan_305_irc.ColorMode.SCROLL]
                                    busking.scanners_animator.set_color(colors[evt.col])
                                    busking.color_sync_mode = ColorSyncMode.NONE

                                # Rows 2 and 3 control par colors.
                                elif evt.row == 2:
                                    if evt.col == 3:
                                        busking.conduit_animator.start_rainbow()
                                    else:
                                        colors = [
                                            ColorRGB(1.0, 0.6, 0.0),
                                            ColorRGB(0.5, 0.0, 1.0),
                                            ColorRGB(1.0, 1.0, 1.0)]
                                        busking.conduit_animator.set_static_color(colors[evt.col])
                                elif evt.row == 3:
                                    colors = [
                                        ColorRGB(1.0, 0.0, 0.0),
                                        ColorRGB(0.0, 1.0, 0.0),
                                        ColorRGB(0.0, 0.0, 1.0),
                                        ColorRGB(0.0, 0.5, 1.0)]
                                    busking.conduit_animator.set_static_color(colors[evt.col])

                        # Handle knob events.
                        elif type(evt) == KnobClickEvent:
                            def adjust_val(cur_val, unit_delta, name, min_val=0.0, max_val=1.0):
                                new_val = cur_val + unit_delta * (max_val-min_val)
                                new_val = clamp(new_val, min_val, max_val)
                                print(f"{name} = {new_val:0.04}")
                                return new_val

                            # Handle bank A of knobs.
                            # This is the main bank for busking, with a focus on controls the wife will want to tweak.
                            if evt.bank == BANK_A:
                                if evt.col == 0:
                                    if evt.row == 1:
                                        dim = busking.conduit_animator.back_pars_min_dim + 1.0/32.0 * evt.clicks
                                        busking.conduit_animator.back_pars_min_dim = clamp(dim, 0.0, 1.0)
                                        busking.conduit_animator.back_pars_max_dim = \
                                            clamp(busking.conduit_animator.back_pars_max_dim, busking.conduit_animator.back_pars_min_dim, 1.0)
                                        print(f"back par dim range = [{busking.conduit_animator.back_pars_min_dim:0.04}, {busking.conduit_animator.back_pars_max_dim:0.04}]")
                                    elif evt.row == 2:
                                        dim = busking.conduit_animator.back_pars_max_dim + 1.0/32.0 * evt.clicks
                                        busking.conduit_animator.back_pars_max_dim = clamp(dim, 0.0, 1.0)
                                        busking.conduit_animator.back_pars_min_dim = \
                                            clamp(busking.conduit_animator.back_pars_min_dim, 0.0, busking.conduit_animator.back_pars_max_dim)
                                        print(f"back par dim range = [{busking.conduit_animator.back_pars_min_dim:0.04}, {busking.conduit_animator.back_pars_max_dim:0.04}]")
                                if evt.col == 1:
                                    if evt.row == 1:
                                        busking.scanners_animator.audience_dim_val = \
                                            adjust_val(busking.scanners_animator.audience_dim_val, evt.clicks / 32.0, "audience_dim_val")
                            elif evt.bank == BANK_B:
                                if evt.col == 1:
                                    if evt.row == 0:
                                         busking.scanners_animator.audience_dim_end = \
                                            adjust_val(busking.scanners_animator.audience_dim_end, evt.clicks / 32.0, "audience_dim_end",
                                                       -scan_305_irc.TILT_FLOAT_EXTENT, scan_305_irc.TILT_FLOAT_EXTENT)
                                    elif evt.row == 1:
                                        busking.scanners_animator.audience_dim_range = \
                                            adjust_val(busking.scanners_animator.audience_dim_range, evt.clicks / 64.0, "audience_dim_range",
                                                       0.0, 2.0 * scan_305_irc.TILT_FLOAT_EXTENT)

                def on_tick():
                    tick_midi()
                    busking.tick(app.metronome)
                    busking.update_dmx(app.dmx_ctrl)

                app.main_loop(on_tick)

    def main():
        arg_to_mode = {
            "conduit" : ConduitAnimatorMode.CONDUIT,
            "none" : ConduitAnimatorMode.NONE,
            "usher" : ConduitAnimatorMode.USHER,
            }

        parser = argparse.ArgumentParser()
        parser.add_argument("-cm", "--conduit-mode", choices=list(arg_to_mode.keys()), default="conduit")
        args = parser.parse_args()

        conduit_mode = arg_to_mode[args.conduit_mode]
        busk(conduit_mode)


    main()