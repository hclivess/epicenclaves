from weapon_generator import id_generator


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
        item_to_unequip = None
        for i, equipped_item in enumerate(player['equipped']):
            if equipped_item.get('role') == 'armor' and equipped_item.get('slot') == slot:
                item_to_unequip = equipped_item
                player['equipped'][i] = item_to_equip
                break

        if item_to_unequip:
            if item_to_unequip.get('type') != 'empty':
                player['unequipped'].append(item_to_unequip)
            player['armor'] -= item_to_unequip.get('protection', 0)

        player['unequipped'].remove(item_to_equip)
        player['armor'] += item_to_equip.get('protection', 0)
    else:
        # For non-armor items (weapons), use the existing logic
        item_to_unequip = None
        for i, equipped_item in enumerate(player['equipped']):
            if equipped_item.get('role') == item_to_equip.get('role'):
                item_to_unequip = equipped_item
                player['equipped'][i] = item_to_equip
                break

        if item_to_unequip:
            player['unequipped'].append(item_to_unequip)

        player['unequipped'].remove(item_to_equip)

    return f"Equipped item with ID: {item_id}, Type: {item_to_equip['type']}"


def create_empty_slot(slot):
    return {
        "id": id_generator(),
        "type": "empty",
        "slot": slot,
        "role": "armor",
        "protection": 0
    }


# Initialize empty slots for a new user
def initialize_empty_slots():
    return [create_empty_slot(slot) for slot in ["head", "body", "arms", "legs", "feet"]]