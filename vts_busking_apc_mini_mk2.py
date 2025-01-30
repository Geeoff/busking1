# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
"""This script controls the lights at Conduit in Winter Park, FL."""
import enum
import apc_mini_mk2
import busking_app
from color_math import *
from conduit_animator import ConduitAnimator
from dmx_controller import DmxController
from metronome import Metronome
from mpd218_input import PadTapEvent
from scanners_animator import ScannerState, ScannersAnimator

####################################################################################################
class ColorSyncMode(enum.IntEnum):
    NONE = 0
    COMPLEMENT = enum.auto()
    TRIADIC = enum.auto()
    RAINBOW = enum.auto()

class VoidTerrorSilenceBusking:
    def __init__(self):
        super().__init__()

        # Init animators.
        self.scanners_animator = ScannersAnimator()
        self.conduit_animator = ConduitAnimator()

        # Init color sync state.
        self.color_sync_mode = ColorSyncMode.NONE

    def tick(self, metronome:Metronome) -> None:
        # Update my own state.
        self._tick_color_sync()

        # Update animators.
        self.scanners_animator.tick(metronome)
        self.conduit_animator.tick(metronome)

    def _tick_color_sync(self) -> None:
        if self.color_sync_mode != ColorSyncMode.NONE:
            # Get hue of the back pars.
            if self.conduit_animator.rainbow_is_enabled:
                par_hue = self.conduit_animator.rainbow_hue
            else:
                par_hue, _, _ = self.conduit_animator.base_color.to_hsv()

            # Set scanner colors.
            if self.color_sync_mode == ColorSyncMode.COMPLEMENT:
                self.scanners_animator.set_comp_color(par_hue)
            elif self.color_sync_mode == ColorSyncMode.TRIADIC:
                self.scanners_animator.set_triadic_colors(par_hue)
            elif self.color_sync_mode == ColorSyncMode.RAINBOW:
                self.scanners_animator.set_rainbow(par_hue)

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.scanners_animator.update_dmx(dmx_ctrl)
        self.conduit_animator.update_dmx(dmx_ctrl)

####################################################################################################
class PadCtrl_Base:
    def on_press(self) -> None: ...
    def on_release(self) -> None: ...
    def get_pad_led_state(self, metronome : Metronome) -> apc_mini_mk2.PadLedState:
        return apc_mini_mk2.PadLedState()

def bytes_to_color_rgb(r, g, b) -> ColorRGB:
    assert type(r) == int
    assert type(g) == int
    assert type(b) == int
    return ColorRGB(float(r) / 255.0, float(g) / 255.0, float(b) / 255.0)

def color_rgb_to_bytes(color : ColorRGB):
    return (int(color.r * 255.0), int(color.g * 255), int(color.b * 255))

class PadCtrl_SetStaticColor(PadCtrl_Base):
    def __init__(self, animator, color : ColorRGB):
        self.animator = animator
        self.color = bytes_to_color_rgb(*color)
        self.pad_color = color

    def on_press(self) -> None:
        self.animator.set_static_color(self.color)

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.get_static_color() == self.color:
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100
        return apc_mini_mk2.PadLedState(behavior, self.pad_color[0], self.pad_color[1], self.pad_color[2])
    
class PadCtrl_SetRainbowColors(PadCtrl_Base):
    def __init__(self, animator):
        self.animator = animator

    def on_press(self) -> None:
        self.animator.set_rainbow_color()

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.is_rainbow_color():
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100

        color = ColorRGB.from_hsv(self.animator.rainbow_hue, 1.0, 1.0)
        return apc_mini_mk2.PadLedState(behavior, color.r, color.g, color.b)
    
class PadCtrl_SetTriadicColors(PadCtrl_Base):
    def __init__(self, animator):
        self.animator = animator

    def on_press(self) -> None:
        self.animator.set_triadic_color()

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.is_triadic_color():
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100

        hue = self.animator.triadic_colors[metronome.now_pos & 1]
        color = ColorRGB.from_hsv(hue, 1.0, 1.0)
        color = color_rgb_to_bytes(color)
        return apc_mini_mk2.PadLedState(behavior, color[0], color[1], color[2])

class PadCtrl_SetDimmerPattern(PadCtrl_Base):
    def __init__(self, animator, pattern, pad_color = [255,255,255]):
        self.animator = animator
        self.pattern = pattern
        self.pad_color = pad_color

    def on_press(self) -> None:
        self.animator.set_dimmer_pattern(self.pattern)

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.get_dimmer_pattern() == self.pattern:
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100
        return apc_mini_mk2.PadLedState(behavior, self.pad_color[0], self.pad_color[1], self.pad_color[2])

class PadCtrl_SetMovementPattern(PadCtrl_Base):
    def __init__(self, animator, pattern, pad_color = [255,255,255]):
        self.animator = animator
        self.pattern = pattern
        self.pad_color = pad_color

    def on_press(self) -> None:
        self.animator.set_movement_pattern(self.pattern)

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.get_movement_pattern() == self.pattern:
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100
        return apc_mini_mk2.PadLedState(behavior, self.pad_color[0], self.pad_color[1], self.pad_color[2])

class PadCtrlMatrix:
    def __init__(self):
        self._matrix = [8 * [None] for _ in range(8)]

    def set_pad(self, row:int, col:int, pad_ctrl):
        self._matrix[col][row] = pad_ctrl

    def get_pad(self, row:int, col:int):
        return self._matrix[col][row]

    def on_midi_event(self, evt : apc_mini_mk2.Event):
        if evt.ctrl_id.is_pad():
            ctrl = self.get_pad(evt.ctrl_id.row, evt.ctrl_id.col)
            if ctrl is not None:
                if evt.ty == apc_mini_mk2.EventType.Pressed:
                    ctrl.on_press()
                elif evt.ty == apc_mini_mk2.EventType.Released:
                    ctrl.on_release()

    def update_led_states(self, midi_input : apc_mini_mk2.Device, metronome : Metronome):
        for c in range(apc_mini_mk2.PAD_COL_COUNT):
            for r in range(apc_mini_mk2.PAD_ROW_COUNT):
                pad = self.get_pad(r, c)
                if pad is not None:
                    ctrl_id = apc_mini_mk2.ControlID.pad(c, r)
                    led_state = pad.get_pad_led_state(metronome)
                    midi_input.set_led_state(ctrl_id, led_state)

####################################################################################################
def init_pad_colors(busking : VoidTerrorSilenceBusking, pad_matrix : PadCtrlMatrix):
    # Init static color pads
    color_list = [
        (0xFF, 0x00, 0x00),
        (0x00, 0xFF, 0x00),
        (0x00, 0x00, 0xFF),
        ((0xFF, 0x00, 0xFF), (0x33, 0x00, 0xFF)),
        (0xFF, 0x44, 0x00),
        (0x00, 0xFF, 0xFF),
        ((0xFF, 0xFF, 0xFF), (0xFF, 0xAF, 0x7F))]

    for i, color in enumerate(color_list):
        if len(color) == 2:
            scanners_color = color[0]
            conduit_color = color[1]
        else:
            scanners_color = color
            conduit_color = color

        pad_matrix.set_pad(0, i, PadCtrl_SetStaticColor(busking.scanners_animator, scanners_color))
        pad_matrix.set_pad(7, i, PadCtrl_SetStaticColor(busking.conduit_animator, conduit_color))

    # Set up special colors
    #pad_matrix.set_pad(7, 0, PadCtrl_SetTriadicColors(busking.scanners_animator))
    #pad_matrix.set_pad(7, 7, PadCtrl_SetRainbowColors(busking.conduit_animator))

def busk() -> None:
    with busking_app.create_busking_app() as app:
        with apc_mini_mk2.Device() as midi_input:
            busking = VoidTerrorSilenceBusking()

            pad_matrix = PadCtrlMatrix()
            init_pad_colors(busking, pad_matrix)

            def tick():
                # Tick midi
                for evt in midi_input.tick():
                    pad_matrix.on_midi_event(evt)

                # Update midi LED state
                pad_matrix.update_led_states(midi_input, app.metronome)

                # Tick faders
                master_fader = float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(0)).pos) / 255.0
                scanners_fader =  float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(1)).pos) / 255.0
                back_pars_fader =  float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(2)).pos) / 255.0
                busking.scanners_animator.master_dimmer = master_fader * scanners_fader
                busking.conduit_animator.back_pars_master_dimmer = master_fader * back_pars_fader

                # Tick animators
                busking.tick(app.metronome)
                busking.update_dmx(app.dmx_ctrl)

            app.main_loop(tick)
busk()
