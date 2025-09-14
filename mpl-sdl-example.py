import os
os.environ["SDL_VIDEODRIVER"] = "kmsdrm"

import pygame
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Init display
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # native mode
W, H = screen.get_size()

# Matplotlib figure roughly matching screen
fig = plt.figure(figsize=(W/100, H/100), dpi=100)
ax = fig.add_subplot(111)

# One-time Agg renderer
fig.canvas.draw()

running = True
clock = pygame.time.Clock()

while running:
    # Update plot
    ax.clear()
    x = np.linspace(0, 10, 100)
    y = np.sin(x + pygame.time.get_ticks() * 0.001)  # animated sine wave
    ax.plot(x, y)
    fig.canvas.draw()

    # Get RGBA bytes from the Agg canvas
    buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf = buf.reshape(H, W, 4)  # match your fig size to W,H for speed

    # Convert ARGB -> RGB for pygame (drop alpha)
    rgb = buf[:, :, 1:4]  # skip A; now R,G,B

    # Create Surface from array (copy=False can be tricky; copy is safer)
    surf = pygame.surfarray.make_surface(np.transpose(rgb, (1,0,2)))  # pygame expects (W,H,3)
    screen.blit(surf, (0,0))
    pygame.display.flip()

    # clock.tick(30)  # cap to ~30 FPS
