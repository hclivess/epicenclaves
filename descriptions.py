from costs import building_costs, upgrade_costs
#TODO: THIS IS LEGACY, DESCRIPTIONS WILL BE ENCAPSULATED SAME WAY AS FOR TOOLS, WEAPONS, ARMOR
class Descriptions:
    def __init__(self):
        self.descriptions_dict = {
            "house": self.format_cost("Increases population limit by 10.", building_costs["house"]),
            "inn": self.format_cost("Allows user to rest and restore health.", building_costs["inn"]),
            "farm": self.format_cost("Generates food and peasants if housing is available.", building_costs["farm"]),
            "barracks": self.format_cost("Turns peasants into army for 2 food per turn and additional housing. Army is the only deployable unit.", building_costs["barracks"]),
            "sawmill": self.format_cost("Passively produces 🪵1 per turn per every sawmill level and forest.", building_costs["sawmill"]),
            "mine": self.format_cost("Passively produces 🪨1 per turn per every mine level and forest.", building_costs["mine"]),
            "archery_range": self.format_cost("Allows you to train army into archers.", building_costs["archery_range"]),
            "laboratory": self.format_cost("Turns peasants into researchers to generate research points.", building_costs["laboratory"]),
            "blacksmith": self.format_cost("Allows you to restore durability of your items.", building_costs["blacksmith"]),
        }

    def format_cost(self, description, cost_dict):
        cost_string = " Cost: " + ", ".join(f"{emoji}{amount}" for resource, amount in cost_dict.items() for emoji in self.get_emoji(resource))
        return description + cost_string

    def get_emoji(self, resource):
        emoji_dict = {
            "wood": "🪵",
            "bismuth": "🪨",
            "gold": "💰",
            # Add more resource emojis as needed
        }
        return emoji_dict.get(resource, "")

    def get(self, type):
        return self.descriptions_dict.get(type, "Description missing.")