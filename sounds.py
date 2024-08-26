import random
import pygame
import os


class SoundSystem:
    def __init__(self, sound_dir='sounds'):
        pygame.mixer.init()
        self.sound_dir = sound_dir
        self.sound_effects = {
            "hit": ["hit1.wav", "hit2.wav", "hit3.wav"],
            "miss": ["miss1.wav", "miss2.wav"],
            "critical": ["crit1.wav", "crit2.wav"],
            "player_death": ["player_death.wav"],
            "enemy_death": ["enemy_death1.wav", "enemy_death2.wav"],
            "battle_start": ["battle_start.wav"],
            "battle_end": ["victory.wav", "defeat.wav"],
            "armor_block": ["armor_block1.wav", "armor_block2.wav"],
            "weapon_swing": ["swing1.wav", "swing2.wav", "swing3.wav"]
        }
        self.loaded_sounds = {}
        self._load_sounds()

    def _load_sounds(self):
        for sound_type, files in self.sound_effects.items():
            self.loaded_sounds[sound_type] = []
            for file in files:
                file_path = os.path.join(self.sound_dir, file)
                if os.path.exists(file_path):
                    sound = pygame.mixer.Sound(file_path)
                    self.loaded_sounds[sound_type].append(sound)
                else:
                    print(f"Warning: Sound file not found: {file_path}")

    def play_sound(self, sound_type):
        if sound_type in self.loaded_sounds and self.loaded_sounds[sound_type]:
            sound = random.choice(self.loaded_sounds[sound_type])
            sound.play()
            print(f"Playing sound: {sound_type}")
        else:
            print(f"Sound type '{sound_type}' not found or no sound files loaded")

    def add_sound_effect(self, sound_type, sound_file):
        file_path = os.path.join(self.sound_dir, sound_file)
        if os.path.exists(file_path):
            if sound_type not in self.sound_effects:
                self.sound_effects[sound_type] = []
                self.loaded_sounds[sound_type] = []
            self.sound_effects[sound_type].append(sound_file)
            sound = pygame.mixer.Sound(file_path)
            self.loaded_sounds[sound_type].append(sound)
            print(f"Added sound effect '{sound_file}' to '{sound_type}'")
        else:
            print(f"Sound file not found: {file_path}")

    def list_sound_effects(self):
        for sound_type, files in self.sound_effects.items():
            print(f"{sound_type}: {', '.join(files)}")


if __name__ == "__main__":
    # Create an instance of the SoundSystem
    sound_system = SoundSystem()

    # Test playing existing sound effects
    print("Testing existing sound effects:")
    sound_system.play_sound("hit")
    sound_system.play_sound("miss")
    sound_system.play_sound("critical")

    # Test playing a non-existent sound effect
    print("\nTesting non-existent sound effect:")
    sound_system.play_sound("explosion")

    # Add a new sound effect
    print("\nAdding a new sound effect:")
    sound_system.add_sound_effect("explosion", "big_boom.wav")

    # Play the newly added sound effect
    print("\nPlaying newly added sound effect:")
    sound_system.play_sound("explosion")

    # List all sound effects
    print("\nListing all sound effects:")
    sound_system.list_sound_effects()

    # Keep the program running to hear the sounds
    print("\nPress Enter to exit...")
    input()