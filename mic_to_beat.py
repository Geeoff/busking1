# mic_to_beat.py

import threading
import time
from collections import deque

import aubio
import numpy as np
import sounddevice as sd


class MicToBeatDetector:
    def __init__(self, device_idx, win_s=2048):
        """
        Real-time beat detection detector using microphone input.
        """
        self.win_s = win_s        # aubio window size
        self.hop_s = win_s // 2   # hop size
        self.device_idx = device_idx
        
        device_info = sd.query_devices(device_idx, 'input')
        self.samplerate = int(device_info['default_samplerate'])

        # Aubio onset detection (better for live mic)
        self.tempo_o = aubio.tempo("default", self.win_s, self.hop_s, self.samplerate)

        # Shared state
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

        # Rolling audio buffer
        self._audio_buffer = np.zeros(0, dtype=np.float32)

        # Beat timestamps
        self._beat_times = deque(maxlen=32)
        self._beat_detected = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None

    def poll(self):
        """
        Returns dict:
        - 'beat': True if a beat occurred since last poll
        - 'bpm': estimated beats per minute
        - 'phase': 0..1 fractional position between last and next beat
        """
        with self._lock:
            now = time.time()
            beat = self._beat_detected
            self._beat_detected = False

            bpm = 0.0
            phase = 0.0

            if len(self._beat_times) >= 4:
                intervals = np.diff(np.array(self._beat_times))
                avg_interval = np.mean(intervals)
                if avg_interval > 0:
                    bpm = 60.0 / avg_interval
                    last_beat = max([t for t in self._beat_times if t <= now], default=None)
                    next_beat = last_beat + avg_interval if last_beat else None
                    if last_beat and next_beat:
                        phase = (now - last_beat) / (next_beat - last_beat)
                        phase = min(max(phase, 0.0), 1.0)

            return {"beat": beat, "bpm": bpm, "phase": phase}

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print("Sounddevice input status:", status)

        samples = indata[:, 0].astype(np.float32)
        self._audio_buffer = np.concatenate((self._audio_buffer, samples))

        while len(self._audio_buffer) >= self.hop_s:
            frame = self._audio_buffer[:self.hop_s]
            self._audio_buffer = self._audio_buffer[self.hop_s:]

            is_beat = self.tempo_o(frame)
            if is_beat:
                t = time.time()
                with self._lock:
                    self._beat_times.append(t)
                    self._beat_detected = True

    def _run(self):
        try:
            with sd.InputStream(
                channels=1,
                device=self.device_idx,
                callback=self._audio_callback,
                blocksize=self.hop_s,
                samplerate=self.samplerate,
            ):
                while self._running:
                    time.sleep(0.01)
        except Exception as e:
            print("Error in audio stream:", e)
            self._running = False


def list_input_devices():
    print("Available input devices (sorted by name + host API):")
    hostapis = sd.query_hostapis()
    
    # Collect all input devices
    devices = [
        {
            "index": i,
            "name": dev['name'],
            "channels": dev['max_input_channels'],
            "rate": dev['default_samplerate'],
            "hostapi": hostapis[dev['hostapi']]['name']
        }
        for i, dev in enumerate(sd.query_devices()) if dev['max_input_channels'] > 0
    ]

    # Sort first by device name, then by host API
    devices.sort(key=lambda d: (d['name'].lower(), d['hostapi'].lower()))

    # Print devices
    for dev in devices:
        print(f"{dev['index']:4}: {dev['name']} "
              f"(channels: {dev['channels']}, "
              f"rate: {dev['rate']}, hostapi: {dev['hostapi']})")

def find_mic_index(device_name="Microphone (Yeti Stereo Microphone)", hostapi_name="Windows WDM-KS"):
    print("Searching for microphone...")

    # Get hostapis and index for the desired hostapi
    hostapi_name_list = [hostapi['name'] for hostapi in sd.query_hostapis()]
    hostapi_idx = hostapi_name_list.index(hostapi_name)

    # Find device index.
    selected_device_idx = None

    for i, dev in enumerate(sd.query_devices()):
        print(f"  {i}: {dev['name']}, {hostapi_name_list[dev['hostapi']]}")

        if dev['name'] != device_name:
            continue
        if dev['hostapi'] != hostapi_idx:
            continue

        assert selected_device_idx is None # Should only find one!
        selected_device_idx = i

    if selected_device_idx is not None:
        print(f"  SELECTED {selected_device_idx}")
    else:
        print(f"  ERROR! Mic not found!")

    return selected_device_idx

if __name__ == "__main__":
    list_input_devices()
    device_idx = input("Enter input device index to use (leave blank for default): ")
    device_idx = int(device_idx)

    detector = MicToBeatDetector(device_idx=device_idx)
    detector.start()
    print("Listening for beats... Press Ctrl+C to stop.")

    try:
        while True:
            state = detector.poll()
            if state["beat"]:
                print(f"Beat! BPM={state['bpm']:.2f} Phase={state['phase']:.2f}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        detector.stop()
        print("Stopped.")