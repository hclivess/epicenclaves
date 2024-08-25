#TODO: THIS IS LEGACY, ACTIONS WILL BE ENCAPSULATED SAME WAY AS FOR TOOLS, WEAPONS, ARMOR
class TileActions:
    def get(self, entry):
        type = list(entry.values())[0].get("type")
        name = list(entry.keys())[0] if type == "player" else None

        actions = []

        # Common actions for all buildings
        building_actions = [
            {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
            {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
            {"name": "upgrade", "action": f"/upgrade"},
            {"name": "conquer", "action": f"/conquer?target={type}"},
        ]

        # Specific actions for different types
        type_actions = {
            "inn": [
                {"name": "sleep 10 hours", "action": "/rest?hours=10"},
                {"name": "sleep 20 hours", "action": "/rest?hours=20"},
            ] + building_actions,
            "forest": [
                {"name": "chop", "action": "/chop?amount=1"},
                {"name": "chop 10", "action": "/chop?amount=10"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ],
            "archery_range": [
                {"name": "train 1 archer", "action": "/train?type=archer&amount=1"},
                {"name": "train 10 archers", "action": "/train?type=archer&amount=10"},
            ] + building_actions,
            "blacksmith": [
                 {"name": "repair all gear", "action": "/repair?type=all"},
             ] + building_actions,
            "mountain": [
                {"name": "mine", "action": "/mine?amount=1"},
                {"name": "mine 10", "action": "/mine?amount=10"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ],
            "farm": building_actions,
            "barracks": building_actions,
            "house": building_actions,
            "sawmill": building_actions,
            "laboratory": building_actions,
            "boar": [{"name": "hunt", "action": f"/fight?target={type}"}],
            "wolf": [{"name": "hunt", "action": f"/fight?target={type}"}],
            "goblin": [{"name": "fight", "action": f"/fight?target={type}"}],
            "specter": [{"name": "fight", "action": f"/fight?target={type}"}],
            "dragon_whelp": [{"name": "slay", "action": f"/fight?target={type}"}],
            "valenthis": [{"name": "slay", "action": f"/fight?target={type}"}],
            "player": [{"name": "challenge", "action": f"/fight?target={type}&name={name}"}],
        }

        # Get actions for the specific type, or an empty list if type is not recognized
        actions = type_actions.get(type, [])

        return actions