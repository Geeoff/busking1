# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import msvcrt
import time
import contextlib
from metronome import Metronome
from ftdi_device import FtdiDevice
import mic_to_beat
import os2l
from mic_to_beat import MicToBeatDetector, find_mic_index
import enum

class BeatInputMode(enum.IntEnum):
    INVALID = 0
    NONE = enum.auto()
    OS2L = enum.auto()
    MIC_TO_BEAT = enum.auto()

class BuskingApp:
    """TBD"""

    def __init__(self, ticks_per_sec=120.0):
        self.ticks_per_sec = ticks_per_sec
        self.metronome = Metronome()
        self.dmx_ctrl = None
        self.os2l_server = None
        self.mic_to_beat : MicToBeatDetector | None = None
        self.beat_input_mode = BeatInputMode.OS2L

    def main_loop(self, on_tick) -> None:
        """Caller can override this to inject more contexts."""
        print("")
        print("~ Started ~")
        print("Press 'X' key to exit.")
        print("Press 'R' to restart OS2L server.")
        print("")

        mic_to_beat_counter = 0

        while True:
            # Consume OS2L messages.
            if self.os2l_server:
                for evt in self.os2l_server.poll():
                    if type(evt) is os2l.BeatEvent:
                        # Sync beats with DJ software.
                        if self.beat_input_mode == BeatInputMode.OS2L:
                            self.metronome.sync_beats(evt.pos, evt.bpm / 60.0)
                    elif type(evt) is os2l.CmdEvent and evt.idnum == 1 and evt.param == 100:
                        pass # Ignore: Dummy event to cause VirtualDJ to connect.
                    else:
                        print(f"Unexpected OS2L event {evt}.")

            # Apply beat from mic_to_beat.
            if self.beat_input_mode == BeatInputMode.MIC_TO_BEAT:
                beat_info = self.mic_to_beat.poll()
                if beat_info["beat"] and beat_info["bpm"] > 0.01:
                    mic_to_beat_counter += 1
                    # IMPORTANT: We need to cast to a float here, otherwise we pass numpy floats to the system and it
                    #            chokes.
                    mic_to_beat_pos = float(mic_to_beat_counter + beat_info["phase"])
                    mic_to_beat_bps = float(beat_info["bpm"] / 60.0) # fudge factor, usually only picks up kick
                    self.metronome.sync_beats(mic_to_beat_pos, mic_to_beat_bps)

            # Update metronome.
            self.metronome.tick()

            # Tick!
            on_tick()

            # Flush DMX
            self.dmx_ctrl.flush()

            # Handle input.
            # TODO: Make this OS agnostic. Currently only works on Windows.
            if msvcrt.kbhit():
                ch = msvcrt.getch().lower()
                if ch == b"x":
                    print("~ Exiting ~")
                    break
                elif ch == b"r":
                    if self.os2l_server:
                        print("~ OS2L Restart ~")
                        self.os2l_server.restart()
                    print("")

            # Loop at a reasonable rate.
            time.sleep(1.0 / self.ticks_per_sec)

@contextlib.contextmanager
def create_busking_app(ticks_per_sec=120.0):
    app = BuskingApp()
    with FtdiDevice() as app.dmx_ctrl:
        with os2l.Server() as app.os2l_server:
            mic_idx = find_mic_index()
            app.mic_to_beat = MicToBeatDetector(mic_idx)
            #app.mic_to_beat.start()
            yield app
