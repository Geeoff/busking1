# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import math
import colorsys
from more_math import float_eq

@dataclass
class ColorRGB:
    r : float = 0.0
    g : float = 0.0
    b : float = 0.0

    def __eq__(self, other) -> bool:
        if other is None:
            return False
        if type(other) is not ColorRGB:
            return False
        else:
            return float_eq(self.r, other.r) and \
                   float_eq(self.g, other.g) and \
                   float_eq(self.b, other.b)

    def __add__(self, other) -> "ColorRGB":
        return ColorRGB(
            self.r + other.r,
            self.g + other.g,
            self.b + other.b)

    def __sub__(self, other) -> "ColorRGB":
        return ColorRGB(
            self.r - other.r,
            self.g - other.g,
            self.b - other.b)

    def __mul__(self, other) -> "ColorRGB":
        if type(other) is float:
            return ColorRGB(
                self.r * other,
                self.g * other,
                self.b * other)
        assert type(other) is ColorRGB
        return ColorRGB(
            self.r * other.r,
            self.g * other.g,
            self.b * other.b)

    def __truediv__(self, other) -> "ColorRGB":
        if type(other) is float:
            return ColorRGB(
                self.r / other,
                self.g / other,
                self.b / other)
        assert type(other) is ColorRGB
        return ColorRGB(
            self.r / other.r,
            self.g / other.g,
            self.b / other.b)

    @property
    def length_sq(self) -> float:
        return self.r*self.r + self.g*self.g + self.b*self.b

    @property
    def length(self) -> float:
        return math.sqrt(self.length_sq)

    def copy(self) -> "ColorRGB":
        return ColorRGB(self.r, self.g, self.b)

    def clamp(self) -> "ColorRGB":
        max_val = max(self.r, self.g, self.b)
        if max_val > 1.0:
            return self / max_val
        return self.copy()

    def lerp(self, other, t) -> "ColorRGB":
        return self + (other - self) * t

    def to_hsv(self) -> tuple[float,float,float]:
        return colorsys.rgb_to_hsv(self.r, self.g, self.b)

    @staticmethod
    def from_hsv(h:float, s:float, v:float) -> "ColorRGB":
        r,g,b = colorsys.hsv_to_rgb(h,s,v)
        return ColorRGB(r,g,b)

    @staticmethod
    def from_hex(col:int) -> "ColorRGB":
        return ColorRGB(
            ((col >>  0) & 0xFF) / 255.0,
            ((col >>  8) & 0xFF) / 255.0,
            ((col >> 16) & 0xFF) / 255.0)
