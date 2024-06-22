# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
import random
from dmx_controller import *
import intimidator_scan_305_irc as scan_305_irc
from metronome import Metronome
from more_math import *
from color_math import *

####################################################################################################
class ScannerState:
    def __init__(self, dmx_offset:int):
        # Dimmer state.
        self.dimmer = 1.0
        self.hide = False # Sets dimmer to 0 to hide a movement.
        self.audience_dim = 1.0

        # Misc state.
        self.rot = EulerAngles()
        self.strobe_speed = None

        # AI movement state
        self.steer_dir = Vec2.make_random_signed().normalize()
        self.wander_dir = self.steer_dir.copy()

        # DMX fiture to update.
        self.fixture = scan_305_irc.Mode1(dmx_offset)

        # Init figure gobo rotation state.
        self.fixture.gobo_rot = scan_305_irc.GoboRotMode.SPIN
        self.fixture.gobo_rot_param = 0.25

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        # Update dimmer.
        if self.hide:
            self.fixture.dimmer = 0
        else:
            self.fixture.dimmer = self.dimmer * self.audience_dim

        # Update rotation.
        rot = self.rot.roll_over_signed()
        self.fixture.pan = rot.yaw
        self.fixture.tilt = rot.pitch

        # If gobo state is angle, use roll to set the position.
        if self.fixture.gobo_rot == scan_305_irc.GoboRotMode.ANGLE:
            self.fixture.gobo_rot_param = rot.roll

        # Update strobe.
        if self.strobe_speed is None:
            self.fixture.shutter = scan_305_irc.ShutterMode.OPEN
        else:
            self.fixture.shutter = scan_305_irc.ShutterMode.SYNC
            self.fixture.shutter_param = self.strobe_speed

        # Sync with DMX controller.
        self.fixture.update_dmx(dmx_ctrl)

####################################################################################################
# Scanner movements:
#

def straight_ahead_movement(metronome:Metronome, scanner_list:list[ScannerState]) -> None:
    for scanner in scanner_list:
        scanner.rot = EulerAngles()

class WanderMovement:
    def __init__(self):
        self.carrot_dist1 = 1.0 / 6.0
        self.carrot_dist2 = self.carrot_dist1 / 8.0
        self.carrot_rand_scaler = self.carrot_dist2 / 1.0
        self.wall_stength = 1.0
        self.wall_thresh = math.pi / 8.0
        self.speed = math.pi / 8.0

    def __call__(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        for scanner in scanner_list:
            # Calc wander vector.
            scanner.wander_dir = (scanner.wander_dir + \
                Vec2.make_random_signed() * self.carrot_rand_scaler).normalize() * self.carrot_dist2

            wander_vec = (scanner.steer_dir * self.carrot_dist1 + scanner.wander_dir).normalize()

            # Calc wall avoidance vector
            wall_vec = Vec2()

            if scanner.rot.yaw < self.wall_thresh - scan_305_irc.PAN_FLOAT_EXTENT:
                wall_vec.x = self.wall_stength
            elif scanner.rot.yaw > scan_305_irc.PAN_FLOAT_EXTENT - self.wall_thresh:
                wall_vec.x = -self.wall_stength

            if scanner.rot.pitch < self.wall_thresh - scan_305_irc.TILT_FLOAT_EXTENT:
                wall_vec.y = self.wall_stength
            elif scanner.rot.pitch > scan_305_irc.TILT_FLOAT_EXTENT - self.wall_thresh:
                wall_vec.y = -self.wall_stength

            # Move
            scanner.steer_dir = (wall_vec + wander_vec).normalize()
            scanner.rot.yaw += scanner.steer_dir.x * self.speed * metronome.dt
            scanner.rot.pitch += scanner.steer_dir.y * self.speed * metronome.dt

            # Clamp
            scanner.rot.yaw = clamp(scanner.rot.yaw, -scan_305_irc.PAN_FLOAT_EXTENT,scan_305_irc.PAN_FLOAT_EXTENT)
            scanner.rot.pitch = clamp(scanner.rot.pitch, -scan_305_irc.TILT_FLOAT_EXTENT, scan_305_irc.TILT_FLOAT_EXTENT)

class SinCosMovement:
    def __init__(self, yaw_speed, pitch_speed):
        self.yaw_speed = yaw_speed
        self.pitch_speed = pitch_speed

    def __call__(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        beat_y = metronome.get_beat_info(self.yaw_speed)
        beat_p = metronome.get_beat_info(self.pitch_speed)
        for i, scanner in enumerate(scanner_list):
            y = (beat_y.t + i / len(scanner_list)) % 1.0
            p = (beat_p.t + i / len(scanner_list)) % 1.0
            scanner.rot.yaw = math.cos(2.0 * math.pi * y) * scan_305_irc.PAN_FLOAT_EXTENT * 0.75
            scanner.rot.pitch = math.sin(2.0 * math.pi * p) * scan_305_irc.TILT_FLOAT_EXTENT

fix8_movement = SinCosMovement(0.125*0.5, 0.125) # Broken!
nice_sincos_movement = SinCosMovement(0.125, 0.125*0.4)

def disco_movement(metronome:Metronome, scanner_list:list[ScannerState]) -> None:
    beat = metronome.get_beat_info(1.0)

    for i, scanner in enumerate(scanner_list):
        beat_idx = (beat.count + i) % len(scanner_list)
        if beat_idx == 0:
            # Move quickly to the start position with no light.
            y = 0.0
            scanner.hide = True
        else:
            # Rotate across the room.
            y = (beat_idx-1 + beat.t) / (len(scanner_list)-1)
            scanner.hide = False

        p = (float(i) / (len(scanner_list)-1))

        scanner.rot.yaw = (2.0 * y - 1.0)  * scan_305_irc.PAN_FLOAT_EXTENT
        scanner.rot.pitch = (2.0 * p - 1.0) * scan_305_irc.TILT_FLOAT_EXTENT

def pendulum_movement(metronome:Metronome, scanner_list:list[ScannerState]) -> None:
    speed = 0.125
    beat = metronome.get_beat_info(speed)
    for i, scanner in enumerate(scanner_list):
        z = (beat.t + i / len(scanner_list)) % 1.0
        scanner.rot.yaw = (0.5 * math.cos(2.0 * math.pi * z)) * scan_305_irc.PAN_FLOAT_EXTENT
        scanner.rot.pitch = (2.0 * abs(math.cos(2.0 * math.pi * z)) - 1.0) * scan_305_irc.TILT_FLOAT_EXTENT


####################################################################################################
class ScannersAnimator:
    def __init__(self, start_addr=101):
        # Init fixture states.
        self.scanner_list = [ScannerState(start_addr + i*scan_305_irc.Mode1.CHANNEL_COUNT) \
                             for i in range(4)]

        # Init audience dimming.
        # This dims the scanners as they lower down into the audience. This avoids blinding the
        # audience while still being nice and bright when off of them.
        self.audience_dim_end = 0.0
        self.audience_dim_range = 0.25
        self.audience_dim_val = 0.25

        # Init animators.
        self.move_func = nice_sincos_movement

        # Strobe state
        self.strobe_enabled = False
        self.strobe_speed = 0.9

    def set_color(self, color) -> None:
        # Convert ColorRGB to ColorMode
        if type(color) is ColorRGB:
            color = scan_305_irc.ColorMode.from_color_rgb(color)
        for scanner in self.scanner_list:
            scanner.fixture.color = color

    def set_comp_color(self, hue) -> None:
        comp_hue = (hue + 0.5) % 1.0
        color = ColorRGB.from_hsv(comp_hue, 0.0, 1.0)
        self.set_color(color)

    def set_triadic_colors(self, hue) -> None:
        def hue_to_mode(hue):
            rgb = ColorRGB.from_hsv(hue, 1.0, 1.0)
            return scan_305_irc.ColorMode.from_color_rgb(rgb)

        col0 = hue_to_mode((hue + (1.0 / 3.0)) % 1.0)
        col1 = hue_to_mode((hue + (2.0 / 3.0)) % 1.0)

        for i, scanner in enumerate(self.scanner_list):
            if i & 1:
                scanner.fixture.color = col1
            else:
                scanner.fixture.color = col0

    def set_rainbow(self, hue) -> None:
        for i, scanner in enumerate(self.scanner_list):
            scanner_hue = hue + float(i) / len(self.scanner_list)
            rgb = ColorRGB.from_hsv(scanner_hue, 1.0, 1.0)
            scanner.fixture.color = scan_305_irc.ColorMode.from_color_rgb(rgb)

    def tick(self, metronome:Metronome) -> None:
        if self.move_func is not None:
            self.move_func(metronome, self.scanner_list)
        self.update_audience_dim()
        self.update_strobe()

    def update_audience_dim(self):
        for scanner in self.scanner_list:
            if self.audience_dim_range > 0.0001:
                t = (scanner.rot.pitch - self.audience_dim_end) / self.audience_dim_range
                t = clamp(t, 0.0, 1.0)
                dim = lerp(self.audience_dim_val, 1.0, t)
            elif scanner.rot.pitch < self.audience_dim_end:
                dim = 1.0
            else:
                dim = 0.0
            scanner.audience_dim = dim

    def update_strobe(self):
        strobe_speed = self.strobe_speed if self.strobe_enabled else None
        for scanner in self.scanner_list:
            scanner.strobe_speed = strobe_speed

    def update_dmx(self, dmx_ctrl:DmxController) -> None:
        for scanner in self.scanner_list:
            scanner.update_dmx(dmx_ctrl)