"""
RadarSuite V4.2.1 - Audio Recorder
Session recording with metadata
FIXED v3.5.0: Buffering for reduced I/O
"""

import time
import numpy as np

from core.logger import log
from core.constants import RECORDING_BUFFER_SIZE


class AudioRecorder:
    """
    Session recording and replay system
    Records audio with metadata (detections, timestamps)
    Supports WAV format playback
    """

    def __init__(self, sample_rate=48000):
        log("AudioRecorder.__init__", "INFO")

        self.sample_rate = sample_rate
        self.is_recording = False
        self.recorded_blocks = []
        self.metadata = []  # Detection events with timestamps
        self.start_time = None
        self.total_samples = 0

        # FIXED v3.5.0: Buffering to reduce I/O (flush every 1s instead of every 50ms)
        self._buffer = []  # Temporary buffer for audio blocks
        self._metadata_buffer = []  # Temporary buffer for metadata

    def start_recording(self):
        """Start recording session"""
        self.is_recording = True
        self.recorded_blocks = []
        self.metadata = []
        self.start_time = time.time()
        self.total_samples = 0
        log("Recording started", "INFO")

    def stop_recording(self):
        """Stop recording session (FIXED v3.5.0: Flush remaining buffer)"""
        self.is_recording = False

        # FIXED v3.5.0: Flush any remaining buffered blocks
        self._flush_buffer()

        log(f"Recording stopped: {len(self.recorded_blocks)} blocks, {self.total_samples} samples", "INFO")

    def add_block(self, audio_block, detections=None):
        """
        Add audio block to recording (FIXED v3.5.0: Buffered I/O)

        Args:
            audio_block: numpy array of audio data
            detections: list of detection events for this block
        """
        if not self.is_recording:
            return

        try:
            # FIXED v3.5.0: Add to buffer instead of direct append
            self._buffer.append(audio_block.copy())
            self.total_samples += len(audio_block)

            # Store metadata in buffer
            if detections:
                timestamp = time.time() - self.start_time
                self._metadata_buffer.append({
                    'timestamp': timestamp,
                    'block_index': len(self.recorded_blocks) + len(self._buffer) - 1,
                    'detections': detections.copy()
                })

            # Flush buffer when it reaches threshold (20 blocks = 1 second @ 20 FPS)
            if len(self._buffer) >= RECORDING_BUFFER_SIZE:
                self._flush_buffer()

        except Exception as e:
            log(f"Error adding block to recording: {e}", "ERROR")

    def _flush_buffer(self):
        """
        Flush buffered blocks to main storage (FIXED v3.5.0: Reduce I/O)
        Called when buffer reaches threshold or recording stops
        """
        if not self._buffer:
            return

        try:
            # Append all buffered blocks at once
            self.recorded_blocks.extend(self._buffer)
            self.metadata.extend(self._metadata_buffer)

            # Clear buffers
            buffer_size = len(self._buffer)
            self._buffer = []
            self._metadata_buffer = []

            log(f"Flushed {buffer_size} blocks to recording", "DEBUG")

        except Exception as e:
            log(f"Error flushing buffer: {e}", "ERROR")

    def save_to_wav(self, filename):
        """
        Save recording to WAV file

        Args:
            filename: output WAV file path
        """
        try:
            if not self.recorded_blocks:
                log("No audio to save", "WARNING")
                return False

            # Concatenate all blocks
            full_audio = np.concatenate(self.recorded_blocks, axis=0)

            # Import wave module
            import wave

            # Save WAV file
            with wave.open(filename, 'wb') as wav_file:
                # Set parameters
                n_channels = full_audio.shape[1] if full_audio.ndim == 2 else 1
                sampwidth = 2  # 16-bit
                framerate = self.sample_rate

                wav_file.setnchannels(n_channels)
                wav_file.setsampwidth(sampwidth)
                wav_file.setframerate(framerate)

                # Convert float32 to int16
                audio_int16 = (full_audio * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())

            log(f"Recording saved to {filename}", "INFO")

            # Save metadata to JSON
            metadata_file = filename.replace('.wav', '_metadata.json')
            import json
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)

            log(f"Metadata saved to {metadata_file}", "INFO")
            return True

        except Exception as e:
            log(f"Error saving WAV: {e}", "ERROR")
            return False

    def get_duration(self):
        """Get recording duration in seconds"""
        if self.total_samples == 0:
            return 0.0
        return self.total_samples / self.sample_rate

    def clear(self):
        """Clear recording buffer (FIXED v3.5.0: Also clear internal buffers)"""
        self.recorded_blocks = []
        self.metadata = []
        self.total_samples = 0
        self.start_time = None

        # FIXED v3.5.0: Clear internal buffers
        self._buffer = []
        self._metadata_buffer = []

