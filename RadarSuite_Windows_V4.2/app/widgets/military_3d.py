"""
RadarSuite v4.2.1-k0006 - Military3DRadar

FIXED v4.2.1-k0006: Extracted from radar.py for improved modularity
Split radar.py (1674 lines) into focused, single-responsibility modules
"""

import math
import numpy as np
import pyqtgraph.opengl as gl
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor

from core import log, VERSION
from .target_state import TargetState


class Military3DRadar(gl.GLViewWidget):
    """
    3D Sphere Wallhack HUD Radar - Military Sci-Fi Style

    Features:
    - Semi-transparent holographic sphere
    - Neon green/cyan color scheme
    - Walk/Run/Shot target markers with colored indicators
    - Lines connecting targets to sphere surface
    - X/Y/Z coordinate axes
    - Player icon at center
    - Wallhack-style visibility effect
    """

    def __init__(self):
        super().__init__()
        log("Military3DRadar.__init__", "INFO")

        # Dark background for contrast
        self.setBackgroundColor('#020508')
        self.setCameraPosition(distance=180, elevation=25, azimuth=45)

        # Enable mouse rotation
        self.setMouseTracking(True)

        # Settings
        self.max_distance = 100
        self.sweep_angle = 0

        # Colors (neon green/cyan theme)
        self.COLOR_SPHERE = (0, 0.8, 0.6, 0.08)
        self.COLOR_SPHERE_EDGE = (0, 1, 0.8, 0.25)
        self.COLOR_GRID = (0, 0.6, 0.5, 0.3)
        self.COLOR_AXIS_X = (1, 0.3, 0.3, 0.8)
        self.COLOR_AXIS_Y = (0.3, 1, 0.3, 0.8)
        self.COLOR_AXIS_Z = (0.3, 0.6, 1, 0.8)
        self.COLOR_SWEEP = (0, 1, 0.5, 0.6)
        self.COLOR_WALK = (0, 0.8, 0.4, 1)
        self.COLOR_RUN = (1, 0.8, 0, 1)
        self.COLOR_SHOT = (1, 0.2, 0.2, 1)
        self.COLOR_UNKNOWN = (0.5, 0.5, 0.5, 1)

        # Target data: list of {id, x, y, z, state, speed, distance}
        self.targets_data = []

        # Build the 3D scene
        self._build_holographic_sphere()
        self._build_coordinate_system()
        self._build_player_marker()
        self._build_sweep_plane()
        self._build_target_markers()

        # Auto-rotation timer
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self._auto_rotate)
        self.rotation_timer.start(50)

    def _build_holographic_sphere(self):
        """Build semi-transparent holographic sphere grid"""
        # Main sphere shells (distance rings)
        self.sphere_shells = []
        for radius in [25, 50, 75, 100]:
            # Create wireframe sphere
            md = gl.MeshData.sphere(rows=16, cols=24, radius=radius)
            sphere = gl.GLMeshItem(
                meshdata=md,
                color=self.COLOR_SPHERE,
                shader='balloon',
                drawEdges=True,
                edgeColor=self.COLOR_SPHERE_EDGE,
                smooth=False,
                glOptions='translucent'
            )
            self.addItem(sphere)
            self.sphere_shells.append(sphere)

        # Horizontal rings (latitude)
        self.h_rings = []
        for z in [-75, -50, -25, 0, 25, 50, 75]:
            # Calculate ring radius at this height
            if abs(z) < 100:
                ring_radius = math.sqrt(100**2 - z**2)
                theta = np.linspace(0, 2 * np.pi, 60)
                x = ring_radius * np.cos(theta)
                y = ring_radius * np.sin(theta)
                z_arr = np.full_like(theta, z)
                pts = np.vstack([x, y, z_arr]).T

                ring = gl.GLLinePlotItem(
                    pos=pts,
                    color=self.COLOR_GRID,
                    width=1.5 if z == 0 else 1,
                    antialias=True
                )
                self.addItem(ring)
                self.h_rings.append(ring)

        # Vertical rings (longitude)
        self.v_rings = []
        for angle in range(0, 180, 30):
            theta = np.linspace(0, 2 * np.pi, 60)
            x = 100 * np.cos(theta) * np.cos(np.radians(angle))
            y = 100 * np.cos(theta) * np.sin(np.radians(angle))
            z = 100 * np.sin(theta)
            pts = np.vstack([x, y, z]).T

            ring = gl.GLLinePlotItem(
                pos=pts,
                color=self.COLOR_GRID,
                width=1,
                antialias=True
            )
            self.addItem(ring)
            self.v_rings.append(ring)

    def _build_coordinate_system(self):
        """Build X/Y/Z axes with arrows"""
        axis_length = 115

        # X axis (Red) - Left/Right
        self.x_axis = gl.GLLinePlotItem(
            pos=np.array([[-axis_length, 0, 0], [axis_length, 0, 0]]),
            color=self.COLOR_AXIS_X,
            width=2,
            antialias=True
        )
        self.addItem(self.x_axis)

        # Y axis (Green) - Forward/Back
        self.y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, -axis_length, 0], [0, axis_length, 0]]),
            color=self.COLOR_AXIS_Y,
            width=2,
            antialias=True
        )
        self.addItem(self.y_axis)

        # Z axis (Blue) - Up/Down
        self.z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, -axis_length], [0, 0, axis_length]]),
            color=self.COLOR_AXIS_Z,
            width=2,
            antialias=True
        )
        self.addItem(self.z_axis)

        # Axis arrow heads
        arrow_size = 8
        for axis, direction, color in [
            ('x', [1, 0, 0], self.COLOR_AXIS_X),
            ('y', [0, 1, 0], self.COLOR_AXIS_Y),
            ('z', [0, 0, 1], self.COLOR_AXIS_Z)
        ]:
            pos = np.array(direction) * axis_length
            # Arrow cone
            md = gl.MeshData.cylinder(rows=4, cols=8, radius=[arrow_size/2, 0], length=arrow_size)
            arrow = gl.GLMeshItem(
                meshdata=md,
                color=color,
                shader='shaded',
                smooth=True
            )
            arrow.translate(*pos)
            # Rotate arrow to point along axis
            if axis == 'x':
                arrow.rotate(90, 0, 1, 0)
            elif axis == 'y':
                arrow.rotate(-90, 1, 0, 0)
            # z axis already points up
            self.addItem(arrow)

    def _build_player_marker(self):
        """Build player position marker at center"""
        # Player dot
        self.player_marker = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(0, 1, 1, 1),
            size=15,
            pxMode=True
        )
        self.addItem(self.player_marker)

        # Player direction indicator (small forward arrow)
        self.player_direction = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 15, 0]]),
            color=(0, 1, 1, 0.8),
            width=3,
            antialias=True
        )
        self.addItem(self.player_direction)

        # Crosshair at player position
        ch_size = 12
        crosshair_pts = np.array([
            [-ch_size, 0, 0], [ch_size, 0, 0],
            [0, -ch_size, 0], [0, ch_size, 0],
            [0, 0, -ch_size], [0, 0, ch_size]
        ])
        self.crosshair = gl.GLLinePlotItem(
            pos=crosshair_pts.reshape(-1, 3),
            color=(0, 1, 1, 0.5),
            width=1,
            antialias=True,
            mode='lines'
        )
        self.addItem(self.crosshair)

    def _build_sweep_plane(self):
        """Build rotating sweep plane"""
        # Sweep line on XY plane
        self.sweep_line = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 100, 0]]),
            color=self.COLOR_SWEEP,
            width=2,
            antialias=True
        )
        self.addItem(self.sweep_line)

        # Sweep arc (fading trail effect simulated with multiple lines)
        self.sweep_trail = []
        for i in range(15):
            alpha = 0.4 * (1 - i / 15)
            trail = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 100, 0]]),
                color=(0, 1, 0.5, alpha),
                width=1,
                antialias=True
            )
            self.addItem(trail)
            self.sweep_trail.append(trail)

    def _build_target_markers(self):
        """Build target scatter plot and connection lines"""
        # Main target scatter
        self.target_scatter = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0),
            size=18,
            pxMode=True
        )
        self.addItem(self.target_scatter)

        # Target glow (larger, semi-transparent)
        self.target_glow = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0),
            size=30,
            pxMode=True
        )
        self.addItem(self.target_glow)

        # Connection lines from targets to sphere surface
        self.target_lines = []
        for _ in range(20):  # Max 20 targets
            line = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, 0]]),
                color=(0, 1, 0.5, 0),
                width=1,
                antialias=True
            )
            self.addItem(line)
            self.target_lines.append(line)

        # Vertical drop lines (from target to XY plane)
        self.target_drops = []
        for _ in range(20):
            drop = gl.GLLinePlotItem(
                pos=np.array([[0, 0, 0], [0, 0, 0]]),
                color=(0, 0.5, 1, 0),
                width=1,
                antialias=True,
                mode='line_strip'
            )
            self.addItem(drop)
            self.target_drops.append(drop)

    def _auto_rotate(self):
        """Auto-rotate sweep and update display"""
        self.sweep_angle = (self.sweep_angle + 2) % 360
        self._update_sweep_visual()

    def _update_sweep_visual(self):
        """Update sweep line and trail"""
        angle_rad = math.radians(self.sweep_angle - 90)
        x = 100 * math.cos(angle_rad)
        y = 100 * math.sin(angle_rad)

        # Main sweep line
        self.sweep_line.setData(pos=np.array([[0, 0, 0], [x, y, 0]]))

        # Trail lines
        for i, trail in enumerate(self.sweep_trail):
            trail_angle = self.sweep_angle - (i + 1) * 4
            trail_rad = math.radians(trail_angle - 90)
            tx = 100 * math.cos(trail_rad)
            ty = 100 * math.sin(trail_rad)
            trail.setData(pos=np.array([[0, 0, 0], [tx, ty, 0]]))

    # =========================================================================
    # TARGET MANAGEMENT
    # =========================================================================

    def add_target(self, target_id, angle, distance, elevation=0,
                   state=TargetState.UNKNOWN, speed=0):
        """Add or update target in 3D space"""
        # Calculate 3D position
        angle_rad = math.radians(angle - 90)
        elev_rad = math.radians(elevation)

        dist = min(distance, self.max_distance)
        horiz_dist = dist * math.cos(elev_rad)
        x = horiz_dist * math.cos(angle_rad)
        y = horiz_dist * math.sin(angle_rad)
        z = dist * math.sin(elev_rad)

        # Check if target exists
        for t in self.targets_data:
            if t['id'] == target_id:
                t.update({
                    'x': x, 'y': y, 'z': z,
                    'angle': angle, 'distance': dist, 'elevation': elevation,
                    'state': state, 'speed': speed
                })
                self._update_target_visuals()
                return

        # Add new target
        self.targets_data.append({
            'id': target_id,
            'x': x, 'y': y, 'z': z,
            'angle': angle, 'distance': dist, 'elevation': elevation,
            'state': state, 'speed': speed
        })
        self._update_target_visuals()

    def remove_target(self, target_id):
        """Remove target"""
        self.targets_data = [t for t in self.targets_data if t['id'] != target_id]
        self._update_target_visuals()

    def clear_targets(self):
        """Clear all targets"""
        self.targets_data = []
        self._update_target_visuals()

    def _update_target_visuals(self):
        """Update all target visual elements"""
        if not self.targets_data:
            # Hide all
            self.target_scatter.setData(
                pos=np.array([[0, 0, 0]]),
                color=(1, 0, 0, 0)
            )
            self.target_glow.setData(
                pos=np.array([[0, 0, 0]]),
                color=(1, 0, 0, 0)
            )
            for line in self.target_lines:
                line.setData(pos=np.array([[0, 0, 0], [0, 0, 0]]), color=(0, 0, 0, 0))
            for drop in self.target_drops:
                drop.setData(pos=np.array([[0, 0, 0], [0, 0, 0]]), color=(0, 0, 0, 0))
            return

        # Build position and color arrays
        positions = []
        colors = []
        glow_colors = []

        for t in self.targets_data:
            positions.append([t['x'], t['y'], t['z']])

            # Color based on state
            if t['state'] == TargetState.WALK:
                color = self.COLOR_WALK
            elif t['state'] == TargetState.RUN:
                color = self.COLOR_RUN
            elif t['state'] == TargetState.SHOT:
                color = self.COLOR_SHOT
            else:
                color = self.COLOR_UNKNOWN

            colors.append(color)
            glow_colors.append((color[0], color[1], color[2], 0.3))

        positions = np.array(positions)
        colors = np.array(colors)
        glow_colors = np.array(glow_colors)

        # Update scatter plots
        self.target_scatter.setData(pos=positions, color=colors, size=18)
        self.target_glow.setData(pos=positions, color=glow_colors, size=35)

        # Update connection lines to sphere surface
        for i, t in enumerate(self.targets_data[:20]):
            if i < len(self.target_lines):
                # Line from target to sphere surface (radial)
                dist = math.sqrt(t['x']**2 + t['y']**2 + t['z']**2)
                if dist > 0:
                    scale = 100 / dist
                    surf_x = t['x'] * scale
                    surf_y = t['y'] * scale
                    surf_z = t['z'] * scale
                else:
                    surf_x, surf_y, surf_z = 0, 0, 100

                state_color = colors[i] if i < len(colors) else self.COLOR_UNKNOWN
                line_color = (state_color[0], state_color[1], state_color[2], 0.4)

                self.target_lines[i].setData(
                    pos=np.array([[t['x'], t['y'], t['z']], [surf_x, surf_y, surf_z]]),
                    color=line_color
                )

                # Vertical drop line to XY plane
                drop_color = (0, 0.6, 1, 0.3)
                self.target_drops[i].setData(
                    pos=np.array([[t['x'], t['y'], t['z']], [t['x'], t['y'], 0]]),
                    color=drop_color
                )

        # Hide unused lines
        for i in range(len(self.targets_data), 20):
            if i < len(self.target_lines):
                self.target_lines[i].setData(
                    pos=np.array([[0, 0, 0], [0, 0, 0]]),
                    color=(0, 0, 0, 0)
                )
            if i < len(self.target_drops):
                self.target_drops[i].setData(
                    pos=np.array([[0, 0, 0], [0, 0, 0]]),
                    color=(0, 0, 0, 0)
                )

    # Legacy compatibility methods
    def update_sweep(self, angle_deg):
        """Update sweep angle (legacy compatibility)"""
        self.sweep_angle = angle_deg
        self._update_sweep_visual()

    def update_target(self, angle_deg, distance, elevation_deg=0):
        """Update single target (legacy compatibility)"""
        if angle_deg is None or distance is None:
            self.clear_targets()
            return

        self.add_target(
            target_id=0,
            angle=angle_deg,
            distance=distance,
            elevation=elevation_deg,
            state=TargetState.UNKNOWN
        )


# =============================================================================
# LEGACY 3D RADAR (kept for compatibility)
# =============================================================================

