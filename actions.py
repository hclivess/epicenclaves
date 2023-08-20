class TileActions:
    def get(self, entry):
        type = list(entry.values())[0].get("type")
        if type == "player":
            name = list(entry.keys())[0]
            print("name", name)
        else:
            name = None

        if type == "inn":
            actions = [
                {"name": "sleep 10 hours", "action": "/rest?hours=10"},
                {"name": "sleep 20 hours", "action": "/rest?hours=20"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
                {"name": "deploy soldiers", "action": f"/deploy?type=soldiers"},
            ]
        elif type == "forest":
            actions = [
                {"name": "chop", "action": "/chop"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "farm":
            actions = [
                {"name": "conquer", "action": f"/conquer?target={type}"},
                {"name": "deploy soldiers", "action": f"/deploy?type=soldiers"},
            ]
        elif type == "barracks":
            actions = [
                {"name": "conquer", "action": f"/conquer?target={type}"},
                {"name": "deploy soldiers", "action": f"/deploy?type=soldiers"},
            ]
        elif type == "house":
            actions = [
                {"name": "conquer", "action": f"/conquer?target={type}"},
                {"name": "deploy soldiers", "action": f"/deploy?type=soldiers"},
            ]

        elif type == "boar":
            actions = [{"name": "fight", "action": f"/fight?target={type}"}]
        elif type == "player":
            actions = [
                {"name": "challenge", "action": f"/fight?target={type}&name={name}"}
            ]
        else:
            actions = []

        return actions
