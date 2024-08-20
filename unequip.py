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
        player['armor'] -= item_to_unequip.get('protection', 0)

    return f"Unequipped item with ID: {item_id}, Type: {item_to_unequip['type']}"