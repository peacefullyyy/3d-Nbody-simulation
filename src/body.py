import numpy as np

class Body:
    def __init__(self, mass, position, velocity, radius=5, color=(255, 255, 255), fixed=False):
        self.mass = mass
        self.position = np.array(position, dtype=float)  # [x, y, z]
        self.velocity = np.array(velocity, dtype=float)  # [vx, vy, vz]
        self.acceleration = np.array([0.0, 0.0, 0.0], dtype=float)
        self.radius = radius
        self.color = color
        self.trail = []  # Список для хранения позиций (БЕЗ ОГРАНИЧЕНИЙ!)
        self.fixed = fixed
