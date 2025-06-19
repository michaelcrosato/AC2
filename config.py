"""
Configuration module for the Asteroids game.

This module contains all game configuration constants, settings, and configuration dictionaries.
"""

from typing import Dict, List, Tuple, Any, Callable
from data_structures import PowerUpType, EnemyAIType, ParticleType, FinisherPhase


class Cfg:
    """Centralized game configuration."""

    # Screen settings
    screen_width: int = 800
    screen_height: int = 600
    fps: int = 60
    reference_height: int = 600

    # Color palette
    colors = {
        "black": (0, 0, 10),
        "white": (255, 255, 255),
        "blue_glow": (100, 150, 255),
        "asteroid": (200, 200, 255),
        "bullet": (255, 255, 100),
        "star": (100, 100, 150),
        "crystal": (150, 255, 255),
        "enemy": (255, 100, 100),
        "boss": (255, 50, 50),
        "gold": (255, 215, 0),
        "damage_flash": (255, 0, 0),
        "shield_flash": (0, 150, 255),
        "dash": (100, 200, 255),
        "score_text": (255, 255, 100),
        "enemy_bullet": (255, 150, 150),
    }

    # Ship parameters
    ship_max_speed: float = 6.4
    ship_turn_speed: int = 6
    ship_thrust_power: float = 0.5
    ship_reverse_thrust_multiplier: float = 0.4
    ship_friction: float = 0.985
    ship_radius: int = 10
    ship_nose_length: int = 15
    ship_wing_length: int = 10
    ship_back_indent: int = 5
    ship_wing_angle: int = 140
    ship_flame_angle: int = 150
    ship_max_lives: int = 5
    ship_invulnerability_time: int = 120
    ship_respawn_duration: int = 90
    ship_thruster_particle_count: int = 2

    # Weapon settings
    bullet_radius: int = 2
    bullet_speed: int = 12
    bullet_lifetime: int = 50
    normal_fire_rate: int = 10
    rapid_fire_rate: int = 5
    triple_shot_spread: int = 10
    bullet_trail_length: int = 8
    enemy_bullet_trail_length: int = 6
    enemy_bullet_speed_mult: float = 0.8

    # Asteroid settings
    asteroid_min_size: int = 1
    asteroid_max_size: int = 3
    asteroid_base_speed: float = 2.0
    asteroid_speed_multiplier: float = 1.5
    asteroid_speed_size_adjustment: float = 0.2
    asteroid_collision_margin: int = 12
    asteroid_spawn_margin: int = 50
    asteroid_hit_flash_duration: int = 8
    asteroid_scores = {3: 100, 2: 50, 1: 20}
    asteroid_crystal_chance: float = 0.2
    asteroid_split_count: int = 2
    asteroid_vertex_count: int = 8
    asteroid_shape_variance_min: int = 8
    asteroid_shape_variance_max: int = 12

    # Boss settings
    boss_health: int = 50
    boss_spawn_interval: int = 5
    boss_size_multiplier: int = 3
    boss_speed_multiplier: float = 0.5
    boss_rotation_multiplier: float = 0.3
    boss_score: int = 1000
    boss_crystal_drops: int = 5
    boss_health_bar_width: int = 100
    boss_health_bar_height: int = 8
    boss_health_bar_offset: int = 20

    # Enemy settings
    enemy_speed: float = 1.5
    enemy_fire_rate: int = 90
    enemy_fire_rate_variance: int = 10
    enemy_max_count: int = 2
    enemy_spawn_chance: float = 0.1
    enemy_min_spawn_distance: int = 200
    enemy_spawn_margin: int = 50
    enemy_max_spawn_attempts: int = 10
    enemy_score: int = 200
    enemy_aim_inaccuracy: int = 5
    enemy_friction: float = 0.96
    enemy_speed_reduction: float = 0.75
    enemy_min_distance: int = 100
    enemy_radius: int = 12
    enemy_health: int = 3
    enemy_firing_warning_frames: int = 20
    enemy_volume: float = 0.4
    enemy_min_fire_distance: int = 50
    enemy_max_fire_distance: int = 250
    enemy_crystal_drop_chance: float = 0.5

    # Enemy AI parameters
    enemy_ai = {
        "hunter": {"approach_rate": 0.05, "retreat_rate": 0.1},
        "circler": {"orbit_speed": 1.5, "orbit_radius": 180, "approach_rate": 0.08},
    }

    # Dash mechanics
    dash_cooldown: int = 120
    dash_duration: int = 15
    dash_speed_multiplier: float = 3.0
    dash_trail_max_length: int = 10
    dash_trail_particle_count: int = 3
    dash_trail_offset_range: int = 10

    # Finisher mechanics
    finisher_lock_on_time: int = 30
    finisher_pre_impact_time: int = 6
    finisher_impact_time: int = 60
    finisher_post_impact_time: int = 30
    finisher_lock_on_scale: float = 0.5
    finisher_time_scale: float = 0.1
    finisher_shockwave_radius: int = 200
    finisher_damage_close: int = 3
    finisher_damage_far: int = 2
    finisher_knockback_force: int = 15
    finisher_particle_count: int = 100
    finisher_score: int = 500
    finisher_volume: float = 0.6
    finisher_shockwave_close_range: float = 0.5
    finisher_core_particles: int = 40
    finisher_mid_particles: int = 70
    finisher_shockwave_rings: int = 48
    finisher_ring_count: int = 3
    finisher_invuln_buffer: float = 0.5

    # Combo system
    combo_timeout: int = 180
    combo_pulse_interval: int = 10
    combo_pulse_max_alpha: int = 100
    combo_milestone_thresholds = [5, 10, 15, 20]
    combo_text_threshold: int = 5
    combo_fill_rates = {"base": 10, "medium": 15, "high": 20}
    combo_medium_threshold: int = 5
    combo_high_threshold: int = 10
    combo_max_pulse: int = 20

    # Powerup settings
    powerup_drop_chance: float = 0.2
    powerup_lifetime: int = 600
    powerup_rapid_fire_duration: int = 600
    powerup_triple_shot_duration: int = 600
    powerup_shield_duration: int = 300
    powerup_pickup_radius: int = 15
    powerup_visual_radius: int = 20
    powerup_symbol_offset_x: int = 8
    powerup_symbol_offset_y: int = 10
    powerup_aura_rotation_speed: int = 2
    powerup_aura_pulse_speed: float = 0.1
    powerup_crystal_value: int = 10
    powerup_volume: float = 0.35
    powerup_crystal_chance: float = 0.3
    powerup_area_scaling_factor: float = 0.3
    powerup_hexagon_vertices: int = 6

    # Particle system
    particle_limit: int = 500
    particle_base_life: int = 30
    particle_life_variance: int = 20
    particle_explosion_count: int = 20
    particle_explosion_large: int = 30
    particle_explosion_small: int = 15
    particle_ship_explosion: int = 50
    particle_thruster_count: int = 2
    particle_respawn_rate: int = 3
    particle_shockwave_rings: int = 48
    particle_muzzle_flash_base: int = 3
    particle_muzzle_flash_triple: int = 5
    particle_thruster_spread: int = 3
    particle_thruster_speed: int = 3
    particle_thruster_velocity_spread: float = 0.5
    particle_respawn_spiral_min: int = 30
    particle_respawn_spiral_max: int = 60
    particle_respawn_center_chance: float = 0.3
    particle_respawn_center_spread: int = 10
    particle_streak_attraction_distance: int = 100
    particle_streak_attraction_force: float = 0.15
    particle_streak_min_life: int = 5
    particle_dash_trail_life: int = 20
    particle_powerup_flash_duration: int = 20
    particle_powerup_flash_max: int = 30

    # UI layout
    ui_margin: int = 10
    ui_element_spacing: int = 40
    ui_health_pip_spacing: int = 10
    ui_high_score_y_offset: int = 18
    ui_combo_pip_spacing: int = 6
    ui_combo_pip_radius: int = 2
    ui_combo_pip_y_offset: int = 25
    ui_dash_bar_width: int = 60
    ui_dash_bar_height: int = 6
    ui_finisher_bar_width: int = 60
    ui_finisher_bar_height: int = 6
    ui_sound_status_y_offset: int = 25
    ui_powerup_indicator_y_base: int = 230
    ui_powerup_indicator_spacing: int = 25
    ui_upgrade_menu_y_start: int = 150
    ui_upgrade_menu_item_height: int = 80
    ui_upgrade_menu_padding: int = 20
    ui_game_over_y_offset: int = 100
    ui_game_over_stat_spacing: int = 40
    ui_game_over_restart_offset: int = 20
    ui_pause_menu_y_start: int = 150
    ui_pause_menu_line_spacing: int = 35
    ui_pause_menu_achievement_offset: int = 20

    # Visual effects
    screen_shake_decay: int = 1
    max_screen_shake: int = 20
    level_transition_duration: int = 120
    damage_flash_duration: int = 60
    shield_flash_duration: int = 30
    resize_debounce_time: int = 200
    scanline_spacing: int = 3
    scanline_alpha: int = 30
    vignette_strength: float = 0.4
    vignette_steps: int = 20
    star_count_base: int = 150
    star_twinkle_speed_min: float = 0.02
    star_twinkle_speed_max: float = 0.08
    star_twinkle_amount_min: float = 0.3
    star_twinkle_amount_max: float = 0.7
    star_parallax_factor: float = 0.5
    dust_count_base: int = 100
    dust_parallax: float = 0.3
    floating_text_life: int = 60
    floating_text_speed: int = 2
    floating_text_friction: float = 0.95
    floating_text_spread: int = 10
    level_text_scale_min: float = 0.5
    level_text_scale_max: float = 2.0
    level_text_appear_threshold: float = 0.3
    level_text_fade_threshold: float = 0.7
    damage_flash_pulse_threshold: float = 0.8
    damage_flash_pulse_speed: float = 0.5
    damage_flash_tint_threshold: float = 0.5
    damage_flash_tint_alpha: int = 30
    combo_pulse_fade_rate: int = 2
    combo_edge_pulse_threshold: int = 10
    combo_edge_pulse_multiplier: int = 3
    combo_edge_thickness_base: int = 30
    combo_edge_thickness_step: int = 8
    combo_edge_alpha_decay: float = 0.3
    pause_fade_speed: int = 15
    game_over_fade_speed: int = 3

    # Sound settings
    sound_enabled: bool = False
    sound_master_volume: float = 0.3
    sound_shoot_volume: float = 0.3
    sound_explosion_volume: float = 0.5
    sound_thrust_volume: float = 0.15
    sound_shoot_variations: int = 3
    sound_explosion_variations: int = 2

    # Controller mappings
    controller_deadzone: float = 0.25
    controller_turn_multiplier: float = 1.2
    controller_axis_threshold: float = 0.5
    controller_buttons = {
        "shoot": [0],
        "thrust": [1],
        "reverse": [2],
        "dash": [3],
        "toggle_sound": [6],
        "restart": [7],
    }

    # Upgrade definitions
    upgrades = {
        "damage": {
            "name": "Damage",
            "max_level": 5,
            "cost_multiplier": 1.5,
            "base_cost": 100,
            "description": "Increases bullet damage",
            "multiplier_per_level": 0.2,
        },
        "fire_rate": {
            "name": "Fire Rate",
            "max_level": 5,
            "cost_multiplier": 1.4,
            "base_cost": 80,
            "description": "Shoot faster",
            "reduction_per_level": 0.1,
        },
        "max_speed": {
            "name": "Max Speed",
            "max_level": 5,
            "cost_multiplier": 1.3,
            "base_cost": 60,
            "description": "Increase ship speed",
            "multiplier_per_level": 0.15,
        },
        "dash_cooldown": {
            "name": "Dash Cooldown",
            "max_level": 3,
            "cost_multiplier": 2.0,
            "base_cost": 150,
            "description": "Dash more frequently",
            "reduction_per_level": 20,
        },
    }

    # Achievement definitions
    achievements = {
        "first_blood": {"name": "First Blood", "desc": "Destroy your first asteroid", "reward": 50},
        "combo_5": {"name": "Combo x5", "desc": "Get a 5x combo", "reward": 100},
        "combo_10": {"name": "Combo Master", "desc": "Get a 10x combo", "reward": 200},
        "survivor": {"name": "Survivor", "desc": "Reach level 10", "reward": 300},
        "boss_slayer": {"name": "Boss Slayer", "desc": "Defeat your first boss", "reward": 500},
        "untouchable": {"name": "Untouchable", "desc": "Complete level undamaged", "reward": 200},
        "speed_demon": {"name": "Speed Demon", "desc": "Max out speed upgrade", "reward": 150},
        "crystal_hoarder": {
            "name": "Crystal Hoarder",
            "desc": "Collect 1000 crystals",
            "reward": 250,
        },
    }

    # Achievement thresholds
    achievement_survivor_level: int = 10
    achievement_speed_demon_level: int = 5
    achievement_crystal_hoarder_amount: int = 1000

    # Powerup type definitions
    powerup_types = {
        PowerUpType.RAPID: {"color": (255, 100, 0), "symbol": "R"},
        PowerUpType.TRIPLE: {"color": (0, 255, 255), "symbol": "3"},
        PowerUpType.SHIELD: {"color": (0, 255, 0), "symbol": "S"},
        PowerUpType.LIFE: {"color": (255, 0, 255), "symbol": "♥"},
        PowerUpType.CRYSTAL: {"color": (150, 255, 255), "symbol": "◆"},
    }

    # Particle renderer definitions
    particle_renderers = {
        ParticleType.STREAK: {
            "radius_calc": lambda p, s: max(1, int(4 * (p.life / 30.0) ** 0.5 * s)),
            "has_glow": True,
            "glow_factor": 0.5,
        },
        ParticleType.RESPAWN: {
            "radius_calc": lambda p, s: max(1, int(3 * (p.life / Cfg.particle_base_life) * s)),
            "has_glow": True,
            "glow_factor": 0.7,
            "glow_radius": 3,
        },
        ParticleType.DASH: {
            "radius_calc": lambda p, s: max(1, int(2 * (p.life / Cfg.particle_base_life) * s)),
            "has_glow": lambda p: p.life / Cfg.particle_base_life > 0.5,
            "glow_radius": 2,
        },
        ParticleType.FINISHER: {
            "radius_calc": lambda p, s: max(1, int((3 + p.life // 8) * s)),
            "has_glow": lambda p: p.life / Cfg.particle_base_life > 0.5,
            "glow_radius": 2,
        },
    }

    # Explosion lookup table
    explosion_config = {3: ((255, 150, 50), 30), 2: ((200, 200, 100), 20), 1: ((150, 150, 255), 15)}

    # Drawing effect constants (extracted from magic numbers)
    glow_default_layers: int = 3
    glow_layer_alpha_base: int = 50
    glow_layer_alpha_step: int = 15
    glow_layer_radius_step: int = 2
    respawn_spiral_layers: int = 3
    respawn_spiral_radius_start: int = 50
    respawn_spiral_radius_step: int = 3
    flame_length_min: int = 8
    flame_length_max: int = 18
    flame_width_min: int = 4
    flame_width_max: int = 8
    finisher_lock_text_appear_threshold: float = 0.5
    finisher_lock_text_y_offset: int = 40
    finisher_reticle_size_base: int = 20
    finisher_reticle_size_variation: int = 10
    finisher_reticle_bracket_ratio: float = 0.4
    finisher_reticle_thickness: int = 3
    finisher_dash_preview_segments: int = 15
    finisher_dash_preview_alpha: int = 80

    # Save file path
    save_file: str = "asteroids_save.json"

    # UI Magic Number Constants (extracted for clarity)
    ship_invulnerability_blink_interval: int = 10
    ship_invulnerability_blink_visible_frames: int = 5
    pause_debounce_frames: int = 20
    frame_visibility_check_modulo: int = 4
    controller_input_check_modulo: int = 2
