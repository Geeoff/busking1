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
class VoidTerrorSilenceBusking:
    def __init__(self):
        super().__init__()

        # Init animators.
        self.scanners_animator = ScannersAnimator()
        self.conduit_animator = ConduitAnimator()

    def tick(self, metronome:Metronome) -> None:
        # Update my own state.
        self._tick_color_sync()

        # Update animators.
        self.scanners_animator.tick(metronome)
        self.conduit_animator.tick(metronome)

    def _tick_color_sync(self) -> None:
        # Get hue of the back pars.
        if self.conduit_animator.rainbow_is_enabled:
            back_pars_hue = self.conduit_animator.rainbow_hue
        else:
            back_pars_hue, _, _ = self.conduit_animator.base_color.to_hsv()

        self.scanners_animator.back_pars_hue = back_pars_hue

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
        color = color_rgb_to_bytes(color)
        return apc_mini_mk2.PadLedState(behavior, color[0], color[1], color[2])
    
class PadCtrl_SetTriadicColors(PadCtrl_Base):
    def __init__(self, animator):
        self.animator = animator

    def on_press(self) -> None:
        self.animator.enable_triadic_colors()

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.is_triadic_colors_enabled:
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100

        beat = int(metronome.now_pos)
        color = self.animator.triadic_colors[beat & 1]
        color = color_rgb_to_bytes(color)
        return apc_mini_mk2.PadLedState(behavior, color[0], color[1], color[2])

class PadCtrl_SetDimmerPattern(PadCtrl_Base):
    def __init__(self, animator, dimmer_animator, pad_color = [255,255,255]):
        self.animator = animator
        self.dimmer_animator = dimmer_animator
        self.pad_color = pad_color

    def on_press(self) -> None:
        self.animator.dimmer_animator = self.dimmer_animator

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.dimmer_animator == self.dimmer_animator:
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100
        return apc_mini_mk2.PadLedState(behavior, self.pad_color[0], self.pad_color[1], self.pad_color[2])

class PadCtrl_SetMovementPattern(PadCtrl_Base):
    def __init__(self, animator, movement, pad_color = [255,255,255]):
        self.animator = animator
        self.movement = movement
        self.pad_color = pad_color

    def on_press(self) -> None:
        self.animator.movement = self.movement

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.movement == self.movement:
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
    pad_matrix.set_pad(0, 7, PadCtrl_SetTriadicColors(busking.scanners_animator))
    pad_matrix.set_pad(7, 7, PadCtrl_SetRainbowColors(busking.conduit_animator))

def init_pad_dimmers(busking : VoidTerrorSilenceBusking, pad_matrix : PadCtrlMatrix):
    def init_common(row : int, col : int, animator, dimmer_animator):
        if (col & 1) == (row & 1):
            lum = 0x44
        else:
            lum = 0xFF
        pad_color = (lum, lum, lum)
        pad_matrix.set_pad(row, col, PadCtrl_SetDimmerPattern(busking.scanners_animator, dimmer_animator, pad_color))
    def init_scanners(row : int, col : int, dimmer_animator):
        init_common(row, col, busking.scanners_animator, dimmer_animator)
    def init_conduit(row : int, col : int, dimmer_animator):
        init_common(row, col, busking.conduit_animator, dimmer_animator)
        
    init_scanners(1, 0, busking.scanners_animator.cos_dimmer_animator)
    init_scanners(1, 1, busking.scanners_animator.shadow_chase_dimmer_animator)
    init_scanners(1, 2, busking.scanners_animator.quick_chase_dimmer_animator)
    init_scanners(1, 3, busking.scanners_animator.saw_dimmer_animator)
    init_scanners(1, 4, busking.scanners_animator.alt_saw_dimmer_animator)
    init_scanners(1, 5, busking.scanners_animator.double_pulse_dimmer_animator)

    init_conduit(6, 0, busking.conduit_animator.cos_dimmer_animator)
    init_conduit(6, 1, busking.conduit_animator.quick_chase_dimmer_animator)
    init_conduit(6, 2, busking.conduit_animator.saw_dimmer_animator)
    init_conduit(6, 3, busking.conduit_animator.alt_saw_dimmer_animator)
    init_conduit(6, 4, busking.conduit_animator.double_pulse_dimmer_animator)

def init_pad_movement(busking : VoidTerrorSilenceBusking, pad_matrix : PadCtrlMatrix):
    def init_scanners(row : int, col : int, movement):
        if (col & 1) == (row & 1):
            lum = 0x44
        else:
            lum = 0xFF
        pad_color = (lum, lum, lum)
        pad_matrix.set_pad(row, col, PadCtrl_SetMovementPattern(busking.scanners_animator, movement, pad_color))

    init_scanners(2, 0, busking.scanners_animator.straight_ahead_movement)
    init_scanners(2, 1, busking.scanners_animator.wander_movement)
    init_scanners(2, 2, busking.scanners_animator.swirl_movement)
    init_scanners(2, 3, busking.scanners_animator.disco_movement)
    init_scanners(2, 4, busking.scanners_animator.pendulum_movement)
    init_scanners(2, 5, busking.scanners_animator.quad_movement)

def busk() -> None:
    with busking_app.create_busking_app() as app:
        with apc_mini_mk2.Device() as midi_input:
            busking = VoidTerrorSilenceBusking()

            pad_matrix = PadCtrlMatrix()
            init_pad_colors(busking, pad_matrix)
            init_pad_dimmers(busking, pad_matrix)
            init_pad_movement(busking, pad_matrix)

            def tick():
                # Tick midi
                for evt in midi_input.tick():
                    # Update tap to beat
                    if evt.ctrl_id.is_scene_button():
                        if evt.ty == apc_mini_mk2.EventType.Pressed:
                            if evt.ctrl_id.row == 0:
                                app.metronome.on_one()
                            elif evt.ctrl_id.row == 1:
                                app.metronome.on_tap()
                    else:
                        pad_matrix.on_midi_event(evt)

                # Update midi LED state
                pad_matrix.update_led_states(midi_input, app.metronome)

                # Tick faders
                master_fader = float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(0)).pos) / 127.0
                scanners_fader =  float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(1)).pos) / 127.0
                back_pars_fader =  float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(2)).pos) / 127.0
                busking.scanners_animator.master_dimmer = master_fader * scanners_fader
                busking.conduit_animator.back_pars_master_dimmer = master_fader * back_pars_fader
                
                # Tick strobe faders
                strobe_fader = float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(3)).pos) / 127.0
                busking.scanners_animator.strobe_speed = strobe_fader
                busking.scanners_animator.strobe_enabled = strobe_fader != 0.0
                strobe_fader = float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(4)).pos) / 127.0
                busking.conduit_animator.back_pars_strobe_speed = strobe_fader
                busking.conduit_animator.back_pars_strobe_enabled = strobe_fader != 0.0
                        
                back_pars_fader =  float() / 255.0

                # Tick animators
                busking.tick(app.metronome)
                busking.update_dmx(app.dmx_ctrl)

            app.main_loop(tick)
busk()
