# Gakkenberry Interactive Toys

Interactive demonstrations and animations for the hemispherical display.

## Animated Eyeball

Realistic 3D eyeball with interactive controls and smooth animations:

```bash
# Basic eyeball (green iris, default performance)
./gakken.sh python toys/eyeball.py

# Full-screen eyeball with configurable decimation
./gakken.sh python toys/eyeball_fullscreen.py --decimation=3

# Different eye colors
./gakken.sh python toys/eyeball_fullscreen.py color=blue --decimation=8

# Performance options (decimation controls internal rendering resolution):
# --decimation=8  # 160x90, very fast (~68 FPS)
# --decimation=3  # 427x240, default (~45 FPS, good balance)
# --decimation=2  # 640x360, higher quality (~20 FPS)
# --decimation=1  # 1280x720, full resolution (~2 FPS)
```

**Interactive controls:**
- Arrow keys: Move eye direction
- Space: Trigger immediate blink
- R: Reset eye to center
- +/-: Adjust pupil size
- ESC/Q: Quit

**Available eye colors:** green, blue, brown, hazel, gray

## GPU Eyeball (High Performance)

GPU-accelerated eyeball using OpenGL fragment shaders for dramatically improved performance:

```bash
# LOCAL TESTING ONLY (requires local display, not compatible with gakken.sh remote execution)
source ~/sandboxes/py3.11/bin/activate
python toys/gpu_eyeball.py --windowed

# GPU eyeball fullscreen (local only)
python toys/gpu_eyeball.py

# Different eye colors
python toys/gpu_eyeball.py --windowed color=blue
```

**Raspberry Pi deployment with xinit:**
```bash
xinit /usr/bin/python3 /home/pi/toys/gpu_eyeball.py -- :0 -nolisten tcp vt1 -keeptty
```

**Required X11 setup for Raspberry Pi:**
- Install xinit: `sudo apt install xinit`
- Configure X11 permissions: `sudo dpkg-reconfigure xserver-xorg-legacy` (choose "Anybody")
- Or directly: `sudo sh -c 'printf "allowed_users=anybody\nneeds_root_rights=yes\n" > /etc/Xwrapper.config'`

This allows non-root users to start X11 sessions for dedicated fullscreen GPU eyeball display.

**Performance:** Runs at 60 FPS at full 1280x720 resolution by moving all pixel computations to the GPU fragment shader. Ideal for Raspberry Pi deployment.

**Interactive controls:**
- Space: Trigger immediate blink
- +/-: Adjust pupil size (dilation/constriction)
- R: Reset eye to center
- ESC/Q: Quit

**Eye colors:** green, blue, brown, hazel, gray

**Technical:** Uses OpenGL ES 2.0 compatible shaders with procedural iris textures (radial `sin(8πr)` and angular `sin(12θ)` patterns) computed per-pixel on GPU.