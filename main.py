# type: ignore
"""
ASTEROIDS ENHANCED - LLM-Optimized Modular Game Architecture
Version: 7.0.0 (Modular Edition)
Last Updated: June, 18 2025
Lead Programmers: Claude 4 Opus/Sonnet (Anthropic)
Code Reviewers: ChatGPT 4o/4.1, Grok 3, Gemini 2.5 Pro
Architecture Evolution: Single-file @ 5,500 lines → Modular

DESIGN PHILOSOPHY & EVOLUTION:
Originally designed as a single-file system for maximum LLM context visibility.
Modularized when file size exceeded reliable LLM editing capabilities (~5,000 lines).
Current architecture balances LLM comprehension with maintainable file sizes.

KEY PRINCIPLES (Updated for Modular Architecture):
1. File Size Limits: Keep modules <5,000 lines for reliable LLM editing
2. Dependency Injection: Avoid circular imports via function passing
3. Explicit State: Full paths (g_game_state['effects']['screen_shake'])
4. Clear Side Effects: Document all state modifications
5. Context Objects: Bundle parameters to reduce function signatures
6. Fail Safely: Wrap risky operations in try-except blocks
7. Copy Don't Abstract: Duplicate similar code rather than over-generalize

MODULE STRUCTURE:
- main.py (This file): Core loop, coordination, game state management
- config.py: All constants and configuration (Cfg.*)
- data_structures.py: Entity types (ShipState, Asteroid, Enemy, etc.)
- particle_system.py: ParticlePool for efficient particle management
- sound_system.py: Audio generation and playback (optional)
- visual_effects.py: Rendering effects (stars, dust, transitions)
- progression_system.py: Save/load, achievements, upgrades
- drawing_system.py: Centralized drawing operations

MODIFICATION GUIDANCE:
- Prefer explicit state and verbose logic for LLM clarity
- Use dependency injection pattern when adding new systems
- Create wrapper functions during migration to maintain compatibility
- Would return to single-file if LLM capabilities improve
- Document side effects meticulously - next LLM depends on it

=== [SECTION INDEX - main.py] ===
1. Imports and Module Integration
2. Global State Variables
3. Helper Functions
4. Text Cache System
5. Progression System Wrappers
6. API: Initialization
7. Controller System
8. Window Management
9. Object Creation
10. Particle Effects
11. Combat Mechanics
12. Finisher Mechanics
13. Collision Detection
14. Movement and Physics
15. Enemy AI
16. Game Object Updates
17. Visual Effects Management
18. Level Management
19. Finisher Target Detection
20. UI State Management
21. Rendering Coordination
22. Game Reset
23. Main Game Loop
24. Entry Point

Note: Drawing operations → drawing_system.py
      Sound operations → sound_system.py
      Visual effects → visual_effects.py
      Save/Load → progression_system.py
"""

import pygame
import math
import random
import sys
import json
import os
from enum import Enum, auto
from functools import lru_cache
from typing import Dict, List, Tuple, Optional, Any, Union, Protocol, Callable, TypeVar, Generic
from dataclasses import dataclass, field

# Import sound system
import sound_system
from sound_system import (
    init_sounds,
    play_sound,
    stop_thrust_sound,
    stop_all_sounds,
    toggle_sound,
    get_sound_enabled,
    set_sound_enabled,
    SoundConfig,
)

# Import data structures
from data_structures import (
    PowerUpType,
    EnemyAIType,
    ParticleType,
    FinisherPhase,
    ShipState,
    Asteroid,
    Bullet,
    Enemy,
    PowerUp,
    Particle,
    FloatingText,
)

# Import configuration
from config import Cfg

# Import particle system
from particle_system import ParticlePool

# Import visual effects
import visual_effects as vfx

# Import progression system
from progression_system import ProgressionSystem, GameContext
from drawing_system import DrawingSystem

# === [CONFIGURATION] ===
# (Configuration moved to config.py module)

# === [GLOBAL STATE VARIABLES] ===

# Dynamic resolution
g_screen_width: int = 800
g_screen_height: int = 600
g_scale_factor: float = 1.0

# Pygame objects
g_screen: Optional[pygame.Surface] = None
g_clock: Optional[pygame.time.Clock] = None
g_font: Any = None
g_big_font: Any = None
g_small_font: Any = None
g_tiny_font: Any = None

# Controller
g_controller: Optional[Any] = None
g_controller_connected: bool = False

# Game state - organized into logical groups
g_game_state = {
    # Core game
    "score": 0,
    "lives": 3,
    "level": 1,
    "game_over": False,
    "paused": False,
    # Resources
    "crystals": 0,
    "high_score": 0,
    "lifetime_crystals": 0,
    "achievements_unlocked": set(),
    "upgrade_levels": {"damage": 0, "fire_rate": 0, "max_speed": 0, "dash_cooldown": 0},
    "boss_kills": 0,
    # Visual effects
    "effects": {
        "screen_shake": 0,
        "game_over_alpha": 0,
        "level_transition": 0,
        "level_transition_text": "",
        "damage_flash": 0,
        "damage_flash_color": Cfg.colors["damage_flash"],
        "aura_rotation": 0,
        "pause_menu_alpha": 0,
        "wave_warning": 0,
        "wave_warning_text": "",
    },
    # Timing
    "bullet_cooldown": 0,
    "frame_count": 0,
    "pause_debounce": 0,
    "resize_pending": None,
    "resize_timer": 0,
    "thrust_sound_playing": False,
    "time_scale": 1.0,
    # Combat systems
    "combo": {"current": 0, "timer": 0, "kills": 0, "max": 0, "pulse": 0},
    "dash": {"cooldown": 0},
    "finisher": {
        "meter": 0.0,
        "ready": False,
        "executing": False,
        "execution_timer": 0,
        "phase": FinisherPhase.IDLE,
        "target": None,
        "shockwave_radius": 0,
        "lock_on_progress": 0.0,
        "impact_x": 0,
        "impact_y": 0,
    },
    # Level state
    "untouchable_level": True,
    # Menu state
    "show_upgrade_menu": False,
    "selected_upgrade": 0,
}

# Ship state (initialized in init_ship_state())
g_ship: ShipState

# Game objects
g_asteroids: List[Asteroid] = []
g_bullets: List[Bullet] = []
g_powerups: List[PowerUp] = []
g_floating_texts: List[FloatingText] = []
g_enemies: List[Enemy] = []
g_enemy_bullets: List[Bullet] = []

# Visual effects are now in visual_effects module

# Sounds are imported from sound_system module

# === [HELPER FUNCTIONS] ===


def scaled(value: float) -> float:
    """Scale a value by the current scale factor.

    Args:
        value: Value to scale

    Returns:
        Scaled value
    """
    return value * g_scale_factor


@lru_cache(maxsize=3600)
def get_sin_cos(angle: float) -> Tuple[float, float]:
    """Get cached sin/cos values for an angle with 0.1 degree precision.

    Args:
        angle: Angle in degrees

    Returns:
        Tuple of (sin, cos) values
    """
    angle = round(angle, 1) % 360
    rad = math.radians(angle)
    return (math.sin(rad), math.cos(rad))


def wrap_position(entity: Union[Dict[str, Any], ShipState, Asteroid, Enemy, PowerUp]) -> None:
    """Wrap an entity's position around screen boundaries.

    This ensures objects moving off one edge appear on the opposite edge,
    creating a continuous playing field.

    Args:
        entity: Object with 'x' and 'y' attributes

    Side effects:
        Modifies entity.x and entity.y
    """
    if isinstance(entity, dict):
        entity["x"] = entity["x"] % g_screen_width
        entity["y"] = entity["y"] % g_screen_height
    else:
        entity.x = entity.x % g_screen_width
        entity.y = entity.y % g_screen_height


def distance_squared(obj1: Any, obj2: Any) -> float:
    """Calculate squared distance between two objects (avoids sqrt for performance).

    Args:
        obj1: First object with x/y coordinates
        obj2: Second object with x/y coordinates

    Returns:
        Squared distance between objects
    """
    x1 = obj1.x if hasattr(obj1, "x") else obj1["x"]
    y1 = obj1.y if hasattr(obj1, "y") else obj1["y"]
    x2 = obj2.x if hasattr(obj2, "x") else obj2["x"]
    y2 = obj2.y if hasattr(obj2, "y") else obj2["y"]

    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


def check_collision(obj1: Any, obj2: Any, r1: float, r2: float) -> bool:
    """Check if two circular objects are colliding.

    Args:
        obj1: First object
        obj2: Second object
        r1: Radius of first object
        r2: Radius of second object

    Returns:
        True if objects are colliding
    """
    return distance_squared(obj1, obj2) < (r1 + r2) ** 2


def get_ship_points(
    x: float, y: float, angle: float, scale_mult: float = 1.0
) -> List[Tuple[float, float]]:
    """Calculate the polygon points for ship shape.

    Args:
        x: Ship x position
        y: Ship y position
        angle: Ship angle in degrees
        scale_mult: Additional scale multiplier

    Returns:
        List of (x, y) tuples forming ship polygon
    """
    sin_a, cos_a = get_sin_cos(angle)
    sin_wing_left, cos_wing_left = get_sin_cos(angle + Cfg.ship_wing_angle)
    sin_wing_right, cos_wing_right = get_sin_cos(angle - Cfg.ship_wing_angle)

    s = g_scale_factor * scale_mult

    return [
        (
            x + scaled(Cfg.ship_nose_length) * cos_a * scale_mult,
            y + scaled(Cfg.ship_nose_length) * sin_a * scale_mult,
        ),
        (
            x + scaled(Cfg.ship_wing_length) * cos_wing_left * scale_mult,
            y + scaled(Cfg.ship_wing_length) * sin_wing_left * scale_mult,
        ),
        (
            x - scaled(Cfg.ship_back_indent) * cos_a * scale_mult,
            y - scaled(Cfg.ship_back_indent) * sin_a * scale_mult,
        ),
        (
            x + scaled(Cfg.ship_wing_length) * cos_wing_right * scale_mult,
            y + scaled(Cfg.ship_wing_length) * sin_wing_right * scale_mult,
        ),
    ]


def update_timer(value: float, decrement: float = 1.0) -> float:
    """Update any timed effect that counts down.

    Args:
        value: Current timer value
        decrement: Amount to decrement per frame

    Returns:
        Updated timer value
    """
    if value > 0:
        return max(0, value - decrement * g_game_state["time_scale"])
    return 0


def calculate_fade(progress: float, max_alpha: int = 255) -> int:
    """Calculate fade alpha value based on progress.

    Args:
        progress: Progress value (0-1)
        max_alpha: Maximum alpha value

    Returns:
        Alpha value
    """
    return int(max_alpha * max(0, min(1, progress)))


def calculate_pulse(
    time: float, frequency: float = 0.1, amplitude: float = 0.5, offset: float = 0.5
) -> float:
    """Calculate pulse value for animations.

    Args:
        time: Time value (typically frame count)
        frequency: Pulse frequency
        amplitude: Pulse amplitude
        offset: Baseline offset

    Returns:
        Pulse value
    """
    return abs(math.sin(time * frequency)) * amplitude + offset


def safe_operation(operation_name: str, func: Callable, *args, **kwargs) -> Optional[Any]:
    """Execute operation with consistent error reporting.

    Args:
        operation_name: Name of operation for error context
        func: Function to execute safely
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function

    Returns:
        Function result or None on error

    Side effects:
        Prints error messages on exceptions
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"[{operation_name}] Error: {e}")
        return None


# === [DRAWING EFFECTS SYSTEM] ===

# === [DRAWING SYSTEM] ===
# DrawEffects class moved to drawing_system.py module

# === [PARTICLE SYSTEM] ===
# ParticlePool class moved to particle_system.py module

g_particle_pool = ParticlePool()

# === [TEXT CACHE SYSTEM] ===


class TextCache:
    """Cache rendered text surfaces to improve performance."""

    def __init__(self):
        self.cache: Dict[Tuple[str, int, Tuple[int, int, int]], Tuple[pygame.Surface, int]] = {}
        self.frame_count: int = 0
        self.max_age: int = 300

    def get_text(
        self, text: str, font: pygame.font.Font, color: Tuple[int, int, int]
    ) -> pygame.Surface:
        """Get cached text surface or create new one.

        Args:
            text: Text to render
            font: Font object
            color: RGB color tuple

        Returns:
            Rendered text surface
        """
        key = (text, id(font), color)

        if key in self.cache:
            surface, _ = self.cache[key]
            self.cache[key] = (surface, self.frame_count)
            return surface

        surface = font.render(text, True, color)
        self.cache[key] = (surface, self.frame_count)
        return surface

    def update(self) -> None:
        """Clean up old cached text surfaces.

        Side effects:
            Removes old entries from cache
        """
        self.frame_count += 1

        if self.frame_count % 300 == 0:
            old_keys = [
                key
                for key, (_, last_access) in self.cache.items()
                if self.frame_count - last_access > self.max_age
            ]

            for key in old_keys:
                del self.cache[key]

    def clear(self) -> None:
        """Clear all cached text surfaces.

        Side effects:
            Empties the cache dictionary
        """
        self.cache.clear()


g_text_cache = TextCache()

# Drawing system (initialized after fonts are ready)
g_drawing: Optional[DrawingSystem] = None

# Progression system (initialized in main())
g_progression: ProgressionSystem

# === [SAVE/LOAD SYSTEM] ===
# Save/load, achievements, and upgrades moved to progression_system.py module


def validate_save_data(save_data: dict) -> bool:
    """Validate save data structure and types.

    Args:
        save_data: Dictionary containing save data

    Returns:
        True if save data is valid, False otherwise
    """
    required_fields = {
        "high_score": (int, float),  # Allow both int and float for backwards compatibility
        "lifetime_crystals": (int, float),
        "achievements_unlocked": (list, set),  # Allow both list and set
        "upgrade_levels": dict,
        "boss_kills": (int, float),
    }

    for field, expected_types in required_fields.items():
        if field not in save_data:
            print(f"[validate_save_data] Missing required field: {field}")
            return False
        if not isinstance(save_data[field], expected_types):
            print(
                f"[validate_save_data] Invalid type for {field}: expected {expected_types}, got {type(save_data[field])}"
            )
            return False

    # Validate upgrade_levels structure
    if not all(
        isinstance(k, str) and isinstance(v, (int, float))
        for k, v in save_data["upgrade_levels"].items()
    ):
        print("[validate_save_data] Invalid upgrade_levels structure")
        return False

    return True


def save_game_state() -> bool:
    """Save persistent game state to file.

    Returns:
        True if save successful, False otherwise

    Side effects:
        Writes to Cfg.save_file

    Globals:
        Reads g_game_state
    """
    save_data = {
        "high_score": g_game_state["high_score"],
        "lifetime_crystals": g_game_state["lifetime_crystals"],
        "achievements_unlocked": list(g_game_state["achievements_unlocked"]),
        "upgrade_levels": g_game_state["upgrade_levels"],
        "boss_kills": g_game_state.get("boss_kills", 0),
    }

    try:
        with open(Cfg.save_file, "w") as f:
            json.dump(save_data, f, indent=2)
        return True
    except Exception as e:
        print(f"[save_game_state] Could not save game state: {e}")
        return False


def load_game_state() -> bool:
    """Load persistent game state from file.

    Returns:
        True if load successful, False if using defaults

    Side effects:
        Modifies g_game_state with loaded values

    Globals:
        Writes to g_game_state
    """
    default_state = {
        "high_score": 0,
        "lifetime_crystals": 0,
        "achievements_unlocked": set(),
        "upgrade_levels": {key: 0 for key in Cfg.upgrades},
        "boss_kills": 0,
    }

    try:
        if not os.path.exists(Cfg.save_file):
            print("[load_game_state] No save file found, using defaults")
            g_game_state.update(default_state)
            return False

        with open(Cfg.save_file, "r") as f:
            save_data = json.load(f)

        # Validate save data structure
        if not validate_save_data(save_data):
            print("[load_game_state] Save data validation failed, using defaults")
            g_game_state.update(default_state)
            return False

        # Validate and load data
        g_game_state["high_score"] = max(0, int(save_data.get("high_score", 0)))
        g_game_state["lifetime_crystals"] = max(0, int(save_data.get("lifetime_crystals", 0)))

        loaded_achievements = save_data.get("achievements_unlocked", [])
        g_game_state["achievements_unlocked"] = set(
            ach for ach in loaded_achievements if ach in Cfg.achievements
        )

        loaded_upgrades = save_data.get("upgrade_levels", {})
        validated_upgrades = {key: 0 for key in Cfg.upgrades}
        for upgrade, level in loaded_upgrades.items():
            if upgrade in Cfg.upgrades:
                max_level = Cfg.upgrades[upgrade]["max_level"]
                validated_upgrades[upgrade] = max(0, min(int(level), max_level))
        g_game_state["upgrade_levels"] = validated_upgrades

        g_game_state["boss_kills"] = max(0, int(save_data.get("boss_kills", 0)))

        print(
            f"[load_game_state] Loaded: High score {g_game_state['high_score']}, "
            f"{len(g_game_state['achievements_unlocked'])} achievements"
        )
        return True

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        print(f"[load_game_state] Save file corrupted, using defaults: {e}")
        g_game_state.update(default_state)
        return False
    except Exception as e:
        print(f"[load_game_state] Unexpected error loading save: {e}")
        g_game_state.update(default_state)
        return False


# === [ACHIEVEMENTS SYSTEM] ===

# === [LLM EXTENSION POINT: Add new achievement conditions here] ===
ACHIEVEMENT_CONDITIONS = {
    "first_blood": lambda: g_game_state["score"] > 0,
    "combo_5": lambda: g_game_state["combo"]["current"] >= Cfg.combo_milestone_thresholds[0],
    "combo_10": lambda: g_game_state["combo"]["current"] >= Cfg.combo_milestone_thresholds[1],
    "survivor": lambda: g_game_state["level"] >= Cfg.achievement_survivor_level,
    "boss_slayer": lambda: g_game_state.get("boss_kills", 0) > 0,
    "untouchable": lambda: g_game_state["level"] > 1 and g_game_state["untouchable_level"],
    "speed_demon": lambda: g_game_state["upgrade_levels"]["max_speed"]
    >= Cfg.achievement_speed_demon_level,
    "crystal_hoarder": lambda: g_game_state["lifetime_crystals"]
    >= Cfg.achievement_crystal_hoarder_amount,
}


def check_achievement(achievement_id: str) -> bool:
    """Check if an achievement has been earned and unlock it if so.

    Args:
        achievement_id: ID of achievement to check

    Returns:
        True if achievement was newly unlocked

    Side effects:
        Modifies g_game_state['achievements_unlocked'], g_game_state['crystals'],
        creates floating text, calls save_game_state()

    Globals:
        Reads/writes g_game_state, writes to g_floating_texts
    """
    if achievement_id in g_game_state["achievements_unlocked"]:
        return False

    # Check achievement condition using lookup table
    if achievement_id in ACHIEVEMENT_CONDITIONS and ACHIEVEMENT_CONDITIONS[achievement_id]():
        g_game_state["achievements_unlocked"].add(achievement_id)
        achievement = Cfg.achievements[achievement_id]
        g_game_state["crystals"] += achievement["reward"]
        create_floating_text(
            g_screen_width // 2,
            g_screen_height // 2 - 100,
            f"ACHIEVEMENT: {achievement['name']}",
            Cfg.colors["gold"],
        )
        create_floating_text(
            g_screen_width // 2,
            g_screen_height // 2 - 70,
            f"+{achievement['reward']} Crystals",
            Cfg.colors["crystal"],
        )
        save_game_state()
        return True

    return False


# === [UPGRADES SYSTEM] ===


def calculate_upgrade_cost(upgrade_type: str) -> Optional[int]:
    """Calculate the cost for the next level of an upgrade.

    Args:
        upgrade_type: Type of upgrade

    Returns:
        Cost in crystals or None if maxed

    Globals:
        Reads g_game_state
    """
    level = g_game_state["upgrade_levels"][upgrade_type]
    if level >= Cfg.upgrades[upgrade_type]["max_level"]:
        return None

    base_cost = Cfg.upgrades[upgrade_type]["base_cost"]
    multiplier = Cfg.upgrades[upgrade_type]["cost_multiplier"]
    return int(base_cost * (multiplier**level))


def apply_upgrade(upgrade_type: str) -> bool:
    """Apply an upgrade if the player can afford it.

    Args:
        upgrade_type: Type of upgrade to apply

    Returns:
        True if upgrade was applied

    Side effects:
        Modifies g_game_state['crystals'], g_game_state['upgrade_levels'],
        calls save_game_state(), update_scaled_values()

    Globals:
        Reads/writes g_game_state
    """
    cost = calculate_upgrade_cost(upgrade_type)
    if cost is None or g_game_state["crystals"] < cost:
        return False

    g_game_state["crystals"] -= cost
    g_game_state["upgrade_levels"][upgrade_type] += 1
    save_game_state()

    update_scaled_values()

    return True


def get_damage_multiplier() -> float:
    """Get current damage multiplier based on upgrades.

    Returns:
        Damage multiplier (1.0 = base damage)

    Globals:
        Reads g_game_state
    """
    return 1.0 + (
        g_game_state["upgrade_levels"].get("damage", 0)
        * Cfg.upgrades["damage"]["multiplier_per_level"]
    )


def get_fire_rate_multiplier() -> float:
    """Get current fire rate multiplier based on upgrades.

    Returns:
        Fire rate multiplier (lower = faster)

    Globals:
        Reads g_game_state
    """
    return 1.0 - (
        g_game_state["upgrade_levels"].get("fire_rate", 0)
        * Cfg.upgrades["fire_rate"]["reduction_per_level"]
    )


def get_speed_multiplier() -> float:
    """Get current speed multiplier based on upgrades.

    Returns:
        Speed multiplier (higher = faster)

    Globals:
        Reads g_game_state
    """
    return 1.0 + (
        g_game_state["upgrade_levels"].get("max_speed", 0)
        * Cfg.upgrades["max_speed"]["multiplier_per_level"]
    )


def get_dash_cooldown_reduction() -> float:
    """Get current dash cooldown reduction based on upgrades.

    Returns:
        Cooldown reduction in frames

    Globals:
        Reads g_game_state
    """
    return (
        g_game_state["upgrade_levels"].get("dash_cooldown", 0)
        * Cfg.upgrades["dash_cooldown"]["reduction_per_level"]
    )


# === [PROGRESSION SYSTEM WRAPPERS] ===
# Temporary compatibility layer during migration


def create_game_context() -> GameContext:
    """Create a game context for the progression system."""
    return GameContext(g_game_state, g_screen_width, g_screen_height)


# Wrapper functions to maintain compatibility during migration
def check_achievement_wrapper(achievement_id: str) -> bool:
    """Wrapper for check_achievement during migration."""
    ctx = create_game_context()
    return g_progression.check_achievement(achievement_id, ctx)


def save_game_state_wrapper() -> bool:
    """Wrapper for save_game_state during migration."""
    ctx = create_game_context()
    return g_progression.save_game_state(ctx)


def load_game_state_wrapper() -> bool:
    """Wrapper for load_game_state during migration."""
    ctx = create_game_context()
    return g_progression.load_game_state(ctx)


def calculate_upgrade_cost_wrapper(upgrade_type: str) -> Optional[int]:
    """Wrapper for calculate_upgrade_cost during migration."""
    ctx = create_game_context()
    return g_progression.calculate_upgrade_cost(upgrade_type, ctx)


def apply_upgrade_wrapper(upgrade_type: str) -> bool:
    """Wrapper for apply_upgrade during migration."""
    ctx = create_game_context()
    return g_progression.apply_upgrade(upgrade_type, ctx)


def get_damage_multiplier_wrapper() -> float:
    """Wrapper for get_damage_multiplier during migration."""
    ctx = create_game_context()
    return g_progression.get_damage_multiplier(ctx)


def get_fire_rate_multiplier_wrapper() -> float:
    """Wrapper for get_fire_rate_multiplier during migration."""
    ctx = create_game_context()
    return g_progression.get_fire_rate_multiplier(ctx)


def get_speed_multiplier_wrapper() -> float:
    """Wrapper for get_speed_multiplier during migration."""
    ctx = create_game_context()
    return g_progression.get_speed_multiplier(ctx)


def get_dash_cooldown_reduction_wrapper() -> float:
    """Wrapper for get_dash_cooldown_reduction during migration."""
    ctx = create_game_context()
    return g_progression.get_dash_cooldown_reduction(ctx)


# === [SOUND SYSTEM] ===
# Sound system functions moved to sound_system.py module

# === [API]: INITIALIZATION ===


def init_ship_state() -> ShipState:
    """Initialize ship state with proper positioning.

    This must be called before any code that accesses g_ship.

    Returns:
        The initialized ShipState object

    Side effects:
        Sets global g_ship to new ShipState

    Globals:
        Writes to g_ship, reads g_screen_width/height
    """
    global g_ship
    g_ship = ShipState(x=g_screen_width // 2, y=g_screen_height // 2)
    return g_ship


def update_scaled_values() -> None:
    """Update all scale-dependent values when resolution changes.

    Side effects:
        Updates g_scale_factor, fonts, clears text cache

    Globals:
        Writes to g_scale_factor, g_font, g_big_font, g_small_font, g_tiny_font
        Reads g_screen_height
    """
    global g_scale_factor, g_font, g_big_font, g_small_font, g_tiny_font, g_drawing

    g_scale_factor = min(2.0, g_screen_height / Cfg.reference_height)

    if pygame.font and pygame.font.get_init():
        g_font = pygame.font.Font(None, int(36 * g_scale_factor))
        g_big_font = pygame.font.Font(None, int(72 * g_scale_factor))
        g_small_font = pygame.font.Font(None, int(24 * g_scale_factor))
        g_tiny_font = pygame.font.Font(None, int(18 * g_scale_factor))
        g_text_cache.clear()

        # Initialize drawing system with fonts
        fonts = {"main": g_font, "big": g_big_font, "small": g_small_font, "tiny": g_tiny_font}
        g_drawing = DrawingSystem(fonts, g_text_cache, lambda: g_scale_factor)


# === [CONTROLLER SYSTEM] ===


def init_controller() -> bool:
    """Initialize game controller if available.

    Returns:
        True if controller connected

    Side effects:
        Sets global g_controller and g_controller_connected

    Globals:
        Writes to g_controller, g_controller_connected
    """
    global g_controller, g_controller_connected

    try:
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()

        if joystick_count > 0:
            g_controller = pygame.joystick.Joystick(0)
            g_controller.init()
            g_controller_connected = True
            print(f"[init_controller] Connected: {g_controller.get_name()}")
            return True
    except pygame.error as e:
        print(f"[init_controller] Failed to initialize: {e}")

    g_controller_connected = False
    return False


def check_controller_connection() -> None:
    """Check if controller was connected or disconnected.

    Side effects:
        May modify g_controller_connected and g_controller globals

    Globals:
        Reads/writes g_controller_connected, g_controller
    """
    global g_controller_connected, g_controller

    try:
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()

        if joystick_count == 0 and g_controller_connected:
            g_controller_connected = False
            g_controller = None
            print("[check_controller_connection] Controller disconnected")
        elif joystick_count > 0 and not g_controller_connected:
            init_controller()
    except:
        pass


def get_controller_input() -> Dict[str, Any]:
    """Get current controller input state.

    Returns:
        Dictionary with turn, thrust, reverse, shoot, dash values

    Globals:
        Reads g_controller_connected, g_controller
    """
    if not g_controller_connected or not g_controller:
        return {"turn": 0, "thrust": False, "reverse": False, "shoot": False, "dash": False}

    try:
        turn = 0
        if g_controller.get_numaxes() >= 1:
            x_axis = g_controller.get_axis(0)
            if abs(x_axis) > Cfg.controller_deadzone:
                turn = x_axis * Cfg.controller_turn_multiplier

        if g_controller.get_numhats() > 0:
            hat = g_controller.get_hat(0)
            if hat[0] != 0:
                turn = hat[0]

        button_states = {"thrust": False, "reverse": False, "shoot": False, "dash": False}

        for action, buttons in Cfg.controller_buttons.items():
            if action in button_states:
                for button in buttons:
                    if g_controller.get_numbuttons() > button and g_controller.get_button(button):
                        button_states[action] = True

        # Check trigger inputs
        if g_controller.get_numaxes() >= 5:
            if g_controller.get_axis(5) > Cfg.controller_axis_threshold:
                button_states["shoot"] = True
        if g_controller.get_numaxes() >= 3 and not button_states["shoot"]:
            if g_controller.get_axis(2) > Cfg.controller_axis_threshold:
                button_states["shoot"] = True

        return {
            "turn": turn,
            "thrust": button_states["thrust"],
            "reverse": button_states["reverse"],
            "shoot": button_states["shoot"],
            "dash": button_states["dash"],
        }
    except pygame.error:
        check_controller_connection()
        return {"turn": 0, "thrust": False, "reverse": False, "shoot": False, "dash": False}


# === [WINDOW MANAGEMENT] ===


def handle_resize(new_width: int, new_height: int) -> None:
    """Handle window resize event.

    Args:
        new_width: New window width
        new_height: New window height

    Side effects:
        Updates g_screen, g_screen_width, g_screen_height, calls update_scaled_values(),
        create_vignette(), create_starfield(), clears particles

    Globals:
        Writes to g_screen, g_screen_width, g_screen_height
    """
    global g_screen, g_screen_width, g_screen_height

    g_screen_width = max(640, new_width)
    g_screen_height = max(480, new_height)

    g_screen = pygame.display.set_mode((g_screen_width, g_screen_height), pygame.RESIZABLE)

    update_scaled_values()

    # Initialize visual effects with context
    ctx = {
        "screen_width": g_screen_width,
        "screen_height": g_screen_height,
        "scale_factor": g_scale_factor,
    }
    vfx.init_visual_effects(ctx)

    g_particle_pool.clear()
    g_game_state["effects"]["level_transition"] = 0


# === [OBJECT CREATION] ===


def create_asteroid(
    x: Optional[float] = None,
    y: Optional[float] = None,
    size: int = 3,
    is_boss: bool = False,
    has_crystals: bool = False,
) -> Asteroid:
    """Create a new asteroid with random properties.

    Args:
        x: X position (None for random edge spawn)
        y: Y position (None for random edge spawn)
        size: Asteroid size (1-3)
        is_boss: Create boss asteroid
        has_crystals: Contains collectible crystals

    Returns:
        New Asteroid object

    Globals:
        Reads g_screen_width, g_screen_height, g_scale_factor
    """
    size = max(Cfg.asteroid_min_size, min(Cfg.asteroid_max_size, size))

    if x is None or y is None:
        margin = int(Cfg.asteroid_spawn_margin * g_scale_factor)
        if random.randint(0, 1):
            if x is None:
                x = random.choice([margin, g_screen_width - margin])
            if y is None:
                y = random.randint(margin, g_screen_height - margin)
        else:
            if x is None:
                x = random.randint(margin, g_screen_width - margin)
            if y is None:
                y = random.choice([margin, g_screen_height - margin])

    # Ensure x and y are never None
    if x is None:
        x = float(g_screen_width // 2)
    if y is None:
        y = float(g_screen_height // 2)

    speed_multiplier = Cfg.asteroid_speed_multiplier - (size * Cfg.asteroid_speed_size_adjustment)
    speed = scaled(Cfg.asteroid_base_speed) * speed_multiplier

    if is_boss:
        speed *= Cfg.boss_speed_multiplier

    angle = random.uniform(0, 360)
    sin_a, cos_a = get_sin_cos(angle)

    radius = size * 10 * g_scale_factor
    if is_boss:
        radius *= Cfg.boss_size_multiplier

    asteroid = Asteroid(
        x=x,
        y=y,
        vx=cos_a * speed,
        vy=sin_a * speed,
        size=size,
        angle=random.uniform(0, 360),
        spin=random.uniform(-3, 3) * (Cfg.boss_rotation_multiplier if is_boss else 1),
        shape=[
            random.randint(Cfg.asteroid_shape_variance_min, Cfg.asteroid_shape_variance_max)
            for _ in range(Cfg.asteroid_vertex_count)
        ],
        radius=radius,
        is_boss=is_boss,
        has_crystals=has_crystals,
        health=Cfg.boss_health if is_boss else 1,
        max_health=Cfg.boss_health if is_boss else 1,
    )

    return asteroid


def create_enemy(x: Optional[float] = None, y: Optional[float] = None) -> Enemy:
    """Create a new enemy at specified or random position.

    Args:
        x: X position (None for random edge spawn)
        y: Y position (None for random edge spawn)

    Returns:
        New Enemy object

    Globals:
        Reads g_ship, g_screen_width, g_screen_height, g_scale_factor
    """
    if x is None or y is None:
        min_spawn_distance = Cfg.enemy_min_spawn_distance * g_scale_factor
        attempts = 0
        while attempts < Cfg.enemy_max_spawn_attempts:
            margin = int(Cfg.enemy_spawn_margin * g_scale_factor)
            if random.randint(0, 1):
                if x is None:
                    x = random.choice([margin, g_screen_width - margin])
                if y is None:
                    y = random.randint(margin, g_screen_height - margin)
            else:
                if x is None:
                    x = random.randint(margin, g_screen_width - margin)
                if y is None:
                    y = random.choice([margin, g_screen_height - margin])

            if g_ship and distance_squared({"x": x, "y": y}, g_ship) >= min_spawn_distance**2:
                break
            attempts += 1

        # Fallback if all attempts failed
        if x is None:
            x = float(g_screen_width - margin)
        if y is None:
            y = float(g_screen_height - margin)

    return Enemy(
        x=x,
        y=y,
        angle=random.uniform(0, 360),
        fire_cooldown=Cfg.enemy_fire_rate
        + random.randint(-Cfg.enemy_fire_rate_variance, Cfg.enemy_fire_rate_variance),
        health=Cfg.enemy_health,
        max_health=Cfg.enemy_health,
        ai_type=random.choice(list(EnemyAIType)),
        orbit_angle=random.uniform(0, 360),
        radius=scaled(Cfg.enemy_radius),
    )


def create_powerup(x: float, y: float, force_type: Optional[PowerUpType] = None) -> None:
    """Create a powerup at specified position.

    Args:
        x: X position
        y: Y position
        force_type: Specific powerup type to create (None for random)

    Side effects:
        Appends to global g_powerups list

    Globals:
        Writes to g_powerups, reads g_screen_width/height, g_scale_factor
    """
    if force_type == PowerUpType.CRYSTAL or (
        force_type is None and random.random() < Cfg.powerup_crystal_chance
    ):
        powerup_type = PowerUpType.CRYSTAL
    elif force_type:
        powerup_type = force_type
    elif random.random() < Cfg.powerup_drop_chance:
        powerup_type = random.choice(
            [PowerUpType.RAPID, PowerUpType.TRIPLE, PowerUpType.SHIELD, PowerUpType.LIFE]
        )
    else:
        return

    # Scale powerup lifetime based on play area
    area_multiplier = (g_screen_width * g_screen_height) / (Cfg.screen_width * Cfg.screen_height)
    lifetime = int(
        Cfg.powerup_lifetime * (1 + (area_multiplier - 1) * Cfg.powerup_area_scaling_factor)
    )

    g_powerups.append(
        PowerUp(
            x=x,
            y=y,
            vx=random.uniform(-1, 1) * g_scale_factor,
            vy=random.uniform(-1, 1) * g_scale_factor,
            type=powerup_type,
            lifetime=lifetime,
        )
    )


# === [PARTICLE EFFECTS] ===


def create_particles(x: float, y: float, config: Dict[str, Any]) -> None:
    """Create particles with specified configuration.

    Args:
        x: Center X position
        y: Center Y position
        config: Dictionary with count, color, speed_range, life_base, life_variance, type

    Side effects:
        Adds particles to g_particle_pool

    Globals:
        Writes to g_particle_pool, reads g_scale_factor
    """
    count = config.get("count", 10)
    color_base = config.get("color", (255, 255, 255))
    speed_range = config.get("speed_range", (0, 8))
    life_base = config.get("life_base", Cfg.particle_base_life)
    life_variance = config.get("life_variance", Cfg.particle_life_variance)
    particle_type = config.get("type", None)

    for _ in range(count):
        speed = random.uniform(*speed_range) * g_scale_factor
        angle = random.uniform(0, 360)
        sin_a, cos_a = get_sin_cos(angle)

        particle = g_particle_pool.get()
        if particle:
            particle.x = x
            particle.y = y
            particle.vx = speed * cos_a
            particle.vy = speed * sin_a
            particle.life = life_base + random.randint(0, life_variance)
            particle.color = color_base
            particle.type = particle_type


def create_explosion(
    x: float,
    y: float,
    count: int = Cfg.particle_explosion_count,
    color_base: Tuple[int, int, int] = (255, 100, 0),
    is_enemy: bool = False,
) -> None:
    """Create explosion effect with particles and sound.

    Args:
        x: Explosion center X
        y: Explosion center Y
        count: Number of particles
        color_base: Base particle color
        is_enemy: True for enemy-specific effects

    Side effects:
        Adds screen shake, plays sound, creates particles

    Globals:
        Writes to g_game_state['effects']['screen_shake'], reads g_ship, g_screen_width/height
    """
    shake_amount = count // 5
    g_game_state["effects"]["screen_shake"] = min(
        g_game_state["effects"]["screen_shake"] + shake_amount, scaled(Cfg.max_screen_shake)
    )

    volume_scale = 1.0
    if count <= 10:
        volume_scale = 0.7
    elif count <= 30:
        volume_scale = 1.0
    else:
        volume_scale = 1.3

    if g_ship:
        distance = math.sqrt(distance_squared({"x": x, "y": y}, g_ship))
        max_distance = math.sqrt(g_screen_width**2 + g_screen_height**2)
        distance_factor = 1.0 - (distance / max_distance) * 0.3
        volume_scale *= distance_factor

    if is_enemy:
        play_sound("enemy_explosion", x, volume_scale)
    elif count <= 10:
        play_sound("explosion_small", x, volume_scale)
    elif count <= 30:
        play_sound("explosion_medium", x, volume_scale)
    else:
        play_sound("explosion_large", x, volume_scale)

    area_factor = min(
        2.0, math.sqrt((g_screen_width * g_screen_height) / (Cfg.screen_width * Cfg.screen_height))
    )
    scaled_count = int(count * (0.7 + 0.3 * area_factor))

    create_particles(
        x,
        y,
        {
            "count": scaled_count,
            "color": color_base,
            "speed_range": (0, 8),
            "type": ParticleType.ENEMY_EXPLOSION if is_enemy else None,
        },
    )


def create_finisher_explosion(x: float, y: float) -> None:
    """Create spectacular finisher explosion effect.

    Args:
        x: Explosion center X
        y: Explosion center Y

    Side effects:
        Creates many particles of different types

    Globals:
        Writes to g_particle_pool, reads g_scale_factor
    """
    # Golden core explosion
    for i in range(Cfg.finisher_particle_count):
        speed = random.uniform(1, 15) * g_scale_factor
        angle = random.uniform(0, 360)
        sin_a, cos_a = get_sin_cos(angle)

        if i < Cfg.finisher_core_particles:
            color = Cfg.colors["gold"]
        elif i < Cfg.finisher_mid_particles:
            color = (255, random.randint(150, 215), 0)
        else:
            color = (255, 255, random.randint(200, 255))

        particle = g_particle_pool.get()
        if particle:
            particle.x = x
            particle.y = y
            particle.vx = speed * cos_a * 0.5
            particle.vy = speed * sin_a * 0.5
            particle.life = Cfg.particle_base_life + random.randint(10, 40)
            particle.color = color
            particle.type = ParticleType.FINISHER

    # Shockwave ring particles
    for i in range(Cfg.particle_shockwave_rings):
        angle = i * (360 / Cfg.particle_shockwave_rings)
        sin_a, cos_a = get_sin_cos(angle)

        for ring in range(Cfg.finisher_ring_count):
            speed = (3 + ring * 2) * g_scale_factor
            particle = g_particle_pool.get()
            if particle:
                particle.x = x
                particle.y = y
                particle.vx = cos_a * speed
                particle.vy = sin_a * speed
                particle.life = 30 - ring * 5
                particle.color = Cfg.colors["gold"] if ring == 0 else (255, 200, 100)
                particle.type = ParticleType.FINISHER


def create_dash_trail() -> None:
    """Create trail particles when dashing.

    Side effects:
        Appends to g_ship.dash_trail, creates particles

    Globals:
        Reads g_ship, writes to g_particle_pool
    """
    if g_ship.dashing <= 0:
        return

    g_ship.dash_trail.append(
        {"x": g_ship.x, "y": g_ship.y, "angle": g_ship.angle, "life": Cfg.particle_dash_trail_life}
    )

    if len(g_ship.dash_trail) > Cfg.dash_trail_max_length:
        g_ship.dash_trail.pop(0)

    for _ in range(Cfg.dash_trail_particle_count):
        offset = (
            random.uniform(-Cfg.dash_trail_offset_range, Cfg.dash_trail_offset_range)
            * g_scale_factor
        )
        sin_a, cos_a = get_sin_cos(g_ship.angle + 90)

        particle = g_particle_pool.get()
        if particle:
            particle.x = g_ship.x + sin_a * offset
            particle.y = g_ship.y + cos_a * offset
            particle.vx = -g_ship.vel_x * 0.3 + random.uniform(-1, 1)
            particle.vy = -g_ship.vel_y * 0.3 + random.uniform(-1, 1)
            particle.life = 15
            particle.color = Cfg.colors["dash"]
            particle.type = ParticleType.DASH


def create_powerup_streak(
    powerup_x: float,
    powerup_y: float,
    target_x: float,
    target_y: float,
    color: Tuple[int, int, int],
) -> None:
    """Create particle streak effect when collecting powerup.

    Args:
        powerup_x: Powerup X position
        powerup_y: Powerup Y position
        target_x: Target X position (usually ship)
        target_y: Target Y position
        color: Streak color

    Side effects:
        Creates particles

    Globals:
        Writes to g_particle_pool, reads g_screen_width/height, g_scale_factor
    """
    dx = target_x - powerup_x
    dy = target_y - powerup_y
    distance = math.sqrt(dx * dx + dy * dy)

    if distance > 0:
        dx /= distance
        dy /= distance

        area_factor = min(
            2.0,
            math.sqrt((g_screen_width * g_screen_height) / (Cfg.screen_width * Cfg.screen_height)),
        )
        particle_count = int(15 * area_factor)

        for i in range(particle_count):
            progress = i / particle_count
            start_x = powerup_x + dx * distance * progress * 0.3
            start_y = powerup_y + dy * distance * progress * 0.3

            spread_angle = random.uniform(-30, 30)
            sin_spread, cos_spread = get_sin_cos(spread_angle)

            vel_x = dx * cos_spread - dy * sin_spread
            vel_y = dx * sin_spread + dy * cos_spread

            speed = (3 + progress * 4) * g_scale_factor

            particle = g_particle_pool.get()
            if particle:
                particle.x = start_x + random.uniform(-5, 5) * g_scale_factor
                particle.y = start_y + random.uniform(-5, 5) * g_scale_factor
                particle.vx = vel_x * speed
                particle.vy = vel_y * speed
                particle.life = 20 + i * 2
                particle.color = color
                particle.type = ParticleType.STREAK

    burst_count = int(8 * min(2.0, area_factor))
    create_particles(
        powerup_x,
        powerup_y,
        {
            "count": burst_count,
            "color": color,
            "speed_range": (1, 3),
            "life_base": 25,
            "life_variance": 0,
            "type": ParticleType.BURST,
        },
    )


def create_thruster_particles() -> None:
    """Create particles from ship thrusters.

    Side effects:
        Creates particles

    Globals:
        Reads g_ship, writes to g_particle_pool
    """
    sin_a, cos_a = get_sin_cos(g_ship.angle)
    base_x = g_ship.x - scaled(Cfg.ship_nose_length * 0.8) * cos_a
    base_y = g_ship.y - scaled(Cfg.ship_nose_length * 0.8) * sin_a

    for _ in range(Cfg.particle_thruster_count):
        particle = g_particle_pool.get()
        if particle:
            particle.x = base_x + random.randint(
                -Cfg.particle_thruster_spread, Cfg.particle_thruster_spread
            )
            particle.y = base_y + random.randint(
                -Cfg.particle_thruster_spread, Cfg.particle_thruster_spread
            )
            particle.vx = -cos_a * Cfg.particle_thruster_speed * g_scale_factor + random.uniform(
                -Cfg.particle_thruster_velocity_spread, Cfg.particle_thruster_velocity_spread
            )
            particle.vy = -sin_a * Cfg.particle_thruster_speed * g_scale_factor + random.uniform(
                -Cfg.particle_thruster_velocity_spread, Cfg.particle_thruster_velocity_spread
            )
            particle.life = 20
            particle.color = (255, 200, 0)
            particle.type = None


def create_respawn_particles() -> None:
    """Create particles during ship respawn animation.

    Side effects:
        Creates particles

    Globals:
        Reads g_ship, writes to g_particle_pool
    """
    # Inward spiral particles
    for _ in range(Cfg.particle_respawn_rate):
        angle = random.uniform(0, 360)
        distance = (
            random.uniform(Cfg.particle_respawn_spiral_min, Cfg.particle_respawn_spiral_max)
            * g_scale_factor
        )
        sin_a, cos_a = get_sin_cos(angle)

        particle = g_particle_pool.get()
        if particle:
            particle.x = g_ship.x + cos_a * distance
            particle.y = g_ship.y + sin_a * distance
            particle.vx = -cos_a * 2 * g_scale_factor + random.uniform(-0.5, 0.5)
            particle.vy = -sin_a * 2 * g_scale_factor + random.uniform(-0.5, 0.5)
            particle.life = 30
            particle.color = Cfg.colors["blue_glow"]
            particle.type = ParticleType.RESPAWN

        # Occasional center sparkle
        if random.random() < Cfg.particle_respawn_center_chance:
            particle = g_particle_pool.get()
            if particle:
                particle.x = (
                    g_ship.x
                    + random.uniform(
                        -Cfg.particle_respawn_center_spread, Cfg.particle_respawn_center_spread
                    )
                    * g_scale_factor
                )
                particle.y = (
                    g_ship.y
                    + random.uniform(
                        -Cfg.particle_respawn_center_spread, Cfg.particle_respawn_center_spread
                    )
                    * g_scale_factor
                )
                particle.vx = random.uniform(-1, 1) * g_scale_factor
                particle.vy = random.uniform(-1, 1) * g_scale_factor
                particle.life = 20
                particle.color = (150, 200, 255)
                particle.type = ParticleType.RESPAWN


# === [COMBAT MECHANICS] ===


def shoot_bullet(
    is_enemy: bool = False, enemy_x: float = 0.0, enemy_y: float = 0.0, enemy_angle: float = 0.0
) -> None:
    """Fire a bullet from ship or enemy.

    Args:
        is_enemy: True if enemy is shooting
        enemy_x: Enemy X position
        enemy_y: Enemy Y position
        enemy_angle: Enemy angle

    Side effects:
        Appends to g_bullets or g_enemy_bullets, plays sound, creates particles,
        sets g_game_state['bullet_cooldown']

    Globals:
        Reads g_ship, writes to g_bullets, g_enemy_bullets, g_game_state, g_particle_pool
    """
    if is_enemy:
        play_sound("enemy_shoot", enemy_x, 0.7)
        sin_a, cos_a = get_sin_cos(enemy_angle)

        g_enemy_bullets.append(
            Bullet(
                x=enemy_x + scaled(Cfg.ship_nose_length) * cos_a,
                y=enemy_y + scaled(Cfg.ship_nose_length) * sin_a,
                vx=cos_a * scaled(Cfg.bullet_speed) * Cfg.enemy_bullet_speed_mult,
                vy=sin_a * scaled(Cfg.bullet_speed) * Cfg.enemy_bullet_speed_mult,
                life=Cfg.bullet_lifetime,
            )
        )
    else:
        play_sound("shoot", g_ship.x, 1.0, g_screen_width)

        sin_a, cos_a = get_sin_cos(g_ship.angle)
        flash_x = g_ship.x + scaled(Cfg.ship_nose_length) * cos_a
        flash_y = g_ship.y + scaled(Cfg.ship_nose_length) * sin_a

        # Muzzle flash particles
        particle_count = (
            Cfg.particle_muzzle_flash_triple
            if g_ship.triple_shot > 0
            else Cfg.particle_muzzle_flash_base
        )
        for _ in range(particle_count):
            angle = g_ship.angle + random.uniform(-15, 15)
            sin_p, cos_p = get_sin_cos(angle)
            particle = g_particle_pool.get()
            if particle:
                particle.x = flash_x
                particle.y = flash_y
                particle.vx = cos_p * 3 * g_scale_factor + random.uniform(-1, 1)
                particle.vy = sin_p * 3 * g_scale_factor + random.uniform(-1, 1)
                particle.life = 10
                particle.color = (255, 255, 150) if g_ship.rapid_fire > 0 else (255, 200, 100)
                particle.type = None

        if g_ship.triple_shot > 0:
            for angle_offset in [-Cfg.triple_shot_spread, 0, Cfg.triple_shot_spread]:
                angle = g_ship.angle + angle_offset
                sin_a, cos_a = get_sin_cos(angle)

                g_bullets.append(
                    Bullet(
                        x=g_ship.x + scaled(Cfg.ship_nose_length) * cos_a,
                        y=g_ship.y + scaled(Cfg.ship_nose_length) * sin_a,
                        vx=cos_a * scaled(Cfg.bullet_speed),
                        vy=sin_a * scaled(Cfg.bullet_speed),
                        life=Cfg.bullet_lifetime,
                    )
                )
        else:
            sin_a, cos_a = get_sin_cos(g_ship.angle)
            g_bullets.append(
                Bullet(
                    x=g_ship.x + scaled(Cfg.ship_nose_length) * cos_a,
                    y=g_ship.y + scaled(Cfg.ship_nose_length) * sin_a,
                    vx=cos_a * scaled(Cfg.bullet_speed),
                    vy=sin_a * scaled(Cfg.bullet_speed),
                    life=Cfg.bullet_lifetime,
                )
            )

        fire_rate_mult = get_fire_rate_multiplier_wrapper()
        base_rate = Cfg.rapid_fire_rate if g_ship.rapid_fire > 0 else Cfg.normal_fire_rate
        g_game_state["bullet_cooldown"] = int(base_rate * fire_rate_mult)


def add_combo() -> None:
    """Add to combo counter and trigger related effects.

    Side effects:
        Modifies g_game_state['combo'], g_game_state['finisher'],
        creates floating text, plays sound, adds screen shake

    Globals:
        Reads/writes g_game_state, reads g_ship, writes to g_floating_texts
    """
    combo = g_game_state["combo"]
    finisher = g_game_state["finisher"]

    if combo["current"] == 0:
        combo["kills"] = 0

    combo["current"] += 1
    combo["timer"] = Cfg.combo_timeout
    combo["kills"] += 1

    if not finisher["ready"]:
        # Determine fill rate based on combo level
        if combo["current"] >= Cfg.combo_high_threshold:
            fill_rate = Cfg.combo_fill_rates["high"]
        elif combo["current"] >= Cfg.combo_medium_threshold:
            fill_rate = Cfg.combo_fill_rates["medium"]
        else:
            fill_rate = Cfg.combo_fill_rates["base"]

        finisher["meter"] = min(100.0, finisher["meter"] + fill_rate)
        if finisher["meter"] >= 100.0:
            finisher["ready"] = True
            play_sound("powerup_life", g_ship.x, 0.5)

    check_achievement_wrapper("combo_5")
    check_achievement_wrapper("combo_10")

    if combo["current"] >= Cfg.combo_text_threshold:
        create_floating_text(
            g_ship.x, g_ship.y - 30, f"COMBO x{combo['current']}!", Cfg.colors["gold"]
        )

        if (
            combo["kills"] % Cfg.combo_pulse_interval == 0
            and combo["current"] >= Cfg.combo_text_threshold
        ):
            combo["pulse"] = min(Cfg.combo_max_pulse, combo["current"] * 2)
            g_game_state["effects"]["screen_shake"] = min(
                g_game_state["effects"]["screen_shake"] + 8, scaled(Cfg.max_screen_shake)
            )
            play_sound("powerup_life", g_ship.x, 0.8)
            create_floating_text(g_ship.x, g_ship.y + 20, "10TH KILL!", (255, 255, 100))

        elif combo["current"] in Cfg.combo_milestone_thresholds:
            g_game_state["effects"]["screen_shake"] = min(
                g_game_state["effects"]["screen_shake"] + 5, scaled(Cfg.max_screen_shake)
            )
            play_sound("powerup_life", g_ship.x, 0.6)


# === [FINISHER MECHANICS] ===


def check_finisher_collision(ship_pos: ShipState, dash_angle: float) -> Optional[Enemy]:
    """Check if a dash would hit an enemy for finisher execution.

    Args:
        ship_pos: Ship state
        dash_angle: Dash direction angle

    Returns:
        Enemy that would be hit or None

    Globals:
        Reads g_enemies
    """
    sin_a, cos_a = get_sin_cos(dash_angle)
    dash_distance = scaled(Cfg.ship_max_speed) * Cfg.dash_speed_multiplier * Cfg.dash_duration

    start_x, start_y = ship_pos.x, ship_pos.y
    end_x = start_x + cos_a * dash_distance
    end_y = start_y + sin_a * dash_distance

    closest_enemy = None
    min_t = float("inf")

    for enemy in g_enemies:
        dx = enemy.x - start_x
        dy = enemy.y - start_y

        dash_dx = end_x - start_x
        dash_dy = end_y - start_y

        dash_length_sq = dash_dx * dash_dx + dash_dy * dash_dy
        if dash_length_sq == 0:
            continue

        t = (dx * dash_dx + dy * dash_dy) / dash_length_sq
        t = max(0, min(1, t))

        closest_x = start_x + t * dash_dx
        closest_y = start_y + t * dash_dy

        dist_x = enemy.x - closest_x
        dist_y = enemy.y - closest_y
        dist_sq = dist_x * dist_x + dist_y * dist_y

        collision_radius = enemy.radius + scaled(Cfg.ship_radius)

        if dist_sq <= collision_radius * collision_radius and t < min_t:
            min_t = t
            closest_enemy = enemy

    return closest_enemy


def start_finisher_execution(target: Enemy) -> None:
    """Begin finisher move execution sequence.

    Args:
        target: Enemy to execute

    Side effects:
        Modifies g_game_state['finisher'], g_ship.angle, g_ship.invulnerable,
        g_game_state['time_scale'], plays sound

    Globals:
        Writes to g_game_state, g_ship
    """
    finisher_state = g_game_state["finisher"]

    finisher_state["executing"] = True
    finisher_state["phase"] = FinisherPhase.LOCK_ON
    finisher_state["execution_timer"] = Cfg.finisher_lock_on_time
    finisher_state["target"] = target
    finisher_state["lock_on_progress"] = 0.0

    dx = target.x - g_ship.x
    dy = target.y - g_ship.y
    angle_to_target = math.degrees(math.atan2(dy, dx))
    g_ship.angle = angle_to_target

    sin_a, cos_a = get_sin_cos(g_ship.angle)
    dash_distance = scaled(Cfg.ship_max_speed) * Cfg.dash_speed_multiplier * Cfg.dash_duration
    finisher_state["impact_x"] = g_ship.x + cos_a * dash_distance / 2
    finisher_state["impact_y"] = g_ship.y + sin_a * dash_distance / 2

    total_finisher_frames = (
        Cfg.finisher_lock_on_time
        + Cfg.finisher_pre_impact_time
        + Cfg.finisher_impact_time
        + Cfg.finisher_post_impact_time
    )
    invuln_duration = total_finisher_frames + int(Cfg.finisher_invuln_buffer * Cfg.fps)
    g_ship.invulnerable = max(g_ship.invulnerable, invuln_duration)

    g_game_state["time_scale"] = Cfg.finisher_lock_on_scale

    play_sound("powerup_shield", g_ship.x, 0.8)


def update_finisher() -> None:
    """Update finisher execution state machine.

    Side effects:
        Modifies g_game_state['finisher'], g_game_state['time_scale'], g_ship.dashing,
        g_game_state['score'], g_game_state['dash']['cooldown'], g_game_state['combo']['timer'],
        g_game_state['effects']['screen_shake'], g_game_state['effects']['damage_flash'],
        removes enemies, creates particles and floating text

    Globals:
        Reads/writes g_game_state, g_ship, g_enemies
    """
    finisher_state = g_game_state["finisher"]

    if not finisher_state["executing"]:
        return

    finisher_state["execution_timer"] -= 1

    if finisher_state["execution_timer"] <= 0:
        if finisher_state["phase"] == FinisherPhase.LOCK_ON:
            # Transition to pre-impact
            finisher_state["phase"] = FinisherPhase.PRE_IMPACT
            finisher_state["execution_timer"] = Cfg.finisher_pre_impact_time

            finisher_state["meter"] = 0.0
            finisher_state["ready"] = False

            total_finisher_frames = (
                Cfg.finisher_pre_impact_time
                + Cfg.finisher_impact_time
                + Cfg.finisher_post_impact_time
            )
            g_ship.dashing = total_finisher_frames

            play_sound("dash", g_ship.x, 1.2)

        elif finisher_state["phase"] == FinisherPhase.PRE_IMPACT:
            # Transition to impact
            finisher_state["phase"] = FinisherPhase.IMPACT
            finisher_state["execution_timer"] = Cfg.finisher_impact_time

            g_game_state["time_scale"] = Cfg.finisher_time_scale

            target = finisher_state["target"]
            if target and target in g_enemies:
                create_finisher_explosion(target.x, target.y)
                create_floating_text(target.x, target.y - 30, "EXECUTED!", Cfg.colors["gold"])

                finisher_state["impact_x"] = target.x
                finisher_state["impact_y"] = target.y

                g_game_state["effects"]["screen_shake"] = 30
                g_game_state["effects"]["damage_flash"] = 20
                g_game_state["effects"]["damage_flash_color"] = (255, 255, 255)

                play_sound("explosion_large", target.x, Cfg.finisher_volume * 1.5)

                finisher_state["shockwave_radius"] = 10 * g_scale_factor

                g_game_state["score"] += Cfg.finisher_score
                g_game_state["dash"]["cooldown"] = 0
                create_powerup(target.x, target.y, PowerUpType.CRYSTAL)

                g_game_state["combo"]["timer"] = Cfg.combo_timeout

                g_enemies.remove(target)

        elif finisher_state["phase"] == FinisherPhase.IMPACT:
            # Update shockwave
            max_radius = Cfg.finisher_shockwave_radius * g_scale_factor
            progress = 1.0 - (finisher_state["execution_timer"] / Cfg.finisher_impact_time)
            finisher_state["shockwave_radius"] = (
                10 * g_scale_factor + (max_radius - 10 * g_scale_factor) * progress
            )

            # Apply damage at specific points
            damage_points = [0.3, 0.6]
            for dmg_point in damage_points:
                if dmg_point <= progress < dmg_point + 0.02:
                    apply_shockwave_damage(
                        finisher_state["impact_x"],
                        finisher_state["impact_y"],
                        finisher_state["shockwave_radius"],
                    )

            if finisher_state["execution_timer"] <= 1:
                finisher_state["phase"] = FinisherPhase.POST_IMPACT
                finisher_state["execution_timer"] = Cfg.finisher_post_impact_time
                g_game_state["time_scale"] = 1.0

        elif finisher_state["phase"] == FinisherPhase.POST_IMPACT:
            # Cleanup
            finisher_state["executing"] = False
            finisher_state["phase"] = FinisherPhase.IDLE
            finisher_state["target"] = None
            finisher_state["shockwave_radius"] = 0
            finisher_state["lock_on_progress"] = 0.0
            g_ship.dashing = 0

    if finisher_state["phase"] == FinisherPhase.LOCK_ON:
        finisher_state["lock_on_progress"] = 1.0 - (
            finisher_state["execution_timer"] / Cfg.finisher_lock_on_time
        )


def apply_shockwave_damage(x: float, y: float, radius: float) -> None:
    """Apply damage to enemies within shockwave radius.

    Args:
        x: Shockwave center X
        y: Shockwave center Y
        radius: Shockwave radius

    Side effects:
        Modifies enemy health and velocity, removes dead enemies,
        creates explosions, adds score and combo

    Globals:
        Reads/writes g_enemies, g_game_state
    """
    for enemy in g_enemies[:]:
        dist_sq = distance_squared({"x": x, "y": y}, enemy)

        if dist_sq < radius * radius:
            dist = math.sqrt(dist_sq)

            damage = (
                Cfg.finisher_damage_close
                if dist < radius * Cfg.finisher_shockwave_close_range
                else Cfg.finisher_damage_far
            )
            enemy.health -= damage
            enemy.hit_flash = Cfg.asteroid_hit_flash_duration

            if dist > 0:
                knockback_force = (
                    (1 - dist / radius) * Cfg.finisher_knockback_force * g_scale_factor
                )
                dx = enemy.x - x
                dy = enemy.y - y
                enemy.vx += (dx / dist) * knockback_force
                enemy.vy += (dy / dist) * knockback_force

            if enemy.health <= 0:
                g_enemies.remove(enemy)
                create_explosion(enemy.x, enemy.y, 20, Cfg.colors["enemy"], True)
                g_game_state["score"] += Cfg.enemy_score
                add_combo()


# === [COLLISION DETECTION] ===


def is_ship_vulnerable() -> bool:
    """Check if ship can take damage.

    Returns:
        True if ship is vulnerable

    Globals:
        Reads g_ship
    """
    return g_ship.invulnerable == 0 and g_ship.dashing == 0


def handle_collisions() -> None:
    """Main collision handling routine.

    Side effects:
        Calls various collision handling functions
    """
    handle_bullet_collisions()
    handle_ship_collisions_if_vulnerable()
    handle_powerup_collisions()


def handle_bullet_collisions() -> None:
    """Handle all bullet-related collisions.

    Side effects:
        Removes bullets, asteroids, enemies; creates explosions and powerups;
        updates score and combo

    Globals:
        Reads/writes g_bullets, g_asteroids, g_enemies
    """
    global g_bullets, g_asteroids, g_enemies

    bullets_to_remove = set()
    asteroids_to_remove = set()
    asteroids_to_add = []
    enemies_to_remove = set()

    # --- [Bullet-asteroid collisions] ---
    for i, bullet in enumerate(g_bullets):
        if i in bullets_to_remove:
            continue

        for j, asteroid in enumerate(g_asteroids):
            if j in asteroids_to_remove:
                continue

            margin = scaled(Cfg.asteroid_collision_margin)
            if check_collision(
                bullet, asteroid, scaled(Cfg.bullet_radius), asteroid.radius + margin
            ):
                bullets_to_remove.add(i)
                handle_asteroid_hit(asteroid, j, asteroids_to_remove, asteroids_to_add)
                break

    # --- [Bullet-enemy collisions] ---
    for i, bullet in enumerate(g_bullets):
        if i in bullets_to_remove:
            continue

        for j, enemy in enumerate(g_enemies):
            if j in enemies_to_remove:
                continue

            if check_collision(bullet, enemy, scaled(Cfg.bullet_radius), enemy.radius):
                bullets_to_remove.add(i)
                handle_enemy_hit(enemy, j, enemies_to_remove)
                break

    g_bullets = [b for i, b in enumerate(g_bullets) if i not in bullets_to_remove]
    g_asteroids = [a for i, a in enumerate(g_asteroids) if i not in asteroids_to_remove]
    g_asteroids.extend(asteroids_to_add)
    g_enemies = [e for i, e in enumerate(g_enemies) if i not in enemies_to_remove]


def handle_ship_collisions_if_vulnerable() -> None:
    """Handle collisions with ship if it's vulnerable.

    Side effects:
        Calls collision check functions if ship is vulnerable
    """
    if is_ship_vulnerable():
        handle_ship_asteroid_collisions()
        handle_ship_enemy_collisions()
        handle_ship_bullet_collisions()


def handle_ship_asteroid_collisions() -> None:
    """Check for ship-asteroid collisions.

    Side effects:
        May call handle_ship_damage()

    Globals:
        Reads g_ship, g_asteroids
    """
    for asteroid in g_asteroids:
        margin = scaled(Cfg.asteroid_collision_margin)
        if check_collision(g_ship, asteroid, scaled(Cfg.ship_radius), asteroid.radius + margin):
            if handle_ship_damage():
                break


def handle_ship_enemy_collisions() -> None:
    """Check for ship-enemy collisions.

    Side effects:
        Removes enemies, creates explosions, calls handle_ship_damage()

    Globals:
        Reads g_ship, reads/writes g_enemies
    """
    global g_enemies
    enemies_to_remove = []

    for i, enemy in enumerate(g_enemies):
        if check_collision(g_ship, enemy, scaled(Cfg.ship_radius), enemy.radius):
            enemies_to_remove.append(i)
            create_explosion(enemy.x, enemy.y, 20, Cfg.colors["enemy"], is_enemy=True)
            if handle_ship_damage():
                break

    g_enemies = [e for i, e in enumerate(g_enemies) if i not in enemies_to_remove]


def handle_ship_bullet_collisions() -> None:
    """Check for ship-enemy bullet collisions.

    Side effects:
        Removes enemy bullets, calls handle_ship_damage()

    Globals:
        Reads g_ship, reads/writes g_enemy_bullets
    """
    global g_enemy_bullets
    enemy_bullets_to_remove = set()

    for i, bullet in enumerate(g_enemy_bullets):
        if check_collision(g_ship, bullet, scaled(Cfg.ship_radius), scaled(Cfg.bullet_radius) * 2):
            enemy_bullets_to_remove.add(i)
            if handle_ship_damage():
                break

    g_enemy_bullets = [b for i, b in enumerate(g_enemy_bullets) if i not in enemy_bullets_to_remove]


def handle_asteroid_hit(asteroid: Asteroid, index: int, to_remove: set, to_add: list) -> None:
    """Handle asteroid being hit by bullet.

    Args:
        asteroid: Asteroid that was hit
        index: Index in asteroid list
        to_remove: Set to add removal indices to
        to_add: List to add new asteroids to

    Side effects:
        Modifies asteroid health/flash, adds to removal lists, creates explosions,
        updates score and combo, creates powerups and new asteroids, spawns enemies

    Globals:
        Reads/writes g_game_state, g_enemies
    """
    damage = int(get_damage_multiplier_wrapper())

    if asteroid.is_boss:
        asteroid.health -= max(1, damage)
        asteroid.hit_flash = Cfg.asteroid_hit_flash_duration

        if asteroid.health <= 0:
            to_remove.add(index)
            create_explosion(asteroid.x, asteroid.y, 60, Cfg.colors["boss"])
            g_game_state["score"] += Cfg.boss_score
            add_combo()
            create_floating_text(asteroid.x, asteroid.y, f"+{Cfg.boss_score}", Cfg.colors["gold"])

            for _ in range(Cfg.boss_crystal_drops):
                create_powerup(
                    asteroid.x + random.uniform(-50, 50) * g_scale_factor,
                    asteroid.y + random.uniform(-50, 50) * g_scale_factor,
                    PowerUpType.CRYSTAL,
                )

            g_game_state["boss_kills"] += 1
            check_achievement_wrapper("boss_slayer")
    else:
        if asteroid.size > 1:
            asteroid.hit_flash = Cfg.asteroid_hit_flash_duration
        else:
            to_remove.add(index)

        explosion_color, particle_count = Cfg.explosion_config[asteroid.size]

        create_explosion(asteroid.x, asteroid.y, particle_count, explosion_color)

        if asteroid.has_crystals:
            create_powerup(asteroid.x, asteroid.y, PowerUpType.CRYSTAL)
        else:
            create_powerup(asteroid.x, asteroid.y)

        base_score = Cfg.asteroid_scores[asteroid.size]
        combo_multiplier = 1 + g_game_state["combo"]["current"] * 0.1
        score_value = int(base_score * combo_multiplier)
        g_game_state["score"] += score_value
        add_combo()

        if g_game_state["score"] > g_game_state.get("high_score", 0):
            g_game_state["high_score"] = g_game_state["score"]

        create_floating_text(asteroid.x, asteroid.y, f"+{score_value}")

        if asteroid.size > 1:
            for _ in range(Cfg.asteroid_split_count):
                new_asteroid = create_asteroid(asteroid.x, asteroid.y, asteroid.size - 1)
                to_add.append(new_asteroid)
            to_remove.add(index)

        if random.random() < Cfg.enemy_spawn_chance and len(g_enemies) < Cfg.enemy_max_count:
            g_enemies.append(create_enemy())

    check_achievement_wrapper("first_blood")


def handle_enemy_hit(enemy: Enemy, index: int, to_remove: set) -> None:
    """Handle enemy being hit by bullet.

    Args:
        enemy: Enemy that was hit
        index: Index in enemy list
        to_remove: Set to add removal indices to

    Side effects:
        Modifies enemy health/flash, removes enemy, creates explosion and powerup,
        updates score and combo

    Globals:
        Reads/writes g_game_state
    """
    damage = int(get_damage_multiplier_wrapper())
    enemy.health -= max(1, damage)
    enemy.hit_flash = Cfg.asteroid_hit_flash_duration

    if enemy.health <= 0:
        to_remove.add(index)
        create_explosion(enemy.x, enemy.y, 25, Cfg.colors["enemy"], is_enemy=True)
        g_game_state["score"] += Cfg.enemy_score
        add_combo()
        create_floating_text(enemy.x, enemy.y, f"+{Cfg.enemy_score}", Cfg.colors["enemy"])

        if random.random() < Cfg.enemy_crystal_drop_chance:
            create_powerup(enemy.x, enemy.y, PowerUpType.CRYSTAL)
        else:
            create_powerup(enemy.x, enemy.y)


def handle_ship_damage() -> bool:
    """Handle ship taking damage.

    Returns:
        True if damage was fatal

    Side effects:
        Modifies g_ship.shield_active, g_game_state['lives'], g_game_state['effects']['damage_flash'],
        g_game_state['effects']['screen_shake'], g_game_state['untouchable_level'],
        g_game_state['game_over'], creates explosions, plays sound, calls reset_ship()

    Globals:
        Reads/writes g_ship, g_game_state
    """
    if g_ship.shield_active > 0:
        g_ship.shield_active = 0
        g_game_state["effects"]["damage_flash"] = Cfg.shield_flash_duration
        g_game_state["effects"]["damage_flash_color"] = Cfg.colors["shield_flash"]
        g_game_state["effects"]["screen_shake"] = min(
            g_game_state["effects"]["screen_shake"] + 10, scaled(Cfg.max_screen_shake)
        )
        create_explosion(g_ship.x, g_ship.y, 20, (0, 200, 255))
        play_sound("explosion_medium", g_ship.x, 0.8)
        return False
    else:
        g_game_state["lives"] -= 1
        g_game_state["untouchable_level"] = False
        g_game_state["effects"]["damage_flash"] = Cfg.damage_flash_duration
        g_game_state["effects"]["damage_flash_color"] = Cfg.colors["damage_flash"]

        create_explosion(g_ship.x, g_ship.y, Cfg.particle_ship_explosion, (255, 100, 0))
        create_explosion(g_ship.x, g_ship.y, 10, (255, 255, 200))

        if g_game_state["lives"] <= 0:
            g_game_state["game_over"] = True
            stop_all_sounds()
            return True
        else:
            reset_ship()
            return True


def handle_powerup_collisions() -> None:
    """Handle ship collecting powerups.

    Side effects:
        Removes powerups, creates particles and floating text, applies powerup effects,
        updates score and crystals

    Globals:
        Reads g_ship, reads/writes g_powerups, g_game_state
    """
    global g_powerups
    powerups_to_remove = []

    for i, powerup in enumerate(g_powerups):
        if check_collision(
            g_ship, powerup, scaled(Cfg.powerup_pickup_radius), scaled(Cfg.powerup_visual_radius)
        ):
            powerups_to_remove.append(i)

            powerup_color = Cfg.powerup_types[powerup.type]["color"]
            create_powerup_streak(powerup.x, powerup.y, g_ship.x, g_ship.y, powerup_color)

            apply_powerup(powerup.type)

            if powerup.type == PowerUpType.CRYSTAL:
                value = Cfg.powerup_crystal_value
                g_game_state["crystals"] += value
                g_game_state["lifetime_crystals"] += value
                create_floating_text(powerup.x, powerup.y, f"+{value} ◆", Cfg.colors["crystal"])
                check_achievement_wrapper("crystal_hoarder")
            else:
                g_game_state["score"] += 50
                if g_game_state["score"] > g_game_state.get("high_score", 0):
                    g_game_state["high_score"] = g_game_state["score"]
                create_floating_text(powerup.x, powerup.y, "+50", powerup_color)

    g_powerups = [p for i, p in enumerate(g_powerups) if i not in powerups_to_remove]


# === [LLM EXTENSION POINT: Add new powerup effects here] ===
POWERUP_EFFECTS = {
    PowerUpType.RAPID: lambda: setattr(g_ship, "rapid_fire", Cfg.powerup_rapid_fire_duration),
    PowerUpType.TRIPLE: lambda: setattr(g_ship, "triple_shot", Cfg.powerup_triple_shot_duration),
    PowerUpType.SHIELD: lambda: setattr(g_ship, "shield_active", Cfg.powerup_shield_duration),
    PowerUpType.LIFE: lambda: handle_life_powerup(),
}


def apply_powerup(powerup_type: PowerUpType) -> None:
    """Apply effect of collected powerup using lookup table.

    Args:
        powerup_type: Type of powerup collected

    Side effects:
        Modifies g_ship powerup timers, g_game_state['lives'], g_game_state['effects']['screen_shake'],
        plays sound

    Globals:
        Reads/writes g_ship, g_game_state
    """
    if powerup_type == PowerUpType.CRYSTAL:
        play_sound("powerup_crystal", g_ship.x)
    else:
        play_sound(f"powerup_{powerup_type.value}", g_ship.x)

    g_ship.powerup_flash = Cfg.particle_powerup_flash_duration
    g_ship.powerup_flash_color = Cfg.powerup_types[powerup_type]["color"]
    g_game_state["effects"]["screen_shake"] = min(
        g_game_state["effects"]["screen_shake"] + 3, scaled(Cfg.max_screen_shake)
    )

    # Apply powerup effect using lookup table
    if powerup_type in POWERUP_EFFECTS:
        POWERUP_EFFECTS[powerup_type]()


def handle_life_powerup() -> None:
    """Handle collecting life powerup.

    Side effects:
        Modifies g_game_state['lives'], g_ship.powerup_flash, g_game_state['effects']['screen_shake']

    Globals:
        Reads/writes g_game_state, g_ship
    """
    g_game_state["lives"] = min(g_game_state["lives"] + 1, Cfg.ship_max_lives)
    g_ship.powerup_flash = Cfg.particle_powerup_flash_max
    g_game_state["effects"]["screen_shake"] = min(
        g_game_state["effects"]["screen_shake"] + 5, scaled(Cfg.max_screen_shake)
    )


# === [MOVEMENT AND PHYSICS] ===


def update_entity_physics(entity: Any, config: Dict[str, Any]) -> None:
    """Update physics for any game entity.

    Args:
        entity: Game object to update
        config: Dictionary with 'wrap' key for screen wrapping

    Side effects:
        Modifies entity position, angle, hit_flash

    Globals:
        Reads g_game_state['time_scale']
    """
    if hasattr(entity, "vx"):
        entity.x += entity.vx * g_game_state["time_scale"]
        entity.y += entity.vy * g_game_state["time_scale"]
    elif hasattr(entity, "vel_x"):
        entity.x += entity.vel_x * g_game_state["time_scale"]
        entity.y += entity.vel_y * g_game_state["time_scale"]

    if config.get("wrap", True):
        wrap_position(entity)

    if hasattr(entity, "angle") and hasattr(entity, "spin"):
        entity.angle += entity.spin * g_game_state["time_scale"]

    if hasattr(entity, "hit_flash") and entity.hit_flash > 0:
        entity.hit_flash = update_timer(entity.hit_flash)


def apply_friction(entity: Any, friction_value: float) -> None:
    """Apply friction to entity velocity.

    Args:
        entity: Object with velocity
        friction_value: Friction coefficient (0-1)

    Side effects:
        Modifies entity velocity

    Globals:
        Reads g_game_state['time_scale']
    """
    friction_factor = friction_value ** g_game_state["time_scale"]

    if hasattr(entity, "vx"):
        entity.vx *= friction_factor
        entity.vy *= friction_factor
    elif hasattr(entity, "vel_x"):
        entity.vel_x *= friction_factor
        entity.vel_y *= friction_factor


def apply_speed_limit(entity: Any, max_speed: float) -> None:
    """Limit entity speed to maximum value.

    Args:
        entity: Object with velocity
        max_speed: Maximum allowed speed

    Side effects:
        Modifies entity velocity to enforce speed limit
    """
    if hasattr(entity, "vx"):
        speed_sq = entity.vx**2 + entity.vy**2
        if speed_sq > max_speed**2:
            speed = math.sqrt(speed_sq)
            entity.vx = (entity.vx / speed) * max_speed
            entity.vy = (entity.vy / speed) * max_speed
    elif hasattr(entity, "vel_x"):
        speed_sq = entity.vel_x**2 + entity.vel_y**2
        if speed_sq > max_speed**2:
            speed = math.sqrt(speed_sq)
            entity.vel_x = (entity.vel_x / speed) * max_speed
            entity.vel_y = (entity.vel_y / speed) * max_speed


def update_ship(keys: dict, controller_input: Dict[str, Any]) -> None:
    """Update ship movement and state.

    Args:
        keys: Pygame keyboard state
        controller_input: Controller input state

    Side effects:
        Modifies ship position, velocity, angle, and various timers;
        creates particles; plays/stops sounds

    Globals:
        Reads/writes g_ship, g_game_state, g_sounds
    """
    if g_game_state["game_over"]:
        return

    if g_ship.respawning > 0:
        g_ship.respawning -= 1
        create_respawn_particles()
        return

    # --- [Dash handling] ---
    if g_ship.dashing > 0:
        if g_game_state["finisher"]["executing"]:
            g_ship.dashing -= 1
        else:
            g_ship.dashing = update_timer(g_ship.dashing)
        create_dash_trail()

        sin_a, cos_a = get_sin_cos(g_ship.angle)
        g_ship.vel_x = cos_a * scaled(Cfg.ship_max_speed) * Cfg.dash_speed_multiplier
        g_ship.vel_y = sin_a * scaled(Cfg.ship_max_speed) * Cfg.dash_speed_multiplier

        g_ship.invulnerable = max(g_ship.invulnerable, g_ship.dashing)
    else:
        # --- [Normal movement] ---
        turn_input = 0
        if keys[pygame.K_LEFT]:
            turn_input -= 1
        if keys[pygame.K_RIGHT]:
            turn_input += 1

        turn_input += controller_input["turn"]
        turn_input = max(-2, min(2, turn_input))
        g_ship.angle += turn_input * Cfg.ship_turn_speed * g_game_state["time_scale"]
        g_ship.angle = g_ship.angle % 360

        sin_a, cos_a = get_sin_cos(g_ship.angle)
        thrust = 0

        if keys[pygame.K_UP] or controller_input["thrust"]:
            thrust = Cfg.ship_thrust_power
            create_thruster_particles()

            if (
                get_sound_enabled()
                and "thrust" in sound_system.g_sounds
                and not g_game_state["thrust_sound_playing"]
            ):
                sound_system.g_sounds["thrust"].play(-1)
                g_game_state["thrust_sound_playing"] = True
        elif keys[pygame.K_DOWN] or controller_input["reverse"]:
            thrust = -Cfg.ship_thrust_power * Cfg.ship_reverse_thrust_multiplier
        else:
            stop_thrust_sound()
            g_game_state["thrust_sound_playing"] = False

        if thrust != 0:
            g_ship.vel_x += cos_a * scaled(thrust) * g_game_state["time_scale"]
            g_ship.vel_y += sin_a * scaled(thrust) * g_game_state["time_scale"]

        apply_speed_limit(g_ship, scaled(Cfg.ship_max_speed) * get_speed_multiplier_wrapper())
        apply_friction(g_ship, Cfg.ship_friction)

    g_ship.x += g_ship.vel_x * g_game_state["time_scale"]
    g_ship.y += g_ship.vel_y * g_game_state["time_scale"]
    wrap_position(g_ship)

    update_dash_trail()
    update_ship_timers()


def update_dash_trail() -> None:
    """Update dash trail visual effect.

    Side effects:
        Modifies g_ship.dash_trail by removing expired trails

    Globals:
        Reads/writes g_ship, reads g_game_state['time_scale']
    """
    for trail in g_ship.dash_trail:
        trail["life"] = update_timer(trail["life"])
    g_ship.dash_trail = [t for t in g_ship.dash_trail if t["life"] > 0]


def update_ship_timers() -> None:
    """Update all ship-related timers.

    Side effects:
        Modifies various g_ship and g_game_state timers

    Globals:
        Reads/writes g_ship, g_game_state
    """
    SHIP_TIMERS = ["invulnerable", "rapid_fire", "triple_shot", "shield_active", "powerup_flash"]
    for timer in SHIP_TIMERS:
        value = getattr(g_ship, timer)
        setattr(g_ship, timer, update_timer(value))

    g_game_state["bullet_cooldown"] = update_timer(g_game_state["bullet_cooldown"])
    g_game_state["dash"]["cooldown"] = update_timer(g_game_state["dash"]["cooldown"])

    g_ship.aura_pulse += Cfg.powerup_aura_pulse_speed * g_game_state["time_scale"]
    g_game_state["effects"]["aura_rotation"] = (
        g_game_state["effects"]["aura_rotation"]
        + Cfg.powerup_aura_rotation_speed * g_game_state["time_scale"]
    ) % 360


def reset_ship() -> None:
    """Reset ship to respawn state.

    Side effects:
        Modifies ship position, velocity, angle, and various state flags;
        stops thrust sound

    Globals:
        Reads/writes g_ship, reads g_screen_width/height
    """
    stop_thrust_sound()
    g_game_state["thrust_sound_playing"] = False

    g_ship.x = g_screen_width // 2
    g_ship.y = g_screen_height // 2
    g_ship.angle = 0
    g_ship.vel_x = 0
    g_ship.vel_y = 0
    g_ship.invulnerable = Cfg.ship_invulnerability_time
    g_ship.powerup_flash = 0
    g_ship.respawning = Cfg.ship_respawn_duration
    g_ship.aura_pulse = 0
    g_ship.dashing = 0
    g_ship.dash_trail = []


# === [ENEMY AI] ===


def update_enemies() -> None:
    """Update all enemy entities.

    Side effects:
        Updates enemy AI, physics, and shooting

    Globals:
        Reads/writes g_enemies
    """
    for enemy in g_enemies:
        if enemy.hit_flash > 0:
            enemy.hit_flash = update_timer(enemy.hit_flash)

        update_enemy_ai(enemy)
        apply_enemy_physics(enemy)
        update_enemy_shooting(enemy)


def update_enemy_ai(enemy: Enemy) -> None:
    """Update enemy AI behavior.

    Args:
        enemy: Enemy to update

    Side effects:
        Modifies enemy velocity and angle

    Globals:
        Reads g_ship, g_game_state['time_scale']
    """
    dx = g_ship.x - enemy.x
    dy = g_ship.y - enemy.y
    distance = math.sqrt(dx * dx + dy * dy)

    if distance > 0:
        dx /= distance
        dy /= distance

    min_distance = Cfg.enemy_min_distance * g_scale_factor
    ai_config = Cfg.enemy_ai[enemy.ai_type.value]

    if enemy.ai_type == EnemyAIType.HUNTER:
        # --- [Hunter AI: approach or retreat based on distance] ---
        if distance > min_distance:
            rate = ai_config["approach_rate"] * scaled(Cfg.enemy_speed) * g_game_state["time_scale"]
            enemy.vx += dx * rate
            enemy.vy += dy * rate
        else:
            rate = ai_config["retreat_rate"] * scaled(Cfg.enemy_speed) * g_game_state["time_scale"]
            enemy.vx -= dx * rate
            enemy.vy -= dy * rate
    else:  # Circler
        # --- [Circler AI: orbit around player] ---
        enemy.orbit_angle += ai_config["orbit_speed"] * g_game_state["time_scale"]
        orbit_radius = ai_config["orbit_radius"] * g_scale_factor

        orbit_cos, orbit_sin = get_sin_cos(enemy.orbit_angle)
        target_x = g_ship.x + orbit_cos * orbit_radius
        target_y = g_ship.y + orbit_sin * orbit_radius

        dx_target = target_x - enemy.x
        dy_target = target_y - enemy.y
        dist = math.sqrt(dx_target * dx_target + dy_target * dy_target)

        if dist > 0:
            rate = ai_config["approach_rate"] * scaled(Cfg.enemy_speed) * g_game_state["time_scale"]
            enemy.vx += (dx_target / dist) * rate
            enemy.vy += (dy_target / dist) * rate

    enemy.angle = math.degrees(math.atan2(dy, dx))


def apply_enemy_physics(enemy: Enemy) -> None:
    """Apply physics to enemy entity.

    Args:
        enemy: Enemy to update

    Side effects:
        Modifies enemy velocity and position via apply_speed_limit,
        apply_friction, and update_entity_physics
    """
    apply_speed_limit(enemy, scaled(Cfg.enemy_speed) * Cfg.enemy_speed_reduction)
    apply_friction(enemy, Cfg.enemy_friction)
    update_entity_physics(enemy, {"wrap": True})


def update_enemy_shooting(enemy: Enemy) -> None:
    """Update enemy shooting behavior.

    Args:
        enemy: Enemy to update

    Side effects:
        Modifies enemy.fire_cooldown, may call shoot_bullet()

    Globals:
        Reads g_ship, g_game_state['time_scale']
    """
    enemy.fire_cooldown = update_timer(enemy.fire_cooldown)

    if enemy.fire_cooldown <= 0:
        dx = g_ship.x - enemy.x
        dy = g_ship.y - enemy.y
        distance = math.sqrt(dx * dx + dy * dy)

        min_fire_distance = Cfg.enemy_min_fire_distance * g_scale_factor
        max_fire_distance = Cfg.enemy_max_fire_distance * g_scale_factor

        if min_fire_distance < distance < max_fire_distance:
            aim_angle = enemy.angle + random.uniform(
                -Cfg.enemy_aim_inaccuracy, Cfg.enemy_aim_inaccuracy
            )
            shoot_bullet(is_enemy=True, enemy_x=enemy.x, enemy_y=enemy.y, enemy_angle=aim_angle)
            enemy.fire_cooldown = Cfg.enemy_fire_rate + random.randint(
                -Cfg.enemy_fire_rate_variance, Cfg.enemy_fire_rate_variance
            )


# === [GAME OBJECT UPDATES] ===


def update_game_objects() -> None:
    """Update all game objects for current frame.

    Side effects:
        Updates all game object lists
    """
    update_asteroids()
    update_bullets()
    update_enemy_bullets()
    update_powerups()
    update_enemies()


def update_asteroids() -> None:
    """Update all asteroids.

    Side effects:
        Updates asteroid positions and rotations

    Globals:
        Reads/writes g_asteroids
    """
    for asteroid in g_asteroids:
        update_entity_physics(asteroid, {"wrap": True})


def update_bullets() -> None:
    """Update player bullets.

    Side effects:
        Modifies bullet positions and trails, removes expired bullets

    Globals:
        Reads/writes g_bullets, reads g_screen_width/height, g_game_state['time_scale']
    """
    global g_bullets

    for bullet in g_bullets:
        bullet.trail.append((bullet.x, bullet.y))
        if len(bullet.trail) > Cfg.bullet_trail_length:
            bullet.trail.pop(0)

        bullet.x += bullet.vx * g_game_state["time_scale"]
        bullet.y += bullet.vy * g_game_state["time_scale"]
        bullet.life = update_timer(bullet.life)

    g_bullets = [
        b
        for b in g_bullets
        if b.life > 0 and 0 <= b.x <= g_screen_width and 0 <= b.y <= g_screen_height
    ]


def update_enemy_bullets() -> None:
    """Update enemy bullets.

    Side effects:
        Modifies enemy bullet positions and trails, removes expired bullets

    Globals:
        Reads/writes g_enemy_bullets, reads g_screen_width/height, g_game_state['time_scale']
    """
    global g_enemy_bullets

    for bullet in g_enemy_bullets:
        bullet.trail.append((bullet.x, bullet.y))
        if len(bullet.trail) > Cfg.enemy_bullet_trail_length:
            bullet.trail.pop(0)

        bullet.x += bullet.vx * g_game_state["time_scale"]
        bullet.y += bullet.vy * g_game_state["time_scale"]
        bullet.life = update_timer(bullet.life)

    g_enemy_bullets = [
        b
        for b in g_enemy_bullets
        if b.life > 0 and 0 <= b.x <= g_screen_width and 0 <= b.y <= g_screen_height
    ]


def update_powerups() -> None:
    """Update powerups.

    Side effects:
        Modifies powerup positions and timers, removes expired powerups

    Globals:
        Reads/writes g_powerups, reads g_game_state['time_scale']
    """
    global g_powerups

    for powerup in g_powerups:
        update_entity_physics(powerup, {"wrap": True})
        powerup.lifetime = update_timer(powerup.lifetime)
        powerup.pulse += 0.2 * g_game_state["time_scale"]

    g_powerups = [p for p in g_powerups if p.lifetime > 0]


# === [VISUAL EFFECTS] ===


def update_visual_effects() -> None:
    """Update all visual effects.

    Side effects:
        Updates particles, floating texts, combo system, finisher meter

    Globals:
        Reads/writes various effect timers in g_game_state
    """
    g_particle_pool.update(g_game_state["time_scale"], g_ship)
    update_floating_texts()
    update_combo_system()
    update_finisher_meter()

    g_game_state["effects"]["wave_warning"] = update_timer(g_game_state["effects"]["wave_warning"])

    g_text_cache.update()


def update_combo_system() -> None:
    """Update combo counter and effects.

    Side effects:
        Modifies g_game_state['combo'] timers and counters

    Globals:
        Reads/writes g_game_state
    """
    combo = g_game_state["combo"]

    if combo["timer"] > 0:
        combo["timer"] = update_timer(combo["timer"])
        if combo["timer"] <= 0:
            if combo["current"] > combo["max"]:
                combo["max"] = combo["current"]
            combo["current"] = 0
            combo["kills"] = 0

    if combo["pulse"] > 0:
        combo["pulse"] -= Cfg.combo_pulse_fade_rate * g_game_state["time_scale"]


def update_finisher_meter() -> None:
    """Update finisher meter decay.

    Side effects:
        Modifies g_game_state['finisher']['meter'] and ['ready']

    Globals:
        Reads/writes g_game_state
    """
    finisher = g_game_state["finisher"]

    if g_game_state["combo"]["current"] == 0 and finisher["meter"] > 0:
        decay_per_frame = 2.0 / Cfg.fps
        finisher["meter"] = max(
            0.0, finisher["meter"] - decay_per_frame * g_game_state["time_scale"]
        )
        if finisher["meter"] < 100.0:
            finisher["ready"] = False


def create_floating_text(
    x: float, y: float, text: str, color: Optional[Tuple[int, int, int]] = None
) -> None:
    """Create floating text effect.

    Args:
        x: X position
        y: Y position
        text: Text to display
        color: RGB color tuple (defaults to score text color)

    Side effects:
        Appends to global g_floating_texts list

    Globals:
        Writes to g_floating_texts
    """
    if color is None:
        color = Cfg.colors["score_text"]

    g_floating_texts.append(
        FloatingText(
            x=x
            + random.randint(-Cfg.floating_text_spread, Cfg.floating_text_spread) * g_scale_factor,
            y=y,
            text=text,
            color=color,
            life=Cfg.floating_text_life,
            vy=-Cfg.floating_text_speed * g_scale_factor,
        )
    )


def update_floating_texts() -> None:
    """Update floating text animations.

    Side effects:
        Modifies floating text positions and life, removes expired texts

    Globals:
        Reads/writes g_floating_texts, reads g_game_state['time_scale']
    """
    global g_floating_texts

    write_idx = 0
    for text in g_floating_texts:
        text.y += text.vy * g_game_state["time_scale"]
        text.life = update_timer(text.life)
        text.vy *= Cfg.floating_text_friction

        if text.life > 0:
            g_floating_texts[write_idx] = text
            write_idx += 1

    del g_floating_texts[write_idx:]


# === [LEVEL MANAGEMENT] ===


def start_new_level() -> None:
    """Initialize a new level.

    Side effects:
        Clears enemies and enemy_bullets, creates new asteroids,
        clears floating_texts, resets ship, sets wave warnings

    Globals:
        Reads/writes g_game_state, g_enemies, g_enemy_bullets, g_asteroids, g_floating_texts
    """
    global g_asteroids, g_floating_texts, g_enemies, g_enemy_bullets

    if g_game_state["level"] > 1 and g_game_state["untouchable_level"]:
        check_achievement_wrapper("untouchable")

    g_game_state["untouchable_level"] = True

    g_enemies.clear()
    g_enemy_bullets.clear()

    if g_game_state["level"] % Cfg.boss_spawn_interval == 0:
        g_game_state["effects"]["wave_warning"] = 120
        g_game_state["effects"]["wave_warning_text"] = "BOSS APPROACHING!"

    base_count = 3 + g_game_state["level"]
    area_multiplier = (g_screen_width * g_screen_height) / (Cfg.screen_width * Cfg.screen_height)
    asteroid_count = int(base_count * math.sqrt(area_multiplier))

    g_asteroids = []

    if g_game_state["level"] % Cfg.boss_spawn_interval == 0:
        g_asteroids.append(create_asteroid(is_boss=True))
        asteroid_count = max(1, asteroid_count - 3)

    for i in range(asteroid_count):
        has_crystals = random.random() < Cfg.asteroid_crystal_chance
        g_asteroids.append(create_asteroid(has_crystals=has_crystals))

    g_floating_texts = []
    reset_ship()

    check_achievement_wrapper("survivor")


# === [OBJECT DRAWING] ===


def get_polygon_points(
    obj: Any,
    num_points: int,
    base_radius: float,
    shape_offsets: Optional[list] = None,
    angle_override: Optional[float] = None,
) -> List[Tuple[float, float]]:
    """Generate polygon points for an object.

    Args:
        obj: Object with position (and optionally angle)
        num_points: Number of polygon vertices
        base_radius: Base radius of polygon
        shape_offsets: List of radius offsets for each vertex
        angle_override: Override object's angle

    Returns:
        List of (x, y) tuples forming polygon
    """
    points = []

    if angle_override is not None:
        angle = angle_override
    else:
        angle = getattr(obj, "angle", 0)

    x = getattr(obj, "x", obj["x"] if isinstance(obj, dict) else 0)
    y = getattr(obj, "y", obj["y"] if isinstance(obj, dict) else 0)

    for i in range(num_points):
        point_angle = (360 / num_points) * i + angle
        sin_a, cos_a = get_sin_cos(point_angle)
        radius = base_radius + (shape_offsets[i] if shape_offsets else 0)
        points.append((x + radius * cos_a, y + radius * sin_a))
    return points


# draw_asteroid DELETED - now handled by g_drawing.draw_asteroid()

# draw_enemy DELETED - now handled by g_drawing.draw_enemy()


def draw_ship(surface: pygame.Surface, keys: dict, controller_input: Dict[str, Any]) -> None:
    """Draw the player ship.

    Args:
        surface: Surface to draw on
        keys: Keyboard state
        controller_input: Controller state

    Globals:
        Reads g_game_state, g_ship
    """
    if g_game_state["game_over"]:
        return

    if g_ship.respawning > 0:
        draw_respawn_animation(surface)
        return

    if (
        g_ship.invulnerable > 0
        and g_ship.invulnerable % Cfg.ship_invulnerability_blink_interval
        >= Cfg.ship_invulnerability_blink_visible_frames
        and g_ship.respawning == 0
    ):
        return

    draw_dash_trail(surface)

    if g_game_state["finisher"]["ready"]:
        draw_finisher_aura(surface)

    draw_powerup_auras(surface)

    if g_ship.shield_active > 0:
        if g_drawing:
            g_drawing.glow(surface, (g_ship.x, g_ship.y), 30 * g_scale_factor, (0, 255, 0))
        pygame.draw.circle(
            surface,
            (0, 255, 0),
            (int(g_ship.x), int(g_ship.y)),
            int(25 * g_scale_factor),
            max(1, int(2 * g_scale_factor)),
        )

    if g_drawing:
        g_drawing.glow(surface, (g_ship.x, g_ship.y), 20 * g_scale_factor, Cfg.colors["blue_glow"])

    if g_ship.powerup_flash > 0:
        draw_powerup_flash(surface)

    draw_ship_body(surface)
    draw_thruster_flame(surface, keys, controller_input)


def draw_respawn_animation(surface: pygame.Surface) -> None:
    """Draw ship respawn animation.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship, g_game_state
    """
    progress = 1.0 - (g_ship.respawning / Cfg.ship_respawn_duration)

    for i in range(Cfg.respawn_spiral_layers):
        radius = (
            Cfg.respawn_spiral_radius_start * (1 - progress) - i * Cfg.respawn_spiral_radius_step
        ) * g_scale_factor
        if radius > 0:
            alpha = (1 - progress) * (1 - i * 0.3)
            if g_drawing:

                g_drawing.glow(
                    surface, (g_ship.x, g_ship.y), radius, Cfg.colors["blue_glow"], alpha
                )

    if progress > Cfg.level_text_appear_threshold:
        if (
            g_game_state["frame_count"] % Cfg.frame_visibility_check_modulo
            < Cfg.controller_input_check_modulo
        ):
            return


def draw_dash_trail(surface: pygame.Surface) -> None:
    """Draw dash trail effect.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship
    """
    for i, trail in enumerate(g_ship.dash_trail):
        alpha = trail["life"] / Cfg.particle_dash_trail_life
        ghost_points = get_ship_points(trail["x"], trail["y"], trail["angle"], 0.8)

        ghost_color = tuple(int(c * alpha) for c in Cfg.colors["dash"])
        pygame.draw.polygon(surface, ghost_color, ghost_points, 1)


def draw_finisher_aura(surface: pygame.Surface) -> None:
    """Draw finisher ready aura.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship, g_game_state
    """
    pulse = calculate_pulse(g_ship.aura_pulse, 1.0, 0.3, 0.7)

    for i in range(8):
        angle = g_game_state["effects"]["aura_rotation"] + i * 45
        sin_a, cos_a = get_sin_cos(angle)
        radius = (scaled(Cfg.ship_radius) + 15 * g_scale_factor) * pulse
        px = g_ship.x + cos_a * radius
        py = g_ship.y + sin_a * radius

        if g_drawing:

            g_drawing.glow(surface, (px, py), 6 * g_scale_factor, Cfg.colors["gold"])
        pygame.draw.circle(surface, Cfg.colors["gold"], (int(px), int(py)), int(2 * g_scale_factor))

    if g_drawing:

        g_drawing.glow(
            surface, (g_ship.x, g_ship.y), 25 * g_scale_factor * pulse, Cfg.colors["gold"], pulse
        )


def draw_powerup_flash(surface: pygame.Surface) -> None:
    """Draw powerup collection flash effect.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship
    """
    flash_intensity = g_ship.powerup_flash / Cfg.particle_powerup_flash_duration
    max_flash = (
        Cfg.particle_powerup_flash_max
        if g_ship.powerup_flash > Cfg.particle_powerup_flash_duration
        else Cfg.particle_powerup_flash_duration
    )
    flash_intensity = min(1.0, g_ship.powerup_flash / max_flash)

    if flash_intensity > 0:
        radius = (25 + 15 * flash_intensity) * g_scale_factor
        if g_drawing:

            g_drawing.glow(
                surface, (g_ship.x, g_ship.y), radius, g_ship.powerup_flash_color, flash_intensity
            )


def draw_ship_body(surface: pygame.Surface) -> None:
    """Draw ship body polygon.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship, g_game_state
    """
    ship_points = get_ship_points(g_ship.x, g_ship.y, g_ship.angle)

    if g_game_state["finisher"]["ready"]:
        pygame.draw.polygon(
            surface, Cfg.colors["gold"], ship_points, max(1, int(3 * g_scale_factor))
        )
    else:
        pygame.draw.polygon(
            surface, Cfg.colors["white"], ship_points, max(1, int(2 * g_scale_factor))
        )


def draw_thruster_flame(
    surface: pygame.Surface, keys: dict, controller_input: Dict[str, Any]
) -> None:
    """Draw thruster flame when ship is accelerating.

    Args:
        surface: Surface to draw on
        keys: Keyboard state
        controller_input: Controller state

    Globals:
        Reads g_ship, g_game_state
    """
    is_thrusting = keys[pygame.K_UP] or controller_input["thrust"]

    if not is_thrusting or g_game_state["game_over"] or g_ship.respawning > 0 or g_ship.dashing > 0:
        return

    sin_a, cos_a = get_sin_cos(g_ship.angle)

    flame_length = scaled(Cfg.ship_back_indent) + random.randint(
        int(Cfg.flame_length_min * g_scale_factor), int(Cfg.flame_length_max * g_scale_factor)
    )
    flame_width = random.randint(
        int(Cfg.flame_width_min * g_scale_factor), int(Cfg.flame_width_max * g_scale_factor)
    )

    flame_tip = (g_ship.x - flame_length * cos_a, g_ship.y - flame_length * sin_a)

    sin_flame_left, cos_flame_left = get_sin_cos(g_ship.angle + Cfg.ship_flame_angle)
    sin_flame_right, cos_flame_right = get_sin_cos(g_ship.angle - Cfg.ship_flame_angle)

    flame_base_left = (
        g_ship.x - scaled(Cfg.ship_back_indent) * cos_a + flame_width * cos_flame_left,
        g_ship.y - scaled(Cfg.ship_back_indent) * sin_a + flame_width * sin_flame_left,
    )

    flame_base_right = (
        g_ship.x - scaled(Cfg.ship_back_indent) * cos_a + flame_width * cos_flame_right,
        g_ship.y - scaled(Cfg.ship_back_indent) * sin_a + flame_width * sin_flame_right,
    )

    pygame.draw.polygon(surface, (255, 100, 0), [flame_tip, flame_base_left, flame_base_right])

    inner_flame_tip = (
        g_ship.x - (flame_length * 0.7) * cos_a,
        g_ship.y - (flame_length * 0.7) * sin_a,
    )
    inner_width = flame_width * 0.6
    inner_base_left = (
        g_ship.x - scaled(Cfg.ship_back_indent) * cos_a + inner_width * cos_flame_left,
        g_ship.y - scaled(Cfg.ship_back_indent) * sin_a + inner_width * sin_flame_left,
    )
    inner_base_right = (
        g_ship.x - scaled(Cfg.ship_back_indent) * cos_a + inner_width * cos_flame_right,
        g_ship.y - scaled(Cfg.ship_back_indent) * sin_a + inner_width * sin_flame_right,
    )
    pygame.draw.polygon(
        surface, (255, 255, 150), [inner_flame_tip, inner_base_left, inner_base_right]
    )


def draw_powerup_auras(surface: pygame.Surface) -> None:
    """Draw auras for active powerups.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship, g_game_state
    """
    if g_ship.rapid_fire > 0:
        pulse = calculate_pulse(g_ship.aura_pulse, 1.0, 0.3, 0.7)
        radius = int(35 * pulse * g_scale_factor)

        for i in range(3):
            angle = g_game_state["effects"]["aura_rotation"] + i * 120
            sin_a, cos_a = get_sin_cos(angle)
            x = g_ship.x + cos_a * radius
            y = g_ship.y + sin_a * radius

            triangle_size = 5 * g_scale_factor
            points = []
            for j in range(3):
                t_angle = angle + j * 120
                t_sin, t_cos = get_sin_cos(t_angle)
                points.append((x + t_cos * triangle_size, y + t_sin * triangle_size))
            pygame.draw.polygon(surface, (255, 100, 0), points, 1)

    if g_ship.triple_shot > 0:
        pulse = calculate_pulse(g_ship.aura_pulse * 0.8, 1.0, 0.3, 0.7)
        radius = int(40 * pulse * g_scale_factor)

        for i in range(3):
            angle = g_game_state["effects"]["aura_rotation"] * -1.5 + i * 120
            sin_a, cos_a = get_sin_cos(angle)
            x = g_ship.x + cos_a * radius
            y = g_ship.y + sin_a * radius

            pygame.draw.circle(surface, (0, 255, 255), (int(x), int(y)), int(3 * g_scale_factor))
            if g_drawing:

                g_drawing.glow(surface, (x, y), 8 * g_scale_factor, (0, 255, 255))


# draw_powerups DELETED - now handled by g_drawing.draw_powerups()

# draw_bullets DELETED - now handled by g_drawing.draw_bullets()

# draw_particles DELETED - now handled by g_drawing.draw_particles()

# === [FINISHER DRAWING] ===


def draw_finisher_target_indicator(surface: pygame.Surface) -> None:
    """Draw indicator for finisher target.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_ship, g_enemies
    """
    finisher_state = g_game_state["finisher"]

    if not finisher_state["ready"] or finisher_state["executing"] or not g_enemies:
        return

    target = check_finisher_collision(g_ship, g_ship.angle)
    if not target:
        return

    pulse = calculate_pulse(g_game_state["frame_count"], 0.15, 0.3, 0.7)

    for i in range(3):
        radius = (target.radius + 15 + i * 5) * pulse * g_scale_factor
        if g_drawing:

            g_drawing.glow(surface, (target.x, target.y), radius, Cfg.colors["gold"], pulse)

    draw_target_reticle(surface, target, pulse)
    draw_dash_preview(surface, target, pulse)


def draw_target_reticle(surface: pygame.Surface, target: Enemy, pulse: float) -> None:
    """Draw targeting reticle on finisher target.

    Args:
        surface: Surface to draw on
        target: Target enemy
        pulse: Pulse animation value
    """
    reticle_radius = int((target.radius + 10) * g_scale_factor)
    bracket_length = int(reticle_radius * Cfg.finisher_reticle_bracket_ratio)
    bracket_thickness = max(2, int(Cfg.finisher_reticle_thickness * g_scale_factor))

    corners = [
        [
            (target.x - reticle_radius, target.y - reticle_radius + bracket_length),
            (target.x - reticle_radius, target.y - reticle_radius),
            (target.x - reticle_radius + bracket_length, target.y - reticle_radius),
        ],
        [
            (target.x + reticle_radius - bracket_length, target.y - reticle_radius),
            (target.x + reticle_radius, target.y - reticle_radius),
            (target.x + reticle_radius, target.y - reticle_radius + bracket_length),
        ],
        [
            (target.x - reticle_radius, target.y + reticle_radius - bracket_length),
            (target.x - reticle_radius, target.y + reticle_radius),
            (target.x - reticle_radius + bracket_length, target.y + reticle_radius),
        ],
        [
            (target.x + reticle_radius - bracket_length, target.y + reticle_radius),
            (target.x + reticle_radius, target.y + reticle_radius),
            (target.x + reticle_radius, target.y + reticle_radius - bracket_length),
        ],
    ]

    for corner in corners:
        pygame.draw.lines(surface, Cfg.colors["gold"], False, corner, bracket_thickness)


def draw_dash_preview(surface: pygame.Surface, target: Enemy, pulse: float) -> None:
    """Draw preview of dash trajectory for finisher.

    Args:
        surface: Surface to draw on
        target: Target enemy
        pulse: Pulse animation value

    Globals:
        Reads g_ship
    """
    sin_a, cos_a = get_sin_cos(g_ship.angle)
    dash_distance = scaled(Cfg.ship_max_speed) * Cfg.dash_speed_multiplier * Cfg.dash_duration

    segments = Cfg.finisher_dash_preview_segments
    for i in range(segments):
        if i % 2 == 0:
            start_t = i / segments
            end_t = min((i + 1) / segments, 1.0)

            start_x = g_ship.x + cos_a * dash_distance * start_t
            start_y = g_ship.y + sin_a * dash_distance * start_t
            end_x = g_ship.x + cos_a * dash_distance * end_t
            end_y = g_ship.y + sin_a * dash_distance * end_t

            alpha = int(Cfg.finisher_dash_preview_alpha * pulse)
            dim_gold = (
                int(Cfg.colors["gold"][0] * alpha / 255),
                int(Cfg.colors["gold"][1] * alpha / 255),
                int(Cfg.colors["gold"][2] * alpha / 255),
            )
            pygame.draw.line(
                surface,
                dim_gold,
                (int(start_x), int(start_y)),
                (int(end_x), int(end_y)),
                max(1, int(2 * g_scale_factor)),
            )


def draw_lock_on_indicator(surface: pygame.Surface) -> None:
    """Draw lock-on animation during finisher execution.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_ship, g_enemies
    """
    finisher_state = g_game_state["finisher"]
    if (
        finisher_state["phase"] != FinisherPhase.LOCK_ON
        or not finisher_state["target"]
        or finisher_state["target"] not in g_enemies
    ):
        return

    sin_a, cos_a = get_sin_cos(g_ship.angle)
    dash_distance = scaled(Cfg.ship_max_speed) * Cfg.dash_speed_multiplier * Cfg.dash_duration

    pulse = abs(math.sin(finisher_state["lock_on_progress"] * math.pi * 3))
    line_color = (255, int(215 * pulse), 0)

    segments = 20
    for i in range(segments):
        if i % 2 == 0:
            start_t = i / segments
            end_t = (i + 1) / segments

            start_x = g_ship.x + cos_a * dash_distance * start_t
            start_y = g_ship.y + sin_a * dash_distance * start_t
            seg_end_x = g_ship.x + cos_a * dash_distance * end_t
            seg_end_y = g_ship.y + sin_a * dash_distance * end_t

            thickness = max(1, int((1 + finisher_state["lock_on_progress"] * 2) * g_scale_factor))
            pygame.draw.line(
                surface,
                line_color,
                (int(start_x), int(start_y)),
                (int(seg_end_x), int(seg_end_y)),
                thickness,
            )

    draw_lock_on_reticle(surface, finisher_state["target"], finisher_state["lock_on_progress"])

    if finisher_state["lock_on_progress"] > Cfg.finisher_lock_text_appear_threshold:
        text_alpha = int(
            255
            * ((finisher_state["lock_on_progress"] - Cfg.finisher_lock_text_appear_threshold) * 2)
        )
        lock_text = g_text_cache.get_text("LOCK ON", g_small_font, Cfg.colors["gold"])
        lock_rect = lock_text.get_rect(
            center=(
                int(finisher_state["target"].x),
                int(finisher_state["target"].y - Cfg.finisher_lock_text_y_offset * g_scale_factor),
            )
        )
        lock_text.set_alpha(text_alpha)
        surface.blit(lock_text, lock_rect)


def draw_lock_on_reticle(surface: pygame.Surface, target: Enemy, progress: float) -> None:
    """Draw animated lock-on reticle.

    Args:
        surface: Surface to draw on
        target: Target enemy
        progress: Lock-on progress (0-1)
    """
    reticle_size = int(
        (
            Cfg.finisher_reticle_size_base
            + Cfg.finisher_reticle_size_variation * abs(math.sin(progress * math.pi))
        )
        * g_scale_factor
        * progress
    )
    if reticle_size <= 0:
        return

    rotation = progress * 360
    for i in range(4):
        angle = rotation + i * 90
        sin_r, cos_r = get_sin_cos(angle)

        corner_length = reticle_size // 3
        start_x = target.x + cos_r * reticle_size
        start_y = target.y + sin_r * reticle_size

        pygame.draw.line(
            surface,
            Cfg.colors["gold"],
            (int(start_x), int(start_y)),
            (int(start_x - cos_r * corner_length), int(start_y - sin_r * corner_length)),
            max(1, int(2 * g_scale_factor)),
        )
        pygame.draw.line(
            surface,
            Cfg.colors["gold"],
            (int(start_x), int(start_y)),
            (int(start_x + sin_r * corner_length), int(start_y - cos_r * corner_length)),
            max(1, int(2 * g_scale_factor)),
        )


def draw_shockwave(surface: pygame.Surface, x: float, y: float, radius: float) -> None:
    """Draw expanding shockwave effect.

    Args:
        surface: Surface to draw on
        x: Center X
        y: Center Y
        radius: Shockwave radius
    """
    if radius <= 0:
        return

    for i in range(3):
        ring_radius = int(radius - i * 10 * g_scale_factor)
        if ring_radius > 0:
            max_radius = Cfg.finisher_shockwave_radius * g_scale_factor
            progress = radius / max_radius
            alpha = int(200 * (1 - progress) * (1 - i * 0.3))

            if alpha > 0:
                ring_surface = pygame.Surface(
                    (surface.get_width(), surface.get_height()), pygame.SRCALPHA
                )

                pygame.draw.circle(
                    ring_surface,
                    (*Cfg.colors["gold"], alpha),
                    (int(x), int(y)),
                    ring_radius,
                    max(1, int(3 * g_scale_factor)),
                )

                if i == 0:
                    for j in range(3):
                        glow_alpha = alpha // (j + 2)
                        if glow_alpha > 0:
                            pygame.draw.circle(
                                ring_surface,
                                (*Cfg.colors["gold"], glow_alpha),
                                (int(x), int(y)),
                                ring_radius + j * 2,
                                1,
                            )

                surface.blit(ring_surface, (0, 0))


# === [UI DRAWING] ===


def draw_ui_text(
    surface: pygame.Surface,
    text: str,
    x: int,
    y: int,
    font_obj: Optional[pygame.font.Font] = None,
    color: Tuple[int, int, int] = Cfg.colors["white"],
) -> pygame.Surface:
    """Draw UI text with caching.

    Args:
        surface: Surface to draw on
        text: Text to render
        x: X position
        y: Y position
        font_obj: Font to use (defaults to g_font)
        color: Text color

    Returns:
        Rendered text surface

    Globals:
        Reads g_font, g_text_cache
    """
    if font_obj is None:
        font_obj = g_font
    text_surface = g_text_cache.get_text(text, font_obj, color)
    surface.blit(text_surface, (x, y))
    return text_surface


def draw_ui(surface: pygame.Surface) -> None:
    """Draw all UI elements.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_ship
    """
    margin = int(scaled(Cfg.ui_margin))
    spacing = int(scaled(Cfg.ui_element_spacing))
    y_offset = margin

    draw_score_and_combo(surface, y_offset)

    draw_high_score(surface)

    y_offset += spacing
    draw_ui_text(
        surface, f"Lives: {'♥' * g_game_state['lives']}", margin, y_offset, g_font, (255, 100, 100)
    )

    y_offset += spacing
    draw_ui_text(surface, f"Level: {g_game_state['level']}", margin, y_offset)

    y_offset += spacing
    draw_ui_text(
        surface, f"◆ {g_game_state['crystals']}", margin, y_offset, g_font, Cfg.colors["crystal"]
    )

    y_offset += spacing
    draw_dash_indicator(surface, y_offset)

    y_offset += spacing
    draw_finisher_meter(surface, y_offset)

    draw_system_status(surface)

    draw_powerup_indicators(surface)

    draw_wave_warning(surface)


def draw_score_and_combo(surface: pygame.Surface, y_offset: int) -> None:
    """Draw score and combo counter.

    Args:
        surface: Surface to draw on
        y_offset: Starting Y position

    Globals:
        Reads g_game_state, g_text_cache, g_font
    """
    combo = g_game_state["combo"]

    score_text = g_text_cache.get_text(
        f"Score: {g_game_state['score']}", g_font, Cfg.colors["white"]
    )
    surface.blit(score_text, (int(scaled(Cfg.ui_margin)), y_offset))

    if combo["current"] > 1:
        kills_until_pulse = Cfg.combo_pulse_interval - (combo["kills"] % Cfg.combo_pulse_interval)
        pulse_speed = 0.1 if kills_until_pulse > 2 else 0.2
        pulse = calculate_pulse(g_game_state["frame_count"], pulse_speed)

        if combo["current"] >= Cfg.combo_milestone_thresholds[1]:
            combo_color = (255, int(50 + 165 * pulse), 0)
        elif combo["current"] >= Cfg.combo_milestone_thresholds[0]:
            combo_color = Cfg.colors["gold"]
        else:
            combo_color = Cfg.colors["white"]

        combo_text = g_text_cache.get_text(f"x{combo['current']}", g_font, combo_color)
        combo_rect = combo_text.get_rect(
            left=int(scaled(Cfg.ui_margin) + score_text.get_width() + 10), top=int(y_offset)
        )

        if combo["current"] >= Cfg.combo_text_threshold:
            glow_radius = int((10 + combo["current"]) * g_scale_factor)
            if kills_until_pulse <= 2:
                glow_radius = int(glow_radius * 1.5)
            if g_drawing:

                g_drawing.glow(
                    surface, (combo_rect.centerx, combo_rect.centery), glow_radius, combo_color
                )

        surface.blit(combo_text, combo_rect)

        if combo["current"] >= Cfg.combo_text_threshold:
            draw_combo_progress(surface, combo_rect.right + int(10 * g_scale_factor), y_offset)


def draw_combo_progress(surface: pygame.Surface, x_start: int, y_offset: int) -> None:
    """Draw combo progress pips.

    Args:
        surface: Surface to draw on
        x_start: Starting X position
        y_offset: Y position offset

    Globals:
        Reads g_game_state
    """
    combo = g_game_state["combo"]
    kills_in_cycle = combo["kills"] % Cfg.combo_pulse_interval
    pip_y = int(y_offset + Cfg.ui_combo_pip_y_offset * g_scale_factor)

    for i in range(Cfg.combo_pulse_interval):
        pip_x = int(x_start + i * Cfg.ui_combo_pip_spacing * g_scale_factor)
        if i < kills_in_cycle:
            pygame.draw.circle(
                surface,
                Cfg.colors["gold"],
                (pip_x, pip_y),
                int(Cfg.ui_combo_pip_radius * g_scale_factor),
            )
        else:
            pygame.draw.circle(
                surface,
                (100, 100, 100),
                (pip_x, pip_y),
                int(Cfg.ui_combo_pip_radius * g_scale_factor),
                1,
            )


def draw_high_score(surface: pygame.Surface) -> None:
    """Draw high score display.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_text_cache, g_font, g_screen_width
    """
    high_score_text = g_text_cache.get_text(
        f"High: {g_game_state.get('high_score', 0)}", g_font, Cfg.colors["white"]
    )
    high_score_rect = high_score_text.get_rect(
        center=(
            g_screen_width // 2,
            int(scaled(Cfg.ui_margin) + Cfg.ui_high_score_y_offset * g_scale_factor),
        )
    )
    surface.blit(high_score_text, high_score_rect)


def draw_dash_indicator(surface: pygame.Surface, y_offset: int) -> None:
    """Draw dash cooldown indicator.

    Args:
        surface: Surface to draw on
        y_offset: Y position

    Globals:
        Reads g_game_state, g_text_cache
    """
    if g_game_state["dash"]["cooldown"] > 0:
        max_cooldown = Cfg.dash_cooldown - get_dash_cooldown_reduction_wrapper()
        cooldown_percent = 1 - (g_game_state["dash"]["cooldown"] / max_cooldown)
        bar_width = int(Cfg.ui_dash_bar_width * g_scale_factor)
        bar_height = int(Cfg.ui_dash_bar_height * g_scale_factor)
        bar_x = int(scaled(Cfg.ui_margin))
        bar_y = y_offset

        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(
            surface,
            Cfg.colors["dash"],
            (bar_x, bar_y, int(bar_width * cooldown_percent), bar_height),
        )
        pygame.draw.rect(surface, Cfg.colors["white"], (bar_x, bar_y, bar_width, bar_height), 1)

        dash_text = g_text_cache.get_text("DASH", g_tiny_font, (150, 150, 150))
        surface.blit(dash_text, (bar_x, bar_y + bar_height + 2))
    else:
        if g_game_state["finisher"]["ready"]:
            dash_text = g_text_cache.get_text(
                "DASH/FINISHER READY! (SHIFT)", g_small_font, Cfg.colors["gold"]
            )
        else:
            dash_text = g_text_cache.get_text(
                "DASH READY (SHIFT)", g_small_font, Cfg.colors["dash"]
            )
        surface.blit(dash_text, (int(scaled(Cfg.ui_margin)), y_offset))


def draw_finisher_meter(surface: pygame.Surface, y_offset: int) -> None:
    """Draw finisher meter and status.

    Args:
        surface: Surface to draw on
        y_offset: Y position

    Globals:
        Reads g_game_state, g_ship, g_enemies
    """
    finisher = g_game_state["finisher"]
    meter_width = int(Cfg.ui_finisher_bar_width * g_scale_factor)
    meter_height = int(Cfg.ui_finisher_bar_height * g_scale_factor)
    bar_x = int(scaled(Cfg.ui_margin))

    has_valid_target = False
    if finisher["ready"] and not finisher["executing"] and g_enemies:
        target = check_finisher_collision(g_ship, g_ship.angle)
        has_valid_target = target is not None

    pygame.draw.rect(surface, (50, 50, 50), (bar_x, y_offset, meter_width, meter_height))

    fill_width = int(meter_width * (finisher["meter"] / 100.0))
    if finisher["ready"]:
        if has_valid_target:
            pulse = calculate_pulse(g_game_state["frame_count"], 0.2)
            fill_color = (int(255), int(215 + 40 * pulse), int(100 * pulse))
        else:
            pulse = calculate_pulse(g_game_state["frame_count"], 0.1, 0.3, 0.7)
            fill_color = (int(255 * pulse), int(215 * pulse), 0)
    else:
        fill_color = (150, 150, 100)

    pygame.draw.rect(surface, fill_color, (bar_x, y_offset, fill_width, meter_height))

    border_color = Cfg.colors["gold"] if has_valid_target else Cfg.colors["white"]
    border_thickness = 2 if has_valid_target else 1
    pygame.draw.rect(
        surface, border_color, (bar_x, y_offset, meter_width, meter_height), border_thickness
    )

    if finisher["ready"]:
        if has_valid_target:
            finisher_text = g_text_cache.get_text(
                "FINISHER LOCKED!", g_small_font, Cfg.colors["gold"]
            )
            text_rect = finisher_text.get_rect(topleft=(bar_x, y_offset + meter_height + 2))
            if g_drawing:

                g_drawing.glow(
                    surface,
                    (text_rect.centerx, text_rect.centery),
                    int(40 * g_scale_factor),
                    Cfg.colors["gold"],
                )
        else:
            finisher_text = g_text_cache.get_text(
                "FINISHER READY!", g_small_font, Cfg.colors["gold"]
            )
    else:
        finisher_text = g_text_cache.get_text(
            f"FINISHER {int(finisher['meter'])}%", g_tiny_font, (150, 150, 150)
        )
    surface.blit(finisher_text, (bar_x, y_offset + meter_height + 2))


def draw_system_status(surface: pygame.Surface) -> None:
    """Draw system status indicators.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_controller_connected, g_text_cache, g_screen_width
    """
    sound_status = "ON" if get_sound_enabled() else "OFF"
    sound_text = g_text_cache.get_text(
        f"Sound: {sound_status} (S)", g_small_font, Cfg.colors["white"]
    )
    sound_text_rect = sound_text.get_rect()
    sound_text_rect.topright = (
        g_screen_width - int(scaled(Cfg.ui_margin)),
        int(scaled(Cfg.ui_margin)),
    )
    surface.blit(sound_text, sound_text_rect)

    controller_status = "Connected" if g_controller_connected else "Not connected"
    controller_color = (100, 255, 100) if g_controller_connected else (150, 150, 150)
    controller_text = g_text_cache.get_text(
        f"Controller: {controller_status}", g_small_font, controller_color
    )
    controller_text_rect = controller_text.get_rect()
    controller_text_rect.topright = (
        g_screen_width - int(scaled(Cfg.ui_margin)),
        int(scaled(Cfg.ui_margin) + Cfg.ui_sound_status_y_offset * g_scale_factor),
    )
    surface.blit(controller_text, controller_text_rect)


def draw_powerup_indicators(surface: pygame.Surface) -> None:
    """Draw active powerup indicators.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_ship, g_text_cache
    """
    y_offset = int(scaled(Cfg.ui_margin) + Cfg.ui_powerup_indicator_y_base * g_scale_factor)

    if g_ship.rapid_fire > 0:
        text = g_text_cache.get_text(
            f"RAPID FIRE: {int(g_ship.rapid_fire // Cfg.fps)}s",
            g_small_font,
            Cfg.powerup_types[PowerUpType.RAPID]["color"],
        )
        surface.blit(text, (int(scaled(Cfg.ui_margin)), y_offset))
        y_offset += int(Cfg.ui_powerup_indicator_spacing * g_scale_factor)

    if g_ship.triple_shot > 0:
        text = g_text_cache.get_text(
            f"TRIPLE SHOT: {int(g_ship.triple_shot // Cfg.fps)}s",
            g_small_font,
            Cfg.powerup_types[PowerUpType.TRIPLE]["color"],
        )
        surface.blit(text, (int(scaled(Cfg.ui_margin)), y_offset))
        y_offset += int(Cfg.ui_powerup_indicator_spacing * g_scale_factor)

    if g_ship.shield_active > 0:
        text = g_text_cache.get_text(
            f"SHIELD: {int(g_ship.shield_active // Cfg.fps)}s",
            g_small_font,
            Cfg.powerup_types[PowerUpType.SHIELD]["color"],
        )
        surface.blit(text, (int(scaled(Cfg.ui_margin)), y_offset))


def draw_wave_warning(surface: pygame.Surface) -> None:
    """Draw wave warning for boss levels.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_screen_width/height
    """
    if g_game_state["effects"]["wave_warning"] > 0:
        warning_alpha = calculate_fade(abs(math.sin(g_game_state["frame_count"] * 0.1)))
        warning_color = (255, warning_alpha, warning_alpha)
        warning_text = g_big_font.render(
            g_game_state["effects"]["wave_warning_text"], True, warning_color
        )
        warning_rect = warning_text.get_rect(center=(g_screen_width // 2, g_screen_height // 4))
        surface.blit(warning_text, warning_rect)


def draw_floating_texts(surface: pygame.Surface) -> None:
    """Draw all floating text effects.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_floating_texts
    """
    for text in g_floating_texts:
        if g_drawing:

            g_drawing.floating_text(surface, text)


# === [VISUAL EFFECTS DRAWING] ===
# Visual effects moved to visual_effects.py module

# === [MENU DRAWING] ===


def draw_menu_overlay(surface: pygame.Surface, title: str, alpha: int = 200) -> None:
    """Draw a semi-transparent overlay with title.

    Args:
        surface: Surface to draw on
        title: Title text to display
        alpha: Overlay transparency

    Globals:
        Reads g_screen_width/height, g_big_font
    """
    overlay = pygame.Surface((g_screen_width, g_screen_height))
    overlay.set_alpha(alpha)
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))

    if title:
        title_text = g_big_font.render(title, True, Cfg.colors["white"])
        title_rect = title_text.get_rect(center=(g_screen_width // 2, 50 * g_scale_factor))
        surface.blit(title_text, title_rect)


def draw_centered_text(
    surface: pygame.Surface,
    text: str,
    font_obj: pygame.font.Font,
    color: Tuple[int, int, int],
    y_pos: Union[int, float],
) -> pygame.Rect:
    """Draw centered text at specified y position.

    Args:
        surface: Surface to draw on
        text: Text to render
        font_obj: Font to use
        color: Text color
        y_pos: Y position

    Returns:
        Text rect for further positioning

    Globals:
        Reads g_screen_width
    """
    text_surface = font_obj.render(text, True, color)
    text_rect = text_surface.get_rect(center=(g_screen_width // 2, y_pos))
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_upgrade_menu(surface: pygame.Surface) -> None:
    """Draw upgrade menu interface.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_font, g_screen_height
    """
    draw_menu_overlay(surface, "UPGRADES")

    draw_centered_text(
        surface,
        f"Crystals: ◆ {g_game_state['crystals']}",
        g_font,
        Cfg.colors["crystal"],
        100 * g_scale_factor,
    )

    draw_upgrade_list(surface)

    draw_centered_text(
        surface,
        "↑↓ Select   ENTER Purchase   ESC Close",
        g_font,
        Cfg.colors["white"],
        g_screen_height - 50 * g_scale_factor,
    )


def draw_upgrade_list(surface: pygame.Surface) -> None:
    """Draw list of available upgrades.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_font, g_small_font, g_screen_width
    """
    y_offset = Cfg.ui_upgrade_menu_y_start * g_scale_factor
    upgrade_keys = list(Cfg.upgrades.keys())

    for i, upgrade_type in enumerate(upgrade_keys):
        upgrade = Cfg.upgrades[upgrade_type]
        level = g_game_state["upgrade_levels"][upgrade_type]
        max_level = upgrade["max_level"]

        if i == g_game_state["selected_upgrade"]:
            pygame.draw.rect(
                surface,
                (50, 50, 100),
                (
                    g_screen_width // 4,
                    y_offset - 10,
                    g_screen_width // 2,
                    Cfg.ui_upgrade_menu_item_height * g_scale_factor - 20,
                ),
            )

        name_text = g_font.render(
            f"{upgrade['name']} (Lv {level}/{max_level})", True, Cfg.colors["white"]
        )
        surface.blit(name_text, (g_screen_width // 4 + Cfg.ui_upgrade_menu_padding, y_offset))

        if level < max_level:
            cost = calculate_upgrade_cost_wrapper(upgrade_type)
            cost_color = (
                Cfg.colors["crystal"] if g_game_state["crystals"] >= cost else (255, 100, 100)
            )
            cost_text = g_font.render(f"Cost: ◆ {cost}", True, cost_color)
        else:
            cost_text = g_font.render("MAXED", True, Cfg.colors["gold"])

        surface.blit(
            cost_text,
            (
                g_screen_width * 3 // 4 - cost_text.get_width() - Cfg.ui_upgrade_menu_padding,
                y_offset,
            ),
        )

        desc_text = g_small_font.render(upgrade["description"], True, (200, 200, 200))
        surface.blit(desc_text, (g_screen_width // 4 + Cfg.ui_upgrade_menu_padding, y_offset + 30))

        y_offset += Cfg.ui_upgrade_menu_item_height * g_scale_factor


def draw_game_over(surface: pygame.Surface) -> None:
    """Draw game over screen.

    Args:
        surface: Surface to draw on

    Globals:
        Reads/writes g_game_state, reads g_big_font, g_font, g_small_font,
        g_screen_width/height, g_controller_connected
    """
    g_game_state["effects"]["game_over_alpha"] = min(
        g_game_state["effects"]["game_over_alpha"] + Cfg.game_over_fade_speed, 128
    )

    overlay = pygame.Surface((g_screen_width, g_screen_height))
    overlay.set_alpha(g_game_state["effects"]["game_over_alpha"])
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))

    if g_game_state["effects"]["game_over_alpha"] > 64:
        draw_centered_text(
            surface,
            "GAME OVER",
            g_big_font,
            (255, 0, 0),
            g_screen_height // 2 - Cfg.ui_game_over_y_offset * g_scale_factor,
        )

        y_offset = g_screen_height // 2 - 30

        stats = [
            (f"Final Score: {g_game_state['score']}", Cfg.colors["white"]),
            (f"Best Combo: x{g_game_state['combo']['max']}", Cfg.colors["gold"]),
            (f"Crystals Earned: ◆ {g_game_state['crystals']}", Cfg.colors["crystal"]),
        ]

        for text, color in stats:
            draw_centered_text(surface, text, g_font, color, y_offset)
            y_offset += Cfg.ui_game_over_stat_spacing

        y_offset += Cfg.ui_game_over_restart_offset
        draw_centered_text(surface, "Press ENTER to restart", g_font, Cfg.colors["white"], y_offset)

        y_offset += 30
        draw_centered_text(
            surface, "Press U to open upgrade menu", g_small_font, (200, 200, 200), y_offset
        )

        if g_controller_connected:
            y_offset += 30
            draw_centered_text(
                surface, "(or press START on controller)", g_small_font, (200, 200, 200), y_offset
            )


def draw_pause_overlay(surface: pygame.Surface) -> None:
    """Draw pause menu overlay.

    Args:
        surface: Surface to draw on

    Globals:
        Reads g_game_state, g_big_font, g_font, g_small_font, g_screen_width/height
    """
    if g_game_state["effects"]["pause_menu_alpha"] <= 0:
        return

    overlay = pygame.Surface((g_screen_width, g_screen_height))
    overlay.set_alpha(int(g_game_state["effects"]["pause_menu_alpha"] * 0.7))
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))

    if g_game_state["effects"]["pause_menu_alpha"] > 128:
        alpha_ratio = (g_game_state["effects"]["pause_menu_alpha"] - 128) / 127

        pause_text = g_big_font.render("PAUSED", True, Cfg.colors["white"])
        pause_text.set_alpha(calculate_fade(alpha_ratio))
        text_rect = pause_text.get_rect(
            center=(
                g_screen_width // 2,
                g_screen_height // 2 - Cfg.ui_pause_menu_y_start * g_scale_factor,
            )
        )
        surface.blit(pause_text, text_rect)

        instructions = [
            "CONTROLS:",
            "Arrow Keys - Move",
            "Space - Shoot",
            "Shift - Dash / Finisher",
            "ESC - Resume",
            "S - Toggle Sound",
            "U - Upgrades",
            "Enter - Restart",
            "",
            f"High Score: {g_game_state.get('high_score', 0)}",
            f"Lifetime Crystals: ◆ {g_game_state.get('lifetime_crystals', 0)}",
        ]

        y_offset = g_screen_height // 2 - 50 * g_scale_factor
        for instruction in instructions:
            if instruction:
                inst_text = g_font.render(instruction, True, Cfg.colors["white"])
                inst_text.set_alpha(calculate_fade(alpha_ratio))
                inst_rect = inst_text.get_rect(center=(g_screen_width // 2, y_offset))
                surface.blit(inst_text, inst_rect)
            y_offset += Cfg.ui_pause_menu_line_spacing * g_scale_factor

        achievements_text = g_small_font.render(
            f"Achievements: {len(g_game_state['achievements_unlocked'])}/{len(Cfg.achievements)}",
            True,
            Cfg.colors["gold"],
        )
        achievements_text.set_alpha(calculate_fade(alpha_ratio))
        ach_rect = achievements_text.get_rect(
            center=(
                g_screen_width // 2,
                y_offset + Cfg.ui_pause_menu_achievement_offset * g_scale_factor,
            )
        )
        surface.blit(achievements_text, ach_rect)


# === [RENDERING SYSTEM] ===


def render_frame(shake_x: int, shake_y: int, keys: dict, controller_input: Dict[str, Any]) -> None:
    """Render complete game frame.

    Args:
        shake_x: Screen shake X offset
        shake_y: Screen shake Y offset
        keys: Keyboard state
        controller_input: Controller state

    Globals:
        Reads g_screen, g_game_state, g_screen_width/height
    """
    render_to_surface(g_screen, shake_x, shake_y, keys, controller_input)

    if g_game_state["combo"]["pulse"] > 0:
        apply_combo_pulse(g_screen)

    pygame.display.flip()


def apply_combo_pulse(surface: pygame.Surface) -> None:
    """Apply combo pulse screen effect.

    Args:
        surface: Surface to apply effect to

    Globals:
        Reads g_game_state, g_screen_width/height
    """
    pulse_alpha = min(Cfg.combo_pulse_max_alpha, g_game_state["combo"]["pulse"] * 5)
    pulse_surface = pygame.Surface((g_screen_width, g_screen_height))
    pulse_surface.set_alpha(pulse_alpha)
    pulse_surface.fill(Cfg.colors["gold"])
    surface.blit(pulse_surface, (0, 0))

    if g_game_state["combo"]["pulse"] > Cfg.combo_edge_pulse_threshold:
        edge_alpha = min(
            50,
            (g_game_state["combo"]["pulse"] - Cfg.combo_edge_pulse_threshold)
            * Cfg.combo_edge_pulse_multiplier,
        )
        for i in range(3):
            edge_surface = pygame.Surface((g_screen_width, g_screen_height), pygame.SRCALPHA)
            thickness = int(
                (Cfg.combo_edge_thickness_base - i * Cfg.combo_edge_thickness_step) * g_scale_factor
            )
            alpha = int(edge_alpha * (1 - i * Cfg.combo_edge_alpha_decay))
            color = (*Cfg.colors["gold"], alpha)

            pygame.draw.rect(edge_surface, color, (0, 0, g_screen_width, thickness))
            pygame.draw.rect(
                edge_surface, color, (0, g_screen_height - thickness, g_screen_width, thickness)
            )
            pygame.draw.rect(edge_surface, color, (0, 0, thickness, g_screen_height))
            pygame.draw.rect(
                edge_surface, color, (g_screen_width - thickness, 0, thickness, g_screen_height)
            )

            surface.blit(edge_surface, (0, 0))


def render_background(surface: pygame.Surface, shake_x: int, shake_y: int) -> None:
    """Render background elements.

    Args:
        surface: Surface to draw on
        shake_x: Screen shake X offset
        shake_y: Screen shake Y offset

    Globals:
        Reads g_game_state for frame count
    """
    surface.fill(Cfg.colors["black"])
    vfx.draw_stars(
        surface, shake_x, shake_y, g_game_state["frame_count"], g_screen_width, g_screen_height
    )

    # Create context for dust rendering
    ctx = {
        "ship": g_ship,
        "game_state": g_game_state,
        "screen_width": g_screen_width,
        "screen_height": g_screen_height,
    }
    vfx.update_and_draw_dust(surface, ctx)


def render_game_objects(
    game_surface: pygame.Surface, keys: dict, controller_input: Dict[str, Any]
) -> None:
    """Render all game objects to the game surface.

    Args:
        game_surface: Surface to draw game objects on
        keys: Keyboard state
        controller_input: Controller state

    Globals:
        Reads g_asteroids, g_enemies, g_game_state
    """
    if g_drawing:
        g_drawing.draw_powerups(game_surface, g_powerups)

    for asteroid in g_asteroids:
        if g_drawing:
            g_drawing.draw_asteroid(game_surface, asteroid, get_polygon_points)

    for enemy in g_enemies:
        if g_drawing:
            is_finisher_target = False
            if g_game_state["finisher"]["ready"] and not g_game_state["finisher"]["executing"]:
                target = check_finisher_collision(g_ship, g_ship.angle)
                is_finisher_target = target == enemy
            g_drawing.draw_enemy(game_surface, enemy, is_finisher_target, g_game_state)

    if g_game_state["finisher"]["ready"] and not g_game_state["finisher"]["executing"]:
        draw_finisher_target_indicator(game_surface)

    if g_game_state["finisher"]["phase"] == FinisherPhase.LOCK_ON:
        draw_lock_on_indicator(game_surface)

    if g_drawing:
        g_drawing.draw_ship(game_surface, g_ship, keys, controller_input, g_game_state)
        g_drawing.draw_bullets(game_surface, g_bullets, g_enemy_bullets)
        g_drawing.draw_particles(game_surface, g_particle_pool)

    if (
        g_game_state["finisher"]["phase"] == FinisherPhase.IMPACT
        and g_game_state["finisher"]["shockwave_radius"] > 0
    ):
        draw_shockwave(
            game_surface,
            g_game_state["finisher"]["impact_x"],
            g_game_state["finisher"]["impact_y"],
            g_game_state["finisher"]["shockwave_radius"],
        )

    draw_floating_texts(game_surface)


def render_effects_and_ui(
    surface: pygame.Surface, game_surface: pygame.Surface, shake_x: int, shake_y: int
) -> None:
    """Render effects, UI, and overlays.

    Args:
        surface: Main surface to draw on
        game_surface: Game objects surface to blit
        shake_x: Screen shake X offset
        shake_y: Screen shake Y offset

    Globals:
        Reads g_game_state for UI state
    """
    surface.blit(game_surface, (shake_x, shake_y))

    vfx.draw_level_transition(
        surface, g_game_state, g_screen_width, g_screen_height, g_scale_factor
    )
    vfx.draw_damage_flash(surface, g_game_state, g_screen_width, g_screen_height, g_scale_factor)
    draw_ui(surface)

    if g_game_state["show_upgrade_menu"]:
        draw_upgrade_menu(surface)

    if g_game_state["game_over"]:
        draw_game_over(surface)

    vfx.draw_crt_effects(surface, g_screen_width, g_screen_height, g_scale_factor)

    if g_game_state["paused"] or g_game_state["effects"]["pause_menu_alpha"] > 0:
        draw_pause_overlay(surface)


def render_to_surface(
    surface: pygame.Surface,
    shake_x: int,
    shake_y: int,
    keys: dict,
    controller_input: Dict[str, Any],
) -> None:
    """Render all game elements to surface.

    Args:
        surface: Surface to render to
        shake_x: Screen shake X offset
        shake_y: Screen shake Y offset
        keys: Keyboard state
        controller_input: Controller state

    Globals:
        Reads various game state and object lists
    """
    render_background(surface, shake_x, shake_y)

    game_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
    render_game_objects(game_surface, keys, controller_input)
    render_effects_and_ui(surface, game_surface, shake_x, shake_y)


# === [GAME RESET] ===


def reset_game() -> None:
    """Reset game to initial state.

    Side effects:
        Resets all game objects and state, preserves persistent data,
        stops sounds, creates new level

    Globals:
        Writes to most game state globals
    """
    global g_asteroids, g_bullets, g_powerups, g_floating_texts, g_enemies, g_enemy_bullets

    stop_all_sounds()

    persistent_data = {
        "high_score": g_game_state.get("high_score", 0),
        "lifetime_crystals": g_game_state.get("lifetime_crystals", 0),
        "achievements_unlocked": g_game_state.get("achievements_unlocked", set()),
        "upgrade_levels": g_game_state.get(
            "upgrade_levels", g_progression.get_default_upgrade_levels()
        ),
        "boss_kills": g_game_state.get("boss_kills", 0),
    }

    g_game_state.update(
        {
            "score": 0,
            "lives": 3,
            "level": 1,
            "game_over": False,
            "paused": False,
            "crystals": 0,
            "untouchable_level": True,
            "show_upgrade_menu": False,
            "selected_upgrade": 0,
            "bullet_cooldown": 0,
            "frame_count": 0,
            "pause_debounce": 0,
            "resize_pending": None,
            "resize_timer": 0,
            "thrust_sound_playing": False,
            "time_scale": 1.0,
            "effects": {
                "screen_shake": 0,
                "game_over_alpha": 0,
                "level_transition": 0,
                "level_transition_text": "",
                "damage_flash": 0,
                "damage_flash_color": Cfg.colors["damage_flash"],
                "aura_rotation": 0,
                "pause_menu_alpha": 0,
                "wave_warning": 0,
                "wave_warning_text": "",
            },
            "combo": {"current": 0, "timer": 0, "kills": 0, "max": 0, "pulse": 0},
            "dash": {"cooldown": 0},
            "finisher": {
                "meter": 0.0,
                "ready": False,
                "executing": False,
                "execution_timer": 0,
                "phase": FinisherPhase.IDLE,
                "target": None,
                "shockwave_radius": 0,
                "lock_on_progress": 0.0,
                "impact_x": 0,
                "impact_y": 0,
            },
        }
    )

    g_game_state.update(persistent_data)

    g_ship.rapid_fire = 0
    g_ship.triple_shot = 0
    g_ship.shield_active = 0
    g_ship.powerup_flash = 0
    g_ship.powerup_flash_color = (255, 255, 255)
    g_ship.respawning = 0
    g_ship.aura_pulse = 0
    g_ship.dashing = 0
    g_ship.dash_trail = []

    update_scaled_values()

    base_count = 4
    area_multiplier = (g_screen_width * g_screen_height) / (Cfg.screen_width * Cfg.screen_height)
    asteroid_count = int(base_count * math.sqrt(area_multiplier))

    g_asteroids = [create_asteroid() for _ in range(asteroid_count)]
    g_bullets = []
    g_particle_pool.clear()
    g_powerups = []
    g_floating_texts = []
    g_enemies = []
    g_enemy_bullets = []

    # Recreate space dust
    vfx.create_space_dust(g_screen_width, g_screen_height)
    reset_ship()


# === [MAIN GAME LOOP] ===


def handle_events() -> bool:
    """Process all pygame events.

    Returns:
        True if game should continue running

    Globals:
        Reads/writes g_game_state
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.VIDEORESIZE:
            g_game_state["resize_pending"] = (event.w, event.h)
            g_game_state["resize_timer"] = pygame.time.get_ticks()

        if (
            event.type == pygame.WINDOWFOCUSLOST
            and not g_game_state["game_over"]
            and not g_game_state["paused"]
        ):
            g_game_state["paused"] = True
            stop_thrust_sound()
            pygame.mixer.pause()

        if event.type == pygame.KEYDOWN:
            handle_keyboard_event(event)

        if event.type == pygame.JOYBUTTONDOWN and g_controller_connected:
            handle_controller_button_event(event)

    return True


def handle_input(keys: dict, controller_input: Dict[str, Any]) -> Tuple[dict, Dict[str, Any]]:
    """Process game input during gameplay.

    Args:
        keys: Keyboard state
        controller_input: Controller state

    Returns:
        Updated keys and controller input

    Side effects:
        May shoot bullets based on input

    Globals:
        Reads g_game_state, g_ship
    """
    if keys[pygame.K_SPACE] and g_game_state["bullet_cooldown"] <= 0 and g_ship.respawning == 0:
        shoot_bullet()

    return keys, controller_input


def update_game_state(keys: dict, controller_input: Dict[str, Any]) -> None:
    """Update all game logic.

    Args:
        keys: Keyboard state
        controller_input: Controller state

    Side effects:
        Updates all game objects and systems

    Globals:
        Reads/writes various game state
    """
    update_visual_effects()
    update_finisher()

    if g_game_state["effects"]["level_transition"] == 0:
        update_ship(keys, controller_input)
        update_game_objects()
        handle_collisions()

    if not g_asteroids and g_game_state["effects"]["level_transition"] == 0:
        g_game_state["level"] += 1
        g_game_state["effects"]["level_transition"] = Cfg.level_transition_duration
        g_game_state["effects"]["level_transition_text"] = f"LEVEL {g_game_state['level']}"
        g_game_state["effects"]["screen_shake"] = 10
        play_sound("level_transition", g_screen_width // 2)

    if g_game_state["effects"]["level_transition"] > 0:
        g_game_state["effects"]["level_transition"] = update_timer(
            g_game_state["effects"]["level_transition"]
        )
        if g_game_state["effects"]["level_transition"] == 0:
            start_new_level()

    if g_game_state["effects"]["damage_flash"] > 0:
        g_game_state["effects"]["damage_flash"] = update_timer(
            g_game_state["effects"]["damage_flash"], 2
        )


def run_game_loop() -> None:
    """Main game loop.

    Globals:
        Reads/writes most game state
    """
    prev_controller_shoot = False
    prev_controller_dash = False
    prev_keys_dash = False

    running = True
    while running:
        keys = pygame.key.get_pressed()
        check_controller_connection()
        controller_input = get_controller_input()

        running = handle_events()
        if not running:
            break

        if g_game_state["pause_debounce"] > 0:
            g_game_state["pause_debounce"] -= 1

        if (
            g_game_state["resize_pending"]
            and pygame.time.get_ticks() - g_game_state["resize_timer"] > Cfg.resize_debounce_time
        ):
            handle_resize(*g_game_state["resize_pending"])
            g_game_state["resize_pending"] = None

        if (
            not g_game_state["game_over"]
            and not g_game_state["paused"]
            and not g_game_state["show_upgrade_menu"]
        ):
            current_dash = (
                keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or controller_input["dash"]
            )
            prev_keys_dash, prev_controller_dash = handle_dash_input(
                current_dash, prev_keys_dash, prev_controller_dash
            )

            if (
                controller_input["shoot"]
                and not prev_controller_shoot
                and g_game_state["bullet_cooldown"] <= 0
                and g_ship.respawning == 0
            ):
                shoot_bullet()
            prev_controller_shoot = controller_input["shoot"]

            keys, controller_input = handle_input(keys, controller_input)
            update_game_state(keys, controller_input)

        update_pause_menu_fade()

        g_game_state["frame_count"] += 1

        shake_x, shake_y = calculate_screen_shake()

        render_frame(shake_x, shake_y, keys, controller_input)

        g_clock.tick(Cfg.fps)


def handle_keyboard_event(event: pygame.event.Event) -> None:
    """Handle keyboard input events.

    Args:
        event: Pygame keyboard event

    Globals:
        Reads/writes g_game_state
    """
    if event.key == pygame.K_ESCAPE and g_game_state["pause_debounce"] == 0:
        if g_game_state["show_upgrade_menu"]:
            g_game_state["show_upgrade_menu"] = False
        else:
            toggle_pause()

    if g_game_state["show_upgrade_menu"]:
        handle_upgrade_menu_keys(event)
    elif not g_game_state["paused"]:
        handle_game_keys(event)


def handle_upgrade_menu_keys(event: pygame.event.Event) -> None:
    """Handle input in upgrade menu.

    Args:
        event: Pygame keyboard event

    Globals:
        Reads/writes g_game_state
    """
    if event.key == pygame.K_UP:
        g_game_state["selected_upgrade"] = (g_game_state["selected_upgrade"] - 1) % len(
            Cfg.upgrades
        )
    elif event.key == pygame.K_DOWN:
        g_game_state["selected_upgrade"] = (g_game_state["selected_upgrade"] + 1) % len(
            Cfg.upgrades
        )
    elif event.key == pygame.K_RETURN:
        upgrade_keys = list(Cfg.upgrades.keys())
        selected = upgrade_keys[g_game_state["selected_upgrade"]]
        if apply_upgrade_wrapper(selected):
            play_sound("powerup_life")


def handle_game_keys(event: pygame.event.Event) -> None:
    """Handle input during gameplay.

    Args:
        event: Pygame keyboard event

    Globals:
        Reads/writes g_game_state, g_ship
    """
    if (
        event.key == pygame.K_SPACE
        and not g_game_state["game_over"]
        and g_game_state["bullet_cooldown"] <= 0
        and g_ship.respawning == 0
    ):
        shoot_bullet()
    elif event.key == pygame.K_RETURN and g_game_state["game_over"]:
        reset_game()
    elif event.key == pygame.K_s:
        toggle_sound()
    elif event.key == pygame.K_u:
        g_game_state["show_upgrade_menu"] = True
        g_game_state["selected_upgrade"] = 0


def toggle_pause() -> None:
    """Toggle game pause state.

    Side effects:
        Modifies g_game_state['paused'], g_game_state['pause_debounce'],
        stops/resumes sounds

    Globals:
        Reads/writes g_game_state
    """
    g_game_state["paused"] = not g_game_state["paused"]
    g_game_state["pause_debounce"] = Cfg.pause_debounce_frames
    if g_game_state["paused"]:
        stop_thrust_sound()
        if get_sound_enabled():
            pygame.mixer.pause()
    else:
        if get_sound_enabled():
            pygame.mixer.unpause()


def handle_controller_button_event(event: pygame.event.Event) -> None:
    """Handle controller button events.

    Args:
        event: Pygame controller button event

    Globals:
        Reads/writes g_game_state
    """
    if event.button in Cfg.controller_buttons["restart"] and g_game_state["pause_debounce"] == 0:
        if g_game_state["game_over"]:
            reset_game()
        else:
            toggle_pause()
    elif not g_game_state["paused"] and event.button in Cfg.controller_buttons["toggle_sound"]:
        toggle_sound()


def handle_dash_input(
    current_dash: bool, prev_keys_dash: bool, prev_controller_dash: bool
) -> Tuple[bool, bool]:
    """Handle dash/finisher input.

    Args:
        current_dash: Current dash input state
        prev_keys_dash: Previous keyboard dash state
        prev_controller_dash: Previous controller dash state

    Returns:
        Updated (prev_keys_dash, prev_controller_dash)

    Side effects:
        May execute dash or finisher move

    Globals:
        Reads g_game_state, g_ship, g_enemies
    """
    if current_dash and not prev_keys_dash and not prev_controller_dash:
        if g_game_state["dash"]["cooldown"] <= 0 and g_ship.respawning == 0 and g_ship.dashing == 0:
            if (
                g_game_state["finisher"]["ready"]
                and not g_game_state["finisher"]["executing"]
                and g_enemies
            ):
                target = check_finisher_collision(g_ship, g_ship.angle)
                if target:
                    start_finisher_execution(target)
                else:
                    execute_normal_dash()
            else:
                execute_normal_dash()

    return current_dash, current_dash


def execute_normal_dash() -> None:
    """Execute a normal dash move.

    Side effects:
        Modifies g_ship.dashing, g_game_state['dash']['cooldown'], plays sound

    Globals:
        Reads/writes g_ship, g_game_state
    """
    g_ship.dashing = Cfg.dash_duration
    g_game_state["dash"]["cooldown"] = Cfg.dash_cooldown - get_dash_cooldown_reduction_wrapper()
    play_sound("dash", g_ship.x)


def update_pause_menu_fade() -> None:
    """Update pause menu fade animation.

    Side effects:
        Modifies g_game_state['effects']['pause_menu_alpha']

    Globals:
        Reads/writes g_game_state
    """
    if g_game_state["effects"]["pause_menu_alpha"] < 255 and g_game_state["paused"]:
        g_game_state["effects"]["pause_menu_alpha"] = min(
            255, g_game_state["effects"]["pause_menu_alpha"] + Cfg.pause_fade_speed
        )
    elif g_game_state["effects"]["pause_menu_alpha"] > 0 and not g_game_state["paused"]:
        g_game_state["effects"]["pause_menu_alpha"] = max(
            0, g_game_state["effects"]["pause_menu_alpha"] - Cfg.pause_fade_speed
        )


def calculate_screen_shake() -> Tuple[int, int]:
    """Calculate screen shake offset.

    Returns:
        (shake_x, shake_y) offset tuple

    Side effects:
        Decreases g_game_state['effects']['screen_shake']

    Globals:
        Reads/writes g_game_state
    """
    shake_x, shake_y = 0, 0
    if g_game_state["effects"]["screen_shake"] > 0:
        if not g_game_state["paused"]:
            g_game_state["effects"]["screen_shake"] = max(
                0, g_game_state["effects"]["screen_shake"] - Cfg.screen_shake_decay
            )
        shake_x = random.randint(
            -int(g_game_state["effects"]["screen_shake"]),
            int(g_game_state["effects"]["screen_shake"]),
        )
        shake_y = random.randint(
            -int(g_game_state["effects"]["screen_shake"]),
            int(g_game_state["effects"]["screen_shake"]),
        )
    return shake_x, shake_y


# === [ENTRY POINT] ===


def main() -> None:
    """Main entry point for the game.

    Globals:
        Initializes and uses most global variables
    """
    global g_screen, g_clock, g_font, g_big_font, g_small_font, g_tiny_font, g_screen_width, g_screen_height, g_progression

    try:
        pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=256)
        pygame.init()
    except pygame.error as e:
        print(f"[main] Failed to initialize Pygame: {e}")
        sys.exit(1)

    g_screen = pygame.display.set_mode((g_screen_width, g_screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Asteroids Enhanced")
    g_clock = pygame.time.Clock()

    # Initialize progression system with dependency injection
    g_progression = ProgressionSystem(
        create_floating_text=create_floating_text, update_scaled_values=update_scaled_values
    )

    load_game_state_wrapper()

    handle_resize(g_screen_width, g_screen_height)
    init_controller()
    init_sounds()
    init_ship_state()

    reset_game()
    run_game_loop()

    save_game_state_wrapper()

    pygame.quit()


if __name__ == "__main__":
    main()
