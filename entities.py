import random
from typing import Dict, List, Any
import inspect

import random
from typing import Dict, List, Any


class Enemy:
    type = "enemy"
    base_hp = 100
    base_min_damage = 1
    base_max_damage = 2
    base_armor = 0
    crit_chance = 0.05
    crit_damage = 1.5
    drop_chance = 0.1
    regular_drop: Dict[str, int] = {}
    probability = 0
    map_size = 1000
    max_entities = None
    max_entities_total = None
    herd_probability = 0.5
    min_level = 1
    max_level = 100
    experience_value = 10
    evasion_chance = 0.0
    block_chance = 0.0
    block_reduction = 0.5
    biome = "any"

    def __init__(self, level: int):
        self.level = max(self.min_level, min(level, self.max_level))
        self.max_hp = self.calculate_hp()
        self.hp = self.max_hp
        self.min_damage, self.max_damage = self.calculate_damage()
        self.armor = self.calculate_armor()
        self.alive = True
        self.experience = self.calculate_experience()
        self.evasion = self.calculate_evasion()
        self.block = self.calculate_block()

    def calculate_hp(self):
        return int(self.base_hp * (1 + 0.1 * (self.level - 1)))  # 10% increase per level

    def calculate_damage(self):
        scaling_factor = 1 + 0.05 * (self.level - 1)  # 5% increase per level
        min_damage = int(self.base_min_damage * scaling_factor)
        max_damage = int(self.base_max_damage * scaling_factor)
        return min_damage, max_damage

    def calculate_armor(self):
        return self.base_armor + int(0.5 * (self.level - 1))  # 0.5 armor increase per level

    def calculate_experience(self):
        return int(self.experience_value * (1 + 0.1 * (self.level - 1)))  # 10% increase per level

    def calculate_evasion(self):
        return self.evasion_chance + (0.002 * (self.level - 1))  # 0.2% increase per level

    def calculate_block(self):
        return self.block_chance + (0.002 * (self.level - 1))  # 0.2% increase per level

    def roll_damage(self):
        damage = random.randint(self.min_damage, self.max_damage)
        message = "normal hit"
        if random.random() < self.crit_chance:
            damage = int(damage * self.crit_damage)
            message = "critical hit"
        return {"damage": damage, "message": message}

    def attempt_evasion(self):
        return random.random() < self.evasion

    def attempt_block(self):
        return random.random() < self.block

    def take_damage(self, damage: int) -> Dict[str, Any]:
        mitigated_damage = max(0, damage - self.armor)
        self.hp -= mitigated_damage
        message = f"The {self.type} took {mitigated_damage} damage."
        special_effect = self.process_special_effects()
        if special_effect:
            message += f" {special_effect}"

        return {
            "damage_taken": damage,
            "current_hp": self.hp,
            "message": message,
            "is_defeated": self.hp <= 0
        }

    def process_special_effects(self) -> str:
        """
        Process any special effects that occur when the enemy takes damage.
        Override this method in subclasses to implement enemy-specific effects.
        """
        return ""

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "fight", "action": f"/fight?target={self.type}"}]

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "level": self.level,
        }


class Skeleton(Enemy):
    type = "skeleton"
    base_hp = 50
    base_min_damage = 5
    base_max_damage = 10
    base_armor = 2
    crit_chance = 0.2
    crit_damage = 1.5
    drop_chance = 0.5
    regular_drop = {"bone": 2}
    probability = 0.24
    max_entities = 300
    max_entities_total = 500
    herd_probability = 0.4
    min_level = 5
    max_level = 30
    experience_value = 20
    reassemble_chance = 0.2
    block_chance = 0.1
    block_reduction = 0.3
    biome = "graveyard"

    def __init__(self, level: int):
        super().__init__(level)
        self.has_reassembled = False

    def process_special_effects(self) -> str:
        if self.hp <= 0 and not self.has_reassembled and random.random() < self.reassemble_chance:
            self.hp = self.calculate_hp() // 2  # Reassemble with half HP
            self.has_reassembled = True
            return "The skeleton has reassembled itself!"
        return ""

class Boar(Enemy):
    type = "boar"
    base_hp = 35
    base_min_damage = 2
    base_max_damage = 4
    crit_chance = 0.1
    crit_damage = 1.5
    drop_chance = 0.2
    regular_drop = {"food": 1}
    probability = 0.1
    max_entities = 500
    max_entities_total = 1500
    herd_probability = 0.7
    min_level = 3
    max_level = 18
    experience_value = 10
    block_chance = 0.1
    block_reduction = 0.3
    biome="forest"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "hunt", "action": f"/fight?target={self.type}"}]

class Wolf(Enemy):
    type = "wolf"
    base_hp = 60
    base_min_damage = 3
    base_max_damage = 7
    crit_chance = 0.25
    crit_damage = 1.8
    drop_chance = 0.3
    regular_drop = {"wolf pelt": 1}
    probability = 0.2
    max_entities = 500
    max_entities_total = 1000
    herd_probability = 0.8
    min_level = 8
    max_level = 25
    experience_value = 15
    evasion_chance = 0.15
    biome="forest"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "hunt", "action": f"/fight?target={self.type}"}]

class Goblin(Enemy):
    type = "goblin"
    base_hp = 45
    base_min_damage = 4
    base_max_damage = 6
    base_armor = 1
    crit_chance = 0.15
    crit_damage = 1.6
    drop_chance = 0.4
    regular_drop = {"gold": 5}
    probability = 0.24
    max_entities = 200
    max_entities_total = 1000
    herd_probability = 0.5
    min_level = 5
    max_level = 45
    experience_value = 12
    evasion_chance = 0.1
    block_chance = 0.05
    block_reduction = 0.2
    biome="pond"

class Specter(Enemy):
    type = "specter"
    base_hp = 80
    base_min_damage = 10
    base_max_damage = 20
    crit_chance = 0.3
    crit_damage = 2.0
    drop_chance = 0.6
    regular_drop = {"ectoplasm": 1}
    probability = 0.24
    max_entities = 100
    max_entities_total = 1000
    herd_probability = 0.3
    min_level = 20
    max_level = 50
    experience_value = 40
    evasion_chance = 0.25
    biome="cavern"

    def roll_damage(self):
        damage_info = super().roll_damage()
        if damage_info["message"] == "critical hit":
            # Specters drain health on critical hits
            self.hp += damage_info["damage"] // 2
        return damage_info

class Hatchling(Enemy):
    type = "hatchling"
    base_hp = 150
    base_min_damage = 15
    base_max_damage = 25
    base_armor = 5
    crit_chance = 0.2
    crit_damage = 1.8
    drop_chance = 0.8
    regular_drop = {"dragon scale": 1}
    probability = 0.24
    max_entities = 50
    max_entities_total = 1000
    herd_probability = 0.2
    min_level = 30
    max_level = 70
    experience_value = 80
    block_chance = 0.15
    block_reduction = 0.4
    biome="cavern"

    def __init__(self, level: int):
        super().__init__(level)
        self.breath_attack_cooldown = 0

    def roll_damage(self):
        if self.breath_attack_cooldown == 0:
            # Use breath attack
            damage = random.randint(int(self.max_damage * 1.5), int(self.max_damage * 2))
            self.breath_attack_cooldown = 3
            return {"damage": damage, "message": "breath attack"}
        else:
            # Normal attack
            damage_info = super().roll_damage()
            self.breath_attack_cooldown -= 1
            return damage_info

class Bandit(Enemy):
    type = "bandit"
    base_hp = 70
    base_min_damage = 8
    base_max_damage = 15
    base_armor = 2
    crit_chance = 0.2
    crit_damage = 1.7
    drop_chance = 0.5
    regular_drop = {"gold": 10}
    probability = 0.24
    max_entities = 250
    max_entities_total = 1000
    herd_probability = 0.4
    min_level = 10
    max_level = 35
    experience_value = 25
    evasion_chance = 0.1
    block_chance = 0.1
    block_reduction = 0.3
    biome = "cavern"

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < 0.1:  # 10% chance to steal gold
            damage_info["message"] += " and stole some gold"
        return damage_info

class Troll(Enemy):
    type = "troll"
    base_hp = 200
    base_min_damage = 15
    base_max_damage = 30
    base_armor = 8
    crit_chance = 0.1
    crit_damage = 2.0
    drop_chance = 0.7
    regular_drop = {"troll hide": 1}
    probability = 0.24
    max_entities = 100
    max_entities_total = 1000
    herd_probability = 0.2
    min_level = 25
    max_level = 60
    experience_value = 70
    regeneration_rate = 5
    block_chance = 0.2
    block_reduction = 0.5
    biome = "mountain"

    def calculate_hp(self):
        hp = super().calculate_hp()
        return hp + self.regeneration_rate * (self.level - 1)  # Additional HP from regeneration

class Harpy(Enemy):
    type = "harpy"
    base_hp = 90
    base_min_damage = 12
    base_max_damage = 18
    base_armor = 1
    crit_chance = 0.3
    crit_damage = 1.6
    drop_chance = 0.6
    regular_drop = {"feather": 3}
    probability = 0.24
    max_entities = 150
    max_entities_total = 1000
    herd_probability = 0.5
    min_level = 15
    max_level = 45
    experience_value = 35
    evasion_chance = 0.2
    biome = "mountain"

    def roll_damage(self):
        damage_info = super().roll_damage()
        if self.attempt_evasion():
            damage_info["damage"] = 0
            damage_info["message"] = "evaded your attack"
        return damage_info

class Orc(Enemy):
    type = "orc"
    base_hp = 120
    base_min_damage = 10
    base_max_damage = 18
    base_armor = 4
    crit_chance = 0.12
    crit_damage = 1.8
    drop_chance = 0.6
    regular_drop = {"orc tusk": 1}
    probability = 0.24
    max_entities = 150
    max_entities_total = 1000
    herd_probability = 0.4
    min_level = 20
    max_level = 50
    experience_value = 50
    block_chance = 0.15
    block_reduction = 0.35
    biome = "cavern"

class Spider(Enemy):
    type = "spider"
    base_hp = 65
    base_min_damage = 6
    base_max_damage = 12
    base_armor = 2
    crit_chance = 0.18
    crit_damage = 1.7
    drop_chance = 0.5
    regular_drop = {"spider silk": 1, "venom sac": 1}
    probability = 0.24
    max_entities = 180
    max_entities_total = 1000
    herd_probability = 0.6
    min_level = 12
    max_level = 40
    experience_value = 30
    poison_chance = 0.15
    poison_duration = 3
    poison_damage = 2
    evasion_chance = 0.15
    biome = "cavern"

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < self.poison_chance:
            damage_info["message"] += f" and poisoned for {self.poison_damage} damage over {self.poison_duration} turns"
        return damage_info

class Rat(Enemy):
    type = "rat"
    base_hp = 20
    base_min_damage = 1
    base_max_damage = 2
    crit_chance = 0.05
    crit_damage = 1.3
    drop_chance = 0.2
    regular_drop = {"rat tail": 1}
    probability = 0.24
    max_entities = 1000
    max_entities_total = 1000
    herd_probability = 0.8
    min_level = 1
    max_level = 10
    experience_value = 5
    evasion_chance = 0.2  # Rats are small and quick, so they have a higher base evasion
    biome = "cavern"

class Minotaur(Enemy):
    type = "minotaur"
    base_hp = 300
    base_min_damage = 25
    base_max_damage = 40
    base_armor = 10
    crit_chance = 0.15
    crit_damage = 2.2
    drop_chance = 0.8
    regular_drop = {"minotaur horn": 1}
    probability = 0.24
    max_entities = 50
    max_entities_total = 1000
    herd_probability = 0.1
    min_level = 35
    max_level = 80
    experience_value = 100
    block_chance = 0.25
    block_reduction = 0.6
    biome = "cavern"

    def __init__(self, level: int):
        super().__init__(level)
        self.charge_cooldown = 0

    def roll_damage(self):
        if self.charge_cooldown == 0:
            damage = random.randint(int(self.max_damage * 1.5), int(self.max_damage * 2.5))
            self.charge_cooldown = 3
            return {"damage": damage, "message": "charging attack"}
        else:
            damage_info = super().roll_damage()
            self.charge_cooldown -= 1
            return damage_info

class Wraith(Enemy):
    type = "wraith"
    base_hp = 120
    base_min_damage = 18
    base_max_damage = 25
    crit_chance = 0.25
    crit_damage = 1.9
    drop_chance = 0.7
    regular_drop = {"soul essence": 1}
    probability = 0.24
    max_entities = 120
    max_entities_total = 1000
    herd_probability = 0.3
    min_level = 30
    max_level = 70
    experience_value = 75
    phase_chance = 0.3
    evasion_chance = 0.3
    biome = "pond"

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < self.phase_chance:
            damage_info["damage"] = int(damage_info["damage"] * 1.5)  # Wraith phases through armor
            damage_info["message"] += " (phased)"
        return damage_info

class Dragon(Enemy):
    type = "dragon"
    base_hp = 500
    base_min_damage = 40
    base_max_damage = 60
    base_armor = 20
    crit_chance = 0.2
    crit_damage = 2.5
    drop_chance = 1.0
    regular_drop = {"dragon scale": 3, "dragon tooth": 1}
    probability = 0.12
    max_entities = 50
    max_entities_total = 250
    herd_probability = 0
    min_level = 60
    max_level = 1000
    experience_value = 500
    block_chance = 0.3
    block_reduction = 0.7
    biome = "cavern"

    def __init__(self, level: int):
        super().__init__(level)
        self.breath_attack_cooldown = 0

    def roll_damage(self):
        if self.breath_attack_cooldown == 0:
            # Use breath attack
            damage = random.randint(int(self.max_damage * 2), int(self.max_damage * 3))
            self.breath_attack_cooldown = 3
            return {"damage": damage, "message": "devastating breath attack"}
        else:
            # Normal attack
            damage_info = super().roll_damage()
            self.breath_attack_cooldown -= 1
            return damage_info

class Lizarian(Enemy):
    type = "lizarian"
    base_hp = 400
    base_min_damage = 35
    base_max_damage = 55
    base_armor = 15
    crit_chance = 0.2
    crit_damage = 2.2
    drop_chance = 0.9
    regular_drop = {"lizard scale": 2, "magic essence": 1}
    probability = 0.15
    max_entities = 75
    max_entities_total = 300
    herd_probability = 0.1
    min_level = 55
    max_level = 750
    experience_value = 300
    evasion_chance = 0.15
    block_chance = 0.2
    block_reduction = 0.5
    biome = "desert"

    def __init__(self, level: int):
        super().__init__(level)
        self.spell_charges = 3

    def roll_damage(self):
        if self.spell_charges > 0:
            spell_type = random.choice(["fireball", "ice_shard", "lightning_bolt"])
            damage = random.randint(int(self.max_damage * 1.5), int(self.max_damage * 2.5))
            self.spell_charges -= 1
            return {"damage": damage, "message": f"cast {spell_type}"}
        else:
            damage_info = super().roll_damage()
            if random.random() < 0.2:  # 20% chance to regain a spell charge
                self.spell_charges = min(self.spell_charges + 1, 3)
                damage_info["message"] += " (regained spell charge)"
            return damage_info

class Golem(Enemy):
    type = "golem"
    base_hp = 600
    base_min_damage = 45
    base_max_damage = 70
    base_armor = 30
    crit_chance = 0.1
    crit_damage = 2.0
    drop_chance = 0.95
    regular_drop = {"golem core": 1, "enchanted stone": 3}
    probability = 0.12
    max_entities = 60
    max_entities_total = 250
    herd_probability = 0.05
    min_level = 65
    max_level = 400
    experience_value = 400
    block_chance = 0.4
    block_reduction = 0.8
    biome = "rock"

    def __init__(self, level: int):
        super().__init__(level)
        self.elemental_state = "neutral"
        self.state_duration = 0

    def roll_damage(self):
        if self.state_duration <= 0:
            self.elemental_state = random.choice(["fire", "ice", "lightning"])
            self.state_duration = 3

        damage_info = super().roll_damage()

        if self.elemental_state == "fire":
            damage_info["damage"] = int(damage_info["damage"] * 1.3)
            damage_info["message"] += " (fire enhanced)"
        elif self.elemental_state == "ice":
            self.armor += 10
            damage_info["message"] += " (ice armored)"
        elif self.elemental_state == "lightning":
            if random.random() < 0.3:
                damage_info["damage"] *= 2
                damage_info["message"] += " (lightning strike)"

        self.state_duration -= 1
        return damage_info

    def calculate_armor(self):
        return super().calculate_armor() + int(0.2 * self.level)  # Additional armor scaling

class Zombie(Enemy):
    type = "zombie"
    base_hp = 450
    base_min_damage = 40
    base_max_damage = 60
    base_armor = 10
    crit_chance = 0.15
    crit_damage = 1.8
    drop_chance = 0.85
    regular_drop = {"rotten flesh": 2, "zombie brain": 1}
    probability = 0.18
    max_entities = 100
    max_entities_total = 400
    herd_probability = 0.4
    min_level = 50
    max_level = 120
    experience_value = 250
    block_chance = 0.1
    block_reduction = 0.3
    biome = "graveyard"

    def __init__(self, level: int):
        super().__init__(level)
        self.infection_chance = 0.2
        self.frenzy_threshold = 0.3

    def roll_damage(self):
        damage_info = super().roll_damage()

        if random.random() < self.infection_chance:
            damage_info["damage"] += int(self.max_damage * 0.5)
            damage_info["message"] += " (infected)"

        if self.hp / self.max_hp <= self.frenzy_threshold:
            damage_info["damage"] = int(damage_info["damage"] * 1.5)
            damage_info["message"] += " (frenzy)"

        return damage_info

    def calculate_hp(self):
        return super().calculate_hp() + int(2 * self.level)


class Basilisk(Enemy):
    type = "basilisk"
    base_hp = 180
    base_min_damage = 20
    base_max_damage = 35
    base_armor = 12
    crit_chance = 0.15
    crit_damage = 2.0
    drop_chance = 0.7
    regular_drop = {"basilisk scale": 2, "petrified venom": 1}
    probability = 0.2
    max_entities = 80
    max_entities_total = 300
    herd_probability = 0.1
    min_level = 40
    max_level = 90
    experience_value = 150
    petrify_chance = 0.2
    block_chance = 0.2
    block_reduction = 0.5
    biome = "desert"

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < self.petrify_chance:
            damage_info["damage"] *= 2  # Double damage on petrify
            damage_info["message"] += " (petrifying gaze)"
        return damage_info

class Djinn(Enemy):
    type = "djinn"
    base_hp = 250
    base_min_damage = 30
    base_max_damage = 45
    base_armor = 8
    crit_chance = 0.2
    crit_damage = 2.2
    drop_chance = 0.8
    regular_drop = {"magical essence": 3, "djinn's lamp": 1}
    probability = 0.15
    max_entities = 60
    max_entities_total = 200
    herd_probability = 0.05
    min_level = 50
    max_level = 100
    experience_value = 200
    wish_chance = 0.25
    evasion_chance = 0.3
    biome = "desert"

    def roll_damage(self):
        if random.random() < self.wish_chance:
            effect = random.choice(["heal", "power", "defense"])
            if effect == "heal":
                self.hp = min(self.hp + self.max_hp // 4, self.max_hp)
                return {"damage": 0, "message": "granted a wish of healing"}
            elif effect == "power":
                damage = random.randint(self.max_damage, self.max_damage * 2)
                return {"damage": damage, "message": "granted a wish of power"}
            else:  # defense
                self.armor *= 2  # Temporary armor boost
                return {"damage": 0, "message": "granted a wish of protection"}
        return super().roll_damage()

class Manticore(Enemy):
    type = "manticore"
    base_hp = 300
    base_min_damage = 35
    base_max_damage = 50
    base_armor = 15
    crit_chance = 0.18
    crit_damage = 2.1
    drop_chance = 0.75
    regular_drop = {"manticore spike": 3, "lion's mane": 1}
    probability = 0.18
    max_entities = 70
    max_entities_total = 250
    herd_probability = 0.15
    min_level = 55
    max_level = 110
    experience_value = 250
    spike_volley_chance = 0.3
    block_chance = 0.15
    block_reduction = 0.4
    biome = "desert"

    def roll_damage(self):
        if random.random() < self.spike_volley_chance:
            num_spikes = random.randint(3, 6)
            total_damage = sum(random.randint(self.base_min_damage, self.base_max_damage) for _ in range(num_spikes))
            return {"damage": total_damage, "message": f"launched a volley of {num_spikes} spikes"}
        return super().roll_damage()

class Sandworm(Enemy):
    type = "sandworm"
    base_hp = 400
    base_min_damage = 40
    base_max_damage = 60
    base_armor = 20
    crit_chance = 0.1
    crit_damage = 2.5
    drop_chance = 0.9
    regular_drop = {"sandworm segment": 5, "desert spice": 2}
    probability = 0.12
    max_entities = 50
    max_entities_total = 150
    herd_probability = 0
    min_level = 70
    max_level = 150
    experience_value = 350
    burrow_chance = 0.4
    swallow_chance = 0.15
    block_chance = 0.25
    block_reduction = 0.6
    biome = "desert"

    def __init__(self, level: int):
        super().__init__(level)
        self.is_burrowed = False

    def roll_damage(self):
        if self.is_burrowed:
            self.is_burrowed = False
            damage = random.randint(int(self.max_damage * 1.5), int(self.max_damage * 2.5))
            return {"damage": damage, "message": "erupted from the sand with a devastating attack"}
        elif random.random() < self.burrow_chance:
            self.is_burrowed = True
            return {"damage": 0, "message": "burrowed into the sand"}
        elif random.random() < self.swallow_chance:
            damage = self.max_damage * 2
            return {"damage": damage, "message": "attempted to swallow you whole"}
        return super().roll_damage()

    def take_damage(self, damage: int) -> Dict[str, Any]:
        if self.is_burrowed:
            damage = damage // 2  # Half damage while burrowed
        return super().take_damage(damage)

class Scenery:
    probability = 0
    biome = "any"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "biome": self.biome
        }

class Forest(Scenery):
    type = "forest"
    biome = "forest"


    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "chop", "action": "/chop?amount=1"},
            {"name": "chop 10", "action": "/chop?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Pond(Scenery):
    type = "pond"
    biome = "pond"


    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "fish", "action": "/fish"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Cavern(Scenery):
    type = "cavern"
    biome = "cavern"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Graveyard(Scenery):
    type = "graveyard"
    biome = "graveyard"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Desert(Scenery):
    type = "desert"
    biome = "desert"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Mountain(Scenery):
    type = "mountain"
    biome = "mountain"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "mine", "action": "/mine?amount=1"},
            {"name": "mine 10", "action": "/mine?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Rock(Scenery):
    type = "rock"
    biome = "rock"

def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)])

# Automatically collect all entity classes
entity_classes = get_all_subclasses(Enemy) | get_all_subclasses(Scenery)

# Create the entity_types dictionary
entity_types = {}
for cls in entity_classes:
    if hasattr(cls, 'type'):
        entity_types[cls.type] = cls
    else:
        print(f"Warning: {cls.__name__} does not have a 'type' attribute.")

# Optionally, you can print out the collected entity types for verification
print("Collected entity types:")
for entity_type, entity_class in entity_types.items():
    print(f"{entity_type}: {entity_class.__name__}")