#!/usr/bin/env python3
"""
Eyeball rendering and animation core for hemispherical display
Uses azimuthal equidistant projection for realistic 3D eyeball appearance
"""
import pygame
import numpy as np
import math
import random
import sys
import os
# Add parent directory to path to import projection_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from projection_utils import azimuthal_equidistant_projection

# Screen dimensions (from your setup)
H, W = 720, 1280

# Global cache for coordinate grids (reusing spherical harmonics approach)
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
            'valid_mask': valid_mask,
            'radius': radius,
            'norm_x': norm_x,
            'norm_y': norm_y
        }

    return _coord_cache[cache_key]

class EyeballRenderer:
    """Renders and animates a 3D eyeball on hemispherical display"""

    def __init__(self):
        # Eyeball geometry parameters
        self.iris_radius = 0.45  # Iris size (relative to hemisphere) - increased by 50%
        self.pupil_radius = 0.12  # Pupil size (relative to hemisphere)
        self.min_pupil_radius = 0.08
        self.max_pupil_radius = 0.16

        # Eye position and rotation
        self.eye_theta = 0.0  # Polar angle (0 = looking forward)
        self.eye_phi = 0.0    # Azimuthal angle (0 = straight ahead)
        self.max_eye_angle = math.pi / 6  # Maximum eye movement (30 degrees)

        # Animation state
        self.target_theta = 0.0
        self.target_phi = 0.0
        self.movement_speed = 0.05
        self.blink_state = 0.0  # 0 = open, 1 = closed
        self.blink_speed = 0.2
        self.next_blink_time = 0.0

        # Colors
        self.sclera_color = (248, 248, 255)  # Off-white
        self.iris_base_color = (34, 139, 34)  # Forest green
        self.iris_dark_color = (0, 100, 0)   # Dark green
        self.pupil_color = (0, 0, 0)         # Black
        self.eyelid_color = (205, 133, 63)   # Peru/skin color

        # Movement timing
        self.last_movement_time = 0.0
        self.movement_interval = random.uniform(2.0, 5.0)  # Seconds between movements

    def update_eye_movement(self, current_time):
        """Update eye movement with realistic saccadic motion"""
        # Check if it's time for a new movement
        if current_time - self.last_movement_time > self.movement_interval:
            # Generate new random target
            self.target_theta = random.uniform(-self.max_eye_angle, self.max_eye_angle)
            self.target_phi = random.uniform(-self.max_eye_angle, self.max_eye_angle)
            self.last_movement_time = current_time
            self.movement_interval = random.uniform(2.0, 5.0)

        # Smooth interpolation to target
        theta_diff = self.target_theta - self.eye_theta
        phi_diff = self.target_phi - self.eye_phi

        self.eye_theta += theta_diff * self.movement_speed
        self.eye_phi += phi_diff * self.movement_speed

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

    def sphere_to_screen_with_eye_rotation(self, theta, phi):
        """Convert spherical coordinates to screen with eye rotation applied"""
        # Apply eye rotation (simple rotation around center)
        adjusted_theta = theta + self.eye_theta
        adjusted_phi = phi + self.eye_phi

        # Convert to cartesian
        x = np.sin(adjusted_theta) * np.cos(adjusted_phi)
        y = np.sin(adjusted_theta) * np.sin(adjusted_phi)
        z = np.cos(adjusted_theta)

        # Use existing projection
        return azimuthal_equidistant_projection(-y, x, z)  # Rotate for front view

    def render_sclera(self, coords):
        """Render the white part of the eye"""
        colors = np.zeros(coords['great_circle_angle'].shape + (3,), dtype=np.uint8)

        # Fill valid hemisphere area with sclera color
        valid_mask = coords['valid_mask']
        colors[valid_mask] = self.sclera_color

        # Add subtle radial gradient for realism
        radius_norm = coords['radius'] / 0.9  # Normalize to max radius
        brightness_factor = 1.0 - 0.1 * radius_norm**2  # Slight darkening at edges

        for i in range(3):  # RGB channels
            colors[valid_mask, i] = np.clip(
                colors[valid_mask, i] * brightness_factor[valid_mask], 0, 255
            ).astype(np.uint8)

        return colors

    def render_iris(self, coords, colors):
        """Render the colored iris part"""
        great_circle_angle = coords['great_circle_angle']
        azimuth = coords['azimuth']
        valid_mask = coords['valid_mask']
        norm_x = coords['norm_x']
        norm_y = coords['norm_y']

        # Calculate iris center offset based on eye movement
        iris_center_x = self.eye_phi * 0.8  # Scale eye movement to iris movement
        iris_center_y = self.eye_theta * 0.8

        # Calculate distance from iris center for each pixel
        iris_distance = np.sqrt((norm_x - iris_center_x)**2 + (norm_y - iris_center_y)**2)

        # Create iris mask (circular region around shifted center)
        iris_mask = valid_mask & (iris_distance <= self.iris_radius)

        if not np.any(iris_mask):
            return colors

        # Radial pattern for iris texture (relative to iris center)
        iris_radius_norm = iris_distance[iris_mask] / self.iris_radius

        # Create radial pattern
        radial_pattern = np.sin(iris_radius_norm * 8 * np.pi) * 0.3 + 0.7

        # Create angular pattern (iris striations) relative to iris center
        iris_azimuth = np.arctan2(norm_y[iris_mask] - iris_center_y, norm_x[iris_mask] - iris_center_x)
        angular_pattern = np.sin(iris_azimuth * 12) * 0.2 + 0.8

        # Combine patterns
        combined_pattern = radial_pattern * angular_pattern

        # Apply iris colors
        for i in range(3):
            base_color = self.iris_base_color[i]
            dark_color = self.iris_dark_color[i]
            iris_color = base_color * combined_pattern + dark_color * (1 - combined_pattern)
            colors[iris_mask, i] = np.clip(iris_color, 0, 255).astype(np.uint8)

        return colors

    def render_pupil(self, coords, colors):
        """Render the black pupil"""
        valid_mask = coords['valid_mask']
        norm_x = coords['norm_x']
        norm_y = coords['norm_y']

        # Calculate pupil center offset (same as iris)
        pupil_center_x = self.eye_phi * 0.8
        pupil_center_y = self.eye_theta * 0.8

        # Calculate distance from pupil center for each pixel
        pupil_distance = np.sqrt((norm_x - pupil_center_x)**2 + (norm_y - pupil_center_y)**2)

        # Create pupil mask
        pupil_mask = valid_mask & (pupil_distance <= self.pupil_radius)

        if np.any(pupil_mask):
            colors[pupil_mask] = self.pupil_color

        return colors

    def apply_blink_effect(self, coords, colors):
        """Apply eyelid closing effect"""
        if self.blink_state <= 0.0:
            return colors

        norm_y = coords['norm_y']
        valid_mask = coords['valid_mask']

        # Create eyelid mask (top and bottom)
        blink_threshold = 0.3 * (1 - self.blink_state)  # Closes from top and bottom

        eyelid_mask = valid_mask & (
            (norm_y > blink_threshold) | (norm_y < -blink_threshold)
        )

        if np.any(eyelid_mask):
            colors[eyelid_mask] = self.eyelid_color

        return colors

    def create_eyeball_surface(self, current_time):
        """Create a pygame surface with the complete eyeball"""
        # Use lower resolution for performance (same as spherical harmonics)
        H_low, W_low = H // 4, W // 4

        # Update animations
        self.update_eye_movement(current_time)
        self.update_blinking(current_time)

        # Get cached coordinate grids
        coords = get_coordinate_grids_cached(H_low, W_low)

        # Start with sclera
        colors = self.render_sclera(coords)

        # Add iris
        colors = self.render_iris(coords, colors)

        # Add pupil
        colors = self.render_pupil(coords, colors)

        # Apply blink effect
        colors = self.apply_blink_effect(coords, colors)

        # Set invalid regions to black
        colors[~coords['valid_mask']] = [0, 0, 0]

        # Create low-resolution pygame surface
        low_surface = pygame.Surface((W_low, H_low))
        pygame.surfarray.blit_array(low_surface, colors.swapaxes(0, 1))

        # Scale up to full resolution
        surface = pygame.transform.scale(low_surface, (W, H))

        return surface