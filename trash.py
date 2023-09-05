def trash_item(usersdb, username, item_id):
    player = usersdb[username]

    # Search for the item to trash in the unequipped list
    item_to_trash = None
    for item in player['unequipped']:
        if item['id'] == item_id:
            item_to_trash = item
            break

    # If the item is not found, return a message
    if item_to_trash is None:
        return "Item not found in unequipped inventory."

    # Remove the item from the unequipped list
    player['unequipped'].remove(item_to_trash)

    return f"Trashed item with ID: {item_id}, Type: {item_to_trash['type']}"
