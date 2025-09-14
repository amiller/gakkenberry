#!/usr/bin/env python3
"""
Wireframe calibration globe using gnomonic projection
Draws latitude/longitude grid lines for projector calibration
"""
import pygame
import numpy as np
import sys
import os

# Screen dimensions (from your setup)
H, W = 720, 1280
# Calibration scaling factors (stronger margins + mpv fine-tuning)
CALIB_SCALE_X = 0.90  # Stronger horizontal compression for calibration match
CALIB_SCALE_Y = 0.88  # Stronger vertical compression for calibration match
MPV_SCALE_X = 0.984  # Fine-tuning from mpv testing (10px margin each side)
MPV_SCALE_Y = 0.972  # Fine-tuning from mpv testing (10px margin each side)
SCALE_X = CALIB_SCALE_X * MPV_SCALE_X  # Combined scaling
SCALE_Y = CALIB_SCALE_Y * MPV_SCALE_Y  # Combined scaling
EFFECTIVE_W = int(W * SCALE_X)
EFFECTIVE_H = int(H * SCALE_Y)

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

    pygame.display.set_caption("Wireframe Globe - Gnomonic Projection")

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

        # Draw latitude lines with equal radial spacing (like calibration reference)
        max_radius_x = (W // 2 - 40) * SCALE_X  # Apply horizontal scale factor
        max_radius_y = (H // 2 - 40) * SCALE_Y  # Apply vertical scale factor
        max_radius = min(max_radius_x, max_radius_y)  # Use smaller to maintain aspect ratio

        import math
        num_rings = 6
        for i in range(1, num_rings + 1):
            radius = (max_radius * i) // num_rings

            # Convert radius back to latitude for this projection with scale compensation
            radius_normalized = radius / (max_radius / 2.0)  # Normalize to projection scale
            if radius_normalized > 0:
                colatitude = math.atan(radius_normalized)
                lat_deg = 90 - math.degrees(colatitude)

                # Draw the latitude line
                color = RED if i == 3 else GRAY  # Highlight middle ring
                draw_latitude_line(screen, lat_deg, color, rotation_offset, num_points=200)

        # Remove debug prints since they work
        # print(f"DEBUG: Drew {len(visible_lats)} latitude lines: {visible_lats}")

        # Draw longitude lines (meridians) - every 15 degrees
        for lon in range(-180, 180, 15):
            color = GREEN if lon == 0 else GRAY  # Prime meridian in green
            draw_longitude_line(screen, lon, color, rotation_offset)

        # Draw center crosshair
        center_x, center_y = W // 2, H // 2
        pygame.draw.line(screen, WHITE, (center_x - 20, center_y), (center_x + 20, center_y), 2)
        pygame.draw.line(screen, WHITE, (center_x, center_y - 20), (center_x, center_y + 20), 2)

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()
