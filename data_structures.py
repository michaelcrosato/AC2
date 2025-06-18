"""
Data structures for the Asteroids game.

This module contains all enums and dataclasses used throughout the game.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Tuple, Optional


class PowerUpType(Enum):
    """Power-up types available in the game."""
    RAPID = 'rapid'
    TRIPLE = 'triple'
    SHIELD = 'shield'
    LIFE = 'life'
    CRYSTAL = 'crystal'


class EnemyAIType(Enum):
    """Enemy AI behavior types."""
    HUNTER = 'hunter'
    CIRCLER = 'circler'


class ParticleType(Enum):
    """Particle effect types."""
    STREAK = 'streak'
    RESPAWN = 'respawn'
    DASH = 'dash'
    FINISHER = 'finisher'
    ENEMY_EXPLOSION = 'enemy_explosion'
    BURST = 'burst'
    DEFAULT = 'default'


class FinisherPhase(Enum):
    """Finisher execution phases."""
    IDLE = 'idle'
    LOCK_ON = 'lock_on'
    PRE_IMPACT = 'pre_impact'
    IMPACT = 'impact'
    POST_IMPACT = 'post_impact'


@dataclass
class ShipState:
    """Complete state for the player ship."""
    x: float
    y: float
    angle: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    invulnerable: float = 0
    rapid_fire: float = 0
    triple_shot: float = 0
    shield_active: float = 0
    powerup_flash: float = 0
    powerup_flash_color: Tuple[int, int, int] = (255, 255, 255)
    respawning: float = 0
    aura_pulse: float = 0.0
    dashing: float = 0
    dash_trail: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Asteroid:
    """Asteroid game object."""
    x: float
    y: float
    vx: float
    vy: float
    size: int
    radius: float
    angle: float
    spin: float
    shape: List[int]
    is_boss: bool = False
    has_crystals: bool = False
    health: int = 1
    max_health: int = 1
    hit_flash: float = 0


@dataclass
class Bullet:
    """Projectile fired by ship or enemies."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    trail: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class Enemy:
    """Enemy ship game object."""
    x: float
    y: float
    vx: float = 0.0
    vy: float = 0.0
    angle: float = 0.0
    fire_cooldown: float = 90
    health: int = 3
    max_health: int = 3
    ai_type: EnemyAIType = EnemyAIType.HUNTER
    orbit_angle: float = 0.0
    radius: float = 12.0
    hit_flash: float = 0


@dataclass
class PowerUp:
    """Collectible power-up game object."""
    x: float
    y: float
    vx: float
    vy: float
    type: PowerUpType
    lifetime: float
    pulse: float = 0.0


@dataclass
class Particle:
    """Visual effect particle."""
    active: bool = False
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    life: float = 0.0
    color: Tuple[int, int, int] = (255, 255, 255)
    type: Optional[ParticleType] = None


@dataclass
class FloatingText:
    """UI floating text effect."""
    x: float
    y: float
    text: str
    color: Tuple[int, int, int]
    life: float
    vy: float 