# Copyright 2026, Geoffrey Cagle (geoff.v.cagle@gmail.com)
from dmx_controller import DmxController
import socket


class ArtNetDevice(DmxController):
    """Art-Net DMX sender."""

    # Note: Standard default port for Art-Net.
    ARTNET_PORT = 6454

    # Note: UE5 starts the universes at 1 so we use that here, but QLC+ starts at 0.
    def __init__(self, target_ip:str="127.0.0.1", universe:int=1, port:int|None=None):
        super().__init__()
        if port is None:
            port = ArtNetDevice.ARTNET_PORT
        self.target = (target_ip, port)

        # Init networking
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Start the packet sequence number at 1. 0 means sequencing is disabled, so this will roll
        # over from 255 to 1.
        self.sequence = 1

        # Pre-build packet buffer (header + 512 DMX bytes)
        self.packet = bytearray(18 + 512)

        # Art-Net header
        # See ArtDmx in Art-Net spec: https://art-net.org.uk/downloads/art-net.pdf
        # Note how HSB and LSB are used inconsistently here. This matches the spec.
        self.packet[0:8] = b'Art-Net\x00'
        self.packet[8:10] = (0x00, 0x50)         # ArtDmx opcode
        self.packet[10:12] = (0x00, 14)          # Art-Net protocol version (14.0)
        self.packet[12] = self.sequence          # packet sequence number
        self.packet[13] = 0                      # physical ID (to disguish between input devices)

        assert universe <= 0xFFFF
        self.packet[14] = universe & 0xFF        # universe LSB ("SubUni" of "Port-Address")
        self.packet[15] = (universe >> 8) & 0xFF # universe HSB ("Net" of "Port-Address")

        chan_ct = 512
        self.packet[16] = (chan_ct >> 8) & 0xFF  # dmx channel count HSB
        self.packet[17] = chan_ct & 0xFF         # dmx channel count LSB

    def flush(self) -> None:
        """Send current DMX state."""
        # Update sequence number.
        self.packet[12] = self.sequence
        self.sequence += 1
        if self.sequence > 255:
            self.sequence = 1

        # Copy DMX state into packet and send the packet.
        self.packet[18:530] = self.state
        self.sock.sendto(self.packet, self.target)
