# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
from metronome import Metronome, BeatInfo

class DimmerAnimator:
    def __init__(self, bpm_scale):
        self.bpm_scale = bpm_scale

    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        raise NotImplemented

class CosDimmerAnimator(DimmerAnimator):
    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        beat = metronome.get_beat_info(self.bpm_scale)
        dim = 0.5 * math.cos(2.0 * math.pi * beat.t) + 0.5
        return [dim] * fixture_count

class ShadowChaseDimmerAnimator(DimmerAnimator):
    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        beat = metronome.get_beat_info(self.bpm_scale)
        prev_i = beat.count % fixture_count
        next_i = (prev_i + 1) % fixture_count

        # NOTE: Fixture brightness doesn't seem to be linear.  Squaring these values gets us a little closer.
        dimmer_list = [1.0] * fixture_count
        dimmer_list[prev_i] = beat.t ** 2
        dimmer_list[next_i] = (1.0 - beat.t) ** 2

        return dimmer_list

class QuickChaseDimmerAnimator(DimmerAnimator):
    def __init__(self, bpm_scale, t_lifespace=0.25):
        super().__init__(bpm_scale)
        self.t_lifespan = t_lifespace

    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        beat = metronome.get_beat_info(self.bpm_scale)

        # This scaler takes us from a fixture index to it's starting beat.t value.
        # First fixture starts at 0 and the last one starts at 0.5.
        if fixture_count > 1:
            i_to_t_scale = 0.5 / float(fixture_count-1)
        else:
            i_to_t_scale = 0.0

        dimmer_list = [0.0] * fixture_count
        for i in range(fixture_count):
            t_start = i * i_to_t_scale

            if beat.t < t_start:
                dimmer_list[i] = 0.0
            else:
                dimmer_list[i] = max(0.0, 1.0 - (beat.t - t_start) / self.t_lifespan)

        return dimmer_list

class SawDimmerAnimator(DimmerAnimator):
    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        beat = metronome.get_beat_info(self.bpm_scale)
        return [1.0 - beat.t] * fixture_count

class AltSawDimmerAnimator(DimmerAnimator):
    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        beat = metronome.get_beat_info(self.bpm_scale)

        dim = 1.0 - beat.t
        odd_is_on = beat.count & 1

        def idx_to_dim(i):
            idx_is_odd = i & 1
            idx_is_on = (idx_is_odd == odd_is_on)
            return dim if idx_is_on else 0.0

        return [idx_to_dim(i) for i in range(fixture_count)]

class DoublePulseDimmerAnimator(DimmerAnimator):
    def tick(self, metronome:Metronome, fixture_count) -> list[float]:
        beat = metronome.get_beat_info(self.bpm_scale)

        if beat.t <= 0.5 / 3.0:
            dim = 1.0
        elif beat.t <= 1.0 / 3.0:
            dim = 0.0
        elif beat.t <= 1.5 / 3.0:
            dim = 1.0
        else:
            dim = 0.0

        return [dim] * fixture_count