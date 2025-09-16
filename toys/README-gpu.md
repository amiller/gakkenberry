# GPU Eyeball - OpenGL Fragment Shader Implementation

A high-performance GPU-accelerated eyeball animation using OpenGL ES 2.0 compatible fragment shaders. This implementation moves all heavy pixel computations to the GPU, dramatically improving performance compared to CPU-based approaches.

## Features

- **GPU-accelerated rendering**: All iris patterns, pupil scaling, and eyelid rendering computed in fragment shader
- **Realistic eye motion**: Automatic saccades every 2-5 seconds with smooth interpolation
- **Natural blinking**: Automatic blinking every 3-6 seconds with configurable speed
- **Multiple eye colors**: Built-in presets for green, blue, brown, hazel, and gray eyes
- **Interactive controls**: Keyboard controls for manual blinking and pupil dilation
- **Pi-compatible**: Uses OpenGL ES 2.0 shaders that work on Raspberry Pi VideoCore GPU

## Usage

### Basic Usage
```bash
# Activate virtual environment
source ~/sandboxes/py3.11/bin/activate

# Run in windowed mode (recommended for testing)
python gpu_eyeball.py --windowed

# Run fullscreen
python gpu_eyeball.py

# Specify eye color
python gpu_eyeball.py --windowed color=blue
```

### Eye Color Options
- `color=green` (default) - Forest green iris
- `color=blue` - Steel blue iris
- `color=brown` - Chocolate brown iris
- `color=hazel` - Yellow-green hazel iris
- `color=gray` - Gray iris

### Interactive Controls
- **Space**: Trigger immediate blink
- **+/=**: Increase pupil size (dilation)
- **-**: Decrease pupil size (constriction)
- **R**: Reset eye position to center
- **Q/Escape**: Quit

## Technical Details

### Performance
- Uses a single full-screen triangle to avoid quad precision seams
- Fragment shader computes all pixel effects (iris patterns, gradients, eyelids)
- CPU only handles eye movement and blink timing
- Targets 60 FPS at 1280x720 resolution

### Shader Features
- **Iris patterns**: Radial and angular texture functions using `sin(8πr)` and `sin(12θ)`
- **Elliptical geometry**: Proper aspect-corrected iris and pupil shapes
- **Smooth eyelids**: Fast threshold-based eyelid rendering
- **Sclera gradient**: Radial brightness falloff from screen center

### Raspberry Pi Compatibility
- Uses OpenGL ES 2.0 (`#version 100`) shaders
- Compatible with Pi 4/5 KMS GL driver
- Avoids precision issues with `mediump float` declarations
- Efficient enough for real-time performance on VideoCore GPU

## Dependencies

- Python 3.11+
- pygame
- PyOpenGL

Install with:
```bash
pip install pygame PyOpenGL
```

## Development Notes

This implementation is based on the original CPU-based eyeball animation but moves all expensive per-pixel operations to the GPU. The fragment shader computes:

1. Screen-space UV coordinates with aspect correction
2. Radial sclera gradient
3. Elliptical iris membership testing
4. Procedural iris texture patterns
5. Pupil overlay with scaling
6. Eyelid occlusion

The CPU retains control over eye movement timing, saccade scheduling, and blink state machines for easy behavioral tuning.