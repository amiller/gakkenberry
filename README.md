# Gakken projector controller on raspberry pi



## Configuring SSH for agents

Add this to your ~/.ssh/config so the coding agent can reuse a session

```
Host gakkenberry
    HostName gakkenberry.local
    User pi
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist yes
```

## Gakken resolution

The hdmi seems already to work well. The resolution is an unusual 1280x720, so if modetest indicates that we're on the right track.

## Play videos/images with mpv

We don't have x11 started, instead we just play videos directly with mpv

Download a test gif:
```bash
curl -o earth.gif https://upload.wikimedia.org/wikipedia/commons/7/7f/Rotating_earth_animated_transparent.gif
```

Copy files to gakkenberry:
```bash
scp earth.gif gakkenberry:~/
scp mpl-sdl-example.py gakkenberry:~/
```

## Remote control script

You can run commands directly via SSH:
```bash
ssh gakkenberry "mpv earth.gif"      # Direct SSH command execution
ssh gakkenberry "pkill mpv"          # Kill processes remotely
```

`gakken.sh` is a utility wrapper that makes coding agents more comfortable with remote execution:

```bash
./gakken.sh "mpv earth.gif"           # Run arbitrary commands
./gakken.sh kill-mpv                  # Kill all mpv processes
./gakken.sh play earth.gif            # Play with 30s timeout and auto-cleanup
./gakken.sh cmd "ls -la"              # Explicit command mode
```

## Control with matplotlib

We expect to use the gakken for scientific visualization with matplotlib.

```python
import matplotlib
matplotlib.use("Agg")
```

Run matplotlib SDL example:
```bash
./gakken.sh "source ~/gakken-venv/bin/activate && python mpl-sdl-example.py"
```