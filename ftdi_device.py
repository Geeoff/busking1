# Copyright 2024, Geoffrey Cagle (geoff.v.cagle@gmail.com)
import ftd2xx
from dmx_controller import DmxController

class FtdiDevice(DmxController):
    """This class is a wrapper around a ftd2xx device.  It simplifies the interface to the rest of
       the code.

       To use this class:
       1. Create an FtdiDevice. This can be done with a with-statement.
       2. Update the state using the set_chan override.
       3. Call flush to send the state to the DMX controller and update the lights.
       """
    def __init__(self, dev_index:int=0):
        super().__init__()

        print("Connecting to FTDI Device...")
        self.d2xx_dev = None
        try:
            self.d2xx_dev = ftd2xx.open(dev_index)
        except Exception as e:
            print(f"  ERROR: Failed to connect with error '{e}'")

        # Not sure what this is for, but the sample app seems to do it.
        if self.d2xx_dev is not None:
            self.d2xx_dev.clrRts()

    def __enter__(self):
        if self.d2xx_dev is not None:
            self.d2xx_dev.__enter__()
        return self

    def __exit__(self, exit_type, exit_value, traceback):
        if self.d2xx_dev is not None:
            print("Resetting DMX devices...")
            # Clear and write state.
            self.reset_chans()
            self.flush()

            # Shutdown ftd2xx device.
            print("Releasing FTDI Device...")
            return self.d2xx_dev.__exit__(exit_type, exit_value, traceback)

        else:
            return False

    def flush(self) -> None:
        """Write current state to the DMX controller."""
        if self.d2xx_dev is not None:
            # Not sure what these are for, but the sample app seems to do it.
            self.d2xx_dev.setBreakOn()
            self.d2xx_dev.setBreakOff()
            self.d2xx_dev.write(b"\0")

            bstate = bytes(self.state)
            self.d2xx_dev.write(bstate)
