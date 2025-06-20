# Asteroids Enhanced (AC2) 🚀

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.x-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **next-generation remake** of the classic Asteroids arcade game, featuring advanced combat mechanics, sophisticated AI, particle systems, and LLM-optimized modular architecture. This isn't just another Asteroids clone—it's a complete reimagining with modern game design principles.

## 🎮 Game Features

### Core Gameplay
- **Classic Asteroids Foundation** with modern enhancements
- **Dynamic Resolution Support** with automatic scaling
- **Smooth 60 FPS Gameplay** with time-scale system
- **Screen-wrapping Physics** for continuous play area

### Advanced Combat System
- **Finisher Moves** - Execute spectacular finishing attacks on enemies
- **Dash Mechanics** with invulnerability frames
- **Combo System** with multipliers and visual feedback
- **Multiple Weapon Types** (single shot, rapid fire, triple shot)
- **Smart Enemy AI** with hunter and circler behavior patterns

### Visual Excellence
- **Advanced Particle System** (5000+ particles supported)
- **Dynamic Visual Effects** (screen shake, damage flashes, aura effects)
- **Animated Starfield Background** with parallax scrolling
- **Floating Damage Numbers** and combo indicators
- **CRT-style Screen Effects** for retro aesthetics
- **Smooth Animation System** with interpolation

### Progression & Customization
- **Persistent Upgrade System** (damage, fire rate, speed, dash cooldown)
- **Achievement System** with 8 unique achievements
- **Crystal Currency** earned through gameplay
- **Boss Battle System** with special rewards
- **Level Progression** with increasing difficulty

### Technical Features
- **Controller Support** (Xbox/PlayStation/Generic gamepads)
- **Dynamic Audio System** with positional sound
- **Modular Architecture** (8 separate modules for maintainability)
- **Comprehensive Configuration System** with 150+ tweakable parameters
- **Save/Load System** with data validation
- **Real-time Performance Optimization**

## 🏗️ Architecture

This project showcases **LLM-optimized modular design**, originally developed as a single 5000+ line file and strategically refactored into maintainable modules:

```
AC2/
├── main.py                 # Core game loop & coordination (5007 lines)
├── config.py              # Centralized configuration system
├── data_structures.py     # Entity definitions & data classes
├── drawing_system.py      # Centralized rendering operations
├── particle_system.py    # High-performance particle management
├── sound_system.py        # Audio generation & playbook
├── visual_effects.py      # Rendering effects & transitions
├── progression_system.py  # Save/load, achievements, upgrades
├── pyproject.toml        # Python project configuration
└── Human Docs/           # Additional documentation
    ├── design-philosophy-human.md
    └── ai-debugging-guide.md
```

### Design Philosophy
- **LLM-Friendly**: Optimized for AI code comprehension and modification
- **Explicit State Management**: Full paths (`g_game_state['effects']['screen_shake']`)
- **Dependency Injection**: Avoids circular imports through function passing
- **Fail-Safe Operations**: Comprehensive error handling
- **Copy Over Abstract**: Duplicates code rather than over-generalizing

## 🎯 Game Systems

### Combat Mechanics
```python
# Finisher System - Execute devastating attacks
if finisher_ready and target_locked:
    execute_finisher_move(target)
    create_shockwave_damage(impact_point)
    
# Combo System - Build multipliers
combo_multiplier = 1 + combo_count * 0.1
score_value = base_score * combo_multiplier
```

### AI Behavior
- **Hunter AI**: Aggressive pursuit with retreat mechanics
- **Circler AI**: Orbital movement patterns around player
- **Boss AI**: Advanced patterns with multiple phases
- **Dynamic Difficulty**: Enemy spawn rates scale with progression

### Particle System
- **Object Pooling**: Efficient memory management for particles
- **Type-based Behaviors**: Specialized particles (explosion, thruster, finisher)
- **Performance Optimized**: Handles 1000+ active particles at 60 FPS

## 🚀 Installation & Setup

### Prerequisites
```bash
Python 3.7+
pygame 2.0+
```

### Quick Start
```bash
# Clone the repository
git clone https://github.com/michaelcrosato/AC2.git
cd AC2

# Install dependencies
pip install pygame

# Run the game
python main.py
```

### Alternative Installation
```bash
# Using pip with pyproject.toml
pip install -e .
```

## 🎮 Controls

### Keyboard Controls
| Key | Action |
|-----|--------|
| `↑` / `W` | Thrust Forward |
| `←` / `A` | Turn Left |
| `→` / `D` | Turn Right |
| `↓` / `S` | Reverse Thrust |
| `Space` | Fire Weapons |
| `Shift` | Dash / Execute Finisher |
| `Esc` | Pause / Resume |
| `U` | Upgrade Menu |
| `S` | Toggle Sound |
| `Enter` | Restart (Game Over) |

### Controller Support
- **Movement**: Left analog stick / D-pad
- **Weapons**: Right trigger / Face buttons
- **Dash**: Shoulder buttons
- **Menu**: Start button for pause

## 🏆 Achievement System

| Achievement | Description | Reward |
|-------------|-------------|---------|
| **First Blood** | Destroy your first asteroid | 10 Crystals |
| **Combo Master** | Achieve 5x combo multiplier | 25 Crystals |
| **Combo Legend** | Achieve 10x combo multiplier | 50 Crystals |
| **Survivor** | Reach level 10 | 100 Crystals |
| **Boss Slayer** | Defeat your first boss | 200 Crystals |
| **Untouchable** | Complete a level without taking damage | 150 Crystals |
| **Speed Demon** | Max out speed upgrades | 75 Crystals |
| **Crystal Hoarder** | Collect 1000 lifetime crystals | 500 Crystals |

## ⚙️ Configuration

The game features **150+ configurable parameters** in `config.py`:

```python
# Gameplay Balance
ship_max_speed = 8.0
bullet_speed = 15.0
enemy_spawn_chance = 0.02

# Visual Effects
max_screen_shake = 20
particle_explosion_count = 30
combo_pulse_max_alpha = 30

# Performance Settings
max_particles = 5000
particle_pool_size = 1000
fps = 60
```

## 🎵 Audio System

- **Positional Audio**: Sounds fade with distance
- **Dynamic Volume**: Adjusts based on screen area
- **Sound Categories**: Weapons, explosions, power-ups, UI
- **Performance**: Optional system that can be disabled

## 💾 Save System

Persistent data includes:
- High scores and statistics
- Upgrade progression
- Achievement unlocks
- Lifetime crystal collection
- Boss kill counts

## 🔧 Development

### Code Quality
- **Type Hints**: Full typing support throughout
- **Documentation**: Comprehensive docstrings
- **Error Handling**: Graceful failure modes
- **Performance**: Optimized for 60 FPS gameplay

### Extending the Game
The modular architecture makes it easy to:
- Add new enemy types in `data_structures.py`
- Create new visual effects in `visual_effects.py`
- Implement new power-ups via the configuration system
- Add achievements through the lookup table system

### LLM Integration
This codebase is specifically optimized for Large Language Model interaction:
- Clear section headers and extensive commenting
- Explicit state management patterns
- Modular design with clean boundaries
- Comprehensive documentation of side effects

## 📊 Performance

- **60 FPS** stable gameplay
- **5000+ particles** simultaneously
- **Dynamic resolution** scaling
- **Memory efficient** object pooling
- **Optimized collision detection**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style
4. Add tests for new features
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎖️ Credits

**Lead Programmers**: Claude 4 Opus/Sonnet (Anthropic)  
**Code Reviewers**: ChatGPT 4o/4.1, Grok 3, Gemini 2.5 Pro  
**Architecture**: LLM-Optimized Modular Design  

---

## 🚀 Ready to Play?

Experience the evolution of Asteroids with modern game design, sophisticated combat mechanics, and cutting-edge architecture. Whether you're here to play, learn, or contribute—welcome to Asteroids Enhanced!

```bash
python main.py
# Prepare for an enhanced asteroid experience! 🎮
``` 