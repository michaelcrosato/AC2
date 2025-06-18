"""
Sound system for the Asteroids game.

This module handles all sound generation, management, and playback functionality.
"""

import pygame
import random
import math
from typing import Dict, Optional, Union, Tuple

# Try to import numpy for sound generation
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Numpy not found. Game will run without sound.")

# Sound system globals
g_sounds: Dict[str, pygame.mixer.Sound] = {}


class SoundConfig:
    """Sound system configuration."""
    sound_enabled: bool = False
    sound_master_volume: float = 0.3
    sound_shoot_volume: float = 0.3
    sound_explosion_volume: float = 0.5
    sound_thrust_volume: float = 0.15
    sound_shoot_variations: int = 3
    sound_explosion_variations: int = 2
    enemy_volume: float = 0.4
    powerup_volume: float = 0.35
    finisher_volume: float = 0.6


def play_sound(sound_name: str, x_pos: Optional[float] = None, volume_scale: float = 1.0, 
               screen_width: int = 800) -> bool:
    """Play a sound with optional positional audio.
    
    Args:
        sound_name: Name of sound to play
        x_pos: X position for stereo panning (None for center)
        volume_scale: Volume multiplier
        screen_width: Screen width for panning calculation
    
    Returns:
        True if sound played successfully
    """
    if not SoundConfig.sound_enabled or not g_sounds:
        return False
    
    try:
        sound_variations = {
            'shoot': ['shoot1', 'shoot2', 'shoot3'],
            'explosion_small': ['explosion_small1', 'explosion_small2'],
            'explosion_medium': ['explosion_medium1', 'explosion_medium2'],
            'explosion_large': ['explosion_large1', 'explosion_large2']
        }
        
        actual_sound_name = sound_name
        if sound_name in sound_variations:
            actual_sound_name = random.choice(sound_variations[sound_name])
        
        if actual_sound_name in g_sounds:
            sound = g_sounds[actual_sound_name]
            
            if x_pos is not None:
                pan = max(0, min(1, x_pos / screen_width))
                channel = sound.play()
                if channel:
                    left_vol = (1 - pan) * volume_scale
                    right_vol = pan * volume_scale
                    channel.set_volume(left_vol, right_vol)
            else:
                channel = sound.play()
                if channel:
                    channel.set_volume(volume_scale)
            
            return True
        return False
    except Exception as e:
        print(f"[play_sound] Error playing sound '{sound_name}': {e}")
        return False


def stop_thrust_sound() -> None:
    """Stop the continuous thrust sound."""
    if 'thrust' in g_sounds:
        try:
            g_sounds['thrust'].stop()
        except:
            pass


def stop_all_sounds() -> None:
    """Stop all currently playing sounds."""
    if SoundConfig.sound_enabled and g_sounds:
        try:
            pygame.mixer.stop()
        except:
            pass


def toggle_sound() -> bool:
    """Toggle sound on/off.
    
    Returns:
        New sound enabled state
    """
    SoundConfig.sound_enabled = not SoundConfig.sound_enabled
    if not SoundConfig.sound_enabled:
        stop_all_sounds()
    return SoundConfig.sound_enabled


# Sound generation functions (only available with numpy)
if NUMPY_AVAILABLE:
    def generate_sound(duration: float, frequency: Union[float, Tuple[float, float]], 
                      wave_type: str = 'sine', sample_rate: int = 22050) -> np.ndarray:
        """Generate basic waveforms for sound effects.
        
        Args:
            duration: Sound duration in seconds
            frequency: Frequency in Hz (single value or start/end tuple for sweep)
            wave_type: Type of wave ('sine', 'sweep', 'noise')
            sample_rate: Sample rate in Hz
            
        Returns:
            Numpy array of sound samples
        """
        frames = int(duration * sample_rate)
        if frames <= 0:
            return np.array([])
        
        t = np.arange(frames) / sample_rate
        
        if wave_type == 'sine':
            wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'sweep':
            if isinstance(frequency, tuple):
                freq_start, freq_end = frequency
                freq_sweep = np.linspace(freq_start, freq_end, frames)
                phase = 2 * np.pi * np.cumsum(freq_sweep) / sample_rate
                wave = np.sin(phase)
            else:
                wave = np.sin(2 * np.pi * frequency * t)
        elif wave_type == 'noise':
            wave = np.random.normal(0, 0.1, frames)
        else:
            wave = np.zeros(frames)
        
        fade_frames = min(int(0.01 * sample_rate), frames // 4)
        if fade_frames > 0:
            wave[:fade_frames] *= np.linspace(0, 1, fade_frames)
            wave[-fade_frames:] *= np.linspace(1, 0, fade_frames)
        
        return wave

    def apply_envelope(sound: np.ndarray, envelope_type: str = 'exp', decay_rate: float = 5) -> np.ndarray:
        """Apply amplitude envelope to sound.
        
        Args:
            sound: Sound samples
            envelope_type: Type of envelope ('exp', 'linear')
            decay_rate: Decay rate for exponential envelope
            
        Returns:
            Sound with envelope applied
        """
        frames = len(sound)
        if frames == 0:
            return sound
        
        if envelope_type == 'exp':
            envelope = np.exp(-np.linspace(0, decay_rate, frames))
        elif envelope_type == 'linear':
            envelope = np.linspace(1, 0, frames)
        else:
            envelope = np.ones(frames)
        
        return sound * envelope

    def mix_sounds(*sounds) -> np.ndarray:
        """Mix multiple sounds together.
        
        Args:
            *sounds: Variable number of sound arrays
            
        Returns:
            Mixed sound array
        """
        if not sounds:
            return np.array([])
        
        max_length = max(len(s) for s in sounds)
        mixed = np.zeros(max_length)
        
        for sound in sounds:
            if len(sound) > 0:
                mixed[:len(sound)] += sound
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 0:
            mixed = mixed / max_val * 0.8
        
        return mixed

    def numpy_to_pygame_sound(numpy_array: np.ndarray, sample_rate: int = 22050) -> pygame.mixer.Sound:
        """Convert numpy array to pygame sound object.
        
        Args:
            numpy_array: Sound samples
            sample_rate: Sample rate (not used but kept for compatibility)
            
        Returns:
            Pygame Sound object
        """
        sound = np.array(numpy_array * 32767, dtype=np.int16)
        stereo_sound = np.zeros((len(sound), 2), dtype=np.int16)
        stereo_sound[:, 0] = sound
        stereo_sound[:, 1] = sound
        
        return pygame.sndarray.make_sound(stereo_sound)


def init_sounds() -> None:
    """Initialize all game sounds."""
    global g_sounds
    
    if not NUMPY_AVAILABLE:
        SoundConfig.sound_enabled = False
        return
    
    try:
        g_sounds = {}
        sample_rate = 22050
        
        # Shooting sounds
        for i in range(SoundConfig.sound_shoot_variations):
            freq_start = 800 + i * 100
            freq_end = 200 - i * 50
            sweep = generate_sound(0.1, (freq_start, freq_end), 'sweep')
            click = generate_sound(0.01, 2000 + i * 200, 'sine') * 0.3
            
            shoot_sound = mix_sounds(
                sweep * 0.7,
                click,
                generate_sound(0.1, 0, 'noise') * 0.1
            )
            shoot_sound = apply_envelope(shoot_sound, 'exp', 10)
            
            g_sounds[f'shoot{i+1}'] = numpy_to_pygame_sound(
                shoot_sound * SoundConfig.sound_shoot_volume * SoundConfig.sound_master_volume)
        
        # Explosion sounds
        explosion_configs = {
            'small': {'duration': 0.2, 'freq': 800, 'rumble': 40, 'decay': 8},
            'medium': {'duration': 0.4, 'freq': 500, 'rumble': 40, 'decay': 5},
            'large': {'duration': 0.6, 'freq': 300, 'rumble': 25, 'decay': 3}
        }
        
        for size, config in explosion_configs.items():
            for i in range(SoundConfig.sound_explosion_variations):
                crack = generate_sound(0.02, config['freq'], 'sine')
                crack = apply_envelope(crack, 'linear')
                
                noise = generate_sound(config['duration'], 0, 'noise')
                noise = apply_envelope(noise, 'exp', config['decay'])
                
                rumble = generate_sound(config['duration'], config['rumble'] + random.randint(-10, 10), 'sine')
                rumble *= 0.3
                
                explosion = mix_sounds(
                    crack * 0.5,
                    noise * 0.7,
                    rumble
                )
                
                g_sounds[f'explosion_{size}{i+1}'] = numpy_to_pygame_sound(
                    explosion * SoundConfig.sound_explosion_volume * SoundConfig.sound_master_volume)
        
        # Dash sound
        dash_sweep = generate_sound(0.3, (3000, 500), 'sweep')
        dash_noise = generate_sound(0.3, 0, 'noise') * 0.2
        dash_sound = mix_sounds(dash_sweep, dash_noise)
        dash_sound[:int(0.02 * sample_rate)] *= np.linspace(0, 1, int(0.02 * sample_rate))
        g_sounds['dash'] = numpy_to_pygame_sound(dash_sound * SoundConfig.sound_master_volume)
        
        # Enemy sounds
        enemy_sweep = generate_sound(0.12, (600, 100), 'sweep')
        enemy_sound = apply_envelope(enemy_sweep, 'exp', 8)
        g_sounds['enemy_shoot'] = numpy_to_pygame_sound(enemy_sound * 0.7 * SoundConfig.sound_master_volume)
        
        enemy_exp = mix_sounds(
            generate_sound(0.3, 150, 'sine') * 0.3,
            generate_sound(0.3, 0, 'noise') * 0.4,
            generate_sound(0.3, 300, 'sine') * 0.2
        )
        enemy_exp = apply_envelope(enemy_exp, 'exp', 10)
        g_sounds['enemy_explosion'] = numpy_to_pygame_sound(enemy_exp * SoundConfig.enemy_volume * SoundConfig.sound_master_volume)
        
        # Crystal pickup sound
        crystal_freqs = [523, 659, 784, 1047, 1319, 1568]
        crystal_sound = np.zeros(int(0.5 * sample_rate))
        for i, freq in enumerate(crystal_freqs):
            start = int(i * 0.08 * sample_rate)
            duration = int(0.15 * sample_rate)
            if start + duration <= len(crystal_sound):
                tone = generate_sound(0.15, freq, 'sine')
                tone = apply_envelope(tone, 'exp', 3)
                crystal_sound[start:start+len(tone)] += tone * 0.4
        
        g_sounds['powerup_crystal'] = numpy_to_pygame_sound(crystal_sound * SoundConfig.powerup_volume * SoundConfig.sound_master_volume)
        
        # Powerup sounds
        powerup_configs = {
            'life': {'freqs': [523, 659, 784], 'duration': 0.3},
            'rapid': {'freqs': [400, 600, 800], 'duration': 0.3},
            'triple': {'freqs': [440, 550, 660], 'duration': 0.3},
            'shield': {'freqs': [300, 400, 500], 'duration': 0.3}
        }
        
        for ptype, config in powerup_configs.items():
            sound_frames = int(config['duration'] * sample_rate)
            powerup_sound = np.zeros(sound_frames)
            
            for i, freq in enumerate(config['freqs']):
                start = int(i * 0.1 * sample_rate)
                if start < sound_frames:
                    tone = generate_sound(0.1, freq, 'sine')
                    tone = apply_envelope(tone, 'exp', 5)
                    end = min(start + len(tone), sound_frames)
                    powerup_sound[start:end] += tone[:end-start] * 0.5
            
            g_sounds[f'powerup_{ptype}'] = numpy_to_pygame_sound(
                powerup_sound * SoundConfig.powerup_volume * SoundConfig.sound_master_volume)
        
        # Thrust sound
        thrust_base = generate_sound(1.0, 60, 'sine')
        thrust_wobble = generate_sound(1.0, 5, 'sine') * 10
        thrust_freq = 60 + thrust_wobble
        thrust_frames = int(1.0 * sample_rate)
        thrust_t = np.arange(thrust_frames) / sample_rate
        thrust_sound = np.sin(2 * np.pi * thrust_freq * thrust_t)
        thrust_sound += generate_sound(1.0, 0, 'noise') * 0.05
        
        g_sounds['thrust'] = numpy_to_pygame_sound(thrust_sound * SoundConfig.sound_thrust_volume * SoundConfig.sound_master_volume)
        
        # Level transition sound
        transition_sound = np.zeros(int(0.5 * sample_rate))
        chord_freqs = [392, 523, 659, 784]
        for i, freq in enumerate(chord_freqs):
            start = int(i * 0.12 * sample_rate)
            if start < len(transition_sound):
                tone = generate_sound(0.2, freq, 'sine')
                tone = apply_envelope(tone, 'exp', 2)
                end = min(start + len(tone), len(transition_sound))
                transition_sound[start:end] += tone[:end-start] * 0.4
        
        g_sounds['level_transition'] = numpy_to_pygame_sound(transition_sound * SoundConfig.sound_master_volume)
        
        SoundConfig.sound_enabled = True
        print(f"[init_sounds] Sound system initialized: {len(g_sounds)} sounds loaded")
        
    except Exception as e:
        print(f"[init_sounds] Could not initialize sound: {e}")
        print("Game will run without sound.")
        SoundConfig.sound_enabled = False


def get_sound_enabled() -> bool:
    """Get current sound enabled state."""
    return SoundConfig.sound_enabled


def set_sound_enabled(enabled: bool) -> None:
    """Set sound enabled state."""
    SoundConfig.sound_enabled = enabled
    if not enabled:
        stop_all_sounds() 