from backend import get_coords, death_roll, update_user_data, Boar, remove_from_map, get_values

def fight_player(entry, target_name, user_data, user, usersdb):
    messages = []
    entry_name = get_coords(entry)

    # Make the entry's data more easily accessible
    target_data = entry[entry_name]

    if target_name == entry_name:
        messages.append(f"You challenged {entry_name}")

        while target_data["alive"] and user_data["alive"]:
            # Only allow the target to attack if they have more than 0 hp
            if target_data["hp"] > 0:
                user_data["hp"] -= 1
                messages.append(
                    f"{entry_name} hits you for 1 damage, you have {user_data['hp']} left"
                )

            # Only allow the user to attack if they have more than 0 hp
            if user_data["hp"] > 0:
                target_data["hp"] -= 1
                messages.append(
                    f"You hit {entry_name} for 1 damage, they have {target_data['hp']} left"
                )

            # Check if target should roll
            if target_data["hp"] < 1:
                messages.append(f"{entry_name} rolls the dice of fate")
                if death_roll(0.5):
                    messages.append("Enemy killed")
                    update_user_data(
                        user=target_name,
                        updated_values={"alive": False, "hp": 0, "action_points": 0},
                        user_data_dict=usersdb,
                    )
                else:
                    messages.append("The enemy barely managed to escape")
                    update_user_data(
                        user=target_name,
                        updated_values={
                            "action_points": target_data["action_points"] - 1,
                            "hp": 1,
                        },
                        user_data_dict=usersdb,
                    )
                update_user_data(
                    user=user,
                    updated_values={"exp": user_data["exp"] + target_data["exp"] / 10},
                    user_data_dict=usersdb,
                )
                break

            # Check if user should roll
            if user_data["hp"] < 1:
                messages.append("You roll the dice of fate")
                if death_roll(0.5):
                    messages.append("You died")
                    update_user_data(
                        user=user,
                        updated_values={"alive": False,
                                        "hp": 0,
                                        "action_points": 0},
                        user_data_dict=usersdb,
                    )
                else:
                    messages.append("You barely managed to escape")
                    update_user_data(
                        user=user,
                        updated_values={
                            "action_points": user_data["action_points"] - 1,
                            "hp": 1,
                        },
                        user_data_dict=usersdb,
                    )
                update_user_data(
                    user=target_name,
                    updated_values={"exp": target_data["exp"] + 10,
                                    "hp": target_data["hp"]},
                    user_data_dict=usersdb,
                )
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
