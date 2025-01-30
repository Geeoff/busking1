# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import time
import math

@dataclass
class BeatInfo:
    t: float
    delta_t: float
    count: int
    this_frame: bool

class Metronome:
    def __init__(self):
        self.beats_per_sec = 60.0 / 60.0
        self.sync_pos = 0.0
        self.sync_secs = time.perf_counter()
        self.prev_pos = self.sync_pos
        self.now_pos = self.sync_pos
        self.now_secs = self.sync_secs
        self.delta_secs = 0.0
        self.tap_queue = []
        self.tap_queue_max_len = 4
        self.tap_queue_reset_secs = 1.0

    @property
    def bpm(self) -> float:
        return self.beats_per_sec * 60.0

    def sync_beats(self, pos:float, beats_per_sec:float) -> None:
        self.beats_per_sec = beats_per_sec
        self.sync_pos = pos
        self.sync_secs = time.perf_counter()

    def on_one(self):
        self.sync_pos = 0
        self.sync_secs = self.now_secs

    def on_tap(self):
        # Update tap_queue.
        if self.tap_queue:
            delta_tap = self.now_secs - self.tap_queue[-1]
            if delta_tap >= self.tap_queue_reset_secs:
                self.tap_queue = []
            elif len(self.tap_queue) >= self.tap_queue_max_len:
                self.tap_queue = self.tap_queue[1:]
        self.tap_queue.append(self.now_secs)

        # If queue is full, sync.
        if len(self.tap_queue) >= self.tap_queue_max_len:
            self.beats_per_sec = (len(self.tap_queue) - 1.0) / (self.tap_queue[-1] - self.tap_queue[0])
            print(f"on_tap: bpm = {self.bpm}")

            frac_part = self.now_pos % 1.0
            if frac_part <= 0.25:
                self.sync_pos = self.now_pos
            else:
                self.sync_pos = self.now_pos + 1.0

            self.sync_secs = self.now_secs

    def tick(self) -> None:
        # Update current time.
        prev_secs = self.now_secs
        self.now_secs = time.perf_counter()
        self.delta_secs = self.now_secs - prev_secs

        # Update song position.
        self.prev_pos = self.now_pos
        self.now_pos = self.sync_pos + self.beats_per_sec * (self.now_secs - self.sync_secs)

    def get_beat_info(self, scaler:float=1.0) -> BeatInfo:
        scaled_prev_pos = scaler * self.prev_pos
        scaled_prev_count = int(scaled_prev_pos)

        scaled_now_pos = scaler * self.now_pos
        scaled_now_count = int(scaled_now_pos)

        return BeatInfo(
            t = scaled_now_pos % 1.0,
            delta_t = scaled_now_pos - scaled_prev_pos,
            count = scaled_now_count,
            this_frame = (scaled_prev_count != scaled_now_count))