#!/usr/bin/env python3
"""
Shared projection utilities for wireframe globe calibration
Eliminates code duplication between different view orientations
"""
import numpy as np
import math

# Calibration constants
H, W = 480, 640
SCALE_X = 0.80  # Even more expansion (was 0.85)
SCALE_Y = 0.78  # Even more expansion (was 0.83)

def azimuthal_equidistant_projection(x, y, z):
    """Clean Azimuthal Equidistant projection from 3D cartesian coordinates to screen"""
    # Skip points behind the hemisphere (x <= 0 for forward-facing view)
    if x <= 0:
        return None, None

    # AZIMUTHAL EQUIDISTANT projection
    # Calculate great-circle distance from center (where we're looking)
    # Center is at (1, 0, 0) in cartesian coordinates
    great_circle_angle = math.acos(max(-1, min(1, x)))  # angle from forward direction

    # In AE projection, radial distance is linear in great-circle angle
    # For hemisphere display, map 0 to π/2 radians (0° to 90°) onto screen radius
    max_angle = math.pi / 2  # 90 degrees for hemisphere
    if great_circle_angle > max_angle:
        return None, None

    # Radial distance is proportional to angle
    radius = great_circle_angle / max_angle  # normalize to [0, 1]

    # Calculate azimuth angle in the projection plane
    azimuth = math.atan2(z, y)  # angle around the center

    # Convert to screen coordinates
    max_screen_radius = min(W, H) / 2 * 0.9  # Leave some margin
    screen_radius = radius * max_screen_radius

    # Apply scaling factors (inverted to expand rather than contract)
    screen_x = int(W/2 + screen_radius * math.cos(azimuth) / SCALE_X)
    screen_y = int(H/2 - screen_radius * math.sin(azimuth) / SCALE_Y)  # flip y

    # Check bounds
    if 0 <= screen_x < W and 0 <= screen_y < H:
        return screen_x, screen_y
    return None, None

def draw_azimuth_ring_polar(surface, azimuth_deg, color, rotation_offset=0, num_points=200):
    """Draw a ring at constant great-circle distance from pole (azimuth ring)"""
    points = []
    theta = np.radians(azimuth_deg)  # great-circle angle from pole

    for i in range(num_points + 1):
        phi = 2 * np.pi * i / num_points - np.pi + rotation_offset  # azimuth around pole

        # Convert to cartesian (pole toward viewer at z=1)
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        screen_x, screen_y = azimuthal_equidistant_projection(z, x, y)  # pole toward viewer (z forward)
        if screen_x is not None and screen_y is not None:
            points.append((screen_x, screen_y))

    # Draw entire polyline in ONE pygame call
    if len(points) > 1:
        import pygame
        pygame.draw.lines(surface, color, False, points, 1)

def draw_longitude_line_polar(surface, lon_deg, color, rotation_offset=0, num_points=144):
    """Draw a line of constant longitude for polar view (pole at center)"""
    points = []
    phi = np.radians(lon_deg) + rotation_offset

    for i in range(num_points + 1):
        lat_deg = 90 - 180 * i / num_points  # latitude from 90 to -90
        theta = np.radians(90 - lat_deg)     # polar angle

        # Convert to cartesian (no rotation - pole toward viewer)
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        screen_x, screen_y = azimuthal_equidistant_projection(z, x, y)  # pole toward viewer (z forward)
        if screen_x is not None and screen_y is not None:
            points.append((screen_x, screen_y))

    # Draw entire polyline in ONE pygame call
    if len(points) > 1:
        import pygame
        pygame.draw.lines(surface, color, False, points, 1)

def draw_latitude_line_standard(surface, lat_deg, color, rotation_offset=0, num_points=200):
    """Draw a line of constant latitude for standard view (pole at top)"""
    points = []
    theta = np.radians(90 - lat_deg)  # convert latitude to polar angle

    for i in range(num_points + 1):
        phi = 2 * np.pi * i / num_points - np.pi + rotation_offset  # azimuth from -π to π

        # Convert to cartesian then rotate for standard view
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        # Rotate for standard view: pole (z) goes to top (y), equator plane becomes forward-facing
        rotated_x = -y  # toward viewer
        rotated_y = x   # right
        rotated_z = z   # up (pole at top)

        screen_x, screen_y = azimuthal_equidistant_projection(rotated_x, rotated_y, rotated_z)
        if screen_x is not None and screen_y is not None:
            points.append((screen_x, screen_y))

    # Draw entire polyline in ONE pygame call
    if len(points) > 1:
        import pygame
        pygame.draw.lines(surface, color, False, points, 1)

def draw_longitude_line_standard(surface, lon_deg, color, rotation_offset=0, num_points=144):
    """Draw a line of constant longitude for standard view (pole at top)"""
    points = []
    phi = np.radians(lon_deg) + rotation_offset

    for i in range(num_points + 1):
        lat_deg = 90 - 180 * i / num_points  # latitude from 90 to -90
        theta = np.radians(90 - lat_deg)     # polar angle

        # Convert to cartesian then rotate for standard view
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        # Rotate for standard view: pole (z) goes to top (y), equator plane becomes forward-facing
        rotated_x = -y  # toward viewer
        rotated_y = x   # right
        rotated_z = z   # up (pole at top)

        screen_x, screen_y = azimuthal_equidistant_projection(rotated_x, rotated_y, rotated_z)
        if screen_x is not None and screen_y is not None:
            points.append((screen_x, screen_y))

    # Draw entire polyline in ONE pygame call
    if len(points) > 1:
        import pygame
        pygame.draw.lines(surface, color, False, points, 1)
