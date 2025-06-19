"""
Particle system for the Asteroids game.

This module contains the ParticlePool class for efficient particle management.
"""

import math
import random
from typing import List, Optional

from data_structures import Particle, ParticleType
from config import Cfg


class ParticlePool:
    """Object pool for efficient particle management."""

    def __init__(self, size: int = 1000):
        self.pool: List[Particle] = []
        self.active_indices: List[int] = []
        self.inactive_indices: List[int] = list(range(size))

        for _ in range(size):
            self.pool.append(Particle())

    def get(self) -> Optional[Particle]:
        """Get an inactive particle from the pool.

        Returns:
            Particle object or None if pool exhausted
        """
        if self.inactive_indices:
            idx = self.inactive_indices.pop()
            particle = self.pool[idx]
            particle.active = True
            self.active_indices.append(idx)
            return particle
        return None

    def update(self, time_scale: float, ship=None) -> None:
        """Update all active particles.

        Args:
            time_scale: Time scaling factor for slow-mo effects
            ship: Ship object for streak particle attraction (optional)

        Side effects:
            Modifies particle positions and life, manages active/inactive lists
        """

        new_active = []

        for idx in self.active_indices:
            particle = self.pool[idx]

            particle.x += particle.vx * time_scale
            particle.y += particle.vy * time_scale
            particle.life -= time_scale

            # Special behavior for streak particles
            if (
                particle.type == ParticleType.STREAK
                and particle.life > Cfg.particle_streak_min_life
                and ship
            ):
                dx = ship.x - particle.x
                dy = ship.y - particle.y
                dist_sq = dx * dx + dy * dy
                if dist_sq > Cfg.particle_streak_attraction_distance:
                    dist = math.sqrt(dist_sq)
                    attraction = Cfg.particle_streak_attraction_force
                    particle.vx += (dx / dist) * attraction * time_scale
                    particle.vy += (dy / dist) * attraction * time_scale
            else:
                friction_factor = 0.95**time_scale
                particle.vx *= friction_factor
                particle.vy *= friction_factor

            if particle.life > 0:
                new_active.append(idx)
            else:
                particle.active = False
                self.inactive_indices.append(idx)

        self.active_indices = new_active

    def get_active_particles(self) -> List[Particle]:
        """Get list of all active particles.

        Returns:
            List of active Particle objects
        """
        return [self.pool[idx] for idx in self.active_indices if self.pool[idx].active]

    def clear(self) -> None:
        """Reset all particles to inactive state.

        Side effects:
            Deactivates all particles and resets pool state
        """
        for particle in self.pool:
            particle.active = False

        self.active_indices.clear()
        self.inactive_indices = list(range(len(self.pool)))
