"""
RadarSuite v4.2.0 - Session Manager for Labeled Audio Data
Manages storage and retrieval of labeled recording sessions

Storage structure:
    Data/LabeledSessions/
    ├── session_2025-12-05_21-15-00/
    │   ├── metadata.json
    │   ├── audio.npy (raw audio data)
    │   └── labels.json
    └── session_2025-12-05_22-30-00/
        ├── metadata.json
        ├── audio.npy
        └── labels.json
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
import threading

from app.core.logger import log
from app.core.constants import VERSION


@dataclass
class AudioLabel:
    """
    Represents a label/annotation in a recording session.

    Attributes:
        id: Unique label ID within session
        label_class: Category (e.g., 'footstep', 'gunshot', 'ambient')
        timestamp_sec: Point-in-time label (seconds from session start)
        end_time_sec: Optional end time for interval labels
        description: Optional text description
        confidence: Optional confidence score (0-100)
    """
    id: int
    label_class: str
    timestamp_sec: float
    end_time_sec: Optional[float] = None
    description: str = ""
    confidence: float = 100.0

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "AudioLabel":
        return AudioLabel(**data)

    @property
    def is_interval(self) -> bool:
        """Check if this is an interval label (has end time)."""
        return self.end_time_sec is not None

    @property
    def duration(self) -> float:
        """Duration in seconds (0 for point labels)."""
        if self.end_time_sec is not None:
            return self.end_time_sec - self.timestamp_sec
        return 0.0


@dataclass
class LabeledSession:
    """
    Represents a complete labeled recording session.

    Attributes:
        session_id: Unique identifier (timestamp-based)
        created_at: Creation timestamp (ISO format)
        app_version: RadarSuite version
        sample_rate: Audio sample rate
        channels: Number of audio channels
        duration_sec: Total recording duration
        labels: List of labels
        notes: Optional session notes
    """
    session_id: str
    created_at: str
    app_version: str
    sample_rate: int
    channels: int
    duration_sec: float = 0.0
    labels: List[AudioLabel] = field(default_factory=list)
    notes: str = ""

    def to_metadata_dict(self) -> dict:
        """Convert to metadata dict (without labels)."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "app_version": self.app_version,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "duration_sec": self.duration_sec,
            "notes": self.notes,
            "label_count": len(self.labels),
        }

    def to_labels_dict(self) -> dict:
        """Convert labels to dict for saving."""
        return {
            "session_id": self.session_id,
            "labels": [label.to_dict() for label in self.labels],
        }

    @staticmethod
    def from_dicts(metadata: dict, labels_data: dict) -> "LabeledSession":
        """Create session from metadata and labels dicts."""
        labels = [AudioLabel.from_dict(l) for l in labels_data.get("labels", [])]
        return LabeledSession(
            session_id=metadata["session_id"],
            created_at=metadata["created_at"],
            app_version=metadata["app_version"],
            sample_rate=metadata["sample_rate"],
            channels=metadata["channels"],
            duration_sec=metadata.get("duration_sec", 0.0),
            labels=labels,
            notes=metadata.get("notes", ""),
        )

    def add_label(
        self,
        label_class: str,
        timestamp_sec: float,
        end_time_sec: Optional[float] = None,
        description: str = "",
        confidence: float = 100.0
    ) -> AudioLabel:
        """Add a new label to this session."""
        label_id = len(self.labels) + 1
        label = AudioLabel(
            id=label_id,
            label_class=label_class,
            timestamp_sec=timestamp_sec,
            end_time_sec=end_time_sec,
            description=description,
            confidence=confidence,
        )
        self.labels.append(label)
        return label

    def remove_label(self, label_id: int) -> bool:
        """Remove a label by ID."""
        for i, label in enumerate(self.labels):
            if label.id == label_id:
                self.labels.pop(i)
                return True
        return False

    def get_labels_in_range(self, start_sec: float, end_sec: float) -> List[AudioLabel]:
        """Get all labels within a time range."""
        result = []
        for label in self.labels:
            if start_sec <= label.timestamp_sec <= end_sec:
                result.append(label)
            elif label.is_interval and label.end_time_sec is not None:
                if start_sec <= label.end_time_sec <= end_sec:
                    result.append(label)
        return result


class SessionManager:
    """
    Manages storage and retrieval of labeled recording sessions.

    Handles:
    - Creating new sessions
    - Saving audio data and labels
    - Loading existing sessions
    - Listing available sessions
    """

    # Default label classes for the UI
    DEFAULT_LABEL_CLASSES = [
        "footstep_walk",
        "footstep_run",
        "gunshot",
        "explosion",
        "vehicle",
        "voice",
        "ambient",
        "other",
    ]

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize session manager.

        Args:
            base_path: Base directory for sessions (default: Data/LabeledSessions)
        """
        if base_path is None:
            # Default path relative to app root
            app_root = Path(__file__).parent.parent.parent.parent
            base_path = app_root / "Data" / "LabeledSessions"

        self.base_path = Path(base_path)
        self._lock = threading.Lock()

        # Ensure directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)

        log(f"SessionManager initialized: {self.base_path}", "INFO")

    def _validate_session_id(self, session_id: str) -> bool:
        """
        Validate session_id to prevent path traversal attacks.

        FIXED v4.2.1: Security - prevent directory traversal.

        Args:
            session_id: Session ID to validate

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If session_id contains invalid characters
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        # Check for path traversal attempts
        dangerous_patterns = ['..', '/', '\\', '\x00']
        for pattern in dangerous_patterns:
            if pattern in session_id:
                raise ValueError(f"Invalid session_id: contains '{pattern}'")

        # Validate format: should match session_YYYY-MM-DD_HH-MM-SS pattern
        import re
        if not re.match(r'^session_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$', session_id):
            log(f"Session ID '{session_id}' doesn't match expected format", "WARNING")
            # Allow non-standard IDs but log warning

        # Final check: resolved path must be under base_path
        resolved = (self.base_path / session_id).resolve()
        if not str(resolved).startswith(str(self.base_path.resolve())):
            raise ValueError(f"Invalid session_id: path traversal detected")

        return True

    def create_session(
        self,
        sample_rate: int = 48000,
        channels: int = 2,
        notes: str = ""
    ) -> LabeledSession:
        """
        Create a new recording session.

        Args:
            sample_rate: Audio sample rate
            channels: Number of audio channels
            notes: Optional session notes

        Returns:
            New LabeledSession instance
        """
        now = datetime.now()
        session_id = f"session_{now.strftime('%Y-%m-%d_%H-%M-%S')}"

        session = LabeledSession(
            session_id=session_id,
            created_at=now.isoformat(),
            app_version=VERSION,
            sample_rate=sample_rate,
            channels=channels,
            notes=notes,
        )

        # Create session directory
        session_dir = self.base_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        log(f"Created new session: {session_id}", "INFO")
        return session

    def get_session_path(self, session_id: str) -> Path:
        """
        Get path to session directory.

        FIXED v4.2.1: Added session_id validation for security.
        """
        self._validate_session_id(session_id)
        return self.base_path / session_id

    def save_session(
        self,
        session: LabeledSession,
        audio_data: Optional[np.ndarray] = None
    ) -> bool:
        """
        Save session metadata, labels, and optionally audio data.

        Args:
            session: Session to save
            audio_data: Optional audio numpy array

        Returns:
            True if successful
        """
        try:
            with self._lock:
                session_dir = self.get_session_path(session.session_id)
                session_dir.mkdir(parents=True, exist_ok=True)

                # Save metadata
                metadata_path = session_dir / "metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(session.to_metadata_dict(), f, indent=2)

                # Save labels
                labels_path = session_dir / "labels.json"
                with open(labels_path, 'w', encoding='utf-8') as f:
                    json.dump(session.to_labels_dict(), f, indent=2)

                # Save audio data if provided
                if audio_data is not None:
                    audio_path = session_dir / "audio.npy"
                    np.save(audio_path, audio_data)
                    log(f"Saved audio: {audio_data.shape} samples", "INFO")

                log(f"Session saved: {session.session_id} ({len(session.labels)} labels)", "INFO")
                return True

        except Exception as e:
            log(f"Error saving session {session.session_id}: {e}", "ERROR")
            return False

    def load_session(self, session_id: str) -> Optional[LabeledSession]:
        """
        Load a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            LabeledSession or None if not found
        """
        try:
            session_dir = self.get_session_path(session_id)

            if not session_dir.exists():
                log(f"Session not found: {session_id}", "WARNING")
                return None

            # Load metadata
            metadata_path = session_dir / "metadata.json"
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # Load labels
            labels_path = session_dir / "labels.json"
            if labels_path.exists():
                with open(labels_path, 'r', encoding='utf-8') as f:
                    labels_data = json.load(f)
            else:
                labels_data = {"labels": []}

            session = LabeledSession.from_dicts(metadata, labels_data)
            log(f"Loaded session: {session_id} ({len(session.labels)} labels)", "INFO")
            return session

        except Exception as e:
            log(f"Error loading session {session_id}: {e}", "ERROR")
            return None

    def load_audio(self, session_id: str) -> Optional[np.ndarray]:
        """
        Load audio data for a session.

        Args:
            session_id: Session identifier

        Returns:
            Audio numpy array or None
        """
        try:
            audio_path = self.get_session_path(session_id) / "audio.npy"

            if not audio_path.exists():
                log(f"Audio not found for session: {session_id}", "WARNING")
                return None

            audio = np.load(audio_path)
            log(f"Loaded audio: {audio.shape} samples", "INFO")
            return audio

        except Exception as e:
            log(f"Error loading audio for {session_id}: {e}", "ERROR")
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions with basic info.

        Returns:
            List of session info dicts
        """
        sessions = []

        try:
            for session_dir in self.base_path.iterdir():
                if not session_dir.is_dir():
                    continue

                if not session_dir.name.startswith("session_"):
                    continue

                metadata_path = session_dir / "metadata.json"
                if not metadata_path.exists():
                    continue

                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    # Check if audio exists
                    has_audio = (session_dir / "audio.npy").exists()

                    sessions.append({
                        "session_id": metadata.get("session_id", session_dir.name),
                        "created_at": metadata.get("created_at", "Unknown"),
                        "duration_sec": metadata.get("duration_sec", 0),
                        "label_count": metadata.get("label_count", 0),
                        "has_audio": has_audio,
                        "notes": metadata.get("notes", ""),
                    })
                except Exception as e:
                    log(f"Error reading session {session_dir.name}: {e}", "WARNING")

            # Sort by creation date (newest first)
            sessions.sort(key=lambda x: x["created_at"], reverse=True)

        except Exception as e:
            log(f"Error listing sessions: {e}", "ERROR")

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its data.

        Args:
            session_id: Session to delete

        Returns:
            True if successful
        """
        try:
            import shutil
            session_dir = self.get_session_path(session_id)

            if session_dir.exists():
                shutil.rmtree(session_dir)
                log(f"Deleted session: {session_id}", "INFO")
                return True
            else:
                log(f"Session not found for deletion: {session_id}", "WARNING")
                return False

        except Exception as e:
            log(f"Error deleting session {session_id}: {e}", "ERROR")
            return False

    def get_total_labeled_duration(self) -> float:
        """Get total duration of all labeled sessions in seconds."""
        total = 0.0
        for session_info in self.list_sessions():
            total += session_info.get("duration_sec", 0)
        return total

    def get_label_statistics(self) -> Dict[str, int]:
        """Get count of each label class across all sessions."""
        stats = {}

        for session_info in self.list_sessions():
            session = self.load_session(session_info["session_id"])
            if session:
                for label in session.labels:
                    stats[label.label_class] = stats.get(label.label_class, 0) + 1

        return stats
