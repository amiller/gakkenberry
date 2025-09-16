#!/usr/bin/env python3
"""
Animated 3D eyeball for hemispherical display
Creates a realistic looking eyeball with movement, blinking, and iris patterns
Uses azimuthal equidistant projection for proper spherical mapping
"""
import pygame
import sys
import math
from eyeball_core import EyeballRenderer

# Screen dimensions (from your setup)
H, W = 720, 1280

def main():
    # Parse command line arguments
    windowed_mode = '--windowed' in sys.argv

    # Eye color options
    eye_colors = {
        'green': ((34, 139, 34), (0, 100, 0)),      # Forest green (default)
        'blue': ((70, 130, 180), (25, 25, 112)),     # Steel blue
        'brown': ((139, 69, 19), (101, 67, 33)),     # Saddle brown
        'hazel': ((154, 205, 50), (107, 142, 35)),   # Yellow green
        'gray': ((105, 105, 105), (64, 64, 64)),     # Gray
    }

    eye_color = 'green'  # Default
    for arg in sys.argv[1:]:
        if arg.startswith('color='):
            color_name = arg[6:]
            if color_name in eye_colors:
                eye_color = color_name
            else:
                print(f"Unknown eye color: {color_name}")
                print(f"Available colors: {list(eye_colors.keys())}")
                sys.exit(1)
        elif arg == '--windowed':
            pass  # Already handled
        elif arg.startswith('--'):
            print(f"Unknown option: {arg}")
            print("Usage: python eyeball.py [color=green|blue|brown|hazel|gray] [--windowed]")
            sys.exit(1)

    print(f"Displaying {eye_color} eyeball animation")

    # Initialize pygame
    pygame.init()

    # Set up display (fullscreen for direct framebuffer)
    if windowed_mode:
        screen = pygame.display.set_mode((W, H))
    else:
        screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)

    pygame.display.set_caption(f"Animated Eyeball - {eye_color.title()}")

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)

    clock = pygame.time.Clock()

    # Create eyeball renderer
    eyeball = EyeballRenderer()

    # Set eye color
    if eye_color in eye_colors:
        eyeball.iris_base_color, eyeball.iris_dark_color = eye_colors[eye_color]

    # Animation variables
    start_time = pygame.time.get_ticks()

    # Performance monitoring
    frame_count = 0
    fps_start_time = start_time

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Trigger immediate blink
                    current_time_sec = pygame.time.get_ticks() / 1000.0
                    eyeball.next_blink_time = current_time_sec
                    eyeball.blink_state = 0.0  # Reset to open state first
                elif event.key == pygame.K_r:
                    # Reset eye position to center
                    eyeball.eye_theta = 0.0
                    eyeball.eye_phi = 0.0
                    eyeball.target_theta = 0.0
                    eyeball.target_phi = 0.0
                elif event.key == pygame.K_UP:
                    # Manual eye movement
                    eyeball.target_theta = max(-eyeball.max_eye_angle,
                                             eyeball.target_theta - 0.1)
                elif event.key == pygame.K_DOWN:
                    eyeball.target_theta = min(eyeball.max_eye_angle,
                                             eyeball.target_theta + 0.1)
                elif event.key == pygame.K_LEFT:
                    eyeball.target_phi = max(-eyeball.max_eye_angle,
                                           eyeball.target_phi - 0.1)
                elif event.key == pygame.K_RIGHT:
                    eyeball.target_phi = min(eyeball.max_eye_angle,
                                           eyeball.target_phi + 0.1)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Dilate pupil
                    eyeball.pupil_radius = min(eyeball.max_pupil_radius,
                                             eyeball.pupil_radius + 0.01)
                elif event.key == pygame.K_MINUS:
                    # Contract pupil
                    eyeball.pupil_radius = max(eyeball.min_pupil_radius,
                                             eyeball.pupil_radius - 0.01)

        # Calculate current time
        current_time = (pygame.time.get_ticks() - start_time) / 1000.0

        # Clear screen
        screen.fill(BLACK)

        # Create and draw eyeball surface
        eyeball_surface = eyeball.create_eyeball_surface(current_time)
        screen.blit(eyeball_surface, (0, 0))

        # Draw center crosshair for reference
        center_x, center_y = W // 2, H // 2
        pygame.draw.line(screen, WHITE, (center_x - 10, center_y), (center_x + 10, center_y), 1)
        pygame.draw.line(screen, WHITE, (center_x, center_y - 10), (center_x, center_y + 10), 1)

        # Display info
        font = pygame.font.Font(None, 24)

        # Eye color and controls
        info_lines = [
            f"Eye: {eye_color.title()}",
            f"Pupil: {eyeball.pupil_radius:.2f}",
            f"Blink: {eyeball.blink_state:.2f}",
            "",
            "Controls:",
            "SPACE - Blink",
            "R - Reset position",
            "Arrows - Move eye",
            "+/- - Pupil size",
            "ESC/Q - Quit"
        ]

        y_offset = 10
        for line in info_lines:
            if line:  # Skip empty lines
                text = font.render(line, True, WHITE)
                screen.blit(text, (10, y_offset))
            y_offset += 20

        # FPS counter
        frame_count += 1
        if frame_count % 30 == 0:  # Update every 30 frames
            elapsed = (pygame.time.get_ticks() - fps_start_time) / 1000.0
            fps = frame_count / elapsed
            if elapsed > 1.0:  # Reset counter periodically
                frame_count = 0
                fps_start_time = pygame.time.get_ticks()

            fps_text = font.render(f"FPS: {fps:.1f}", True, WHITE)
            screen.blit(fps_text, (W - 80, 10))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == "__main__":
    main()