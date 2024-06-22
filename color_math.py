# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import colorsys

@dataclass
class ColorRGB:
    r : float = 0.0
    g : float = 0.0
    b : float = 0.0

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

    def __div__(self, other) -> "ColorRGB":
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
