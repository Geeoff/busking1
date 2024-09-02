# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import mido
import enum
from dataclasses import dataclass
from typing import Iterator

####################################################################################################
# Constants
####################################################################################################

# Pads (aka Clip buttons).  These are full RGB with different pulse and blink modes.
PAD_ROW_COUNT = 8
PAD_COL_COUNT = 8
PAD_COUNT = PAD_COL_COUNT * PAD_ROW_COUNT
PAD_NOTE_START = 0x0
PAD_NOTE_END = PAD_NOTE_START + PAD_COUNT

# Buttons.  These are just on, off, or blink.
TRACK_BTN_COUNT = 8
TRACK_BTN_NOTE_START = 0x64
TRACK_BTN_NOTE_END = TRACK_BTN_NOTE_START + TRACK_BTN_COUNT
SCENE_BTN_COUNT = 8
SCENE_BTN_NOTE_START = 0x70
SCENE_BTN_NOTE_END = SCENE_BTN_NOTE_START + SCENE_BTN_COUNT
SHIFT_BTN_NOTE = 0x7A

# Faders
FADER_COUNT = 9
FADER_CONTROL_START = 0x30
FADER_CONTROL_END = FADER_CONTROL_START + FADER_COUNT

# Device info for SysEx messages.
SYSEX_MANUFACTURER_ID = 0x47
SYSEX_DEVICE_ID = 0x7F
SYSEX_PRODUCT_MODEL_ID = 0x4F

# Message types for SysEx messages.
SYSEX_MSG_PAD_COLORS = 0x24
SYSEX_MSG_INTRO = 0x60
SYSEX_MSG_INTRO_ACK = 0x61

####################################################################################################
# Generic SysEx Messaging for APC Mini Mk2
####################################################################################################

def split_int_for_midi(x:int) -> tuple[int, int]:
    """Breaks a 14-bit int into two 7-bit ints.
       Each byte in a MIDI message can only be 7-bits, so we need this function to split larger
       numbers."""
    assert(x < (1 << 14))
    return ((x >> 7) & 0x7F, x & 0x7F)

def MakeSysExMessage(msg_type:int, data) -> mido.Message:
    header = (
        SYSEX_MANUFACTURER_ID,
        SYSEX_DEVICE_ID,
        SYSEX_PRODUCT_MODEL_ID,
        msg_type)

    data_len = split_int_for_midi(len(data))

    return mido.Message(type="sysex", data=header+data_len+tuple(data))

####################################################################################################
# LED states
####################################################################################################

class PadLedBehavior(enum.IntEnum):
    # Solid
    PCT_10 = 0
    PCT_25 = enum.auto()
    PCT_50 = enum.auto()
    PCT_65 = enum.auto()
    PCT_75 = enum.auto()
    PCT_90 = enum.auto()
    PCT_100 = enum.auto()

    # Pulse
    PULSE_1_16 = enum.auto()
    PULSE_1_8 = enum.auto()
    PULSE_1_4 = enum.auto()
    PULSE_1_2 = enum.auto()

    # Blink
    BLINK_1_24 = enum.auto()
    BLINK_1_16 = enum.auto()
    BLINK_1_8 = enum.auto()
    BLINK_1_4 = enum.auto()
    BLINK_1_2 = enum.auto()

class ButtonLedBehavior(enum.IntEnum):
    OFF = 0
    ON = 1
    BLINK = 2

PadColorPalette = [
    0x000000, 0x1e1e1e, 0x7f7f7f, 0xffffff, 0xff4c4c, 0xff0000, 0x590000, 0x190000,
    0xffbd6c, 0xff5400, 0x591d00, 0x271b00, 0xffff4c, 0xffff00, 0x595900, 0x191900,
    0x88ff4c, 0x54ff00, 0x1d5900, 0x142b00, 0x4cff4c, 0x00ff00, 0x005900, 0x001900,
    0x4cff5e, 0x00ff19, 0x00590d, 0x001902, 0x4cff88, 0x00ff55, 0x00591d, 0x001f12,
    0x4cffb7, 0x00ff99, 0x005935, 0x001912, 0x4cc3ff, 0x00a9ff, 0x004152, 0x001019,
    0x4c88ff, 0x0055ff, 0x001d59, 0x000819, 0x4c4cff, 0x0000ff, 0x000059, 0x000019,
    0x874cff, 0x5400ff, 0x190064, 0x0f0030, 0xff4cff, 0xff00ff, 0x590059, 0x190019,
    0xff4c87, 0xff0054, 0x59001d, 0x220013, 0xff1500, 0x993500, 0x795100, 0x436400,
    0x033900, 0x005735, 0x00547f, 0x0000ff, 0x00454f, 0x2500cc, 0x7f7f7f, 0x202020,
    0xff0000, 0xbdff2d, 0xafed06, 0x64ff09, 0x108b00, 0x00ff87, 0x00a9ff, 0x002aff,
    0x3f00ff, 0x7a00ff, 0xb21a7d, 0x402100, 0xff4a00, 0x88e106, 0x72ff15, 0x00ff00,
    0x3bff26, 0x59ff71, 0x38ffcc, 0x5b8aff, 0x3151c6, 0x877fe9, 0xd31dff, 0xff005d,
    0xff7f00, 0xb9b000, 0x90ff00, 0x835d07, 0x392b00, 0x144c10, 0x0d5038, 0x15152a,
    0x16205a, 0x693c1c, 0xa8000a, 0xde513d, 0xd86a1c, 0xffe126, 0x9ee12f, 0x67b50f,
    0x1e1e30, 0xdcff6b, 0x80ffbd, 0x9a99ff, 0x8e66ff, 0x404040, 0x757575, 0xe0ffff,
    0xa00000, 0x350000, 0x1ad000, 0x074200, 0xb9b000, 0x3f3100, 0xb35f00, 0x4b1502,
]

def rgb_to_pad_palette_index(r:int, g:int, b:int) -> int:
    """Find a palette color that is closest to the desired color."""
    best_idx = None
    best_dist_sq = 0xFFFFFFFF

    for i, c in enumerate(PadColorPalette):
        cr = (c >> 16) & 0xFF
        cg = (c >> 8) & 0xFF
        cb = c & 0xFF

        dr = r - cr
        dg = g - cg
        db = b - cb

        dist_sq = dr*dr + dg*dg + db*db
        if dist_sq < best_dist_sq:
            best_idx = i
            best_dist_sq = dist_sq

    return best_idx

@dataclass
class PadLedState:
    behavior : PadLedBehavior = PadLedBehavior.PCT_100
    r : int = 0
    g : int = 0
    b : int = 0

    def copy(self) -> "PadLedState":
        return PadLedState(self.behavior, self.r, self.g, self.b)

@dataclass
class ButtonLedState:
    behavior : ButtonLedBehavior = ButtonLedBehavior.OFF

    def copy(self) -> "ButtonLedState":
        return ButtonLedState(self.behavior)

type LedStateType = PadLedState | ButtonLedState

####################################################################################################
# Control states
####################################################################################################

@dataclass
class ButtonInputState:
    is_down : bool = False
    was_down : bool = False

    def copy(self) -> "ButtonInputState":
        return ButtonInputState(self.is_down, self.was_down)

    @property
    def was_pressed(self):
        return self.is_down and not self.was_down

    @property
    def was_released(self):
        return not self.is_down and self.was_down

    def update_prev_state(self):
        self.was_down = self.is_down

@dataclass
class FaderInputState:
    pos : int = 0

    def copy(self) -> "FaderInputState":
        return FaderInputState(self.pos)

    def update_prev_state(self):
        pass

type InputStateType = ButtonInputState | FaderInputState

####################################################################################################
# Control ID
####################################################################################################

class ControlType(enum.IntEnum):
    Invalid = 0
    Pad = enum.auto()
    TrackButton = enum.auto()
    SceneButton = enum.auto()
    ShiftButton = enum.auto()
    Fader = enum.auto()

@dataclass
class ControlID:
    ty : ControlType
    col : int = 0
    row : int = 0

    def copy(self) -> "ControlID":
        return ControlID(self.ty, self.col, self.row)

    def to_tuple(self) -> tuple[ControlType, int, int]:
        return (int(self.ty), self.col, self.row)

    def __eq__(self, other) -> bool:
        if isinstance(other, ControlID):
            return self.to_tuple() == other.to_tuple()
        return False

    def __hash__(self) -> int:
        return hash(self.to_tuple())

    @staticmethod
    def pad(col : int, row : int) -> "ControlID":
        return ControlID(ControlType.Pad, col, row)

    def is_pad(self) -> bool:
        return self.ty == ControlType.Pad

    @staticmethod
    def track_button(col : int) -> "ControlID":
        return ControlID(ControlType.TrackButton, col)

    def is_track_button(self) -> bool:
        return self.ty == ControlType.TrackButton

    @staticmethod
    def scene_button(row : int) -> "ControlID":
        return ControlID(ControlType.SceneButton, 0, row)

    def is_scene_button(self) -> bool:
        return self.ty == ControlType.SceneButton

    @staticmethod
    def shift_button() -> "ControlID":
        return ControlID(ControlType.ShiftButton)

    def is_shift_button(self) -> bool:
        return self.ty == ControlType.ShiftButton

    def is_button(self) -> bool:
        return (self.ty == ControlType.TrackButton) or \
               (self.ty == ControlType.SceneButton) or \
               (self.ty == ControlType.ShiftButton)

    @staticmethod
    def fader(col : int) -> "ControlID":
        return ControlID(ControlType.Fader, col)

    def is_fader(self) -> bool:
        return self.ty == ControlType.Fader

    @staticmethod
    def iter_pad_ids() -> Iterator["ControlID"]:
        for r in range(PAD_ROW_COUNT):
            for c in range(PAD_COL_COUNT):
                yield ControlID(ControlType.Pad, c, r)

    @staticmethod
    def iter_button_ids() -> Iterator["ControlID"]:
        note_range_list = [
            (TRACK_BTN_NOTE_START, TRACK_BTN_NOTE_END),
            (SCENE_BTN_NOTE_START, SCENE_BTN_NOTE_END)]

        for note_range in note_range_list:
            for note in range(note_range[0], note_range[1]):
                yield ControlID._from_midi_note(note)

        yield ControlID(ControlType.ShiftButton)

    @staticmethod
    def iter_fader_ids() -> Iterator["ControlID"]:
        for midi_ctrl in range(FADER_CONTROL_START, FADER_CONTROL_END):
            yield ControlID._from_midi_control(midi_ctrl)

    @staticmethod
    def _from_midi_note(note : int) -> "ControlID":
        if note < PAD_COUNT:
            return ControlID(ControlType.Pad, note%8, note//8)
        elif (TRACK_BTN_NOTE_START <= note) and (note < TRACK_BTN_NOTE_END):
            return ControlID(ControlType.TrackButton, note-TRACK_BTN_NOTE_START, 0)
        elif (SCENE_BTN_NOTE_START <= note) and (note < SCENE_BTN_NOTE_END):
            return ControlID(ControlType.SceneButton, 0, note-SCENE_BTN_NOTE_START)
        elif note == SHIFT_BTN_NOTE:
            return ControlID(ControlType.ShiftButton, 0, 0)
        raise ValueError(f"Bad note value: {note}!")

    def _to_midi_note(self) -> int:
        if self.ty == ControlType.Pad:
            return self.col + self.row * PAD_COL_COUNT
        elif self.ty == ControlType.TrackButton:
            return self.col + TRACK_BTN_NOTE_START
        elif self.ty == ControlType.SceneButton:
            return self.row + SCENE_BTN_NOTE_START
        elif self.ty == ControlType.ShiftButton:
            return SHIFT_BTN_NOTE
        raise ValueError(f"Unexpected type to convert to MIDI note: {self.ty}.")

    @staticmethod
    def _from_midi_control(midi_ctrl : int) -> "ControlID":
        if (FADER_CONTROL_START <= midi_ctrl) and (midi_ctrl < FADER_CONTROL_END):
            return ControlID(ControlType.Fader, midi_ctrl-FADER_CONTROL_START, 0)
        raise ValueError(f"Bad MIDI control value: {midi_ctrl}!")

    def _to_midi_control(self) -> int:
        if self.ty == ControlType.Fader:
            return self.col + FADER_CONTROL_START
        raise ValueError(f"Unexpected type to convert to MIDI control: {self.ty}.")

####################################################################################################
# Events
####################################################################################################

class EventType(enum.IntEnum):
    Invalid = 0
    Pressed = enum.auto()
    Released = enum.auto()
    Moved = enum.auto()

@dataclass
class Event:
    ty : EventType
    ctrl_id : ControlID
    pos : int | None = None

####################################################################################################
# Device
####################################################################################################

class Device:
    def __init__(self):
        self.inport = None
        self.outport = None

        #
        # Init control states
        #
        #
        self.input_state_by_id : dict[ControlID, InputStateType] = {}
        self.led_state_by_id : dict[ControlID, LedStateType] = {}

        for ctrl_id in ControlID.iter_pad_ids():
            self.input_state_by_id[ctrl_id] = ButtonInputState()
            self.led_state_by_id[ctrl_id] = PadLedState()
        for ctrl_id in ControlID.iter_button_ids():
            self.input_state_by_id[ctrl_id] = ButtonInputState()
            if not ctrl_id.is_shift_button():
                self.led_state_by_id[ctrl_id] = ButtonLedState()
        for ctrl_id in ControlID.iter_fader_ids():
            self.input_state_by_id[ctrl_id] = FaderInputState()

    def __enter__(self) -> "Device":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        res = False

        if self.outport is not None:
            res = self.outport.__exit__(exc_type, exc_value, traceback)

        if not res and \
          self.inport is not None:
            res = self.inport.__exit__(exc_type, exc_value, traceback)

        return res

    def connect(self) -> None:
        midi_name = "APC mini mk2"
        print(f"Connecting to '{midi_name}'...")

        #
        # Open input port.
        #
        print("  Looking for input port...")
        inport_name = None
        for name in mido.get_input_names():
            if name.startswith(midi_name):
                inport_name = name
                print(f"    Found '{name}.")
            else:
                print(f"    Ignoring '{name}'.")

        if inport_name is None:
            print("    ERROR: Unable to find APC Mini MK2.")
            self.inport = None
        else:
            print(f"    Connecting to '{inport_name}'...")
            self.inport = mido.open_input(inport_name)

        #
        # Open output port.
        #
        print("  Looking for output port...")
        outport_name = None
        for name in mido.get_output_names():
            if name.startswith(midi_name):
                outport_name = name
                print(f"    Found '{name}.")
            else:
                print(f"    Ignoring '{name}'.")

        if outport_name is None:
            print("    ERROR: Unable to find APC Mini MK2.")
            self.outport = None
        else:
            print(f"    Connecting to '{outport_name}'...")
            self.outport = mido.open_output(outport_name)

        # Send introduction message to device.  The controller will respond with it's own introduction message which
        # includes the state of the faders.
        #
        # Note:
        # We are sending less bytes than we're supposed to.  The spec says to include an ID and version numbers for this
        # program.  I assume this is to put the controller in an Ableton mode or something.  Since this is a custom
        # program, we just want the default behvaior of the controller.  Truncating the message to leave out the program
        # info seems to work.
        msg = MakeSysExMessage(SYSEX_MSG_INTRO, ())
        self.outport.send(msg)

        # Init LED state.
        # We send note_on messages first.
        for ctrl_id, led_state in self.led_state_by_id.items():
            if ctrl_id.is_pad():
                note = ctrl_id._to_midi_note()
                self._send_pad_led_state_by_note_on(note, led_state)

            elif ctrl_id.is_button():
                note = ctrl_id._to_midi_note()
                self._send_btn_led_state_by_note_on(note, led_state)

            else:
                print(f"ERROR: Unexpected control type when initializing LED states: {ctrl_id.ty}")

        # Sync all pad colors at once.
        self._send_pad_colors_by_sysex()

        # FIXME
        # If I change the colors again right after this, they won't stick. Adding a small sleep seems to help.
        # Hopefully this is not a problem during use.
        time.sleep(0.25)

    def disconnect(self) -> None:
        if self.outport is not None:
            self.outport.close()
            self.outport = None

        if self.inport is not None:
            self.inport.close()
            self.inport = None

    def tick(self) -> Iterator[Event]:
        if self.inport is None:
            return

        # Update previous states
        for input_state in self.input_state_by_id.values():
            input_state.update_prev_state()

        # Process incoming MIDI messages.
        while True:
            msg = self.inport.poll()
            if msg is None:
                break

            was_handled = False

            # Handle pads and buttons
            if msg.type == "note_on":
                ctrl_id = ControlID._from_midi_note(msg.note)
                btn_state = self.input_state_by_id[ctrl_id]
                btn_state.is_down = True
                yield Event(EventType.Pressed, ctrl_id)
                was_handled = True

            elif msg.type == "note_off":
                ctrl_id = ControlID._from_midi_note(msg.note)
                btn_state = self.input_state_by_id[ctrl_id]
                btn_state.is_down = False
                yield Event(EventType.Released, ctrl_id)
                was_handled = True

            # Handle faders
            elif msg.type == "sysex":
                if msg.data[3] == SYSEX_MSG_INTRO_ACK:
                    # Init fader states
                    for i in range(FADER_COUNT):
                        ctrl_id = ControlID._from_midi_control(i + FADER_CONTROL_START)
                        fader_state = self.input_state_by_id[ctrl_id]
                        fader_state.pos = msg.data[i+6]
                    was_handled = True

            elif msg.type == "control_change":
                fader_id = ControlID._from_midi_control(msg.control)
                fader_state = self.input_state_by_id[fader_id]
                fader_state.pos = msg.value
                yield Event(EventType.Moved, fader_id, msg.value)
                was_handled = True

            # We expect to process all messages, so print any we missed.
            if not was_handled:
                print(f"WARNING: Unhandled MIDI message from APC Mini Mk2: {msg}")

    def get_input_state(self, ctrl_id : ControlID) -> InputStateType:
        return self.input_state_by_id[ctrl_id].copy()

    def get_led_state(self, ctrl_id : ControlID) -> LedStateType:
        return self.led_state_by_id[ctrl_id].copy()

    def set_led_state(self, ctrl_id : ControlID, led_state : LedStateType) -> None:
        # Update shadow state.
        self.led_state_by_id[ctrl_id] = led_state.copy()

        # Update controller.
        note = ctrl_id._to_midi_note()
        if ctrl_id.is_pad():
            self._send_pad_led_state_by_note_on(note, led_state)
            self._send_pad_colors_by_sysex(note, 1)
        elif ctrl_id.is_button():
            self._send_btn_led_state_by_note_on(note, led_state)

    def _send_pad_led_state_by_note_on(self, note:int, led_state : PadLedState) -> None:
        # This message requires a color from the color palette.
        # Find the closest palette color.
        # When the behavior is PCT_100, the SysEx color will override.
        pal_idx = rgb_to_pad_palette_index(led_state.r, led_state.g, led_state.b)

        msg = mido.Message(
            "note_on",
            channel = int(led_state.behavior),
            note = note,
            velocity = pal_idx)

        self.outport.send(msg)

    def _send_btn_led_state_by_note_on(self, note:int, led_state : ButtonLedState) -> None:
        msg = mido.Message(
            "note_on",
            note = note,
            velocity = int(led_state.behavior))

        self.outport.send(msg)

    def _send_pad_colors_by_sysex(self, note_start:int=0, note_count:int=PAD_COUNT) -> None:
        data = []
        def append_int14(x):
            x = split_int_for_midi(x)
            data.append(x[0])
            data.append(x[1])

        # Pad color messages are RLE.  We use a flush system to group consecutive pads with the same color.
        run_start = None
        run_end = None
        run_state = None
        def append_run():
            if run_state is not None:
                data.append(run_start)
                data.append(run_end)
                append_int14(run_state.r)
                append_int14(run_state.g)
                append_int14(run_state.b)

        for note in range(note_start, note_start+note_count):
            ctrl_id = ControlID._from_midi_note(note)
            cur_state = self.led_state_by_id[ctrl_id]

            if run_state is not None and \
               run_state.r == cur_state.r and \
               run_state.g == cur_state.g and \
               run_state.b == cur_state.b:
                # Same color.  Continue run.
                run_end = note

            else:
                # Different color.  Flush and start a new run.
                append_run()
                run_start = note
                run_end = note
                run_state = cur_state

        # Flush the last run.
        append_run()

        # Send message.
        msg = MakeSysExMessage(SYSEX_MSG_PAD_COLORS, data)
        self.outport.send(msg)

####################################################################################################
# __main__
####################################################################################################

if __name__ == "__main__":
    import time
    import colorsys

    def main() -> None:
        with Device() as dev:
            selected_colors = [6, 4]

            color_list = [
                (0xFF, 0x00, 0x00),
                (0x00, 0xFF, 0x00),
                (0x00, 0x00, 0xFF),
                ((0xFF, 0x00, 0xFF), (0x33, 0x00, 0xFF)),
                (0xFF, 0x44, 0x00),
                (0x00, 0xFF, 0xFF),
                ((0xFF, 0xFF, 0xFF), (0xFF, 0xAF, 0x7F))]

            for col in range(2):
                for i, color in enumerate(color_list):
                    # This row has a different color per column.
                    if len(color) == 2:
                        color = color[col]

                    row = PAD_ROW_COUNT - i - 1
                    ctrl_id = ControlID.pad(col, row)

                    led_state = PadLedState()
                    led_state.r = color[0]
                    led_state.g = color[1]
                    led_state.b = color[2]

                    if row == selected_colors[col]:
                        led_state.behavior = PadLedBehavior.PULSE_1_8

                    dev.set_led_state(ctrl_id, led_state)

            def select_color(new_id : ControlID):
                cur_color = selected_colors[new_id.col]
                new_color = new_id.row
                if cur_color != new_color:
                    # Stop pulsing the current color.
                    cur_id = ControlID.pad(new_id.col, cur_color)
                    led_state = dev.get_led_state(cur_id)
                    led_state.behavior = PadLedBehavior.PCT_100
                    dev.set_led_state(cur_id, led_state)

                    # Pulse the new color.
                    led_state = dev.get_led_state(new_id)
                    led_state.behavior = PadLedBehavior.PULSE_1_8
                    dev.set_led_state(new_id, led_state)

                    # Update state
                    selected_colors[new_id.col] = new_color

            rainbow_hue = 0.0

            while True:
                # Process events
                for evt in dev.tick():
                    if evt.ty == EventType.Pressed and \
                       evt.ctrl_id.is_pad() and \
                       evt.ctrl_id.col < len(selected_colors):
                            select_color(evt.ctrl_id)

                    print(evt)

                # Update rainbow button
                rainbow_hue = (rainbow_hue + 0.25 / 120.0) % 1.0
                rainbow_col = colorsys.hsv_to_rgb(rainbow_hue, 1.0, 1.0)
                rainbow_col = [int(255.0 * chan) for chan in rainbow_col]
                rainbow_id = ControlID.pad(1, 0)
                led_state = dev.get_led_state(rainbow_id)
                led_state.r = rainbow_col[0]
                led_state.g = rainbow_col[1]
                led_state.b = rainbow_col[2]
                dev.set_led_state(rainbow_id, led_state)

                # sleep
                time.sleep(1.0 / 120.0)
    main()