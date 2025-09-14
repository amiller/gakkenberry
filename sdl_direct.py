import os
os.environ["SDL_VIDEODRIVER"] = "kmsdrm"

import pygame
import numpy as np
import math

# Init display
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
W, H = screen.get_size()

running = True
clock = pygame.time.Clock()
frame = 0

while running:
    # Clear screen
    screen.fill((0, 0, 0))

    # Draw animated sine wave directly with pygame
    points = []
    for x in range(0, W, 4):  # Every 4 pixels for performance
        # Animated sine wave
        y = H//2 + int(100 * math.sin(x * 0.02 + frame * 0.1))
        points.append((x, y))

    # Draw the wave
    if len(points) > 1:
        pygame.draw.lines(screen, (0, 255, 0), False, points, 2)

    # Draw some moving circles
    for i in range(5):
        x = int(W//2 + 200 * math.cos(frame * 0.05 + i * 2 * math.pi / 5))
        y = int(H//2 + 100 * math.sin(frame * 0.07 + i * 2 * math.pi / 5))
        pygame.draw.circle(screen, (255, i*50, 255-i*50), (x, y), 20)

    # Draw frame counter
    font = pygame.font.Font(None, 36)
    text = font.render(f"Frame: {frame}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()
    frame += 1

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        if event.type == pygame.QUIT:
            running = False

    clock.tick(60)  # Target 60 FPS

pygame.quit()