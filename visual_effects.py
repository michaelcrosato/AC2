"""
Visual effects system for the Asteroids game.

This module handles all purely cosmetic visual effects including starfield, 
space dust, vignette, CRT effects, level transitions, and damage flash.
"""

import pygame
import math
import random
from typing import List, Dict, Any, Optional

from config import Cfg


# Module globals for visual effects
g_stars: List[Dict[str, Any]] = []
g_dust_particles: List[Dict[str, Any]] = []
g_vignette_surface: Optional[pygame.Surface] = None


# Helper functions (duplicated to avoid circular imports)
def scaled(value: float, scale_factor: float = 1.0) -> float:
    """Scale a value by the global scale factor."""
    return value * scale_factor


def calculate_fade(progress: float, max_alpha: int = 255) -> int:
    """Calculate fade alpha based on progress (0.0 to 1.0)."""
    return int(max_alpha * max(0, min(1, progress)))


def init_visual_effects(ctx: Dict[str, Any]) -> None:
    """Initialize visual effects with game context.
    
    Args:
        ctx: Context dict with screen_width, screen_height, scale_factor
    """
    global g_stars, g_dust_particles, g_vignette_surface
    
    # Initialize starfield
    create_starfield(ctx['screen_width'], ctx['screen_height'])
    
    # Initialize space dust
    create_space_dust(ctx['screen_width'], ctx['screen_height'])
    
    # Initialize vignette
    create_vignette(ctx['screen_width'], ctx['screen_height'], ctx['scale_factor'])


def create_starfield(screen_width: int, screen_height: int) -> None:
    """Generate random starfield background.
    
    Args:
        screen_width: Screen width
        screen_height: Screen height
    
    Side effects:
        Populates global g_stars list
    """
    global g_stars
    g_stars = []
    
    area_multiplier = (screen_width * screen_height) / (Cfg.screen_width * Cfg.screen_height)
    star_count = int(Cfg.star_count_base * math.sqrt(area_multiplier))
    
    for i in range(star_count):
        g_stars.append({
            'x': random.randint(0, screen_width),
            'y': random.randint(0, screen_height),
            'base_brightness': random.randint(30, 150),
            'size': random.choice([1, 1, 1, 2]),
            'twinkle_speed': random.uniform(Cfg.star_twinkle_speed_min, Cfg.star_twinkle_speed_max),
            'twinkle_phase': random.uniform(0, math.pi * 2),
            'twinkle_amount': random.uniform(Cfg.star_twinkle_amount_min, Cfg.star_twinkle_amount_max)
        })


def draw_stars(surface: pygame.Surface, shake_x: int, shake_y: int, frame_count: int,
              screen_width: int, screen_height: int) -> None:
    """Draw starfield with parallax and twinkling.
    
    Args:
        surface: Surface to draw on
        shake_x: Screen shake X offset
        shake_y: Screen shake Y offset
        frame_count: Current frame for animation
        screen_width: Screen width
        screen_height: Screen height
    """
    for star in g_stars:
        twinkle = math.sin(star['twinkle_phase'] + frame_count * star['twinkle_speed'])
        brightness_factor = 1.0 + (twinkle * star['twinkle_amount'])
        brightness = int(star['base_brightness'] * brightness_factor)
        brightness = max(20, min(255, brightness))
        
        color = (brightness, brightness, min(255, brightness + 30))
        
        parallax_factor = star['base_brightness'] / 150.0
        x = int(star['x'] + shake_x * parallax_factor * Cfg.star_parallax_factor)
        y = int(star['y'] + shake_y * parallax_factor * Cfg.star_parallax_factor)
        
        if star['size'] == 1:
            surface.set_at((x % screen_width, y % screen_height), color)
        else:
            glow_radius = star['size'] + 1
            glow_color = (color[0] // 3, color[1] // 3, color[2] // 2)
            pygame.draw.circle(surface, glow_color, (x % screen_width, y % screen_height), glow_radius)
            pygame.draw.circle(surface, color, (x % screen_width, y % screen_height), star['size'])


def create_space_dust(screen_width: int, screen_height: int, count: Optional[int] = None) -> None:
    """Create space dust particles for depth effect.
    
    Args:
        screen_width: Screen width
        screen_height: Screen height
        count: Number of dust particles (defaults to Cfg.dust_count_base)
    
    Side effects:
        Clears and repopulates g_dust_particles list
    """
    global g_dust_particles
    
    if count is None:
        count = Cfg.dust_count_base
        
    g_dust_particles.clear()
    area_multiplier = (screen_width * screen_height) / (Cfg.screen_width * Cfg.screen_height)
    dust_count = int(count * math.sqrt(area_multiplier))
    
    for _ in range(dust_count):
        g_dust_particles.append({
            'x': random.randint(0, screen_width),
            'y': random.randint(0, screen_height),
            'size': random.choice([1, 1, 1, 2]),
            'brightness': random.randint(40, 80)
        })


def update_and_draw_dust(surface: pygame.Surface, ctx: Dict[str, Any], offset_x: int = 0, offset_y: int = 0) -> None:
    """Update and draw space dust with parallax scrolling.
    
    Args:
        surface: Surface to draw on
        ctx: Context dict with ship, game_state, screen_width, screen_height
        offset_x: X offset for drawing
        offset_y: Y offset for drawing
    
    Side effects:
        Modifies dust particle positions
    """
    global g_dust_particles
    
    ship = ctx['ship']
    game_state = ctx['game_state']
    screen_width = ctx['screen_width']
    screen_height = ctx['screen_height']
    
    if game_state['effects']['level_transition'] == 0:
        parallax_scale = min(screen_width / 800, screen_height / 600)
        
        dx = -ship.vel_x * Cfg.dust_parallax * parallax_scale * game_state['time_scale']
        dy = -ship.vel_y * Cfg.dust_parallax * parallax_scale * game_state['time_scale']
        
        for dust in g_dust_particles:
            dust['x'] = (dust['x'] + dx) % screen_width
            dust['y'] = (dust['y'] + dy) % screen_height
    
    for dust in g_dust_particles:
        color = (dust['brightness'], dust['brightness'], dust['brightness'] + 20)
        dust_x = int(dust['x'] - offset_x)
        dust_y = int(dust['y'] - offset_y)
        if 0 <= dust_x < surface.get_width() and 0 <= dust_y < surface.get_height():
            if dust['size'] == 1:
                surface.set_at((dust_x, dust_y), color)
            else:
                pygame.draw.circle(surface, color, (dust_x, dust_y), dust['size'])


def create_vignette(screen_width: int, screen_height: int, scale_factor: float) -> None:
    """Create vignette effect surface.
    
    Args:
        screen_width: Screen width
        screen_height: Screen height
        scale_factor: Global scale factor
    
    Side effects:
        Sets global g_vignette_surface
    """
    global g_vignette_surface
    g_vignette_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    
    center_x = screen_width // 2
    center_y = screen_height // 2
    max_radius = math.sqrt(center_x**2 + center_y**2)
    
    for step in range(Cfg.vignette_steps):
        progress = step / Cfg.vignette_steps
        radius = int(max_radius * (1 - progress))
        alpha = int(255 * Cfg.vignette_strength * progress * progress)
        
        if alpha > 0:
            ring_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
            pygame.draw.circle(ring_surface, (0, 0, 0, alpha), (center_x, center_y), radius, 
                             max(1, int(max_radius / Cfg.vignette_steps)))
            g_vignette_surface.blit(ring_surface, (0, 0))


def draw_crt_effects(surface: pygame.Surface, screen_width: int, screen_height: int, scale_factor: float) -> None:
    """Draw CRT-style scanlines and vignette.
    
    Args:
        surface: Surface to draw on
        screen_width: Screen width
        screen_height: Screen height
        scale_factor: Global scale factor
    """
    scanline_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    
    scanline_spacing = max(2, int(scaled(Cfg.scanline_spacing, scale_factor)))
    for y in range(0, screen_height, scanline_spacing):
        if (y // scanline_spacing) % 2 == 0:
            alpha = Cfg.scanline_alpha
        else:
            alpha = Cfg.scanline_alpha // 2
        
        pygame.draw.line(scanline_surface, (0, 0, 0, alpha), (0, y), (screen_width, y), 1)
    
    surface.blit(scanline_surface, (0, 0))
    
    if g_vignette_surface:
        surface.blit(g_vignette_surface, (0, 0))


def draw_level_transition(surface: pygame.Surface, game_state: Dict[str, Any], 
                         screen_width: int, screen_height: int, scale_factor: float) -> None:
    """Draw level transition effect.
    
    Args:
        surface: Surface to draw on
        game_state: Game state dict
        screen_width: Screen width
        screen_height: Screen height
        scale_factor: Global scale factor
    """
    if game_state['effects']['level_transition'] <= 0:
        return
    
    progress = 1.0 - (game_state['effects']['level_transition'] / Cfg.level_transition_duration)
    
    if progress < 0.5:
        ring_progress = progress * 2
        
        flash_alpha = int(255 * (1 - ring_progress) * 0.5)
        if flash_alpha > 0:
            flash_surface = pygame.Surface((screen_width, screen_height))
            flash_surface.set_alpha(flash_alpha)
            flash_surface.fill((255, 255, 255))
            surface.blit(flash_surface, (0, 0))
        
        ring_radius = int(ring_progress * math.sqrt(screen_width**2 + screen_height**2))
        ring_thickness = max(1, int(10 * (1 - ring_progress) * scale_factor))
        if ring_radius > ring_thickness:
            pygame.draw.circle(surface, (255, 255, 255), 
                               (screen_width // 2, screen_height // 2), 
                               ring_radius, ring_thickness)
    
    if progress > Cfg.level_text_appear_threshold:
        draw_level_transition_text(surface, progress, game_state, screen_width, screen_height, scale_factor)


def draw_level_transition_text(surface: pygame.Surface, progress: float, game_state: Dict[str, Any],
                              screen_width: int, screen_height: int, scale_factor: float) -> None:
    """Draw level transition text.
    
    Args:
        surface: Surface to draw on
        progress: Transition progress (0.0 to 1.0)
        game_state: Game state dict
        screen_width: Screen width
        screen_height: Screen height
        scale_factor: Global scale factor
    """
    # Import font here to avoid circular imports
    from main import g_big_font
    
    if not g_big_font:
        return
    
    text_progress = (progress - Cfg.level_text_appear_threshold) / (1 - Cfg.level_text_appear_threshold)
    
    if text_progress < Cfg.level_text_fade_threshold:
        scale = Cfg.level_text_scale_min + (Cfg.level_text_scale_max - Cfg.level_text_scale_min) * text_progress
        alpha = 255
    else:
        scale = Cfg.level_text_scale_max
        fade_progress = (text_progress - Cfg.level_text_fade_threshold) / (1 - Cfg.level_text_fade_threshold)
        alpha = int(255 * (1 - fade_progress))
    
    if alpha <= 0:
        return
    
    text = game_state['effects']['level_transition_text']
    text_surface = g_big_font.render(text, True, (255, 255, 255))
    
    if scale != 1.0:
        new_width = int(text_surface.get_width() * scale)
        new_height = int(text_surface.get_height() * scale)
        text_surface = pygame.transform.scale(text_surface, (new_width, new_height))
    
    text_surface.set_alpha(alpha)
    text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
    surface.blit(text_surface, text_rect)


def draw_damage_flash(surface: pygame.Surface, game_state: Dict[str, Any], 
                     screen_width: int, screen_height: int, scale_factor: float) -> None:
    """Draw damage flash effect on screen edges.
    
    Args:
        surface: Surface to draw on
        game_state: Game state dict
        screen_width: Screen width
        screen_height: Screen height
        scale_factor: Global scale factor
    """
    if game_state['effects']['damage_flash'] <= 0:
        return
    
    vignette = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    
    max_duration = (Cfg.damage_flash_duration if game_state['effects']['damage_flash_color'][0] > 200 
                   else Cfg.shield_flash_duration)
    intensity = game_state['effects']['damage_flash'] / max_duration
    
    if game_state['effects']['damage_flash'] > max_duration * Cfg.damage_flash_pulse_threshold:
        pulse = math.sin((max_duration - game_state['effects']['damage_flash']) * Cfg.damage_flash_pulse_speed) * 0.3
        intensity = min(1.0, intensity + pulse)
    
    max_layers = 6
    for i in range(max_layers):
        layer_intensity = intensity * (1 - i * 0.15)
        if layer_intensity <= 0:
            continue
            
        alpha = int(200 * layer_intensity)
        inset = int(i * 50 * scale_factor)
        thickness = int((80 - i * 10) * scale_factor)
        
        color = (*game_state['effects']['damage_flash_color'], alpha)
        
        pygame.draw.rect(vignette, color, (0, inset, screen_width, thickness))
        pygame.draw.rect(vignette, color, (0, screen_height - inset - thickness, screen_width, thickness))
        pygame.draw.rect(vignette, color, (inset, inset, thickness, screen_height - inset * 2))
        pygame.draw.rect(vignette, color, (screen_width - inset - thickness, inset, thickness, 
                                           screen_height - inset * 2))
    
    surface.blit(vignette, (0, 0))
    
    if intensity > Cfg.damage_flash_tint_threshold:
        tint_alpha = int(Cfg.damage_flash_tint_alpha * (intensity - 0.5))
        tint = pygame.Surface((screen_width, screen_height))
        tint.set_alpha(tint_alpha)
        tint.fill(game_state['effects']['damage_flash_color'])
        surface.blit(tint, (0, 0)) 