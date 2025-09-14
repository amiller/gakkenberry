#!/usr/bin/env python3
"""
Spherical harmonics visualization using azimuthal equidistant projection
Draws animated spherical harmonics on the hemispherical display
"""
import pygame
import numpy as np
import sys
import os
import math
from scipy.special import sph_harm

# Screen dimensions (from your setup)
H, W = 720, 1280

# Global cache for coordinate grids
_coord_cache = {}

def get_coordinate_grids_cached(H_res, W_res):
    """Get coordinate grids, using cache if available"""
    cache_key = (H_res, W_res)

    if cache_key not in _coord_cache:
        # Create coordinate grid
        y_coords, x_coords = np.mgrid[0:H_res, 0:W_res]

        # Convert screen coordinates to normalized coordinates [-1, 1]
        # Scale from low-res to 640x480 coordinate system (reverse of wireframe scaling)
        norm_x = (x_coords * 640 / W_res - 320) / 320
        norm_y = (y_coords * 480 / H_res - 240) / 240

        # Convert to spherical coordinates using inverse azimuthal equidistant projection
        # Calculate radius from center
        radius = np.sqrt(norm_x**2 + norm_y**2)

        # In azimuthal equidistant, radius is proportional to great-circle angle
        # Max radius corresponds to π/2 (hemisphere edge)
        max_radius = 0.9  # Match the projection_utils.py margin
        great_circle_angle = radius * (np.pi / 2) / max_radius

        # Calculate azimuth angle
        azimuth = np.arctan2(norm_y, norm_x)

        # Mask for valid hemisphere points
        valid_mask = (radius <= max_radius) & (great_circle_angle <= np.pi/2)

        _coord_cache[cache_key] = {
            'great_circle_angle': great_circle_angle,
            'azimuth': azimuth,
            'valid_mask': valid_mask
        }

    return _coord_cache[cache_key]

def spherical_harmonics(l, m, theta, phi):
    """Calculate spherical harmonics Y_l^m(theta, phi)

    Args:
        l: degree (non-negative integer)
        m: order (-l <= m <= l)
        theta: polar angle (0 to π)
        phi: azimuthal angle (0 to 2π)

    Returns:
        Complex spherical harmonic values
    """
    # scipy.special.sph_harm uses (m, l, phi, theta) order
    return sph_harm(m, l, phi, theta)


def values_to_colors(values, min_val=-1, max_val=1):
    """Convert spherical harmonic values to RGB colors using numpy

    Args:
        values: numpy array of real values (should be normalized to [-1, 1])
        min_val: Minimum value (-1)
        max_val: Maximum value (+1)

    Returns:
        RGB array with shape (..., 3) where each component is 0-255
    """
    # Normalize to [0, 1]
    normalized = (values - min_val) / (max_val - min_val)
    normalized = np.clip(normalized, 0, 1)

    # Initialize RGB arrays
    colors = np.zeros(normalized.shape + (3,), dtype=np.uint8)

    # Blue to white to red colormap
    # For normalized < 0.5: Blue to white
    mask1 = normalized < 0.5
    t1 = normalized[mask1] * 2  # 0 to 1
    colors[mask1, 0] = (t1 * 255).astype(np.uint8)  # r
    colors[mask1, 1] = (t1 * 255).astype(np.uint8)  # g
    colors[mask1, 2] = 255  # b

    # For normalized >= 0.5: White to red
    mask2 = normalized >= 0.5
    t2 = (normalized[mask2] - 0.5) * 2  # 0 to 1
    colors[mask2, 0] = 255  # r
    colors[mask2, 1] = ((1 - t2) * 255).astype(np.uint8)  # g
    colors[mask2, 2] = ((1 - t2) * 255).astype(np.uint8)  # b

    return colors

def create_spherical_harmonics_surface(l, m, rotation_offset=0):
    """Create a pygame surface with spherical harmonics visualization"""
    # Use lower resolution for faster computation (1/4 resolution = 16x fewer pixels)
    H_low, W_low = H // 4, W // 4  # 180x320 instead of 720x1280

    # Get cached coordinate grids
    coords = get_coordinate_grids_cached(H_low, W_low)

    # Apply rotation to phi coordinate
    theta = coords['great_circle_angle']  # polar angle from forward direction
    phi = coords['azimuth'] + rotation_offset  # azimuthal angle with rotation
    valid_mask = coords['valid_mask']

    # Calculate spherical harmonics values only for valid points
    Y_lm = np.zeros_like(theta, dtype=complex)
    Y_lm[valid_mask] = spherical_harmonics(l, m, theta[valid_mask], phi[valid_mask])

    # Take real part
    Y_real = np.real(Y_lm)

    # Convert to colors
    colors = values_to_colors(Y_real)

    # Set invalid regions to black
    colors[~valid_mask] = [0, 0, 0]

    # Create low-resolution pygame surface from color array
    low_surface = pygame.Surface((W_low, H_low))
    pygame.surfarray.blit_array(low_surface, colors.swapaxes(0, 1))  # pygame expects (width, height, 3)

    # Scale up to full resolution using pygame's transform.scale
    surface = pygame.transform.scale(low_surface, (W, H))

    return surface

def main():
    # Parse command line arguments
    l = 2  # default degree
    m = 1  # default order

    if len(sys.argv) >= 2:
        try:
            # Parse l=2 m=1 format
            for arg in sys.argv[1:]:
                if arg.startswith('l='):
                    l = int(arg[2:])
                elif arg.startswith('m='):
                    m = int(arg[2:])
                elif arg == '--windowed':
                    pass  # Handle later
        except ValueError:
            print("Usage: python spherical_harmonics.py [l=degree] [m=order] [--windowed]")
            print("Example: python spherical_harmonics.py l=2 m=1")
            sys.exit(1)

    # Validate parameters
    if l < 0:
        print("Error: l must be non-negative")
        sys.exit(1)
    if abs(m) > l:
        print(f"Error: |m| must be <= l. Got m={m}, l={l}")
        sys.exit(1)

    print(f"Displaying spherical harmonics Y_{l}^{m}")

    # Initialize pygame
    pygame.init()

    # Set up display (fullscreen for direct framebuffer)
    if '--windowed' in sys.argv:
        screen = pygame.display.set_mode((W, H))
    else:
        screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)

    pygame.display.set_caption(f"Spherical Harmonics Y_{l}^{m}")

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    clock = pygame.time.Clock()

    # Animation variables
    rotation_speed = 0.3  # radians per second
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

        # Create and draw spherical harmonics surface
        harmonics_surface = create_spherical_harmonics_surface(l, m, rotation_offset)
        screen.blit(harmonics_surface, (0, 0))

        # Draw center crosshair
        center_x, center_y = W // 2, H // 2
        pygame.draw.line(screen, WHITE, (center_x - 20, center_y), (center_x + 20, center_y), 2)
        pygame.draw.line(screen, WHITE, (center_x, center_y - 20), (center_x, center_y + 20), 2)

        # Display current parameters
        font = pygame.font.Font(None, 36)
        text = font.render(f"Y_{l}^{m}", True, WHITE)
        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()