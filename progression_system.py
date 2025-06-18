"""
Progression system for the Asteroids game.

This module handles save/load functionality, achievements, and upgrades using
a class-based architecture with dependency injection to avoid circular imports.
"""

import json
import os
from typing import Dict, Optional, Callable, Set, Any
from dataclasses import dataclass

from config import Cfg


@dataclass
class GameContext:
    """Bundle of game state and display info to avoid excessive parameter passing."""
    game_state: dict
    screen_width: int
    screen_height: int


class ProgressionSystem:
    """Manages save/load, achievements, and upgrades."""
    
    def __init__(self, create_floating_text: Callable, update_scaled_values: Callable):
        """Initialize with dependency injection to avoid circular imports.
        
        Args:
            create_floating_text: Function to create floating text
            update_scaled_values: Function to update scaled values after upgrades
        """
        self.create_floating_text = create_floating_text
        self.update_scaled_values = update_scaled_values
        
        # Achievement conditions using context to avoid global access
        self.achievement_conditions = {
            'first_blood': lambda ctx: ctx.game_state['score'] > 0,
            'combo_5': lambda ctx: ctx.game_state['combo']['current'] >= Cfg.combo_milestone_thresholds[0],
            'combo_10': lambda ctx: ctx.game_state['combo']['current'] >= Cfg.combo_milestone_thresholds[1],
            'survivor': lambda ctx: ctx.game_state['level'] >= Cfg.achievement_survivor_level,
            'boss_slayer': lambda ctx: ctx.game_state.get('boss_kills', 0) > 0,
            'untouchable': lambda ctx: ctx.game_state['level'] > 1 and ctx.game_state['untouchable_level'],
            'speed_demon': lambda ctx: ctx.game_state['upgrade_levels']['max_speed'] >= Cfg.achievement_speed_demon_level,
            'crystal_hoarder': lambda ctx: ctx.game_state['lifetime_crystals'] >= Cfg.achievement_crystal_hoarder_amount
        }
    
    def get_default_upgrade_levels(self) -> Dict[str, int]:
        """Get default upgrade levels for all upgrades.
        
        Returns:
            Dictionary mapping upgrade names to level 0
        """
        return {key: 0 for key in Cfg.upgrades}
    
    def validate_save_data(self, save_data: dict) -> bool:
        """Validate save data structure and types.
        
        Args:
            save_data: Dictionary containing save data
            
        Returns:
            True if save data is valid, False otherwise
        """
        required_fields = {
            'high_score': (int, float),  # Allow both int and float for backwards compatibility
            'lifetime_crystals': (int, float),
            'achievements_unlocked': (list, set),  # Allow both list and set
            'upgrade_levels': dict,
            'boss_kills': (int, float)
        }
        
        for field, expected_types in required_fields.items():
            if field not in save_data:
                print(f"[validate_save_data] Missing required field: {field}")
                return False
            if not isinstance(save_data[field], expected_types):
                print(f"[validate_save_data] Invalid type for {field}: expected {expected_types}, got {type(save_data[field])}")
                return False
        
        # Validate upgrade_levels structure
        if not all(isinstance(k, str) and isinstance(v, (int, float)) for k, v in save_data['upgrade_levels'].items()):
            print("[validate_save_data] Invalid upgrade_levels structure")
            return False
        
        return True
    
    def save_game_state(self, ctx: GameContext) -> bool:
        """Save persistent game state to file with robust error handling.
        
        Args:
            ctx: Game context containing state to save
            
        Returns:
            True if save successful, False otherwise
        """
        save_data = {
            'high_score': ctx.game_state['high_score'],
            'lifetime_crystals': ctx.game_state['lifetime_crystals'],
            'achievements_unlocked': list(ctx.game_state['achievements_unlocked']),
            'upgrade_levels': ctx.game_state['upgrade_levels'],
            'boss_kills': ctx.game_state.get('boss_kills', 0)
        }
        
        try:
            with open(Cfg.save_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            return True
        except (IOError, OSError, PermissionError) as e:
            print(f"[save_game_state] Failed to save: {e}")
            return False
        except Exception as e:
            print(f"[save_game_state] Unexpected error: {e}")
            return False
    
    def load_game_state(self, ctx: GameContext) -> bool:
        """Load persistent game state from file with robust error handling.
        
        Args:
            ctx: Game context to update with loaded state
            
        Returns:
            True if load successful, False if using defaults
        """
        default_state = {
            'high_score': 0,
            'lifetime_crystals': 0,
            'achievements_unlocked': set(),
            'upgrade_levels': self.get_default_upgrade_levels(),
            'boss_kills': 0
        }
        
        try:
            if not os.path.exists(Cfg.save_file):
                print("[load_game_state] No save file found, using defaults")
                ctx.game_state.update(default_state)
                return False
                
            with open(Cfg.save_file, 'r') as f:
                save_data = json.load(f)
            
            # Validate save data structure
            if not self.validate_save_data(save_data):
                print("[load_game_state] Save data validation failed, using defaults")
                ctx.game_state.update(default_state)
                return False
            
            # Validate and load data
            ctx.game_state['high_score'] = max(0, int(save_data.get('high_score', 0)))
            ctx.game_state['lifetime_crystals'] = max(0, int(save_data.get('lifetime_crystals', 0)))
            
            loaded_achievements = save_data.get('achievements_unlocked', [])
            ctx.game_state['achievements_unlocked'] = set(
                ach for ach in loaded_achievements if ach in Cfg.achievements
            )
            
            loaded_upgrades = save_data.get('upgrade_levels', {})
            validated_upgrades = self.get_default_upgrade_levels()
            for upgrade, level in loaded_upgrades.items():
                if upgrade in Cfg.upgrades:
                    max_level = Cfg.upgrades[upgrade]['max_level']
                    validated_upgrades[upgrade] = max(0, min(int(level), max_level))
            ctx.game_state['upgrade_levels'] = validated_upgrades
            
            ctx.game_state['boss_kills'] = max(0, int(save_data.get('boss_kills', 0)))
            
            achievement_count = len(ctx.game_state['achievements_unlocked'])
            print(f"[load_game_state] Loaded: High score {ctx.game_state['high_score']}, {achievement_count} achievements")
            return True
            
        except (IOError, OSError, PermissionError) as e:
            print(f"[load_game_state] File access error: {e}")
            ctx.game_state.update(default_state)
            return False
        except json.JSONDecodeError as e:
            print(f"[load_game_state] JSON decode error: {e}")
            ctx.game_state.update(default_state)
            return False
        except Exception as e:
            print(f"[load_game_state] Unexpected error: {e}")
            ctx.game_state.update(default_state)
            return False
    
    def check_achievement(self, achievement_id: str, ctx: GameContext) -> bool:
        """Check and unlock achievement if conditions are met.
        
        Args:
            achievement_id: ID of achievement to check
            ctx: Game context containing current state
            
        Returns:
            True if achievement was newly unlocked, False otherwise
        """
        if achievement_id not in Cfg.achievements:
            print(f"[check_achievement] Unknown achievement: {achievement_id}")
            return False
        
        if achievement_id in ctx.game_state['achievements_unlocked']:
            return False
        
        if achievement_id not in self.achievement_conditions:
            print(f"[check_achievement] No condition defined for: {achievement_id}")
            return False
        
        try:
            if self.achievement_conditions[achievement_id](ctx):
                ctx.game_state['achievements_unlocked'].add(achievement_id)
                
                achievement = Cfg.achievements[achievement_id]
                reward = achievement['reward']
                ctx.game_state['crystals'] += reward
                ctx.game_state['lifetime_crystals'] += reward
                
                # Create floating text using injected function
                self.create_floating_text(
                    ctx.screen_width // 2, 
                    ctx.screen_height // 3, 
                    f"ACHIEVEMENT: {achievement['name']}", 
                    Cfg.colors['gold']
                )
                self.create_floating_text(
                    ctx.screen_width // 2, 
                    ctx.screen_height // 3 + 30, 
                    f"◆ +{reward}", 
                    Cfg.colors['crystal']
                )
                
                print(f"[check_achievement] Unlocked: {achievement['name']}")
                return True
                
        except Exception as e:
            print(f"[check_achievement] Error checking {achievement_id}: {e}")
            return False
        
        return False
    
    def calculate_upgrade_cost(self, upgrade_type: str, ctx: GameContext) -> Optional[int]:
        """Calculate the cost for the next level of an upgrade.
        
        Args:
            upgrade_type: Type of upgrade
            ctx: Game context containing current upgrade levels
            
        Returns:
            Cost in crystals or None if maxed
        """
        if upgrade_type not in Cfg.upgrades:
            return None
            
        level = ctx.game_state['upgrade_levels'].get(upgrade_type, 0)
        if level >= Cfg.upgrades[upgrade_type]['max_level']:
            return None
        
        base_cost = Cfg.upgrades[upgrade_type]['base_cost']
        multiplier = Cfg.upgrades[upgrade_type]['cost_multiplier']
        return int(base_cost * (multiplier ** level))
    
    def apply_upgrade(self, upgrade_type: str, ctx: GameContext) -> bool:
        """Apply an upgrade if the player can afford it.
        
        Args:
            upgrade_type: Type of upgrade to apply
            ctx: Game context containing current state
            
        Returns:
            True if upgrade was applied
        """
        cost = self.calculate_upgrade_cost(upgrade_type, ctx)
        if cost is None or ctx.game_state['crystals'] < cost:
            return False
        
        ctx.game_state['crystals'] -= cost
        ctx.game_state['upgrade_levels'][upgrade_type] += 1
        
        # Save state after upgrade
        self.save_game_state(ctx)
        
        # Update scaled values using injected function
        self.update_scaled_values()
        
        return True
    
    def get_damage_multiplier(self, ctx: GameContext) -> float:
        """Get current damage multiplier based on upgrades.
        
        Args:
            ctx: Game context containing upgrade levels
            
        Returns:
            Damage multiplier (1.0 = base damage)
        """
        level = ctx.game_state['upgrade_levels'].get('damage', 0)
        return 1.0 + (level * Cfg.upgrades['damage']['multiplier_per_level'])
    
    def get_fire_rate_multiplier(self, ctx: GameContext) -> float:
        """Get current fire rate multiplier based on upgrades.
        
        Args:
            ctx: Game context containing upgrade levels
            
        Returns:
            Fire rate multiplier (lower = faster)
        """
        level = ctx.game_state['upgrade_levels'].get('fire_rate', 0)
        return 1.0 - (level * Cfg.upgrades['fire_rate']['reduction_per_level'])
    
    def get_speed_multiplier(self, ctx: GameContext) -> float:
        """Get current speed multiplier based on upgrades.
        
        Args:
            ctx: Game context containing upgrade levels
            
        Returns:
            Speed multiplier (higher = faster)
        """
        level = ctx.game_state['upgrade_levels'].get('max_speed', 0)
        return 1.0 + (level * Cfg.upgrades['max_speed']['multiplier_per_level'])
    
    def get_dash_cooldown_reduction(self, ctx: GameContext) -> float:
        """Get current dash cooldown reduction based on upgrades.
        
        Args:
            ctx: Game context containing upgrade levels
            
        Returns:
            Cooldown reduction in frames
        """
        level = ctx.game_state['upgrade_levels'].get('dash_cooldown', 0)
        return level * Cfg.upgrades['dash_cooldown']['reduction_per_level'] 