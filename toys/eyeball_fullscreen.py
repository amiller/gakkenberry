#!/usr/bin/env python3
"""
Full-screen animated eyeball that uses the entire 1280x720 display
No longer constrained by hemispherical projection - fills the whole screen
"""
import pygame
import numpy as np
import sys
import math
import random
import time
import cProfile
import pstats
from io import StringIO

# Screen dimensions (from your setup)
H, W = 720, 1280

# Global coordinate cache
_coord_cache = {}

def get_fullscreen_coords_cached(decimation=4):
    """Get coordinate grids for full-screen rendering with decimation, using cache if available"""
    # Calculate actual rendering resolution
    H_render = H // decimation
    W_render = W // decimation
    cache_key = (H_render, W_render)

    if cache_key not in _coord_cache:
        # Create coordinate grids at rendering resolution
        y_coords, x_coords = np.mgrid[0:H_render, 0:W_render]

        # Convert to normalized coordinates [-1, 1] using float32 for reduced bandwidth
        norm_x = ((x_coords - W_render/2) / (W_render/2)).astype(np.float32)
        norm_y = ((y_coords - H_render/2) / (H_render/2)).astype(np.float32)

        # Pre-calculate common distance from center (for sclera gradient)
        center_distance = np.sqrt(norm_x**2 + norm_y**2, dtype=np.float32)

        # Precompute sclera gradient as uint8 image once (eliminates per-frame np.clip)
        sclera_rgb = np.array([248, 248, 255], dtype=np.float32)
        brightness = (1.0 - 0.1 * np.clip(center_distance, 0, 1)).astype(np.float32)
        sclera_img = (sclera_rgb * brightness[:, :, None]).astype(np.uint8)

        # Pre-compute eyelid masks for different blink states
        eyelid_masks = {}
        blink_steps = 20  # Number of pre-computed blink positions
        for i in range(blink_steps + 1):
            blink_state = i / blink_steps  # 0.0 to 1.0
            if blink_state > 0.0:
                blink_threshold = 0.6 * (1 - blink_state)
                eyelid_mask = (norm_y > blink_threshold) | (norm_y < -blink_threshold)
                eyelid_masks[blink_state] = eyelid_mask

        _coord_cache[cache_key] = {
            'norm_x': norm_x,
            'norm_y': norm_y,
            'center_distance': center_distance,
            'H_render': H_render,
            'W_render': W_render,
            'eyelid_masks': eyelid_masks,
            'sclera_img': sclera_img
        }

    return _coord_cache[cache_key]

class FullscreenEyeballRenderer:
    """Renders eyeball using full rectangular screen space"""

    def __init__(self, decimation=4):
        # Store decimation level
        self.decimation = decimation

        # Eyeball geometry parameters (relative to screen dimensions)
        self.iris_radius_x = 0.3  # Iris width (relative to screen width)
        self.iris_radius_y = 0.4  # Iris height (relative to screen height)
        self.pupil_radius_x = 0.08  # Pupil width
        self.pupil_radius_y = 0.11  # Pupil height
        self.min_pupil_scale = 0.6
        self.max_pupil_scale = 1.4
        self.pupil_scale = 1.0

        # Eye position (in normalized screen coordinates -1 to 1)
        self.eye_x = 0.0  # Left-right movement
        self.eye_y = 0.0  # Up-down movement
        self.target_x = 0.0
        self.target_y = 0.0
        self.max_eye_movement = 0.3  # Maximum eye movement
        self.movement_speed = 0.05

        # Animation state
        self.blink_state = 0.0  # 0 = open, 1 = closed
        self.blink_speed = 0.2  # Original blink speed
        self.next_blink_time = 0.5  # Start with a blink at 0.5 seconds

        # Colors
        self.sclera_color = (248, 248, 255)  # Off-white
        self.iris_base_color = (34, 139, 34)  # Forest green
        self.iris_dark_color = (0, 100, 0)   # Dark green
        self.pupil_color = (0, 0, 0)         # Black
        self.eyelid_color = (205, 133, 63)   # Peru/skin color

        # Movement timing - start with immediate movement
        self.last_movement_time = -1.0  # Negative time to trigger immediate movement
        self.movement_interval = 0.0  # Will trigger on first update

        # Persistent surface (no per-frame allocations)
        H_render = H // decimation
        W_render = W // decimation
        self.surface = pygame.Surface((W_render, H_render))

        # Get cached coordinates and precomputed sclera
        coords = get_fullscreen_coords_cached(decimation)
        self.sclera_img = coords['sclera_img']

    def update_eye_movement(self, current_time):
        """Update eye movement with realistic saccadic motion"""
        # Check if it's time for a new movement
        if current_time - self.last_movement_time > self.movement_interval:
            # Generate new random target
            self.target_x = random.uniform(-self.max_eye_movement, self.max_eye_movement)
            self.target_y = random.uniform(-self.max_eye_movement, self.max_eye_movement)
            self.last_movement_time = current_time
            self.movement_interval = random.uniform(2.0, 5.0)

        # Smooth interpolation to target
        x_diff = self.target_x - self.eye_x
        y_diff = self.target_y - self.eye_y

        self.eye_x += x_diff * self.movement_speed
        self.eye_y += y_diff * self.movement_speed

    def update_blinking(self, current_time):
        """Update blinking animation"""
        # Initialize next blink time if not set
        if self.next_blink_time == 0.0:
            self.next_blink_time = current_time + random.uniform(3.0, 6.0)

        # Check if it's time for a new blink
        if current_time >= self.next_blink_time and self.blink_state == 0.0:
            # Start blinking (close)
            self.blink_state = 0.01  # Start closing
            self.blink_closing = True

        # Handle blink animation
        if hasattr(self, 'blink_closing') and self.blink_closing:
            # Closing phase
            self.blink_state = min(1.0, self.blink_state + self.blink_speed)
            if self.blink_state >= 1.0:
                self.blink_closing = False  # Switch to opening
        elif self.blink_state > 0.0:
            # Opening phase
            self.blink_state = max(0.0, self.blink_state - self.blink_speed)
            if self.blink_state <= 0.0:
                # Blink complete, schedule next one
                self.next_blink_time = current_time + random.uniform(3.0, 6.0)

    def create_eyeball_surface(self, current_time):
        """Create a pygame surface with the full-screen eyeball"""
        # Update animations
        self.update_eye_movement(current_time)
        self.update_blinking(current_time)

        # Get cached coordinate grids with decimation
        coords = get_fullscreen_coords_cached(self.decimation)
        norm_x = coords['norm_x']
        norm_y = coords['norm_y']
        center_distance = coords['center_distance']
        H_render = coords['H_render']
        W_render = coords['W_render']

        # Start from precomputed sclera image (eliminates expensive np.clip operations)
        colors = np.copy(self.sclera_img)

        # Calculate iris center based on eye movement
        iris_center_x = self.eye_x
        iris_center_y = self.eye_y

        # ROI: Calculate bounding box around iris (avoid processing full screen)
        margin = max(self.iris_radius_x, self.iris_radius_y) * 1.2  # Add 20% margin
        x_min = max(0, int((iris_center_x + 1) * W_render / 2 - margin * W_render / 2))
        x_max = min(W_render, int((iris_center_x + 1) * W_render / 2 + margin * W_render / 2))
        y_min = max(0, int((iris_center_y + 1) * H_render / 2 - margin * H_render / 2))
        y_max = min(H_render, int((iris_center_y + 1) * H_render / 2 + margin * H_render / 2))

        # Work only on ROI slices
        roi_norm_x = norm_x[y_min:y_max, x_min:x_max]
        roi_norm_y = norm_y[y_min:y_max, x_min:x_max]

        # Create iris mask (elliptical) - only on ROI
        iris_dist_x = (roi_norm_x - iris_center_x) / self.iris_radius_x
        iris_dist_y = (roi_norm_y - iris_center_y) / self.iris_radius_y
        iris_distance_squared = iris_dist_x**2 + iris_dist_y**2
        iris_mask = iris_distance_squared <= 1.0

        if np.any(iris_mask):
            # Create iris texture - only calculate sqrt where needed
            iris_radius_norm = np.sqrt(iris_distance_squared[iris_mask])

            # Radial pattern
            radial_pattern = np.sin(iris_radius_norm * 8 * np.pi) * 0.3 + 0.7

            # Angular pattern relative to iris center
            iris_azimuth = np.arctan2(roi_norm_y[iris_mask] - iris_center_y,
                                    roi_norm_x[iris_mask] - iris_center_x)
            angular_pattern = np.sin(iris_azimuth * 12) * 0.2 + 0.8

            # Combine patterns
            combined_pattern = radial_pattern * angular_pattern

            # Apply iris colors to ROI region
            roi_colors = colors[y_min:y_max, x_min:x_max]
            for i in range(3):
                base_color = self.iris_base_color[i]
                dark_color = self.iris_dark_color[i]
                iris_color = base_color * combined_pattern + dark_color * (1 - combined_pattern)
                roi_colors[iris_mask, i] = np.clip(iris_color, 0, 255).astype(np.uint8)

        # Create pupil mask (smaller ellipse) - reuse ROI
        pupil_radius_x = self.pupil_radius_x * self.pupil_scale
        pupil_radius_y = self.pupil_radius_y * self.pupil_scale
        pupil_dist_x = (roi_norm_x - iris_center_x) / pupil_radius_x
        pupil_dist_y = (roi_norm_y - iris_center_y) / pupil_radius_y
        pupil_distance_squared = pupil_dist_x**2 + pupil_dist_y**2
        pupil_mask = pupil_distance_squared <= 1.0

        if np.any(pupil_mask):
            roi_colors[pupil_mask] = self.pupil_color

        # Apply blink effect (eyelids) - using precomputed masks
        if self.blink_state > 0.0:
            # Find closest precomputed blink state
            blink_steps = 20
            blink_index = round(self.blink_state * blink_steps) / blink_steps

            # Use precomputed eyelid mask
            eyelid_masks = coords['eyelid_masks']
            if blink_index in eyelid_masks:
                eyelid_mask = eyelid_masks[blink_index]
                colors[eyelid_mask] = self.eyelid_color

        # Write pixels into the persistent surface (no new Surface allocation)
        pygame.surfarray.blit_array(self.surface, colors.swapaxes(0, 1))

        # Scale up to full resolution if decimation > 1
        if self.decimation > 1:
            scaled_surface = pygame.transform.scale(self.surface, (W, H))
            return scaled_surface
        else:
            return self.surface

def main():
    # Parse command line arguments
    windowed_mode = '--windowed' in sys.argv
    profile_mode = '--profile' in sys.argv

    # Parse decimation level
    decimation = 3  # Default 3x decimation for good balance
    for arg in sys.argv[1:]:
        if arg.startswith('--decimation='):
            try:
                decimation = int(arg[13:])
                if decimation < 1:
                    print("Error: decimation must be >= 1")
                    sys.exit(1)
            except ValueError:
                print("Error: decimation must be an integer")
                print("Usage: --decimation=3 (default), --decimation=1 (full res), --decimation=8 (very fast)")
                sys.exit(1)

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

    print(f"Displaying full-screen {eye_color} eyeball (decimation={decimation})")

    # Initialize pygame
    pygame.init()

    # Set up display
    if windowed_mode:
        screen = pygame.display.set_mode((W, H))
    else:
        screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)

    pygame.display.set_caption(f"Full-screen Eyeball - {eye_color.title()}")

    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    clock = pygame.time.Clock()

    # Create eyeball renderer with decimation
    eyeball = FullscreenEyeballRenderer(decimation)

    # Set eye color
    if eye_color in eye_colors:
        eyeball.iris_base_color, eyeball.iris_dark_color = eye_colors[eye_color]

    # Animation variables
    start_time = pygame.time.get_ticks()

    # Performance monitoring
    frame_count = 0
    total_render_time = 0.0
    fps_update_interval = 30  # Update FPS every N frames
    last_fps_update = start_time

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
                    eyeball.blink_state = 0.0
                elif event.key == pygame.K_r:
                    # Reset eye position to center
                    eyeball.eye_x = 0.0
                    eyeball.eye_y = 0.0
                    eyeball.target_x = 0.0
                    eyeball.target_y = 0.0
                elif event.key == pygame.K_UP:
                    # Manual eye movement
                    eyeball.target_y = max(-eyeball.max_eye_movement,
                                         eyeball.target_y - 0.1)
                elif event.key == pygame.K_DOWN:
                    eyeball.target_y = min(eyeball.max_eye_movement,
                                         eyeball.target_y + 0.1)
                elif event.key == pygame.K_LEFT:
                    eyeball.target_x = max(-eyeball.max_eye_movement,
                                         eyeball.target_x - 0.1)
                elif event.key == pygame.K_RIGHT:
                    eyeball.target_x = min(eyeball.max_eye_movement,
                                         eyeball.target_x + 0.1)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    # Dilate pupil
                    eyeball.pupil_scale = min(eyeball.max_pupil_scale,
                                            eyeball.pupil_scale + 0.1)
                elif event.key == pygame.K_MINUS:
                    # Contract pupil
                    eyeball.pupil_scale = max(eyeball.min_pupil_scale,
                                            eyeball.pupil_scale - 0.1)

        # Calculate current time
        current_time = (pygame.time.get_ticks() - start_time) / 1000.0

        # Clear screen and draw eyeball
        screen.fill(BLACK)

        # Measure eyeball rendering performance
        render_start = time.perf_counter()
        eyeball_surface = eyeball.create_eyeball_surface(current_time)
        render_end = time.perf_counter()

        render_time_ms = (render_end - render_start) * 1000
        total_render_time += render_time_ms
        frame_count += 1

        screen.blit(eyeball_surface, (0, 0))

        # Calculate and display performance info
        current_fps = 0.0
        avg_render_time = 0.0
        if frame_count > 0:
            elapsed_time = (pygame.time.get_ticks() - last_fps_update) / 1000.0
            if elapsed_time > 0:
                current_fps = fps_update_interval / elapsed_time if frame_count % fps_update_interval == 0 else 0
            avg_render_time = total_render_time / frame_count

        # Reset counters periodically
        if frame_count % fps_update_interval == 0:
            last_fps_update = pygame.time.get_ticks()

        # Display info in corner
        font = pygame.font.Font(None, 24)
        render_res = f"{W//decimation}x{H//decimation}"
        info_lines = [
            f"Full-screen {eye_color.title()} Eye",
            f"Decimation: {decimation} ({render_res})",
            f"FPS: {current_fps:.1f}" if current_fps > 0 else "FPS: Calculating...",
            f"Render: {render_time_ms:.2f}ms",
            f"Avg Render: {avg_render_time:.2f}ms",
            f"Position: ({eyeball.eye_x:.2f}, {eyeball.eye_y:.2f})",
            f"Pupil: {eyeball.pupil_scale:.2f}",
            f"Blink: {eyeball.blink_state:.2f}",
        ]

        y_offset = 10
        for line in info_lines:
            text = font.render(line, True, WHITE)
            screen.blit(text, (10, y_offset))
            y_offset += 25

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

    # Print final performance stats
    if frame_count > 0:
        final_avg_render = total_render_time / frame_count
        print(f"\n=== Performance Summary ===")
        print(f"Total frames: {frame_count}")
        print(f"Average render time: {final_avg_render:.2f}ms")
        print(f"Theoretical max FPS: {1000/final_avg_render:.1f}")

if __name__ == "__main__":
    if '--profile' in sys.argv:
        # Run with profiling
        profiler = cProfile.Profile()
        profiler.enable()
        main()
        profiler.disable()

        # Print profiling results
        s = StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        print(s.getvalue())
    else:
        main()