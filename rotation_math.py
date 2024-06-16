# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dataclasses import dataclass
import math

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

    