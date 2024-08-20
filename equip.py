def equip_item(usersdb, username, item_id):
    player = usersdb[username]

    # Search for the item to equip in the unequipped list
    item_to_equip = None
    for item in player['unequipped']:
        if item['id'] == item_id:
            item_to_equip = item
            break

    # If the item is not found, return a message
    if item_to_equip is None:
        return "Item not found in unequipped inventory."

    # Check if the item is armor
    if item_to_equip.get('role') == 'armor':
        slot = item_to_equip['slot']
        # Find the currently equipped item in this slot
        for i, equipped_item in enumerate(player['equipped']):
            if equipped_item.get('role') == 'armor' and equipped_item.get('slot') == slot:
                if equipped_item.get('type') != 'empty':
                    player['unequipped'].append(equipped_item)
                player['armor'] -= equipped_item.get('protection', 0)
                player['equipped'][i] = item_to_equip
                break
        else:
            player['equipped'].append(item_to_equip)

        player['armor'] += item_to_equip.get('protection', 0)
    else:
        # For weapons, find the currently equipped weapon
        currently_equipped_weapon = None
        for i, equipped_item in enumerate(player['equipped']):
            if equipped_item.get('role') == 'right_hand':
                currently_equipped_weapon = equipped_item
                player['equipped'][i] = item_to_equip
                break

        # If there was a weapon equipped, move it to unequipped
        if currently_equipped_weapon:
            player['unequipped'].append(currently_equipped_weapon)
        else:
            # If no weapon was equipped, just add the new weapon to equipped
            player['equipped'].append(item_to_equip)

    # Remove the newly equipped item from the unequipped list
    player['unequipped'].remove(item_to_equip)

    return f"Equipped item with ID: {item_id}, Type: {item_to_equip['type']}"


def unequip_item(usersdb, username, item_id):
    player = usersdb[username]

    # Search for the item to unequip in the equipped list
    item_to_unequip = None
    for item in player['equipped']:
        if item['id'] == item_id:
            item_to_unequip = item
            break

    # If the item is not found, return a message
    if item_to_unequip is None:
        return "Item not found in equipped inventory."

    # Remove the item from the equipped list and add it to the unequipped list
    player['equipped'].remove(item_to_unequip)
    player['unequipped'].append(item_to_unequip)

    # If it's an armor item, update the player's total armor value
    if item_to_unequip.get('role') == 'armor':
        player['armor'] = max(0, player['armor'] - item_to_unequip.get('protection', 0))

        # Replace with an empty slot
        empty_slot = {
            "type": "empty",
            "slot": item_to_unequip['slot'],
            "role": "armor",
            "protection": 0
        }
        player['equipped'].append(empty_slot)
    elif item_to_unequip.get('role') == 'right_hand':
        # If it's a weapon, we don't need to replace it with an empty slot
        pass

    return f"Unequipped item with ID: {item_id}, Type: {item_to_unequip['type']}"