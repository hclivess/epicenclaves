def trash_weapons(usersdb, username):
    player = usersdb[username]
    trashed_count = 0
    weapons_to_trash = [item for item in player['unequipped'] if item.get('role') == 'weapon']
    for item in weapons_to_trash:
        player['unequipped'].remove(item)
        trashed_count += 1
    return f"Trashed {trashed_count} weapons."

def trash_armor(usersdb, username):
    player = usersdb[username]
    trashed_count = 0
    armor_to_trash = [item for item in player['unequipped'] if item.get('role') == 'armor']
    for item in armor_to_trash:
        player['unequipped'].remove(item)
        trashed_count += 1
    return f"Trashed {trashed_count} armor pieces."

def trash_all(usersdb, username):
    player = usersdb[username]
    trashed_count = 0
    items_to_trash = [item for item in player['unequipped'] if item.get('role') != 'tool']
    for item in items_to_trash:
        player['unequipped'].remove(item)
        trashed_count += 1
    return f"Trashed {trashed_count} items (kept tools)."

# The original trash_item function remains unchanged
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