"""
RadarSuite v4.2.1-k0006 - Radar3DWidget

FIXED v4.2.1-k0006: Extracted from radar.py for improved modularity
Split radar.py (1674 lines) into focused, single-responsibility modules
"""

import numpy as np
import pyqtgraph.opengl as gl

from core import log, VERSION


class Radar3DWidget(gl.GLViewWidget):
    """
    Legacy 3D Sphere Radar - kept for compatibility
    Use Military3DRadar for new implementations
    """

    def __init__(self):
        super().__init__()
        log("Radar3DWidget.__init__ (legacy)", "INFO")

        self.setBackgroundColor('#050505')
        self.setCameraPosition(distance=150, elevation=20, azimuth=45)

        # Create sphere grid
        self.sphere_items = []
        for radius in [25, 50, 75, 100]:
            md = gl.MeshData.sphere(rows=20, cols=20, radius=radius)
            sphere = gl.GLMeshItem(
                meshdata=md,
                color=(0, 0.4, 0.8, 0.15),
                shader='balloon',
                drawEdges=True,
                edgeColor=(0, 0.4, 0.8, 0.3),
                smooth=False
            )
            self.addItem(sphere)
            self.sphere_items.append(sphere)

        # Coordinate axes
        axis_length = 110
        axis_width = 2

        x_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
            color=(1, 0, 0, 0.8), width=axis_width, antialias=True
        )
        self.addItem(x_axis)

        y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
            color=(0, 1, 0, 0.8), width=axis_width, antialias=True
        )
        self.addItem(y_axis)

        z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
            color=(0, 0, 1, 0.8), width=axis_width, antialias=True
        )
        self.addItem(z_axis)

        # Grid
        grid = gl.GLGridItem()
        grid.scale(10, 10, 1)
        grid.setColor((0.3, 0.3, 0.3, 0.5))
        self.addItem(grid)

        # Target scatter
        self.targets = []
        self.target_scatter = gl.GLScatterPlotItem(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0), size=12, pxMode=True
        )
        self.addItem(self.target_scatter)

        # Sweep line
        self.sweep_line_3d = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 100, 0]]),
            color=(0, 1, 0, 0.6), width=2, antialias=True
        )
        self.addItem(self.sweep_line_3d)
        self.sweep_angle = 0

    def update_sweep(self, angle_deg):
        """Update 3D sweep line angle"""
        self.sweep_angle = angle_deg
        angle_rad = math.radians(angle_deg - 90)
        x = 100 * math.cos(angle_rad)
        y = 100 * math.sin(angle_rad)
        self.sweep_line_3d.setData(
            pos=np.array([[0, 0, 0], [x, y, 0]]),
            color=(0, 1, 0, 0.6), width=2
        )

    def update_target(self, angle_deg, distance, elevation_deg=0):
        """Update target position in 3D space"""
        if angle_deg is None or distance is None:
            self.target_scatter.setData(
                pos=np.array([[0, 0, 0]]),
                color=(1, 0, 0, 0)
            )
            self.targets = []
            return

        distance = max(5, min(100, distance))
        elevation_deg = max(-90, min(90, elevation_deg))

        angle_rad = math.radians(angle_deg - 90)
        elevation_rad = math.radians(elevation_deg)

        horizontal_distance = distance * math.cos(elevation_rad)
        x = horizontal_distance * math.cos(angle_rad)
        y = horizontal_distance * math.sin(angle_rad)
        z = distance * math.sin(elevation_rad)

        self.targets = [(x, y, z)]

        if elevation_deg > 15:
            color = (1, 0.5, 0, 1)
        elif elevation_deg < -15:
            color = (0.5, 0, 1, 1)
        else:
            color = (1, 0, 0, 1)

        self.target_scatter.setData(
            pos=np.array([[x, y, z]]),
            color=color, size=12
        )

    def clear_targets(self):
        """Clear all targets"""
        self.targets = []
        self.target_scatter.setData(
            pos=np.array([[0, 0, 0]]),
            color=(1, 0, 0, 0)
        )
