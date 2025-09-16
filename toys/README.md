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