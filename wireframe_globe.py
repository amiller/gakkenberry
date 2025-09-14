#!/usr/bin/env python3
"""
Wireframe calibration globe using shared azimuthal equidistant projection
Draws latitude/longitude grid lines for projector calibration with animation
"""
import pygame
import numpy as np
import sys
import os
import math

# Screen dimensions (from your setup)
H, W = 720, 1280

# Create scaled drawing functions that work at 1280x720 resolution
def draw_azimuth_ring_polar_1280(surface, azimuth_deg, color, rotation_offset=0, num_points=200):
    """Draw azimuth ring scaled for 1280x720 display"""
    from projection_utils import azimuthal_equidistant_projection

    points = []
    theta = np.radians(azimuth_deg)  # great-circle angle from pole

    for i in range(num_points + 1):
        phi = 2 * np.pi * i / num_points - np.pi + rotation_offset  # azimuth around pole

        # Convert to cartesian (pole toward viewer at z=1)
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        # Use the projection but scale for our screen size
        temp_x, temp_y = azimuthal_equidistant_projection(z, x, y)
        if temp_x is not None and temp_y is not None:
            # Scale from 640x480 to 1280x720
            scaled_x = int(temp_x * W / 640)
            scaled_y = int(temp_y * H / 480)
            if 0 <= scaled_x < W and 0 <= scaled_y < H:
                points.append((scaled_x, scaled_y))

    # Draw entire polyline
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, 1)

def draw_longitude_line_polar_1280(surface, lon_deg, color, rotation_offset=0, num_points=144):
    """Draw longitude line scaled for 1280x720 display"""
    from projection_utils import azimuthal_equidistant_projection

    points = []
    phi = np.radians(lon_deg) + rotation_offset

    for i in range(num_points + 1):
        lat_deg = 90 - 180 * i / num_points  # latitude from 90 to -90
        theta = np.radians(90 - lat_deg)     # polar angle

        # Convert to cartesian (pole toward viewer)
        x = np.sin(theta) * np.cos(phi)
        y = np.sin(theta) * np.sin(phi)
        z = np.cos(theta)

        # Use the projection but scale for our screen size
        temp_x, temp_y = azimuthal_equidistant_projection(z, x, y)
        if temp_x is not None and temp_y is not None:
            # Scale from 640x480 to 1280x720
            scaled_x = int(temp_x * W / 640)
            scaled_y = int(temp_y * H / 480)
            if 0 <= scaled_x < W and 0 <= scaled_y < H:
                points.append((scaled_x, scaled_y))

    # Draw entire polyline
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, 1)

def gnomonic_projection():
    """Generate gnomonic projection mapping from screen to sphere"""
    # FOV mapping: screen coordinates to gnomonic plane (doubled FOV for hemispherical display)
    # Start with 4:3 aspect ratio, then stretch to fill 16:9, with doubled field of view
    base_aspect = 4.0/3.0  # Original calibration video aspect ratio
    fov_scale = 2.0  # Double the field of view to match hemispherical calibration
    u = np.linspace(-base_aspect * SCALE_X * fov_scale, base_aspect * SCALE_X * fov_scale, W)
    v = np.linspace(-SCALE_Y * fov_scale, SCALE_Y * fov_scale, H)
    U, V = np.meshgrid(u, v)

    # Gnomonic projection: pixel maps to direction vector (X, Y, Z)
    norm = np.sqrt(1 + U**2 + V**2)
    X = 1 / norm
    Y = U / norm
    Z = V / norm

    # Mask points behind the projection plane (grazing angle filter)
    mask = X < 0
    X[mask] = np.nan
    Y[mask] = np.nan
    Z[mask] = np.nan

    # Convert to spherical coordinates
    theta = np.arccos(np.clip(Z, -1, 1))  # polar angle [0, π]
    phi = np.arctan2(Y, X)                # azimuth [-π, π]

    return theta, phi, mask

def sphere_to_screen(theta, phi, rotation_offset=0):
    """Convert spherical coordinates back to screen coordinates with rotation"""
    # Apply rotation around z-axis (vertical)
    phi_rotated = phi + rotation_offset

    # Convert spherical to cartesian with pole at center (rotate theta by pi/2)
    # This puts the north pole (theta=0) at the center of the view
    x = np.cos(theta)                        # forward direction (pole at center)
    y = np.sin(phi_rotated) * np.sin(theta)  # right direction
    z = np.cos(phi_rotated) * np.sin(theta)  # up direction

    # Skip points behind the hemisphere
    if x <= 0:
        return None, None

    # Gnomonic projection: project onto plane at x=1
    u = y / x  # horizontal on projection plane
    v = z / x  # vertical on projection plane

    # Map projection plane to screen coordinates (4:3 to 16:9 stretch, with doubled FOV)
    base_aspect = 4.0/3.0
    fov_scale = 2.0  # Must match the FOV scaling above
    screen_x = int((u / (base_aspect * SCALE_X * fov_scale) + 1.0) * W / 2.0)
    screen_y = int((1.0 - v / (SCALE_Y * fov_scale)) * H / 2.0)  # flip y for screen coordinates

    # Check bounds
    if 0 <= screen_x < W and 0 <= screen_y < H:
        return screen_x, screen_y
    return None, None

def draw_latitude_line(surface, lat_deg, color, rotation_offset=0, num_points=72):
    """Draw a line of constant latitude using bulk drawing"""
    points = []
    theta = np.radians(90 - lat_deg)  # convert latitude to polar angle

    for i in range(num_points + 1):
        phi = 2 * np.pi * i / num_points - np.pi  # azimuth from -π to π
        x, y = sphere_to_screen(theta, phi, rotation_offset)
        if x is not None and y is not None:
            points.append((x, y))

    # Draw entire polyline in ONE pygame call
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, 1)
# Debug removed

def draw_longitude_line(surface, lon_deg, color, rotation_offset=0, num_points=36):
    """Draw a line of constant longitude using bulk drawing"""
    points = []
    phi = np.radians(lon_deg)

    for i in range(num_points + 1):
        lat_deg = 90 - 180 * i / num_points  # latitude from 90 to -90
        theta = np.radians(90 - lat_deg)     # polar angle
        x, y = sphere_to_screen(theta, phi, rotation_offset)
        if x is not None and y is not None:
            points.append((x, y))

    # Draw entire polyline in ONE pygame call
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, 1)

def main():
    # Initialize pygame
    pygame.init()
# Debug removed

    # Set up display (fullscreen for direct framebuffer)
    if len(sys.argv) > 1 and sys.argv[1] == '--windowed':
        screen = pygame.display.set_mode((W, H))
    else:
        screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)

    pygame.display.set_caption("Wireframe Globe - Azimuthal Equidistant Projection")

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    GRAY = (128, 128, 128)

    clock = pygame.time.Clock()

    # Animation variables
    rotation_speed = 0.2  # radians per second (slower rotation)
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False

        # Calculate rotation based on elapsed time
        current_time = pygame.time.get_ticks()
        elapsed_seconds = (current_time - start_time) / 1000.0
        rotation_offset = elapsed_seconds * rotation_speed

        # Clear screen
        screen.fill(BLACK)

        # Draw azimuth rings (great-circle distances from pole) using shared projection
        calibration_azimuths = [15, 30, 45, 60, 75]  # Don't draw 90° (edge)
        for azimuth in calibration_azimuths:
            color = RED if azimuth == 45 else GRAY  # Highlight 45° ring
            draw_azimuth_ring_polar_1280(screen, azimuth, color, rotation_offset, num_points=200)

        # Draw longitude lines (meridians) - every 15 degrees
        for lon in range(-180, 180, 15):
            color = GREEN if lon == 0 else GRAY  # Prime meridian in green
            draw_longitude_line_polar_1280(screen, lon, color, rotation_offset, num_points=144)

        # Draw center crosshair
        center_x, center_y = W // 2, H // 2
        pygame.draw.line(screen, WHITE, (center_x - 20, center_y), (center_x + 20, center_y), 2)
        pygame.draw.line(screen, WHITE, (center_x, center_y - 20), (center_x, center_y + 20), 2)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
