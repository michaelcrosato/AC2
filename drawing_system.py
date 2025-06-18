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
from data_structures import ShipState, Asteroid, Enemy, PowerUp, FloatingText
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