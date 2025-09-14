# Gakken projector controller on raspberry pi

## Initial setup (Raspberry Pi)

The Raspberry Pi was set up with:
- RPi OS Lite
- Python virtual environment with system site packages: `~/gakken-venv`
- System packages: `mpv`, `python3-matplotlib`
- Python packages: `pygame`, `numpy`

The HDMI resolution is 1280x720. We run without X11, using direct framebuffer access.

## Setup (Control computer)

Add this to your ~/.ssh/config so the coding agent can reuse a session:

```
Host gakkenberry
    HostName gakkenberry.local
    User pi
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist yes
```

Download test files:
```bash
curl -o earth.gif https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif
```

Copy files to gakkenberry:
```bash
scp earth.gif gakkenberry:~/
scp mpl-sdl-example.py gakkenberry:~/
scp sdl_direct.py gakkenberry:~/
```

### Remote control script

You can run commands directly via SSH:
```bash
ssh gakkenberry "mpv earth.gif"      # Direct SSH command execution
ssh gakkenberry "pkill mpv"          # Kill processes remotely
```

`gakken.sh` is a utility wrapper that makes coding agents more comfortable with remote execution:

```bash
./gakken.sh "mpv earth.gif"           # Run arbitrary commands
./gakken.sh kill-mpv                  # Kill all mpv processes
./gakken.sh kill-python               # Kill all python processes
./gakken.sh play earth.gif            # Play file with mpv
./gakken.sh cmd "ls -la"              # Explicit command mode
```

## Getting started

### Play videos/images with mpv

```bash
./gakken.sh play earth.gif
```

### Matplotlib visualization

For scientific visualization with matplotlib, use the "Agg" backend:

```python
import matplotlib
matplotlib.use("Agg")
```

Run matplotlib SDL example:
```bash
./gakken.sh "source ~/gakken-venv/bin/activate && python mpl-sdl-example.py"
```

### Direct pygame drawing (fastest)

Run direct pygame drawing example:
```bash
./gakken.sh "source ~/gakken-venv/bin/activate && python sdl_direct.py"
```

This is much faster than matplotlib since it does direct drawing without buffer conversions.

## Hemispherical Display Calibration

The Gakken WorldEye is a hemispherical display using **Azimuthal Equidistant (AE) projection**, also known as "fisheye-equidistant" mapping. In this projection, radial distance on the screen is linear in great-circle angle from the viewing direction.

### Projection System

The projection utilities are implemented in `projection_utils.py` and `generate_calibration_grids.py`:

- **Single projection function**: `azimuthal_equidistant_projection(x, y, z)`
- **Clean separation**: Projection logic separate from coordinate generation
- **Two view modes**: Polar (pole at center) and Standard (pole at top)

### Calibration References

Two reference frames extracted from the original Gakken WorldEye calibration video:

- `polar_view_reference.png` - Frame at 48s showing pole-centered view with azimuth rings
- `standard_view_reference.png` - Frame at 8s showing standard globe view with lat/lon grid

Generated calibration wireframes (not checked in, create with `generate_calibration_grids.py`):

- `polar_view_wireframe.png` - Shows azimuth rings (15°, 30°, 45°, 60°, 75°, 90° from pole)
- `standard_view_wireframe.png` - Shows latitude/longitude grid with pole at top

### Playing Calibration Images

Play calibration images with the same scaling used for the original calibration video:

```bash
# Play polar view calibration
./gakken.sh "mpv polar_view_wireframe.png --video-scale-x=0.984 --video-scale-y=0.972 --video-aspect-override=16:9 --loop=inf --no-audio --fullscreen"

# Play standard view calibration
./gakken.sh "mpv standard_view_wireframe.png --video-scale-x=0.984 --video-scale-y=0.972 --video-aspect-override=16:9 --loop=inf --no-audio --fullscreen"
```

The scale factors (0.984, 0.972) provide fine-tuning for display margins, while `--video-aspect-override=16:9` handles the 4:3 to 16:9 aspect ratio conversion.

### Generating New Calibration Patterns

To generate updated calibration wireframes:

```bash
./gakken.sh "source ~/gakken-venv/bin/activate && python generate_calibration_grids.py"
```

This creates both `polar_view_wireframe.png` and `standard_view_wireframe.png` using the shared projection utilities.

### Key Calibration Insights

- **Azimuth rings not latitude lines**: The equally-spaced rings in polar view represent great-circle distances from the pole (15°, 30°, 45°, etc.), not geographic latitude lines
- **AE projection characteristic**: Equal spacing of azimuth rings is the key indicator of proper azimuthal equidistant projection
- **Unified math**: Both views use the same AE projection with different 3D coordinate rotations