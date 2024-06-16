# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import msvcrt
import time
import contextlib
from metronome import Metronome
from ftdi_device import FtdiDevice
import os2l

class BuskingApp:
    """TBD"""
       
    def __init__(self, ticks_per_sec=120.0):
        self.ticks_per_sec = ticks_per_sec
        self.metronome = Metronome()
        self.dmx_ctrl = None
        self.os2l_server = None
                    
    def main_loop(self, on_tick) -> None:
        """Caller can override this to inject more contexts."""
        print("")
        print("~ Started ~")
        print("Press 'X' key to exit.")
        print("Press 'R' to restart OS2L server.")
        print("")
                    
        while True:
            # Consume OS2L messages.
            for evt in self.os2l_server.poll():
                if type(evt) is os2l.BeatEvent:
                    # Sync beats with DJ software.
                    self.metronome.sync_beats(evt.pos, evt.bpm / 60.0)
                elif type(evt) is os2l.CmdEvent and evt.idnum == 1 and evt.param == 100:
                    pass # Ignore: Dummy event to cause VirtualDJ to connect.
                else:
                    print(f"Unexpected OS2L event {evt}.")

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
            yield app
    