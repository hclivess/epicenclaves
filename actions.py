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
                {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
                {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
                {"name": "upgrade", "action": f"/upgrade"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "forest":
            actions = [
                {"name": "chop", "action": "/chop?amount=1"},
                {"name": "chop 10", "action": "/chop?amount=10"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "archery_range":
            actions = [
                {"name": "train 1 archer", "action": "/train?type=archer&amount=1"},
                {"name": "train 10 archers", "action": "/train?type=archer&amount=10"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "mountain":
            actions = [
                {"name": "mine", "action": "/mine?amount=1"},
                {"name": "mine 10", "action": "/mine?amount=10"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "farm":
            actions = [
                {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
                {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
                {"name": "upgrade", "action": f"/upgrade"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "barracks":
            actions = [
                {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
                {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
                {"name": "upgrade", "action": f"/upgrade"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]
        elif type == "house":
            actions = [
                {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
                {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
                {"name": "upgrade", "action": f"/upgrade"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]

        elif type == "sawmill":
            actions = [
                {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
                {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
                {"name": "upgrade", "action": f"/upgrade"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]

        elif type == "laboratory":
            actions = [
                {"name": "deploy army", "action": f"/deploy?type=army&action=add"},
                {"name": "remove army", "action": f"/deploy?type=army&action=remove"},
                {"name": "upgrade", "action": f"/upgrade"},
                {"name": "conquer", "action": f"/conquer?target={type}"},
            ]

        elif type == "boar":
            actions = [{"name": "fight", "action": f"/fight?target={type}"}]
        elif type == "wolf":
            actions = [{"name": "fight", "action": f"/fight?target={type}"}]
        elif type == "player":
            actions = [
                {"name": "challenge", "action": f"/fight?target={type}&name={name}"}
            ]
        else:
            actions = []

        return actions
