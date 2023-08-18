from backend import get_coords, death_roll, update_user_data, Boar, remove_from_map, get_values


def player_attack(attacker, defender, attacker_name, messages):
    if attacker["hp"] > 0:
        defender["hp"] -= 1
        if attacker_name == "You":
            messages.append(f"You hit for 1 damage, they have {defender['hp']} left")
        else:
            messages.append(f"{attacker_name} hits you for 1 damage, you have {defender['hp']} left")


def defeat_outcome(entity, entity_name, chance, usersdb):
    """Handles the outcome when an entity's HP drops to 0 or below."""
    messages = []
    if death_roll(chance):
        messages.append(f"{entity_name} is defeated.")
        new_data = {
            "alive": False,
            "hp": 0,
            "action_points": 0
        }
    else:
        messages.append(f"{entity_name} barely managed to escape.")
        new_data = {
            "action_points": entity["action_points"] - 1,
            "hp": 1
        }

    update_user_data(user=entity_name, updated_values=new_data, user_data_dict=usersdb)
    return messages


def fight_player(entry, target_name, user_data, user, usersdb):
    messages = []
    entry_name = get_coords(entry)
    target_data = entry[entry_name]

    if target_name == entry_name:
        if target_data["hp"] == 0:
            messages.append(f"{entry_name} is already dead!")
            return messages

        if target_data["exp"] < 50:
            messages.append(f"{entry_name} is too inexperienced to challenge!")
            return messages

        messages.append(f"You challenged {entry_name}")

        while target_data["alive"] and user_data["alive"]:

            player_attack(target_data, user_data, entry_name, messages)
            player_attack(user_data, target_data, "You", messages)

            if 10 > target_data["hp"] > 0:
                messages.append(f"{entry_name} has run seeing they stand no chance against you!")
                break

            defeated_entity = None
            defeated_name = None

            if target_data["hp"] <= 0:
                defeated_entity = target_data
                defeated_name = entry_name
                exp_gain = user_data["exp"] + target_data["exp"] / 10
                update_user_data(user=user, updated_values={"exp": exp_gain}, user_data_dict=usersdb)

            elif user_data["hp"] <= 0:
                defeated_entity = user_data
                defeated_name = user
                update_user_data(user=target_name, updated_values={"exp": target_data["exp"] + 10},
                                 user_data_dict=usersdb)

            if defeated_entity:
                messages.extend(defeat_outcome(defeated_entity, defeated_name, 0.5, usersdb))
                break

    return messages


def fight_boar(entry, user_data, user, usersdb, mapdb):
    messages = []
    boar = Boar()
    escaped = False

    while boar.alive and user_data["alive"] and not escaped:
        # Check if the boar should be dead
        if boar.hp < 1:
            messages.append("The boar is dead")
            boar.alive = False
            remove_from_map(
                entity_type="boar", coords=get_coords(entry), map_data_dict=mapdb
            )
            update_user_data(
                user=user,
                updated_values={
                    "action_points": user_data["action_points"] - 1,
                    "exp": user_data["exp"] + 1,
                    "food": user_data["food"] + 1,
                    "hp": user_data["hp"],
                },
                user_data_dict=usersdb,
            )

        # Check if the user should be dead or escape
        elif user_data["hp"] < 1:
            if death_roll(boar.kill_chance):
                messages.append("You died")
                user_data["alive"] = False
                update_user_data(
                    user=user,
                    updated_values={"alive": user_data["alive"], "hp": 0},
                    user_data_dict=usersdb,
                )
            else:
                messages.append("You are almost dead but managed to escape")
                update_user_data(
                    user=user,
                    updated_values={
                        "action_points": user_data["action_points"] - 1,
                        "hp": 1,
                    },
                    user_data_dict=usersdb,
                )
                escaped = True

        # Attack logic, ensuring entities with 0 hp don't attack
        else:
            # User attacks the boar if they have more than 0 hp
            if user_data["hp"] > 0:
                boar.hp -= 1
                messages.append(
                    f"The boar takes 1 damage and is left with {boar.hp} hp"
                )

            # Boar attacks the user if it has more than 0 hp
            if boar.hp > 0:
                boar_dmg_roll = boar.roll_damage()
                user_data["hp"] -= boar_dmg_roll
                messages.append(
                    f"You take {boar_dmg_roll} damage and are left with {user_data['hp']} hp"
                )

    return messages


def fight(target, target_name, on_tile_map, on_tile_users, user_data, user, usersdb, mapdb):
    messages = []

    for entry in on_tile_map:
        entry_type = get_values(entry).get("type")

        if target == "boar" and entry_type == "boar":
            messages.extend(fight_boar(entry, user_data, user, usersdb, mapdb))
        elif target == "player" and entry_type == "player":
            messages.extend(fight_player(entry, target_name, user_data, user, usersdb))

    for entry in on_tile_users:
        entry_type = get_values(entry).get("type")
        entry_name = get_coords(entry)

        if target == "player" and entry_type == "player" and target_name == entry_name:
            messages.extend(fight_player(entry, target_name, user_data, user, usersdb))

    return messages


def get_fight_preconditions(user_data):
    if user_data["action_points"] < 1:
        return "Not enough action points to slay"
    if not user_data["alive"]:
        return "You are dead"
    return None
