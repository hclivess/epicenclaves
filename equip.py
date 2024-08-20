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
            if equipped_item['role'] == 'armor' and equipped_item['slot'] == slot:
                # If the slot is not empty, move the current item to unequipped
                if equipped_item['type'] != 'empty':
                    player['unequipped'].append(equipped_item)
                # Replace the item in the equipped list
                player['equipped'][i] = item_to_equip
                player['unequipped'].remove(item_to_equip)
                return f"Equipped {item_to_equip['type']} in {slot} slot."
    else:
        # For non-armor items, use the existing logic
        item_to_unequip = None
        for equipped_item in player['equipped']:
            if equipped_item['role'] == item_to_equip['role']:
                item_to_unequip = equipped_item
                break

        if item_to_unequip is not None:
            player['equipped'].remove(item_to_unequip)
            player['unequipped'].append(item_to_unequip)

        player['equipped'].append(item_to_equip)
        player['unequipped'].remove(item_to_equip)

    return f"Equipped item with ID: {item_id}, Type: {item_to_equip['type']}"