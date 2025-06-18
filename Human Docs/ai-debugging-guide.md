# AI-Assisted Debugging Best Practices

## Overview
This guide outlines effective strategies for debugging software issues with the help of AI assistants (like ChatGPT, Claude, or Copilot). The key principle is that AI can analyze code patterns but cannot see your runtime environment—print debugging creates the visibility bridge.

**Note**: In environments where prints are hidden (GUIs, background threads), redirect output to log files or use logging frameworks instead of `print()`.

## Why Print Debugging Works Best with AI

- **Visibility**: AI can only analyze what you share as text
- **Persistence**: Logs create a permanent record of execution
- **Context**: Print statements capture the exact state at critical moments
- **Speed**: Faster iteration than describing debugger states

## The 5-Step Debugging Workflow

### 1. Formulate a Clear Hypothesis
Before adding any debug code:
- **State the expected behavior**: "The user login should redirect to dashboard"
- **Describe the actual behavior**: "The login succeeds but stays on login page"
- **Initial hypothesis**: "The redirect logic might have a conditional error"

### 2. Add Strategic Debug Prints
Place prints at decision points, not randomly:

```python
# Function entry/exit
print(f"[DEBUG] Entering {function_name} with args: {args}")
print(f"[DEBUG] Exiting {function_name} with result: {result}")

# Conditional branches
print(f"[DEBUG] Checking condition: user.is_authenticated = {user.is_authenticated}")
print(f"[DEBUG] Taking branch: {'authenticated' if user.is_authenticated else 'guest'}")

# State snapshots
print(f"[DEBUG] Current state: {{'user_id': {user_id}, 'session': {session_id}}}")

# Loop progress
print(f"[DEBUG] Loop iteration {i}: processing {item}")
```

### 3. Capture Expected vs Actual
This pattern reveals logic errors instantly:

```python
# Compare expectations to reality
print(f"[DEBUG] Expected user role: 'admin'")
print(f"[DEBUG] Actual user role: '{user.role}'")

# Show data structure contents
print(f"[DEBUG] Cache contents: {list(cache.keys())}")
print(f"[DEBUG] Active sessions: {len(active_sessions)}")
```

### 4. Run Tests and Collect Output
- Execute the exact steps that trigger the bug
- Copy the **complete** terminal output
- Include any error messages or stack traces
- Note the sequence of actions taken

### 5. Present to AI Assistant
Structure your request effectively:

```
I'm debugging a [brief description of issue].

**Expected behavior:** [What should happen]
**Actual behavior:** [What actually happens]

**Relevant code:**
[paste code with debug prints]

**Debug output:**
[paste complete terminal output]

**What I've tried:** [Any fixes attempted]
```

## Debug Print Patterns

### Pattern 1: Trace Execution Flow
```python
print("[DEBUG] === Starting user authentication ===")
print(f"[DEBUG] Step 1: Validating credentials for {username}")
print(f"[DEBUG] Step 2: Credentials valid: {is_valid}")
print(f"[DEBUG] Step 3: Creating session")
print("[DEBUG] === Authentication complete ===")
```

### Pattern 2: Data Structure Inspection
```python
print(f"[DEBUG] Object type: {type(obj).__name__}")
print(f"[DEBUG] Object attributes: {vars(obj)}")
print(f"[DEBUG] Dictionary keys: {list(my_dict.keys())}")
print(f"[DEBUG] List length: {len(my_list)}, first item: {my_list[0] if my_list else 'empty'}")
```

### Pattern 3: Timing and Performance
```python
import time
start = time.time()
# ... code to measure ...
print(f"[DEBUG] Operation took: {time.time() - start:.3f} seconds")
```

## Common Debugging Scenarios

| Issue Type | What to Print | Example |
|------------|---------------|---------|
| Variable is None/null | The variable and where it's set | `print(f"[DEBUG] user = {user}, set at line X")` |
| Wrong calculation | Input values and result | `print(f"[DEBUG] calc: {a} + {b} = {result}")` |
| Missing data | Container contents | `print(f"[DEBUG] keys in response: {response.keys()}")` |
| Logic error | Condition values | `print(f"[DEBUG] if {x} > {y}: {x > y}")` |
| Import issues | Module attributes | `print(f"[DEBUG] module attrs: {dir(module)}")` |
| State corruption | Before/after state | `print(f"[DEBUG] state before: {state}")` |

## When to Use Other Tools

### Use IDE Debugger for:
- Inspecting complex nested objects
- Analyzing call stacks
- Memory profiling
- Performance bottlenecks

### Use Error Logs for:
- Production issues
- Intermittent bugs
- Multi-threaded problems

### Use Unit Tests for:
- Regression prevention
- Edge case documentation
- Behavior verification

## Pro Tips

1. **Label your prints clearly**: Use `[DEBUG]` prefix for easy filtering
2. **Include context**: Don't just print `x`, print `after calculation: x={x}`
3. **Keep prints temporarily**: Remove only after bug is confirmed fixed
4. **Version control**: Commit working code before adding debug prints
5. **Binary search**: Start with broad prints, then narrow down
6. **Avoid print overload in loops**: Sample or summarize:
   ```python
   # Instead of printing every item
   if i % 100 == 0:  # Print every 100th item
       print(f"[DEBUG] Processing item {i} of {total}")
   ```
7. **Security warning**: Never print passwords, API keys, or sensitive user data that might be shared with external AI services

## Debug Print Utilities

Consider adding these helper functions to your project:

```python
def debug_vars(**kwargs):
    """Print multiple variables with their names"""
    for name, value in kwargs.items():
        print(f"[DEBUG] {name} = {value} (type: {type(value).__name__})")

def debug_trace(message):
    """Print with timestamp and location"""
    import inspect
    frame = inspect.currentframe().f_back
    print(f"[DEBUG] {frame.f_code.co_filename}:{frame.f_lineno} - {message}")

# Usage:
debug_vars(user_id=123, status='active')
debug_trace("Entering validation")
```

## Checklist Before Asking AI

- [ ] Added prints at all key decision points
- [ ] Captured expected vs actual values
- [ ] Captured relevant inputs (user actions, data values, config settings)
- [ ] Included complete error messages/stack traces
- [ ] Ran the buggy scenario and collected output
- [ ] Identified what changed recently (if applicable)
- [ ] Prepared minimal reproducible example (if possible)

## Sample AI Request Template

```
I'm debugging an issue where [describe the problem].

Expected: [what should happen]
Actual: [what happens instead]

Here's my instrumented code:
```python
[paste relevant code with debug prints]
```

Debug output:
```
[paste the terminal output]
```

The issue seems to occur at [specific point]. Any ideas?
```

---

**Remember**: The goal is to make the invisible visible. Good debug prints tell the complete story of your program's execution, allowing AI to spot patterns and issues that might be missed otherwise.