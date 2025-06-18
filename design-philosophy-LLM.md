# Asteroids Enhanced - LLM Development Specification

Version: 1.1.0
Original Game Created: December 2024
Document Created: December 2024
Last Updated: June 2025
Primary Authors: Claude (Anthropic), ChatGPT (OpenAI)
Purpose: Living development guide for LLM developers

## Design Philosophy
This specification guides LLM developers working on Asteroids Enhanced. Unlike traditional documentation, this document self-updates as the codebase evolves. LLMs should modify this document when implementation details change, while preserving core principles.

## Primary Directive
If code is unclear to you, it's wrong. Refactor for clarity.
Optimize all code for LLM comprehension and modification. Humans never read code.

## Document Index
1. [Design Philosophy](#design-philosophy)
2. [Primary Directive](#primary-directive)
3. [Document Maintenance](#document-maintenance)
4. [Critical Architecture Rules](#critical-architecture-rules)
5. [File Structure](#file-structure)
6. [Required Patterns](#required-patterns)
7. [Human Communication](#human-communication)
8. [Debugging Protocol](#debugging-protocol)
9. [Global State Reference](#global-state-reference)
10. [Constraints](#constraints)
11. [Update Order](#update-order-critical)
12. [Common Operations](#common-operations)
13. [Version Control Protocol](#version-control-protocol)
14. [Modification Priority](#modification-priority)

## Document Maintenance

This specification contains two types of information:
1. **Principles** - Architectural rules that rarely change
2. **Examples** - Current code structure that may evolve

When examples become outdated:
- LLMs should recognize discrepancies between this doc and actual code
- Apply the principles to current code
- Update examples in this document if discrepancy causes confusion
- Add new patterns or insights that helped understand the project
- Principles always override examples

Example: If `g_game_state` structure changes, update the structure shown here. If "Copy don't abstract" rule remains valid, never change it.

### What to Update
- File sizes and line counts
- Data structure examples that have changed
- New global variables or state keys
- Function signatures that have evolved
- Performance constraints if hardware improves
- New patterns discovered during development

### What NOT to Update
- Core architectural principles
- LLM-first development philosophy
- Documentation requirements
- Error handling patterns
- Human communication guidelines

## Critical Architecture Rules

1. **Explicit state** - `g_game_state['effects']['screen_shake']` not `shake`
2. **Copy don't abstract** - Duplicate similar code rather than generalize
3. **Flat hierarchy** - Minimize nesting and indirection
4. **Global visibility** - Use globals when it clarifies data flow
5. **Document side effects** - Every function must list what it modifies
6. **Fail safely** - Wrap risky operations (file I/O, parsing) in try-except

## File Structure
```
main.py          - Core loop, coordination (target: <5000 lines)
config.py        - All constants as Cfg.* 
data_structures.py - Entity types (ShipState, Asteroid, Enemy, etc.)
particle_system.py - ParticlePool class
sound_system.py  - Audio (optional system)
visual_effects.py - Pure rendering functions
progression_system.py - Save/load, achievements
drawing_system.py - DrawingSystem class
```

**Modularization Rule**: Split files only when LLMs cannot reliably edit them (>5000 lines) or when systems are completely independent. Single file preferred when possible.

**Current Status**: Originally a single file, modularized at ~5,500 lines due to LLM editing limitations. Would return to single file if LLM capabilities improve.

## Required Patterns

### Adding Features
```python
# 1. Add type to data_structures.py
PowerUpType.NEW_TYPE = 'new_type'

# 2. Configure in config.py
Cfg.powerup_types[PowerUpType.NEW_TYPE] = {'color': (R,G,B), 'symbol': 'X'}
Cfg.powerup_new_type_duration = 300

# 3. Add state to ShipState
class ShipState:
    new_type_active: float = 0

# 4. Implement effect
POWERUP_EFFECTS[PowerUpType.NEW_TYPE] = lambda: setattr(g_ship, 'new_type_active', duration)

# 5. Update logic in relevant update_* functions
```

### Function Documentation
```python
def function_name(param: type) -> return_type:
    """One line description.
    
    Side effects:
        - Modifies g_game_state['key']
        - Creates particles in g_particle_pool
        
    Globals:
        Reads: g_ship, g_screen_width
        Writes: g_game_state, g_particles
    """
```

### State Access Pattern
```python
# Always use full paths for clarity and searchability
g_game_state['combo']['current'] += 1
g_game_state['effects']['damage_flash'] = 60
```

### Error Handling Pattern
```python
try:
    with open(Cfg.save_file, 'w') as f:
        json.dump(save_data, f)
except Exception as e:
    print(f"[save_game] Failed: {e}")
    return False
```

## Human Communication

### Input Translation
- "Ship too slow" → Increase `Cfg.ship_max_speed`
- "Enemies too aggressive" → Adjust `enemy_ai` parameters in config
- "Crashes when X" → Add bounds checking at X interaction
- "Feels laggy" → Check particle counts, reduce if >1000

### Output Translation  
- Code change → Player experience description
- Never mention functions, variables, or technical details
- Focus on what player will see/feel

## Debugging Protocol

1. **Reproduction** - Get exact steps from human
2. **Instrumentation** - Add logging at suspected points
3. **State verification** - Log `g_game_state` before/after issue
4. **Edge cases** - Check bounds, nulls, empty lists
5. **Revert option** - Use git if changes break more than fix

## Global State Reference

### Entity Classes
See `data_structures.py` for: `ShipState`, `Asteroid`, `Bullet`, `Enemy`, `PowerUp`, `Particle`, `FloatingText`

### Core Globals
- `g_game_state` - All mutable game state (see structure below)
- `g_ship: ShipState` - Player ship instance  
- `g_asteroids: List[Asteroid]` - Active asteroids
- `g_bullets: List[Bullet]` - Player projectiles
- `g_enemies: List[Enemy]` - Enemy list
- `g_powerups: List[PowerUp]` - Active powerups
- `g_particle_pool: ParticlePool` - Particle system
- `g_screen_width/height: int` - Display dimensions

### State Dictionary Structure
```python
g_game_state = {
    'score': int,
    'lives': int,
    'level': int,
    'crystals': int,
    'game_over': bool,
    'paused': bool,
    'show_upgrade_menu': bool,
    'effects': {
        'screen_shake': float,
        'damage_flash': float,
        'damage_flash_color': tuple,
        'level_transition': float,
        'level_transition_text': str,
        'aura_rotation': float,
        'pause_menu_alpha': int,
        'wave_warning': float,
        'wave_warning_text': str
    },
    'combo': {
        'current': int,
        'timer': float,
        'kills': int,
        'max': int,
        'pulse': float
    },
    'finisher': {
        'meter': float,
        'ready': bool,
        'executing': bool,
        'execution_timer': int,
        'phase': FinisherPhase,
        'target': Optional[Enemy],
        'shockwave_radius': float,
        'lock_on_progress': float,
        'impact_x': float,
        'impact_y': float
    },
    'dash': {
        'cooldown': float
    },
    # Persistent data
    'high_score': int,
    'lifetime_crystals': int,
    'achievements_unlocked': set,
    'upgrade_levels': dict,
    'boss_kills': int
}
```

## Constraints
- Maintain 60 FPS (frame time < 16ms)
- Active particles < 1000 (ParticlePool limit)
- Simultaneous enemies < 10 
- Save format: JSON to `Cfg.save_file`
- File size targets: <5000 lines per file for reliable LLM editing

## Update Order (Critical)
1. `handle_events()` - Input processing
2. `update_game_state()` - Ship, enemies, bullets physics
3. `handle_collisions()` - Collision detection/resolution
4. `update_visual_effects()` - Particles, floating text
5. `render_frame()` - Draw everything

## Common Operations

### Create Explosion
```python
create_explosion(x, y, particle_count, color, is_enemy=False)
# Side effects: adds screen shake, plays sound, creates particles
```

### Spawn Enemy
```python
g_enemies.append(create_enemy(x, y))  # None for random position
```

### Add Score with Combo
```python
g_game_state['score'] += points
add_combo()  # Updates combo counter and finisher meter
```

### Check Achievement
```python
check_achievement('achievement_id')  # Auto-saves if unlocked
```

### Create Floating Text
```python
create_floating_text(x, y, "Text", color_tuple)
# Shows temporary text that floats upward
```

## Version Control Protocol
- Commit before major changes
- If 3 attempts fail to fix issue: revert to last working commit
- Small commits reduce revert impact
- Each commit should leave game playable

## Modification Priority
1. **Works correctly** - Game runs without crashes
2. **LLM understandable** - Next LLM can modify it
3. **Pattern consistent** - Matches existing code style
4. **Debuggable** - Can trace issues easily

Traditional software principles (DRY, SOLID, etc.) explicitly ignored unless they serve above priorities.

## Implementation Insights
*This section captures lessons learned and patterns discovered during development*

### Dependency Injection Pattern
Used in `ProgressionSystem` and `DrawingSystem` to avoid circular imports while maintaining modularity:
```python
# Pass functions as dependencies instead of importing
progression = ProgressionSystem(
    create_floating_text=create_floating_text,
    update_scaled_values=update_scaled_values
)
```

### Wrapper Functions During Migration
When refactoring to classes, maintain compatibility with temporary wrappers:
```python
def old_function_name():
    ctx = create_game_context()
    return new_class.method(ctx)
```

### Context Objects for Parameter Reduction
Bundle related parameters to avoid excessive function arguments:
```python
ctx = {
    'screen_width': g_screen_width,
    'screen_height': g_screen_height,
    'scale_factor': g_scale_factor
}
```

---
*Last Updated: June 2025 - Added modular architecture patterns and self-updating mechanism*