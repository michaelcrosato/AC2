"""
Drawing system for the Asteroids game.

This module contains all drawing-related functionality moved from main.py
to improve code organization and modularity.
"""

import pygame
import math
import random
from typing import Dict, Any, List, Tuple, Optional, Union

from config import Cfg
from data_structures import ShipState, Asteroid, Enemy, PowerUp, FloatingText, PowerUpType, EnemyAIType
# Do NOT import from main to avoid circular imports


class DrawingSystem:
    """Centralized drawing system for the Asteroids game."""
    
    def __init__(self, fonts: Dict[str, pygame.font.Font], text_cache, scale_factor_fn):
        """Initialize the drawing system.
        
        Args:
            fonts: Dictionary of font objects {'main': font, 'big': font, 'small': font, 'tiny': font}
            text_cache: Text cache instance for efficient text rendering
            scale_factor_fn: Callable that returns current scale factor
        """
        self.fonts = fonts
        self.text_cache = text_cache
        self.get_scale_factor = scale_factor_fn
    
    def glow(self, surface: pygame.Surface, pos: Tuple[float, float], radius: float, 
             color: Tuple[int, int, int], intensity: float = 1.0, 
             layers: Optional[int] = None) -> None:
        """Draw a multi-layered glow effect.
        
        Args:
            surface: Surface to draw on
            pos: Center position (x, y)
            radius: Glow radius
            color: RGB color tuple
            intensity: Glow intensity (0-1)
            layers: Number of glow layers (defaults to config value)
        """
        if layers is None:
            layers = Cfg.glow_default_layers
            
        scaled_radius = int(radius)
        if scaled_radius <= 0:
            return
        
        for i in range(layers):
            alpha = int((Cfg.glow_layer_alpha_base - i * Cfg.glow_layer_alpha_step) * intensity)
            if alpha <= 0:
                continue
                
            layer_radius = scaled_radius - i * Cfg.glow_layer_radius_step
            if layer_radius <= 0:
                continue
                
            glow_surface = pygame.Surface((scaled_radius * 2, scaled_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*color, alpha), 
                             (scaled_radius, scaled_radius), layer_radius)
            surface.blit(glow_surface, (int(pos[0] - scaled_radius), int(pos[1] - scaled_radius)))
    
    def polygon_with_flash(self, surface: pygame.Surface, entity: Union[Asteroid, Enemy], 
                          points: List[Tuple[float, float]], base_color: Tuple[int, int, int],
                          border_width: int = 2) -> None:
        """Draw polygon entity with hit flash support.
        
        Args:
            surface: Surface to draw on
            entity: Entity with hit_flash attribute
            points: Polygon points
            base_color: Normal color when not flashing
            border_width: Line width
        """
        scale_factor = self.get_scale_factor()
        
        if entity.hit_flash > 0:
            flash_intensity = entity.hit_flash / Cfg.asteroid_hit_flash_duration
            flash_color = tuple(int(200 + 55 * flash_intensity) for _ in range(3))
            pygame.draw.polygon(surface, flash_color, points, max(1, int(3 * scale_factor)))
            
            # Flash glow
            self.glow(surface, (entity.x, entity.y), 
                     entity.radius * 2 * scale_factor * flash_intensity,
                     (255, 255, 255), flash_intensity)
        else:
            pygame.draw.polygon(surface, base_color, points, max(1, int(border_width * scale_factor)))
    
    def health_bar(self, surface: pygame.Surface, entity: Union[Asteroid, Enemy], 
                  width: int, height: int, offset: int) -> None:
        """Draw a health bar for any entity with health.
        
        Args:
            surface: Surface to draw on
            entity: Entity with health and max_health attributes
            width: Bar width (unscaled)
            height: Bar height (unscaled)
            offset: Vertical offset from entity center (unscaled)
        """
        if not hasattr(entity, 'health') or not hasattr(entity, 'max_health'):
            return
        
        scale_factor = self.get_scale_factor()
        bar_width = int(width * scale_factor)
        bar_height = int(height * scale_factor)
        bar_x = entity.x - bar_width // 2
        bar_y = entity.y - int(offset * scale_factor)
        
        # Background
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Health fill
        health_percent = entity.health / entity.max_health
        health_color = (255, int(255 * health_percent), 0)
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, bar_width * health_percent, bar_height))
        
        # Border
        pygame.draw.rect(surface, Cfg.colors['white'], (bar_x, bar_y, bar_width, bar_height), 1)
    
    def floating_text(self, surface: pygame.Surface, text_obj: FloatingText) -> None:
        """Draw a floating text effect.
        
        Args:
            surface: Surface to draw on
            text_obj: FloatingText object
        """
        alpha = text_obj.life / Cfg.floating_text_life
        color = tuple(int(c * alpha) for c in text_obj.color)
        
        text_surface = self.fonts['small'].render(text_obj.text, True, color)
        text_rect = text_surface.get_rect(center=(int(text_obj.x), int(text_obj.y)))
        surface.blit(text_surface, text_rect)
    
    def enemy_health_pips(self, surface: pygame.Surface, enemy: Enemy) -> None:
        """Draw health pips for an enemy.
        
        Args:
            surface: Surface to draw on
            enemy: Enemy object
        """
        scale_factor = self.get_scale_factor()
        
        for i in range(int(enemy.health)):
            pip_x = enemy.x - Cfg.ui_health_pip_spacing * scale_factor + i * Cfg.ui_health_pip_spacing * scale_factor
            pip_y = enemy.y + 20 * scale_factor
            pygame.draw.circle(surface, (255, 100, 100), (int(pip_x), int(pip_y)), 
                             int(2 * scale_factor))
    
    # Helper methods
    def _get_sin_cos(self, angle: float) -> Tuple[float, float]:
        """Get sin and cos values for an angle."""
        return math.sin(math.radians(angle)), math.cos(math.radians(angle))
    
    def _calculate_pulse(self, time: float, frequency: float = 0.1, amplitude: float = 0.5, offset: float = 0.5) -> float:
        """Calculate a pulsing value."""
        return amplitude * math.sin(time * frequency) + offset
    
    def _get_polygon_points(self, obj: Any, num_points: int, base_radius: float, 
                           shape_offsets: Optional[list] = None, angle_override: Optional[float] = None) -> List[Tuple[float, float]]:
        """Get polygon points for an object."""
        scale_factor = self.get_scale_factor()
        points = []
        angle_start = angle_override if angle_override is not None else (obj.angle if hasattr(obj, 'angle') else 0)
        
        for i in range(num_points):
            angle = angle_start + (360 / num_points) * i
            offset = shape_offsets[i] if shape_offsets and i < len(shape_offsets) else 1.0
            radius = base_radius * offset * scale_factor
            sin_a, cos_a = self._get_sin_cos(angle)
            x = obj.x + radius * cos_a
            y = obj.y + radius * sin_a
            points.append((x, y))
        
        return points
    
    def _get_ship_points(self, x: float, y: float, angle: float, scale_mult: float = 1.0) -> List[Tuple[float, float]]:
        """Get ship polygon points."""
        sin_a, cos_a = self._get_sin_cos(angle)
        sin_wing_left, cos_wing_left = self._get_sin_cos(angle + Cfg.ship_wing_angle)
        sin_wing_right, cos_wing_right = self._get_sin_cos(angle - Cfg.ship_wing_angle)
        
        return [
            (x + self._scaled(Cfg.ship_nose_length) * cos_a * scale_mult, 
             y + self._scaled(Cfg.ship_nose_length) * sin_a * scale_mult),
            (x + self._scaled(Cfg.ship_wing_length) * cos_wing_left * scale_mult, 
             y + self._scaled(Cfg.ship_wing_length) * sin_wing_left * scale_mult),
            (x - self._scaled(Cfg.ship_back_indent) * cos_a * scale_mult, 
             y - self._scaled(Cfg.ship_back_indent) * sin_a * scale_mult),
            (x + self._scaled(Cfg.ship_wing_length) * cos_wing_right * scale_mult, 
             y + self._scaled(Cfg.ship_wing_length) * sin_wing_right * scale_mult)
        ]
    
    def _scaled(self, value: float) -> float:
        """Scale a value by the current scale factor."""
        return value * self.get_scale_factor()
    
    # Object Drawing Methods
    def draw_asteroid(self, surface: pygame.Surface, asteroid: Asteroid, get_polygon_points_func) -> None:
        """Draw an asteroid entity.
        
        Args:
            surface: Surface to draw on
            asteroid: Asteroid to draw
            get_polygon_points_func: Function to get polygon points
        """
        points = get_polygon_points_func(asteroid, Cfg.asteroid_vertex_count, asteroid.radius, asteroid.shape)
        
        if asteroid.is_boss:
            base_color = Cfg.colors['boss']
            glow_color = (255, 100, 100)
        elif asteroid.has_crystals:
            base_color = (150, 200, 255)
            glow_color = Cfg.colors['crystal']
        else:
            base_color = Cfg.colors['asteroid']
            glow_color = tuple(int(c * 0.7) for c in Cfg.colors['star'])[:3]
        
        scale_factor = self.get_scale_factor()
        glow_intensity = 0.6 + (asteroid.size / Cfg.asteroid_max_size) * 0.4
        glow_color_list = [int(c * glow_intensity) for c in glow_color]
        glow_color = (glow_color_list[0], glow_color_list[1], glow_color_list[2])
        
        self.glow(surface, (asteroid.x, asteroid.y), 
                  asteroid.size * 15 * scale_factor, glow_color)
        self.polygon_with_flash(surface, asteroid, points, base_color)
        
        if asteroid.is_boss and asteroid.health:
            self.health_bar(surface, asteroid, Cfg.boss_health_bar_width,
                           Cfg.boss_health_bar_height, 
                           int(asteroid.radius + Cfg.boss_health_bar_offset))
    
    def draw_enemy(self, surface: pygame.Surface, enemy: Enemy, is_finisher_target: bool, 
                   game_state: Dict[str, Any]) -> None:
        """Draw an enemy entity.
        
        Args:
            surface: Surface to draw on
            enemy: Enemy to draw
            is_finisher_target: Whether this enemy is a finisher target
            game_state: Current game state
        """
        scale_factor = self.get_scale_factor()
        
        if is_finisher_target:
            pulse = self._calculate_pulse(game_state['frame_count'], 0.1, 0.3, 0.7)
            self.glow(surface, (enemy.x, enemy.y), 25 * pulse * scale_factor, 
                      Cfg.colors['gold'], pulse)
        else:
            self.glow(surface, (enemy.x, enemy.y), enemy.radius * 1.2 * scale_factor,
                      Cfg.colors['enemy'], 0.8)
        
        sin_a, cos_a = self._get_sin_cos(enemy.angle)
        
        points = [
            (enemy.x + 15 * scale_factor * cos_a, enemy.y + 15 * scale_factor * sin_a),
            (enemy.x + 10 * scale_factor * cos_a * 0.7 - 10 * scale_factor * sin_a, 
             enemy.y + 10 * scale_factor * sin_a * 0.7 + 10 * scale_factor * cos_a),
            (enemy.x - 10 * scale_factor * cos_a, enemy.y - 10 * scale_factor * sin_a),
            (enemy.x + 10 * scale_factor * cos_a * 0.7 + 10 * scale_factor * sin_a, 
             enemy.y + 10 * scale_factor * sin_a * 0.7 - 10 * scale_factor * cos_a),
        ]
        
        ship_color = (255, 255, 255) if enemy.hit_flash > 0 else Cfg.colors['enemy']
        pygame.draw.polygon(surface, ship_color, points, max(1, int(2 * scale_factor)))
        
        if is_finisher_target:
            pygame.draw.polygon(surface, Cfg.colors['gold'], points, max(1, int(3 * scale_factor)))
        
        if enemy.ai_type == EnemyAIType.HUNTER:
            size = 4 * scale_factor
            color = (200, 50, 50)
            pygame.draw.line(surface, color, (enemy.x - size, enemy.y), (enemy.x + size, enemy.y), 1)
            pygame.draw.line(surface, color, (enemy.x, enemy.y - size), (enemy.x, enemy.y + size), 1)
        else:
            pygame.draw.circle(surface, (200, 50, 50), (int(enemy.x), int(enemy.y)), 
                              int(3 * scale_factor), 1)
        
        if enemy.fire_cooldown < Cfg.enemy_firing_warning_frames and enemy.fire_cooldown > 0:
            warning_x = enemy.x + 20 * scale_factor * cos_a
            warning_y = enemy.y + 20 * scale_factor * sin_a
            warning_intensity = (Cfg.enemy_firing_warning_frames - enemy.fire_cooldown) / Cfg.enemy_firing_warning_frames
            warning_radius = int(5 * warning_intensity * scale_factor)
            if warning_radius > 0:
                self.glow(surface, (warning_x, warning_y), warning_radius, 
                         (255, 200, 0), warning_intensity)
        
        self.enemy_health_pips(surface, enemy)
    
    def draw_ship(self, surface: pygame.Surface, ship: ShipState, keys: dict, controller_input: Dict[str, Any],
                  game_state: Dict[str, Any]) -> None:
        """Draw the player ship.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
            keys: Keyboard state
            controller_input: Controller state
            game_state: Current game state
        """
        if game_state['game_over']:
            return
        
        if ship.respawning > 0:
            self.draw_respawn_animation(surface, ship, game_state)
            return
        
        if (ship.invulnerable > 0 and 
            ship.invulnerable % Cfg.ship_invulnerability_blink_interval >= Cfg.ship_invulnerability_blink_visible_frames and 
            ship.respawning == 0):
            return
        
        self.draw_dash_trail(surface, ship)
        
        if game_state['finisher']['ready']:
            self.draw_finisher_aura(surface, ship, game_state)
        
        self.draw_powerup_auras(surface, ship, game_state)
        
        scale_factor = self.get_scale_factor()
        
        if ship.shield_active > 0:
            self.glow(surface, (ship.x, ship.y), 30 * scale_factor, (0, 255, 0))
            pygame.draw.circle(surface, (0, 255, 0), (int(ship.x), int(ship.y)), 
                              int(25 * scale_factor), max(1, int(2 * scale_factor)))
        
        self.glow(surface, (ship.x, ship.y), 20 * scale_factor, Cfg.colors['blue_glow'])
        
        if ship.powerup_flash > 0:
            self.draw_powerup_flash(surface, ship)
        
        self.draw_ship_body(surface, ship, game_state)
        self.draw_thruster_flame(surface, ship, keys, controller_input, game_state)
    
    def draw_respawn_animation(self, surface: pygame.Surface, ship: ShipState, game_state: Dict[str, Any]) -> None:
        """Draw ship respawn animation.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
            game_state: Current game state
        """
        progress = 1.0 - (ship.respawning / Cfg.ship_respawn_duration)
        scale_factor = self.get_scale_factor()
        
        for i in range(Cfg.respawn_spiral_layers):
            radius = (Cfg.respawn_spiral_radius_start * (1 - progress) - i * Cfg.respawn_spiral_radius_step) * scale_factor
            if radius > 0:
                alpha = (1 - progress) * (1 - i * 0.3)
                self.glow(surface, (ship.x, ship.y), radius, 
                         Cfg.colors['blue_glow'], alpha)
        
        if progress > Cfg.level_text_appear_threshold:
            if game_state['frame_count'] % Cfg.frame_visibility_check_modulo < Cfg.controller_input_check_modulo:
                return
    
    def draw_dash_trail(self, surface: pygame.Surface, ship: ShipState) -> None:
        """Draw dash trail effect.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
        """
        for i, trail in enumerate(ship.dash_trail):
            alpha = trail['life'] / Cfg.particle_dash_trail_life
            ghost_points = self._get_ship_points(trail['x'], trail['y'], trail['angle'], 0.8)
            
            ghost_color = tuple(int(c * alpha) for c in Cfg.colors['dash'])
            pygame.draw.polygon(surface, ghost_color, ghost_points, 1)
    
    def draw_finisher_aura(self, surface: pygame.Surface, ship: ShipState, game_state: Dict[str, Any]) -> None:
        """Draw finisher ready aura.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
            game_state: Current game state
        """
        pulse = self._calculate_pulse(ship.aura_pulse, 1.0, 0.3, 0.7)
        scale_factor = self.get_scale_factor()
        
        for i in range(8):
            angle = game_state['effects']['aura_rotation'] + i * 45
            sin_a, cos_a = self._get_sin_cos(angle)
            radius = (self._scaled(Cfg.ship_radius) + 15 * scale_factor) * pulse
            px = ship.x + cos_a * radius
            py = ship.y + sin_a * radius
            
            self.glow(surface, (px, py), 10 * scale_factor, Cfg.colors['gold'], pulse)
    
    def draw_powerup_flash(self, surface: pygame.Surface, ship: ShipState) -> None:
        """Draw powerup collection flash effect.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
        """
        flash_intensity = ship.powerup_flash / Cfg.particle_powerup_flash_duration
        max_flash = Cfg.particle_powerup_flash_max if ship.powerup_flash > Cfg.particle_powerup_flash_duration else Cfg.particle_powerup_flash_duration
        flash_intensity = min(1.0, ship.powerup_flash / max_flash)
        
        if flash_intensity > 0:
            radius = (25 + 15 * flash_intensity) * self.get_scale_factor()
            self.glow(surface, (ship.x, ship.y), radius, 
                     ship.powerup_flash_color, flash_intensity)
    
    def draw_ship_body(self, surface: pygame.Surface, ship: ShipState, game_state: Dict[str, Any]) -> None:
        """Draw ship body polygon.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
            game_state: Current game state
        """
        ship_points = self._get_ship_points(ship.x, ship.y, ship.angle)
        scale_factor = self.get_scale_factor()
        
        if game_state['finisher']['ready']:
            pygame.draw.polygon(surface, Cfg.colors['gold'], ship_points, max(1, int(3 * scale_factor)))
        else:
            pygame.draw.polygon(surface, Cfg.colors['white'], ship_points, max(1, int(2 * scale_factor)))
    
    def draw_thruster_flame(self, surface: pygame.Surface, ship: ShipState, keys: dict, 
                           controller_input: Dict[str, Any], game_state: Dict[str, Any]) -> None:
        """Draw thruster flame when ship is accelerating.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
            keys: Keyboard state
            controller_input: Controller state
            game_state: Current game state
        """
        is_thrusting = keys[pygame.K_UP] or controller_input['thrust']
        
        if not is_thrusting or game_state['game_over'] or ship.respawning > 0 or ship.dashing > 0:
            return
        
        scale_factor = self.get_scale_factor()
        sin_a, cos_a = self._get_sin_cos(ship.angle)
        
        flame_length = self._scaled(Cfg.ship_back_indent) + random.randint(int(Cfg.flame_length_min * scale_factor), 
                                                                         int(Cfg.flame_length_max * scale_factor))
        flame_width = random.randint(int(Cfg.flame_width_min * scale_factor), 
                                    int(Cfg.flame_width_max * scale_factor))
        
        flame_tip = (
            ship.x - flame_length * cos_a,
            ship.y - flame_length * sin_a
        )
        
        sin_flame_left, cos_flame_left = self._get_sin_cos(ship.angle + Cfg.ship_flame_angle)
        sin_flame_right, cos_flame_right = self._get_sin_cos(ship.angle - Cfg.ship_flame_angle)
        
        flame_base_left = (
            ship.x - self._scaled(Cfg.ship_back_indent) * cos_a + flame_width * cos_flame_left,
            ship.y - self._scaled(Cfg.ship_back_indent) * sin_a + flame_width * sin_flame_left
        )
        
        flame_base_right = (
            ship.x - self._scaled(Cfg.ship_back_indent) * cos_a + flame_width * cos_flame_right,
            ship.y - self._scaled(Cfg.ship_back_indent) * sin_a + flame_width * sin_flame_right
        )
        
        pygame.draw.polygon(surface, (255, 100, 0), [flame_tip, flame_base_left, flame_base_right])
        
        inner_flame_tip = (
            ship.x - (flame_length * 0.7) * cos_a,
            ship.y - (flame_length * 0.7) * sin_a
        )
        inner_width = flame_width * 0.6
        inner_base_left = (
            ship.x - self._scaled(Cfg.ship_back_indent) * cos_a + inner_width * cos_flame_left,
            ship.y - self._scaled(Cfg.ship_back_indent) * sin_a + inner_width * sin_flame_left
        )
        inner_base_right = (
            ship.x - self._scaled(Cfg.ship_back_indent) * cos_a + inner_width * cos_flame_right,
            ship.y - self._scaled(Cfg.ship_back_indent) * sin_a + inner_width * sin_flame_right
        )
        pygame.draw.polygon(surface, (255, 255, 150), [inner_flame_tip, inner_base_left, inner_base_right])
    
    def draw_powerup_auras(self, surface: pygame.Surface, ship: ShipState, game_state: Dict[str, Any]) -> None:
        """Draw auras for active powerups.
        
        Args:
            surface: Surface to draw on
            ship: Ship state
            game_state: Current game state
        """
        scale_factor = self.get_scale_factor()
        
        if ship.rapid_fire > 0:
            pulse = self._calculate_pulse(ship.aura_pulse, 1.0, 0.3, 0.7)
            radius = int(35 * pulse * scale_factor)
            
            for i in range(3):
                angle = game_state['effects']['aura_rotation'] + i * 120
                sin_a, cos_a = self._get_sin_cos(angle)
                x = ship.x + cos_a * radius
                y = ship.y + sin_a * radius
                
                triangle_size = 5 * scale_factor
                points = []
                for j in range(3):
                    t_angle = angle + j * 120
                    t_sin, t_cos = self._get_sin_cos(t_angle)
                    points.append((x + t_cos * triangle_size, y + t_sin * triangle_size))
                pygame.draw.polygon(surface, (255, 100, 0), points, 1)
        
        if ship.triple_shot > 0:
            pulse = self._calculate_pulse(ship.aura_pulse * 0.8, 1.0, 0.3, 0.7)
            radius = int(40 * pulse * scale_factor)
            
            for i in range(3):
                angle = game_state['effects']['aura_rotation'] * -1.5 + i * 120
                sin_a, cos_a = self._get_sin_cos(angle)
                x = ship.x + cos_a * radius
                y = ship.y + sin_a * radius
                
                pygame.draw.circle(surface, (0, 255, 255), (int(x), int(y)), int(3 * scale_factor))
                self.glow(surface, (x, y), 8 * scale_factor, (0, 255, 255))
    
    def draw_powerups(self, surface: pygame.Surface, powerups: List[PowerUp]) -> None:
        """Draw all powerup entities.
        
        Args:
            surface: Surface to draw on
            powerups: List of powerups to draw
        """
        scale_factor = self.get_scale_factor()
        
        for powerup in powerups:
            pulse = self._calculate_pulse(powerup.pulse, 1.0)
            color = Cfg.powerup_types[powerup.type]['color']
            
            self.glow(surface, (powerup.x, powerup.y), 25 * pulse * scale_factor, 
                     color, pulse)
            
            symbol_text = self.fonts['small'].render(Cfg.powerup_types[powerup.type]['symbol'], True, color)
            surface.blit(symbol_text, 
                        (int(powerup.x - self._scaled(Cfg.powerup_symbol_offset_x)), 
                         int(powerup.y - self._scaled(Cfg.powerup_symbol_offset_y))))
            
            if powerup.type == PowerUpType.CRYSTAL:
                points = []
                angle = powerup.pulse * 50
                for i in range(4):
                    point_angle = angle + i * 90
                    sin_a, cos_a = self._get_sin_cos(point_angle)
                    points.append((powerup.x + self._scaled(Cfg.powerup_visual_radius) * cos_a,
                                 powerup.y + self._scaled(Cfg.powerup_visual_radius) * sin_a))
                pygame.draw.polygon(surface, color, points, max(1, int(2 * scale_factor)))
            else:
                points = self._get_polygon_points(powerup, Cfg.powerup_hexagon_vertices, 
                                                 self._scaled(Cfg.powerup_visual_radius), 
                                                 angle_override=powerup.pulse * 20)
                pygame.draw.polygon(surface, color, points, max(1, int(2 * scale_factor)))
    
    def draw_bullets(self, surface: pygame.Surface, bullets: List[Any], enemy_bullets: List[Any]) -> None:
        """Draw all bullets.
        
        Args:
            surface: Surface to draw on
            bullets: List of player bullets
            enemy_bullets: List of enemy bullets
        """
        scale_factor = self.get_scale_factor()
        
        for bullet in bullets:
            for i, pos in enumerate(bullet.trail):
                if i > 0:
                    alpha = i / len(bullet.trail)
                    radius = max(1, int(3 * alpha * scale_factor))
                    color = tuple(int(c * alpha * m) for c, m in zip((255, 255, 255), (0.8, 0.8, 0.4)))
                    pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), radius)
            
            self.glow(surface, (bullet.x, bullet.y), self._scaled(Cfg.bullet_radius * 4), 
                     (255, 255, 0))
            pygame.draw.circle(surface, Cfg.colors['bullet'], (int(bullet.x), int(bullet.y)), 
                             int(3 * scale_factor))
        
        for bullet in enemy_bullets:
            for i, pos in enumerate(bullet.trail):
                if i > 0:
                    alpha = i / len(bullet.trail)
                    radius = max(1, int(3 * alpha * scale_factor))
                    color = tuple(int(c * alpha * m) for c, m in zip((255, 255, 255), (1.0, 0.4, 0.4)))
                    pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), radius)
            
            self.glow(surface, (bullet.x, bullet.y), self._scaled(Cfg.bullet_radius * 4) * 0.8, 
                     (255, 100, 100), 0.8)
            pygame.draw.circle(surface, Cfg.colors['enemy_bullet'], (int(bullet.x), int(bullet.y)), 
                             int(3 * scale_factor))
    
    def draw_particles(self, surface: pygame.Surface, particle_pool) -> None:
        """Draw all active particles.
        
        Args:
            surface: Surface to draw on
            particle_pool: Particle pool containing particles to draw
        """
        for particle in particle_pool.get_active_particles():
            life_ratio = max(0, min(1, particle.life / Cfg.particle_base_life))
            
            particle_type = particle.type
            renderer = Cfg.particle_renderers.get(particle_type, {})
            
            if 'radius_calc' in renderer:
                radius = renderer['radius_calc'](particle, self.get_scale_factor())
            else:
                radius = max(1, int((2 + particle.life // 10) * self.get_scale_factor()))
            
            color = tuple(max(0, min(255, int(c * life_ratio))) for c in particle.color)
            
            pygame.draw.circle(surface, color, (int(particle.x), int(particle.y)), radius)
            
            if 'has_glow' in renderer:
                has_glow = renderer['has_glow']
                if callable(has_glow):
                    has_glow = has_glow(particle)
                
                if has_glow:
                    glow_radius = renderer.get('glow_radius', 2)
                    glow_factor = renderer.get('glow_factor', 0.5)
                    glow_color_list = [max(0, min(255, int(c * life_ratio * glow_factor))) 
                                     for c in particle.color]
                    glow_color = (glow_color_list[0], glow_color_list[1], glow_color_list[2])
                    self.glow(surface, (particle.x, particle.y), 
                             radius * glow_radius, glow_color, life_ratio * glow_factor) 