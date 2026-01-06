"""Screen capture module using MSS for cross-platform support.

NOTE: For optimal Windows performance, consider implementing Desktop Duplication API (DXGI).
MSS is used here for cross-platform compatibility.
"""

import time
from typing import Tuple, Optional
import numpy as np
import mss
import cv2


class ScreenCapture:
    """High-performance screen capture using MSS."""

    def __init__(self, monitor: int = 0, region: Optional[Tuple[int, int, int, int]] = None,
                 target_fps: int = 30):
        """Initialize screen capture.

        Args:
            monitor: Monitor index (0 for primary, 1+ for additional monitors).
            region: Optional region to capture (x, y, width, height).
            target_fps: Target capture FPS.
        """
        self.sct = mss.mss()
        self.monitor_index = monitor
        self.region = region
        self.target_fps = target_fps
        self.frame_time = 1.0 / target_fps

        # Get monitor info
        if monitor == 0:
            # Capture all monitors
            self.monitor = self.sct.monitors[0]
        else:
            # Capture specific monitor
            if monitor < len(self.sct.monitors):
                self.monitor = self.sct.monitors[monitor]
            else:
                print(f"Monitor {monitor} not found, using primary monitor")
                self.monitor = self.sct.monitors[1]

        # Override with custom region if provided
        if region:
            x, y, w, h = region
            self.monitor = {"top": y, "left": x, "width": w, "height": h}

        # Statistics
        self.frame_count = 0
        self.fps = 0
        self.last_fps_update = time.time()

    def capture_frame(self) -> np.ndarray:
        """Capture a single frame.

        Returns:
            Frame as numpy array (BGR format for OpenCV compatibility).
        """
        # Capture screenshot
        screenshot = self.sct.grab(self.monitor)

        # Convert to numpy array
        frame = np.array(screenshot)

        # Convert from BGRA to BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        # Update statistics
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_update >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_update = current_time

        return frame

    def capture_stream(self):
        """Continuous frame capture generator with FPS control.

        Yields:
            Captured frames as numpy arrays.
        """
        last_capture_time = time.time()

        while True:
            # FPS limiting
            current_time = time.time()
            elapsed = current_time - last_capture_time

            if elapsed < self.frame_time:
                time.sleep(self.frame_time - elapsed)

            frame = self.capture_frame()
            last_capture_time = time.time()

            yield frame

    def get_monitor_info(self) -> dict:
        """Get current monitor information.

        Returns:
            Dictionary with monitor dimensions and position.
        """
        return {
            "left": self.monitor["left"],
            "top": self.monitor["top"],
            "width": self.monitor["width"],
            "height": self.monitor["height"]
        }

    def get_fps(self) -> float:
        """Get current capture FPS.

        Returns:
            Current FPS.
        """
        return self.fps

    def close(self):
        """Release resources."""
        self.sct.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
