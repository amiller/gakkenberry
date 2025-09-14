#!/usr/bin/env python3
"""
Generate both polar and standard view calibration grids using shared projection code
Eliminates code duplication and ensures consistency
"""
import pygame
import numpy as np
import math
from projection_utils import *

def generate_polar_view():
    """Generate polar view calibration grid (pole at center)"""
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    font = pygame.font.Font(None, 24)

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    GRAY = (128, 128, 128)

    # Clear screen
    screen.fill(BLACK)

    # Draw azimuth rings (great-circle distances from pole) to match polar reference
    calibration_azimuths = [15, 30, 45, 60, 75, 90]  # Great-circle angles from pole

    for azimuth in calibration_azimuths:
        color = RED if azimuth == 45 else GRAY  # Highlight 45° ring
        draw_azimuth_ring_polar(screen, azimuth, color, 0, num_points=200)

        # Label the rings
        center_x, center_y = W // 2, H // 2
        text = font.render(f"{azimuth}°", True, WHITE)
        text_rect = text.get_rect()

        # Position label based on the expected AE radius
        expected_radius = (azimuth / 90.0) * (min(W, H) / 2 * 0.9) * SCALE_X
        label_x = center_x + int(expected_radius) + 25
        text_rect.center = (label_x, center_y)
        screen.blit(text, text_rect)

    # Draw longitude lines - every 30 degrees
    for lon in range(-180, 180, 30):
        color = GREEN if lon == 0 else GRAY
        draw_longitude_line_polar(screen, lon, color, 0, num_points=144)

    # Draw center crosshair
    center_x, center_y = W // 2, H // 2
    pygame.draw.line(screen, WHITE, (center_x - 20, center_y), (center_x + 20, center_y), 2)
    pygame.draw.line(screen, WHITE, (center_x, center_y - 20), (center_x, center_y + 20), 2)

    # Save the image
    pygame.image.save(screen, "polar_view_wireframe.png")
    print("Saved polar_view_wireframe.png")

    pygame.quit()

def generate_standard_view():
    """Generate standard view calibration grid (pole at top)"""
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    font = pygame.font.Font(None, 24)

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    GRAY = (128, 128, 128)

    # Clear screen
    screen.fill(BLACK)

    # Draw latitude lines (horizontal curves) - every 20 degrees
    for lat in range(-80, 90, 20):
        color = RED if lat == 0 else GRAY  # Highlight equator in red
        draw_latitude_line_standard(screen, lat, color, 0, num_points=200)

    # Draw longitude lines (vertical curves) - every 30 degrees
    for lon in range(-180, 180, 30):
        color = GREEN if lon == 0 else GRAY  # Prime meridian in green
        draw_longitude_line_standard(screen, lon, color, 0, num_points=144)

    # Draw center crosshair
    center_x, center_y = W // 2, H // 2
    pygame.draw.line(screen, WHITE, (center_x - 20, center_y), (center_x + 20, center_y), 2)
    pygame.draw.line(screen, WHITE, (center_x, center_y - 20), (center_x, center_y + 20), 2)

    # Save the image
    pygame.image.save(screen, "standard_view_wireframe.png")
    print("Saved standard_view_wireframe.png")

    pygame.quit()

def main():
    print("Generating calibration grids with shared projection code...")
    generate_polar_view()
    generate_standard_view()
    print("Both grids generated successfully!")

if __name__ == "__main__":
    main()