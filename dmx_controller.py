# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
"""Contains DmxController interface/base class and some helper functions."""
import math

####################################################################################################
def in_range(x0, x1, x2) -> bool:
    return (x0 <= x1) and (x1 <= x2)

def float_to_dmx(val, min_val=0.0, max_val=1.0):
    """Converts a float from [min_val, max_val] to a byte from [0, 255].
       If val is an int, it is consider a raw value."""
    if type(val) is float:
        # normalize: [min_val, max_val] -> [0, 1]
        normalized = (val - min_val) / (max_val - min_val)
        val = int(255 * normalized)
    assert in_range(0, val, 255)
    return val

def angle_to_dmx(ang, extent) -> int:
    """Converts an angle from [-extent, extent] to a byte from [0, 255].
       If ang is an int, it is consider a raw value."""
    if type(ang) is float:
        # normalize: [-extent, extent] -> [0, 1]
        normalized = 0.5 * (ang / extent) + 0.5
        ang = int(255 * normalized)
    assert in_range(0, ang, 255)
    return ang

def param_to_dmx(dmx_start:int, dmx_end:int, param) -> int:
    """Converts a param value to an int from [dmx_start, dmx_end].
       If param is a float, it is assumed to be in [0, 1.0].
       If param is an int it is assumed to be in [0, dmx_start-dm_end].
       TODO: This is probably not a practical way to handle int values of param. I should rework
             this."""
    if type(param) is float:
        # [0, 1] -> [dmx_start, dmx_end]
        param = int(dmx_start + param * (dmx_end - dmx_start))
    else:
        # param is assumed to be a value in [0, dmx_start-dmx_end]
        param += dmx_start
    assert in_range(dmx_start, param, dmx_end)
    return param

####################################################################################################
class DmxController:
    """Base interface for a DMX controller.
       For subclasses, this already has a bytearray that represents all 512 channels to send out."""
    def __init__(self):
        self.state = bytearray(512)

    def set_chan(self, base_addr:int, chan:int, val:int) -> None:
        """Set a specific channel.
           Base address and channels both start at 1, to match DMX manuals."""
        self.state[base_addr + chan - 2] = val
        
    def reset_chans(self) -> None:
        """Reset all channels to 0."""
        for i in range(len(self.state)):
            self.state[i] = 0
        
    def flush(self) -> None:
        raise NotImplemented()

def dump_state(state:bytearray|bytes, start_idx=0, count=512) -> str:
    """Helper function for debugging DMX channels."""
    s = ""
    
    # Append rows like:
    # 016: 127, 000, 255, 064, 127, 000, 255, 064, 127, 000, 255, 064, 127, 000, 255, 064
    # Where 016 is the starting OFFSET (address - 1) and the rest are channel values.
    col_count = 16
    for i in range(start_idx, start_idx+count, col_count):
        # Write starting offset.
        row = f"{i:03}: "
        
        # Write values, up to col_count at a time.
        row_count = min(col_count, (i + count - start_idx))
        for b in range(row_count):
            row += f"{state[i+b]:03}, "

        # Append to final string.
        if s:
            s += "\n" + row
        else:
            s = row
            
    return s