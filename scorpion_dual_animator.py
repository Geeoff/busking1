# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
from scorpion_dual import *
from dmx_controller import *
from metronome import Metronome

class ScorpionDualAnimator:
    def __init__(self, addr : int = 30):
        self.fixture = ScorpionDual(addr)
        self.fixture.pattern.mode = Pattern.LINE
        self.fixture.pan = ModeParam(RotMode.SPIN, 0.25)

    def tick(self, metronome:Metronome) -> None:
        beat_info = metronome.get_beat_info(0.5)
        self.fixture.tilt.param = 0.875 + 0.125 * math.sin(2.0 * math.pi * beat_info.t)
        beat_info = metronome.get_beat_info(0.25)
        amount = 0.05
        self.fixture.rot_z.param = amount + amount * math.sin(2.0 * math.pi * beat_info.t)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.fixture.update_dmx(dmx_ctrl)
