# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
"""This script controls the lights at Conduit in Winter Park, FL."""
import enum
from metronome import Metronome
from dmx_controller import DmxController
from scanners_animator import ScannersAnimator
from conduit_animator import ConduitAnimator, UsherAsConduitAnimator

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

    def main() -> None:
        with create_busking_app() as app:
            busking = VoidTerrorSilenceBusking(ConduitAnimatorMode.CONDUIT)
            
            def on_tick():
                busking.tick(app.metronome)
                busking.update_dmx(app.dmx_ctrl)

            app.main_loop(on_tick)
        
    main()