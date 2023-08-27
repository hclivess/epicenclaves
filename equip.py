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

    # Check if an item with the same class is currently equipped
    item_to_unequip = None
    for equipped_item in player['equipped']:
        if equipped_item['role'] == item_to_equip['role']:
            item_to_unequip = equipped_item
            break

    # If an item with the same class is equipped, move it to the unequipped list
    if item_to_unequip is not None:
        player['equipped'].remove(item_to_unequip)
        player['unequipped'].append(item_to_unequip)

    # Equip the new item and remove it from the unequipped list
    player['equipped'].append(item_to_equip)
    player['unequipped'].remove(item_to_equip)

    return f"Equipped item with ID: {item_id}, Type: {item_to_equip['type']}"
