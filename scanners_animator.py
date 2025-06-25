# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import math
import random
import enum
from dmx_controller import *
import intimidator_scan_305_irc as scan_305_irc
from metronome import Metronome
from more_math import *
from color_math import *
from dimmer_animators import *

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
        self.fixture.color = scan_305_irc.ColorMode.GREEN
        self.fixture.gobo_rot = scan_305_irc.GoboRotMode.SPIN
        self.fixture.gobo_rot_param = 0.25
        self.fixture.gobo = scan_305_irc.GoboMode.SCROLL
        self.fixture.gobo_param = 0.25
        self.fixture.prism_raw = 255
        

    def update_dmx(self, dmx_ctrl:DmxController, master_dimmer:float) -> None:
        # Update dimmer.
        if self.hide:
            self.fixture.dimmer = 0
        else:
            self.fixture.dimmer = master_dimmer * self.dimmer * self.audience_dim

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

class Movement:
    def __init__(self, speed):
        self.speed = speed

    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        raise NotImplemented()

class StraightAheadMovement(Movement):
    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        for scanner in scanner_list:
            scanner.hide = False
            scanner.rot = EulerAngles()

class WanderMovement(Movement):
    def __init__(self, speed=math.pi / 8.0):
        super().__init__(speed)
        self.carrot_dist1 = 1.0 / 6.0
        self.carrot_dist2 = self.carrot_dist1 / 8.0
        self.carrot_rand_scaler = self.carrot_dist2 / 1.0
        self.wall_stength = 1.0
        self.wall_thresh = math.pi / 8.0

    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        for scanner in scanner_list:
            # Don't hide
            scanner.hide = False

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
            scanner.rot.yaw += scanner.steer_dir.x * self.speed * metronome.delta_secs
            scanner.rot.pitch += scanner.steer_dir.y * self.speed * metronome.delta_secs

            # Clamp
            scanner.rot.yaw = clamp(scanner.rot.yaw, -scan_305_irc.PAN_FLOAT_EXTENT,scan_305_irc.PAN_FLOAT_EXTENT)
            scanner.rot.pitch = clamp(scanner.rot.pitch, -scan_305_irc.TILT_FLOAT_EXTENT, scan_305_irc.TILT_FLOAT_EXTENT)

class SinCosMovement(Movement):
    def __init__(self, yaw_speed, pitch_speed):
        super().__init__(yaw_speed)
        self.yaw_to_pitch_speed = pitch_speed / yaw_speed
        self.y = 0.0
        self.p = 0.0

    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        beat = metronome.get_beat_info(self.speed)
        self.y = (self.y + beat.delta_t) % 1.0
        self.p = (self.p + beat.delta_t * self.yaw_to_pitch_speed) % 1.0

        for i, scanner in enumerate(scanner_list):
            # Don't hide
            scanner.hide = False

            # Update rot.
            y = (self.y + i / len(scanner_list)) % 1.0
            p = (self.p + i / len(scanner_list)) % 1.0
            scanner.rot.yaw = math.cos(2.0 * math.pi * y) * scan_305_irc.PAN_FLOAT_EXTENT * 0.75
            scanner.rot.pitch = math.sin(2.0 * math.pi * p) * scan_305_irc.TILT_FLOAT_EXTENT

class DiscoMovement(Movement):
    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        beat = metronome.get_beat_info(self.speed)

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

class PendulumMovement(Movement):
    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        beat = metronome.get_beat_info(self.speed)
        for i, scanner in enumerate(scanner_list):
            # Don't hide
            scanner.hide = False

            # Update rot.
            z = (beat.t + i / len(scanner_list)) % 1.0
            scanner.rot.yaw = (0.5 * math.cos(2.0 * math.pi * z)) * scan_305_irc.PAN_FLOAT_EXTENT
            scanner.rot.pitch = (2.0 * abs(math.cos(2.0 * math.pi * z)) - 1.0) * scan_305_irc.TILT_FLOAT_EXTENT

class QuadMove(enum.IntEnum):
    NONE = 0
    HORZ = enum.auto()
    VERT = enum.auto()
    BOTH = enum.auto()

class QuadMovement(Movement):
    def __init__(self, speed):
        super().__init__(speed)
        self.prev_move = QuadMove.NONE
        self.lead_time = 0.5
        self.quad_pos_start = Vec2()
        self.quad_pos_end = Vec2()
        self.pitch_offset = 0.2

    def tick(self, metronome:Metronome, scanner_list:list[ScannerState]) -> None:
        # Don't hide
        for scanner in scanner_list:
            scanner.hide = False

        # FIXME: Implement real snapping.
        if self.speed < 0.75:
            speed_fixme = 0.5
        elif self.speed >= 1.5:
            speed_fixme = 2.0
        else:
            speed_fixme = 1.0
            
        beat = metronome.get_beat_info(speed_fixme)
        if beat.this_frame:                
            potential_moves = []
            if self.prev_move != QuadMove.HORZ:
                potential_moves.append(QuadMove.HORZ)
            if self.prev_move != QuadMove.VERT:
                potential_moves.append(QuadMove.VERT)
            if self.prev_move != QuadMove.BOTH:
                potential_moves.append(QuadMove.BOTH)

            move = random.choice(potential_moves)
            
            def flip(val:float, extent):
                offset = extent * lerp(0.25, 0.75, random.random())
                if val > 0.0:
                    offset = -offset
                return offset
            
            self.quad_pos_end.copy_to(self.quad_pos_start)
            pos = self.quad_pos_end.copy()
            
            if (move == QuadMove.HORZ) or (move == QuadMove.BOTH):
                self.quad_pos_end.x = flip(self.quad_pos_end.x, scan_305_irc.PAN_FLOAT_EXTENT)
            if (move == QuadMove.VERT) or (move == QuadMove.BOTH):
                self.quad_pos_end.y = flip(self.quad_pos_end.y, scan_305_irc.TILT_FLOAT_EXTENT-self.pitch_offset)
                
            self.prev_move = move                
                
        else:
            t = clamp(beat.t - (1.0 - self.lead_time), 0.0, 1.0)
            pos = lerp(self.quad_pos_start, self.quad_pos_end, t)
            
        def set_pos(i, yaw, pitch): # FIXME: pitch_offset causes bad values
            scanner = scanner_list[i]
            scanner.rot.yaw = yaw
            scanner.rot.pitch = pitch + self.pitch_offset
                
        set_pos(0,  pos.x, -pos.y)
        set_pos(1,  pos.x,  pos.y)
        set_pos(2, -pos.x,  pos.y)
        set_pos(3, -pos.x, -pos.y)

####################################################################################################
class ScannersAnimator:
    def __init__(self, start_addr=101):
        # Init fixture states.
        self.scanner_list = [ScannerState(start_addr + i*scan_305_irc.Mode1.CHANNEL_COUNT) \
                             for i in range(4)]

        # Init master dimmer.
        self.master_dimmer = 1.0

        # Color state
        self.base_color : ColorRGB = ColorRGB()
        self.is_triadic_colors_enabled : bool = False
        self.back_pars_hue = 0.0
        self.triadic_colors = (ColorRGB(), ColorRGB())

        # Init audience dimming.
        # This dims the scanners as they lower down into the audience. This avoids blinding the
        # audience while still being nice and bright when off of them.
        self.audience_dim_end = 0.25
        self.audience_dim_range = 0.20
        self.audience_dim_val = 1.0 #0.25

        # Init animators.
        self.cos_dimmer_animator = CosDimmerAnimator(2.0)
        self.shadow_chase_dimmer_animator = ShadowChaseDimmerAnimator(0.25)
        self.quick_chase_dimmer_animator = QuickChaseDimmerAnimator(1.0)
        self.saw_dimmer_animator = SawDimmerAnimator(1.0)
        self.alt_saw_dimmer_animator = AltSawDimmerAnimator(1.0)
        self.double_pulse_dimmer_animator = DoublePulseDimmerAnimator(1.0)
        self.dimmer_animator = self.shadow_chase_dimmer_animator

        # Movements
        self.straight_ahead_movement = StraightAheadMovement(1.0)
        self.wander_movement = WanderMovement()
        self.swirl_movement = SinCosMovement(0.125, 0.125*0.4)
        self.disco_movement = DiscoMovement(1.0)
        self.pendulum_movement = PendulumMovement(0.125)
        self.quad_movement = QuadMovement(1.0)
        self.movement = self.swirl_movement

        # Strobe state
        self.strobe_enabled = False
        self.strobe_speed = 0.9

        # Blackout FX
        self.blackout_enabled = False

    def set_static_color(self, color) -> None:
        # Convert ColorRGB to ColorMode
        self.base_color = color
        self.is_triadic_colors_enabled = False

        if type(color) is ColorRGB:
            color = scan_305_irc.ColorMode.from_color_rgb(color)
        for scanner in self.scanner_list:
            scanner.fixture.color = color

    def get_static_color(self) -> None | ColorRGB:
        if self.is_triadic_colors_enabled:
            return None
        else:
            return self.base_color

    def set_comp_color(self, hue) -> None:
        assert False
        comp_hue = (hue + 0.5) % 1.0
        color = ColorRGB.from_hsv(comp_hue, 0.0, 1.0)
        self.set_static_color(color)

    def enable_triadic_colors(self) -> None:
        self.is_triadic_colors_enabled = True

    def tick_triadic_colors(self) -> None:
        def hue_to_mode(hue):
            rgb = ColorRGB.from_hsv(hue, 1.0, 1.0)
            return scan_305_irc.ColorMode.from_color_rgb(rgb)

        self.triadic_colors = (
            ColorRGB.from_hsv((self.back_pars_hue + (1.0 / 3.0)) % 1.0, 1.0, 1.0),
            ColorRGB.from_hsv((self.back_pars_hue + (2.0 / 3.0)) % 1.0, 1.0, 1.0))

        if self.is_triadic_colors_enabled:
            for i, scanner in enumerate(self.scanner_list):
                color = self.triadic_colors[i & 1]
                color_mode = scan_305_irc.ColorMode.from_color_rgb(color)
                scanner.fixture.color = color_mode

    def set_rainbow(self, hue) -> None:
        assert False
        for i, scanner in enumerate(self.scanner_list):
            scanner_hue = hue + float(i) / len(self.scanner_list)
            rgb = ColorRGB.from_hsv(scanner_hue, 1.0, 1.0)
            scanner.fixture.color = scan_305_irc.ColorMode.from_color_rgb(rgb)

    def tick(self, metronome:Metronome) -> None:
        self.tick_triadic_colors()
        self._tick_dimmer_animator(metronome)
        if self.movement is not None:
            self.movement.tick(metronome, self.scanner_list)
        self.update_audience_dim()
        self.update_strobe()

    def _tick_dimmer_animator(self, metronome:Metronome) -> None:
        dim_list = self.dimmer_animator.tick(metronome, len(self.scanner_list))
        for i, scanner in enumerate(self.scanner_list):
            scanner.dimmer = dim_list[i]

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
        if self.blackout_enabled:
            master_dimmer = 0.0
        else:
            master_dimmer = self.master_dimmer

        for scanner in self.scanner_list:
            scanner.update_dmx(dmx_ctrl, master_dimmer)