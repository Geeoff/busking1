# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
from typing import Iterator, Union
import mido

@dataclass
class PadTapEvent:
    col : int
    row : int
    bank : int

@dataclass
class KnobClickEvent:
    col : int
    row : int
    bank : int
    clicks: int # Signed: negative for CCW, positive for CW

@dataclass
class KnobState:
    """MPD218's knobs are too sensitive, so this class reduces the number of clicks being reported
       to high level code."""
    pos : int = 0
    click_sensitivity : int = 5

    def on_turn(self, magnitude) -> int:
        self.pos += magnitude

        clicks : int = 0

        while self.pos <= -self.click_sensitivity:
            clicks -= 1
            self.pos += self.click_sensitivity

        while self.pos >= self.click_sensitivity:
            clicks += 1
            self.pos -= self.click_sensitivity

        return clicks

class ControlMatrix:
    """This class handles a 3D matrix of controls.  This is easier than dealing with lists of lists of lists."""
    def __init__(self, ctrl_cls, col_ct:int, row_ct:int, bank_ct:int):
        self.col_ct = col_ct
        self.row_ct = row_ct
        self.bank_ct = bank_ct
        ctrl_ct = col_ct * row_ct * bank_ct
        self.ctrl_list = [ctrl_cls() for _ in range(ctrl_ct)]

    def __call__(self, col:int, row:int, bank:int):
        assert (0 <= col) and (col < self.col_ct)
        assert (0 <= row) and (row < self.row_ct)
        assert (0 <= bank) and (bank < self.bank_ct)
        i = col + self.col_ct * (row + self.row_ct * bank)
        return self.ctrl_list[i]

class Mpd218Input:
    """This class handles the MIDI output of MPD218 and turns them into easy to use events for
       high level code.

       This class can be used in a with-statement."""
    BANK_COUNT = 3
    PAD_COL_COUNT = 4
    PAD_ROW_COUNT = 4
    KNOB_COL_COUNT = 2
    KNOB_ROW_COUNT = 3

    def __init__(self, tap_vel:int=40):
        # Try to open port.  If the MPD218 can't be found, this object will fail quietly and simply not be open.
        # mido.open_input will throw an exception if the device doesn't exist, so we check for the name first.
        port_name = "MPD218 0"
        self.port = None
        if port_name in mido.get_input_names():
            self.port = mido.open_input(port_name)
        else:
            print("Unable to find MPD218.")

        self.tap_vel = tap_vel
        self.knob_mtx = ControlMatrix(
            KnobState, Mpd218Input.KNOB_COL_COUNT, Mpd218Input.KNOB_ROW_COUNT, Mpd218Input.BANK_COUNT)

    def __enter__(self):
        if self.port is not None:
            self.port.__enter__()
        return self

    def __exit__(self, exit_type, exit_value, traceback):
        if self.port is not None:
            return self.port.__exit__(exit_type, exit_value, traceback)
        return False

    @property
    def is_open(self) -> bool:
        return (self.port is not None) and (not self.port.closed)

    def poll(self) -> Iterator[Union[PadTapEvent, KnobClickEvent]]:
        """This is a generator that yields new events from MPD218."""
        if self.port is None:
            return

        while True:
            msg = self.port.poll()
            if msg is None:
                break

            #print(msg)

            if msg.type == "note_on":
                if msg.velocity >= self.tap_vel:
                    yield PadTapEvent(
                        col = msg.note % Mpd218Input.PAD_COL_COUNT,
                        row = msg.note // Mpd218Input.PAD_COL_COUNT,
                        bank = msg.channel)

            if msg.type == "control_change":
                # Convert to a signed number.  Left/CCW is negative.  Right/CW is positive.
                #
                # Knobs are set to INC/DEC2 mode.  Turning to the left gives values like 127 and
                # 126.  The faster you turn the smaller.  Turing to the right gives 1 and higher.
                # The faster you turn the larger.  I'm guessing that around 63 or 64 is where it
                # switches from right to left, but I don't know the exact value.  In practice this
                # will probably not be an issue as you cannot turn the knob fast enough to get more
                # than 2 or 3 "clicks".
                if msg.value > 64:
                    magnitude = msg.value - 128
                else:
                    magnitude = msg.value

                col = msg.control % Mpd218Input.KNOB_COL_COUNT
                row = msg.control // Mpd218Input.KNOB_COL_COUNT
                bank = msg.channel - 9
                clicks = self.knob_mtx(col,row,bank).on_turn(magnitude)

                if clicks != 0:
                    yield KnobClickEvent(
                        col = col,
                        row = row,
                        bank = bank,
                        clicks = clicks)
