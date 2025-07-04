# Copyright 2025, Geoffrey Cagle (geoff.v.cagle@gmail.com)
"""This script controls the lights at Conduit in Winter Park, FL."""
import enum
from subprocess import CREATE_DEFAULT_ERROR_MODE
from tracemalloc import is_tracing
import apc_mini_mk2
import busking_app
from color_math import *
from conduit_animator import ConduitAnimator
from dmx_controller import DmxController
from metronome import Metronome
from mpd218_input import PadTapEvent
from scanners_animator import ScannerState, ScannersAnimator
from scorpion_dual_animator import ScorpionDualAnimator
import venue_rotating_laser
from venus_rotating_laser_animator import VenueRotatingLaserAnimator

####################################################################################################
class VoidTerrorSilenceBusking:
    def __init__(self):
        super().__init__()

        # Init animators.
        self.scanners_animator = ScannersAnimator()
        self.conduit_animator = ConduitAnimator()
        self.laser_animator = VenueRotatingLaserAnimator()
        self.scorpion_animator = ScorpionDualAnimator()

    def tick(self, metronome:Metronome) -> None:
        # Update my own state.
        self._tick_color_sync()

        # Update animators.
        self.scanners_animator.tick(metronome)
        self.conduit_animator.tick(metronome)
        self.laser_animator.tick(metronome)
        self.scorpion_animator.tick(metronome)

    def _tick_color_sync(self) -> None:
        # Get hue of the back pars.
        if self.conduit_animator.rainbow_is_enabled:
            back_pars_hue = self.conduit_animator.rainbow_hue
            back_pars_col = ColorRGB.from_hsv(back_pars_hue, 1.0, 1.0)
        else:
            back_pars_hue, _, _ = self.conduit_animator.base_color.to_hsv()
            back_pars_col = self.conduit_animator.base_color.copy()

        # Sync colors with scanners.
        self.scanners_animator.back_pars_hue = back_pars_hue

        # Sync colors with lasers.
        self.laser_animator.light_color = back_pars_col

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        self.scanners_animator.update_dmx(dmx_ctrl)
        self.conduit_animator.update_dmx(dmx_ctrl)
        self.laser_animator.update_dmx(dmx_ctrl)
        self.scorpion_animator.update_dmx(dmx_ctrl)

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

class PadCtrl_BeatFlash(PadCtrl_Base):
    def __init__(self, animator, beat_flash_enabled:bool, beat_flash_speed:int, pad_color = [255,255,255]):
        self.animator = animator
        self.pad_color = pad_color
        self.beat_flash_enabled = beat_flash_enabled
        self.beat_flash_speed = beat_flash_speed

    def on_press(self) -> None:
        self.animator.beat_flash_enabled = self.beat_flash_enabled
        self.animator.beat_flash_speed = self.beat_flash_speed

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        if self.animator.beat_flash_enabled == self.beat_flash_enabled and \
           self.animator.beat_flash_speed == self.beat_flash_speed:
            behavior = apc_mini_mk2.PadLedBehavior.PULSE_1_8
        else:
            behavior = apc_mini_mk2.PadLedBehavior.PCT_100
        return apc_mini_mk2.PadLedState(behavior, self.pad_color[0], self.pad_color[1], self.pad_color[2])

class PadCtrl_CallBack(PadCtrl_Base):
    def __init__(self, callback, pad_color):
        self.callback = callback
        self.pad_color = pad_color

    def on_press(self) -> None:
        self.callback()

    def get_pad_led_state(self, metronome: Metronome) -> apc_mini_mk2.PadLedState:
        return apc_mini_mk2.PadLedState(
            apc_mini_mk2.PadLedBehavior.PCT_100, self.pad_color[0], self.pad_color[1], self.pad_color[2])

class PadCtrlMatrix:
    def __init__(self):
        self._matrix = [[None, None,None, None,None, None,None, None] for _ in range(8)]

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
                    midi_input.set_led_state(ctrl_id, led_state)#, False)
        #midi_input.send_pad_colors_by_sysex()

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
        pad_matrix.set_pad(row, col, PadCtrl_SetDimmerPattern(animator, dimmer_animator, pad_color))
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

def init_beat_flash(busking : VoidTerrorSilenceBusking, pad_matrix : PadCtrlMatrix):
    def init_pad(row : int, col : int, beat_flash_enabled:bool, beat_flash_speed:int, lum:int):
        pad_color = (lum, lum, lum)
        pad_matrix.set_pad(row, col, PadCtrl_BeatFlash(
            busking.conduit_animator, beat_flash_enabled, beat_flash_speed, pad_color))

    init_pad(5, 0, False, 2, 0x22)
    init_pad(5, 1, True, 2, 0xFF)
    init_pad(5, 2, True, 4, 0xFF)

    callback_color = [0xFF, 0xFF, 0xFF]
    pad_matrix.set_pad(5, 6, PadCtrl_CallBack(busking.conduit_animator.start_quick_flash, callback_color))
    pad_matrix.set_pad(5, 7, PadCtrl_CallBack(busking.conduit_animator.start_long_flash, callback_color))

# Hacky state.
_tick_beat_leds_prev_beat = None

def tick_beat_leds(midi_input : apc_mini_mk2.Device, beat:int):
    global _tick_beat_leds_prev_beat

    # Only update if there was a change.
    beat = beat % 4
    if _tick_beat_leds_prev_beat == beat:
        return

    # Update LED states.
    def set_led_state(scene_btn_idx:int, on : bool):
        led_state = apc_mini_mk2.ButtonLedState()
        if on:
            led_state.behavior = apc_mini_mk2.ButtonLedBehavior.ON
        else:
            led_state.behavior = apc_mini_mk2.ButtonLedBehavior.OFF

        btn_id = apc_mini_mk2.ControlID.scene_button(scene_btn_idx)
        midi_input.set_led_state(btn_id, led_state)

    if _tick_beat_leds_prev_beat is not None:
        set_led_state(_tick_beat_leds_prev_beat, False)
    set_led_state(beat, True)

    # Update prev beat.
    _tick_beat_leds_prev_beat = beat

def busk() -> None:
    with busking_app.create_busking_app() as app:
        with apc_mini_mk2.Device() as midi_input:
            busking = VoidTerrorSilenceBusking()

            pad_matrix = PadCtrlMatrix()
            init_pad_colors(busking, pad_matrix)
            init_pad_dimmers(busking, pad_matrix)
            init_pad_movement(busking, pad_matrix)
            init_beat_flash(busking, pad_matrix)

            # Set up stroggle toggle buttons
            scanner_strobe_enabled = False
            par_strobe_enabled = False
            def set_track_button_led(col_idx:int, enabled:bool):
                btn_id = apc_mini_mk2.ControlID.track_button(col_idx)
                if enabled:
                    btn_behavior = apc_mini_mk2.ButtonLedBehavior.ON
                else:
                    btn_behavior = apc_mini_mk2.ButtonLedBehavior.BLINK
                midi_input.set_led_state(btn_id, apc_mini_mk2.ButtonLedState(btn_behavior))

            # Light up first few track IDs, just so we know they are active. However pressing the buttons won't do
            # anything.
            for i in range(3):
                set_track_button_led(i, True)

            def tick():
                nonlocal scanner_strobe_enabled
                nonlocal par_strobe_enabled

                # Tick midi
                for evt in midi_input.tick():
                    # Update tap to beat
                    if evt.ctrl_id.is_scene_button():
                        if evt.ty == apc_mini_mk2.EventType.Pressed:
                            if evt.ctrl_id.row == 0:
                                app.metronome.on_one()
                            elif 1 <= evt.ctrl_id.row and evt.ctrl_id.row <= 3:
                                app.metronome.on_tap()
                    elif evt.ctrl_id.is_track_button():
                        if evt.ty == apc_mini_mk2.EventType.Pressed:
                            if evt.ctrl_id.col == 3:
                                scanner_strobe_enabled = not scanner_strobe_enabled
                            elif evt.ctrl_id.col == 4:
                                par_strobe_enabled = not par_strobe_enabled
                    else:
                        pad_matrix.on_midi_event(evt)

                # Update midi LED state
                pad_matrix.update_led_states(midi_input, app.metronome)
                tick_beat_leds(midi_input, app.metronome.get_beat_info().count)

                # Tick faders
                master_fader = float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(0)).pos) / 127.0
                scanners_fader =  float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(1)).pos) / 127.0
                back_pars_fader =  float(midi_input.get_input_state(apc_mini_mk2.ControlID.fader(2)).pos) / 127.0
                busking.scanners_animator.master_dimmer = master_fader * scanners_fader
                busking.conduit_animator.back_pars_master_dimmer = master_fader * back_pars_fader
                busking.laser_animator.master_dimmer = master_fader
                busking.laser_animator.light_dimmer = back_pars_fader
                busking.scorpion_animator.fixture.hide = master_fader <= 0.0
                
                # Tick strobe faders
                set_track_button_led(3, scanner_strobe_enabled)
                set_track_button_led(4, par_strobe_enabled)

                strobe_fader = midi_input.get_input_state(apc_mini_mk2.ControlID.fader(3)).pos
                busking.scanners_animator.strobe_enabled = scanner_strobe_enabled and (strobe_fader != 0)
                strobe_fader = float(strobe_fader) / 127.0
                strobe_fader = 1.0 - 0.25 * (1.0 - strobe_fader)
                busking.scanners_animator.strobe_speed = strobe_fader
                
                strobe_fader = midi_input.get_input_state(apc_mini_mk2.ControlID.fader(4)).pos
                busking.conduit_animator.back_pars_strobe_enabled = par_strobe_enabled and (strobe_fader != 0)
                strobe_fader = float(strobe_fader) / 127.0
                strobe_fader = 1.0 - 0.25 * (1.0 - strobe_fader)
                busking.conduit_animator.back_pars_strobe_speed = strobe_fader

                if busking.conduit_animator.back_pars_strobe_enabled:
                    busking.laser_animator.device.strobe = venue_rotating_laser.StrobeMode.STROBE
                    busking.laser_animator.device.strobe_param = strobe_fader
                else:
                    busking.laser_animator.device.strobe = venue_rotating_laser.StrobeMode.OPEN

                # The laser strobes very slowly. When the back pars have any stobe, just set strobe the Scorpion at max
                # speed.
                if par_strobe_enabled and (midi_input.get_input_state(apc_mini_mk2.ControlID.fader(4)).pos > 8):
                    busking.scorpion_animator.fixture.strobe = 1.0
                else:
                    busking.scorpion_animator.fixture.strobe = None


                # Tick animators
                busking.tick(app.metronome)
                busking.update_dmx(app.dmx_ctrl)

            app.main_loop(tick)
busk()
