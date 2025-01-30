# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import math
import random

####################################################################################################
def in_range(x, start, end):
    return (start <= x) and (x < end)

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def lerp(val1, val2, t):
    return (val2 - val1) * t + val1

def float_eq(val1, val2, tol=0.00001) -> bool:
    return abs(val1 - val2) < tol

####################################################################################################
@dataclass
class Vec2:
    x : float = 0.0
    y : float = 0.0

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def copy_to(self, other) -> None:
        other.x = self.x
        other.y = self.y

    @staticmethod
    def make_random_signed() -> "Vec2":
        return Vec2(2.0 * random.random() - 1.0,
                    2.0 * random.random() - 1.0)

    def __add__(self, other) -> "Vec2":
        return Vec2(
            self.x + other.x,
            self.y + other.y)

    def __sub__(self, other) -> "Vec2":
        return Vec2(
            self.x - other.x,
            self.y - other.y)

    def __mul__(self, scaler:float) -> "Vec2":
        return Vec2(
            self.x * scaler,
            self.y * scaler)

    def dot(self, other) -> float:
        return self.x*other.x + self.y*other.y

    @property
    def length_sq(self) -> float:
        return self.x*self.x + self.y*self.y

    @property
    def length(self) -> float:
        return math.sqrt(self.length_sq)

    def normalize(self) -> "Vec2":
        len_sq = self.length_sq
        if len_sq > 0.0001:
            return self * (1.0 / math.sqrt(len_sq))
        return Vec2()

####################################################################################################
@dataclass
class Vec3:
    x : float = 0.0
    y : float = 0.0
    z : float = 0.0

    def copy(self) -> "Vec3":
        return Vec3(self.x, self.y, self.z)

    @staticmethod
    def make_random_signed() -> "Vec3":
        return Vec3(2.0 * random.random() - 1.0,
                    2.0 * random.random() - 1.0,
                    2.0 * random.random() - 1.0)

    def __add__(self, other) -> "Vec3":
        return Vec3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z)

    def __sub__(self, other) -> "Vec3":
        return Vec3(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z)

    def __mul__(self, scaler) -> "Vec3":
        return Vec3(
            self.x * scaler,
            self.y * scaler,
            self.z * scaler)

    def dot(self, other) -> float:
        return self.x*other.x + self.y*other.y + self.z*other.z

    @property
    def length_sq(self) -> float:
        return self.x*self.x + self.y*self.y + self.z*self.z

    @property
    def length(self) -> float:
        return math.sqrt(self.length_sq)

    def normalize(self) -> "Vec2":
        len_sq = self.length_sq
        if len_sq > 0.0001:
            return self * (1.0 / math.sqrt(len_sq))
        return Vec3()

####################################################################################################
def roll_over_unsigned(ang) -> float:
    while ang < -2.0 * math.pi:
        ang += 2.0 * math.pi
    ang = ang % 2.0 * math.pi
    return ang

def roll_over_signed(ang) -> float:
    while ang < -math.pi:
        ang += 2.0 * math.pi
    while ang > math.pi:
        ang -= 2.0 * math.pi
    return ang

@dataclass
class EulerAngles:
    roll : float = 0.0
    pitch : float = 0.0
    yaw : float = 0.0

    def copy(self) -> "EulerAngles":
        return EulerAngles(self.roll, self.pitch, self.yaw)

    def __add__(self, other) -> "EulerAngles":
        return EulerAngles(
            self.roll + other.roll,
            self.pitch + other.pitch,
            self.yaw + other.yaw)

    def __sub__(self, other) -> "EulerAngles":
        return EulerAngles(
            self.roll - other.roll,
            self.pitch - other.pitch,
            self.yaw - other.yaw)

    def __mul__(self, scaler) -> "EulerAngles":
        return EulerAngles(
            self.roll * scaler,
            self.pitch * scaler,
            self.yaw * scaler)

    def roll_over_unsigned(self) -> "EulerAngles":
        return EulerAngles(
            roll_over_unsigned(self.roll),
            roll_over_unsigned(self.pitch),
            roll_over_unsigned(self.yaw))

    def roll_over_signed(self) -> "EulerAngles":
        return EulerAngles(
            roll_over_signed(self.roll),
            roll_over_signed(self.pitch),
            roll_over_signed(self.yaw))