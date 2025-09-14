import numpy as np
import matplotlib.pyplot as plt

# Screen dimensions
H, W = 720, 1280

# FOV: azimuth from -π/2 to π/2, elevation from -π/2 to π/2 (but we clip outside the hemisphere)
u = np.linspace(-1.0, 1.0, W)  # horizontal: azimuth
v = np.linspace(-1.0, 1.0, H)  # vertical: elevation

U, V = np.meshgrid(u, v)  # shape (H, W)

# Gnomonic projection: each pixel maps to direction vector
# (x, y, z) ∝ (1, U, V)
norm = np.sqrt(1 + U**2 + V**2)
X = 1 / norm
Y = U / norm
Z = V / norm

# Grazing angle: keep only points where dot((1,0,0), (X,Y,Z)) > 0
mask = X < 0
X[mask] = np.nan
Y[mask] = np.nan
Z[mask] = np.nan

# Spherical coordinates
THETA = np.arccos(np.clip(Z, -1, 1))  # [0, pi]
PHI   = np.arctan2(Y, X)              # [-pi, pi]

# Debug: show PHI as an image
plt.imshow(PHI, cmap='twilight', origin='lower')
plt.title('Azimuth (φ)')
plt.colorbar(label='Radians')
plt.show()
