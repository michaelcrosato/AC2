# Refactoring Protocol for LLM-First Development

Version: 1.0.0  
Created: June 18, 2025  
Purpose: Prevent incomplete refactoring and code duplication

## Core Principle

**Code must exist in exactly ONE location**. During refactoring, the most dangerous state is having the same code in two places.

## The Five-Step Protocol

When moving code between files, **ALL FIVE STEPS ARE MANDATORY**:

### 1. **COPY** - Duplicate code to new location
```python
# progression_system.py
class ProgressionSystem:
    def save_game_state(self, ctx):
        # Full implementation copied here
        save_data = {...}
        with open(file, 'w') as f:
            json.dump(save_data, f)
```

### 2. **VERIFY** - Test new code works correctly
```python
# For simple functions:
g_progression = ProgressionSystem()
ctx = create_game_context()
result = g_progression.save_game_state(ctx)
assert result == True  # Verify it works

# For complex functions with side effects:
# - Rendering: Visually confirm output matches
# - File I/O: Check file contents are identical
# - Network: Log and compare requests
```

### 3. **UPDATE** - Change all call sites
```python
# Before: save_game_state()
# After:  g_progression.save_game_state(ctx)
# Or:     save_game_state_wrapper()  # If using compatibility layer
```

### 4. **DELETE** - Remove original immediately ⚠️
```python
# main.py
# DELETE THIS ENTIRE FUNCTION:
# def save_game_state():
#     save_data = {...}
#     with open(file, 'w') as f:
#         json.dump(save_data, f)
```

### 5. **TEST** - Run full game verification
- Start game
- Test moved functionality
- Verify no crashes or missing features

## Handling Dependencies

When moving a function, also move or handle its dependencies:

### Direct Dependencies (Helper Functions)
```python
# If moving save_game_state(), also move/handle:
def save_game_state():  # Main function
    if not validate_save_data(data):  # Helper function
        return False

# Options:
# 1. Move both together (preferred if helper is only used by main)
# 2. Import helper from original location (if shared)
# 3. Pass as parameter to avoid circular imports
```

### Circular Import Solutions
```python
# If circular import would occur:
# Option 1: Dependency injection (preferred - used in Asteroids)
class ProgressionSystem:
    def __init__(self, create_floating_text_fn):
        self.create_floating_text = create_floating_text_fn

# Option 2: Import inside function
def check_achievement(self):
    from main import create_floating_text  # Import when needed

# Option 3: Pass as parameter
def check_achievement(self, ctx, create_floating_text):
    # Use passed function
```

**Note**: The Asteroids project uses Option 1 (dependency injection) in both ProgressionSystem and DrawingSystem. Stay consistent with this pattern.

## Common Antipatterns

### ❌ The Worst Case: Dual Implementation
```python
# main.py
def draw_asteroid(surface, asteroid):
    # Original implementation
    ...

# drawing_system.py  
class DrawingSystem:
    def draw_asteroid(self, surface, asteroid):
        # Duplicate implementation
        ...

# Game calls both randomly!
```

**Why this is terrible:**
- Bug fixes might only update one version
- Features might diverge between implementations
- Doubles maintenance burden
- Confuses future LLMs

### ❌ The Half-Migration
```python
# Moved logic but kept helpers
# main.py
def save_game_state():  # Deleted ✓
def validate_save_data():  # Forgot to delete ✗
    # This helper is now orphaned!
```

### ❌ The Wrapper Trap
```python
# Added wrapper but kept original
def save_game_state():  # Original still here!
    ...

def save_game_state_wrapper():  # Wrapper added
    return g_progression.save_game_state()
```

## Correct Patterns

### ✓ Clean Module Migration
```python
# main.py (BEFORE)
def calculate_damage(weapon, armor):
    return weapon.power - armor.defense

# combat_system.py (AFTER)
class CombatSystem:
    def calculate_damage(self, weapon, armor):
        return weapon.power - armor.defense

# main.py (AFTER)
# Function completely removed, all calls updated to g_combat.calculate_damage()
```

### ✓ Temporary Compatibility Layer
```python
# main.py
# Original function DELETED
# Only wrapper remains during transition
def calculate_damage_wrapper(weapon, armor):
    return g_combat.calculate_damage(weapon, armor)

# Plan: Remove wrapper after all calls updated
```

**Wrapper Removal Rule**: After 1-2 commits or once all call sites are updated, wrappers MUST be deleted. They are technical debt, not permanent fixtures.

## When to Apply This Protocol

### Always Apply When:
- Moving functions between files
- Creating new modules from existing code
- Refactoring single-file → multi-file architecture
- Extracting classes from procedural code

### Exception: Copy Don't Abstract
The "copy don't abstract" principle from design-philosophy-LLM.md still applies to:
- Similar but distinct logic (e.g., enemy AI variants)
- Helper functions that would create circular imports
- Small utilities under 10 lines

But NEVER maintain two copies of the exact same function!

## Verification Checklist

After refactoring, verify:

- [ ] Original function deleted from source file
- [ ] No duplicate implementations exist
- [ ] All call sites updated
- [ ] No orphaned helper functions
- [ ] Game runs without errors
- [ ] `grep "def function_name"` returns only one result
- [ ] Any wrapper functions are marked for removal within 1-2 commits

## Quick Reference

```bash
# Find all definitions of a function
grep -r "def function_name" *.py

# Find all calls to a function
grep -r "function_name(" *.py

# Check for duplicate implementations
# If this returns >1 result, you have a problem:
grep -r "def draw_asteroid" *.py
```

## Specific to Asteroids Project

Based on the current incomplete refactoring:

### Functions to Migrate Completely:
1. **Drawing**: All `draw_*` → `DrawingSystem`
2. **Progression**: save/load/achievements → `ProgressionSystem`  
3. **Visual Effects**: helpers → `visual_effects.py`
4. **Sound**: audio functions → `sound_system.py`

### Current Status Check:
```python
# These should return 0 results in main.py:
# grep "def draw_" main.py
# grep "def save_game_state(" main.py  # (except wrapper)
# grep "def check_achievement(" main.py  # (except wrapper)
```

## Remember

**The refactoring isn't complete until the old code is deleted.**

Every function should have exactly one home. If an LLM can find the same function in two places, the refactoring has failed.

## LLM-Specific Guidance

If you are an LLM performing refactoring:

### When to Ask for Human Confirmation:
- You find the same function in multiple files
- You're unsure if all call sites have been updated
- Dependencies create circular imports you can't resolve
- The VERIFY step fails and you can't determine why

### Your Responsibilities:
1. **Always run the verification checklist** before declaring success
2. **Never skip the DELETE step** - this is where most refactors fail
3. **Document what you moved** in your response:
   ```
   Moved: save_game_state() from main.py → ProgressionSystem
   Deleted: Original function at line 750
   Updated: 12 call sites to use wrapper
   ```

### Red Flags to Report:
- Finding a function implementation AND its wrapper AND the new version (triple duplication!)
- Wrappers older than 2 commits
- Functions that appear to do the same thing with different names