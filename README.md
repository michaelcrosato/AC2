# Asteroids Game (AC2)

A modern take on the classic Asteroids arcade game built with Python and Pygame.

## Features

- Classic asteroids gameplay with modern enhancements
- Power-ups system (rapid fire, triple shot, shields, extra lives)
- Combo system for scoring multipliers
- Enemy AI with different behavior patterns
- Boss battles
- Particle effects and visual enhancements
- Dash mechanics and finisher moves
- Upgrade system with persistent progression
- Achievement system
- Controller support
- Configurable sound system

## Game Files

- `main.py` - Main game loop and core game logic
- `config.py` - Centralized configuration and settings
- `data_structures.py` - Game data structures and enums
- `particle_system.py` - Particle effects system
- `progression_system.py` - Player progression and upgrades
- `sound_system.py` - Audio management
- `visual_effects.py` - Visual effects and rendering
- `asteroids_save.json` - Save file for player progress

## Requirements

- Python 3.x
- Pygame
- (Optional) Controller for gamepad support

## How to Play

Run the game with:
```bash
python main.py
```

### Controls

- **Arrow Keys** or **WASD**: Move ship
- **Space**: Shoot
- **Shift**: Dash (when available)
- **M**: Toggle sound
- **P**: Pause
- **R**: Restart (when game over)
- **Controller**: Supported for all actions

### Gameplay

- Destroy asteroids to earn points and crystals
- Collect power-ups for temporary advantages
- Build combos for score multipliers
- Use crystals to purchase permanent upgrades
- Survive increasingly difficult waves
- Face off against boss enemies

## Development

This project uses a modular architecture with separate systems for:
- Game state management
- Entity systems
- Visual effects
- Audio
- Configuration management
- Save/load functionality

The game features a comprehensive configuration system in `config.py` that allows easy tweaking of all game parameters. 