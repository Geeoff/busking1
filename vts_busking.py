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

    def tick(self, metronome:Metronome) -> None:
        self.scanners_animator.tick(metronome)
        if self.conduit_animator is not None:
            self.conduit_animator.tick(metronome)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.scanners_animator.update_dmx(dmx_ctrl)
        if self.conduit_animator is not None:
            self.conduit_animator.update_dmx(dmx_ctrl)

####################################################################################################
if __name__ == "__main__":
    from busking_app import *
    from mpd218_input import *
    import scanners_animator
    import intimidator_scan_305_irc as scan_305_irc

    def main() -> None:
        with create_busking_app() as app:
            with Mpd218Input() as midi_input:
                busking = VoidTerrorSilenceBusking(ConduitAnimatorMode.USHER)

                def on_tick():
                    # Handle midi input
                    is_shift_touched = midi_input.pad_mtx(0,0,0).is_touched

                    for evt in midi_input.poll():
                        if type(evt) is PadTapEvent:
                            if evt.bank == 0:
                                if evt.row == 3:
                                    if evt.col == 0:
                                        print("Wander")
                                        busking.scanners_animator.move_func = scanners_animator.WanderMovement()
                                    if evt.col == 1:
                                        if is_shift_touched:
                                            print("Disco")
                                            busking.scanners_animator.move_func = scanners_animator.disco_movement
                                        else:
                                            print("SinCos")
                                            busking.scanners_animator.move_func = scanners_animator.nice_sincos_movement
                                    if evt.col == 2:
                                        if is_shift_touched:
                                            print("Fig8")
                                            busking.scanners_animator.move_func = scanners_animator.fix8_movement
                                        else:
                                            print("Pendulum")
                                            busking.scanners_animator.move_func = scanners_animator.pendulum_movement

                            if evt.bank == 2:
                                if evt.row == 0:
                                    if evt.col == 3:
                                        pass # TODO: Triadic
                                    else:
                                        colors = [
                                            scan_305_irc.ColorMode.ORANGE,
                                            scan_305_irc.ColorMode.PURPLE,
                                            scan_305_irc.ColorMode.WHITE]
                                        busking.scanners_animator.set_color(colors[evt.col])
                                elif evt.row == 1:
                                    colors = [
                                        scan_305_irc.ColorMode.RED,
                                        scan_305_irc.ColorMode.GREEN,
                                        scan_305_irc.ColorMode.DARK_BLUE,
                                        scan_305_irc.ColorMode.SCROLL]
                                    busking.scanners_animator.set_color(colors[evt.col])
                                elif evt.row == 2:
                                    if evt.col == 3:
                                        busking.conduit_animator.start_rainbow()
                                    else:
                                        colors = [
                                            ColorRGB(1.0, 0.5, 0.0),
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


                        elif type(evt) == KnobClickEvent:
                            if evt.bank == 0:
                                if evt.col == 0:
                                    if evt.row == 0:
                                        dim = busking.scanners_animator.audience_dim_val + 1.0/32.0 * evt.clicks
                                        busking.scanners_animator.audience_dim_val = max(0.0, min(dim, 1.0))
                                        print(f"audience_dim_val = {busking.scanners_animator.audience_dim_val:0.04}")
                                if evt.col == 1:
                                    if evt.row == 0:
                                        end = busking.scanners_animator.audience_dim_end + scan_305_irc.TILT_FLOAT_EXTENT/32.0 * evt.clicks
                                        busking.scanners_animator.audience_dim_end = max(-scan_305_irc.TILT_FLOAT_EXTENT, min(end, scan_305_irc.TILT_FLOAT_EXTENT))
                                        print(f"audience_dim_end = {busking.scanners_animator.audience_dim_end:0.04}")

                    busking.tick(app.metronome)
                    busking.update_dmx(app.dmx_ctrl)

                app.main_loop(on_tick)

    main()