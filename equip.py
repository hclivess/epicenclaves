def unequip_item(username, usersdb, item_id):
    player = usersdb[username]

    # Search for the item to unequip in the equipped list
    item_to_unequip = next((item for item in player['equipped'] if item['id'] == item_id), None)

    # If the item is not found, return a message
    if item_to_unequip is None:
        return "Item not found in equipped inventory."

    # Remove the item from the equipped list and add it to the unequipped list
    player['equipped'].remove(item_to_unequip)
    player['unequipped'].append(item_to_unequip)

    # Get the slot from the item directly
    slot = item_to_unequip.get('slot', 'right_hand')

    # If it's an armor item, update the player's total armor value
    if item_to_unequip.get('role') == 'armor':
        player['armor'] = max(0, player['armor'] - item_to_unequip.get('protection', 0))

    # Replace with an empty slot
    empty_slot = {
        "type": "empty",
        "slot": slot,
        "role": item_to_unequip.get('role', 'weapon'),
        "protection": 0
    }
    player['equipped'].append(empty_slot)

    usersdb[username] = player

    return f"Unequipped item with ID: {item_id}, Type: {item_to_unequip['type']}"

def equip_item(username, usersdb, item_id):
    player = usersdb[username]

    # Search for the item to equip in the unequipped list
    item_to_equip = next((item for item in player['unequipped'] if item['id'] == item_id), None)

    if item_to_equip is None:
        return "Item not found in unequipped inventory."

    # Get the slot from the item directly
    slot = item_to_equip.get('slot', 'right_hand')

    # Find the currently equipped item in this slot
    for i, equipped_item in enumerate(player['equipped']):
        if equipped_item.get('slot') == slot:
            # Always swap out the old item, regardless of type
            if equipped_item.get('type') != 'empty':
                player['unequipped'].append(equipped_item)
                # If it's armor, update the player's armor value
                if equipped_item.get('role') == 'armor':
                    player['armor'] -= equipped_item.get('protection', 0)
            # Equip the new item
            player['equipped'][i] = item_to_equip
            break
    else:
        # If no item was in that slot, simply add the new item
        player['equipped'].append(item_to_equip)

    # Update player's armor if the new item is armor
    if item_to_equip.get('role') == 'armor':
        player['armor'] += item_to_equip.get('protection', 0)

    # Remove the newly equipped item from the unequipped list
    player['unequipped'].remove(item_to_equip)

    usersdb[username] = player

    return f"Equipped item with ID: {item_id}, Type: {item_to_equip['type']}"