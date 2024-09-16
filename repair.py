from backend import update_user_data
from map import occupied_by, owned_by
from typing import List, Dict


def repair_all_items(user, usersdb, mapdb, wood_cost=10, bismuth_cost=5):
    user_data = usersdb[user]
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    # Check if the user is on a blacksmith tile and controls it
    proper_tile = occupied_by(x_pos, y_pos, what="blacksmith", mapdb=mapdb)
    under_control = owned_by(x_pos, y_pos, control=user, mapdb=mapdb)

    if not proper_tile:
        return "You cannot repair items here, a blacksmith is required"
    elif not under_control:
        return "This blacksmith is not under your control"

    items_to_repair = []
    total_missing_durability = 0

    # Count items that need repair and calculate total missing durability
    for item in user_data['equipped'] + user_data['unequipped']:
        if 'durability' in item and 'max_durability' in item:
            missing_durability = item['max_durability'] - item['durability']
            if missing_durability > 0:
                items_to_repair.append(item)
                total_missing_durability += missing_durability

    # Calculate costs based on missing durability
    total_wood_cost = total_missing_durability * wood_cost
    total_bismuth_cost = total_missing_durability * bismuth_cost

    if user_data['ingredients'].get('wood', 0) < total_wood_cost:
        return f"Not enough wood. You need {total_wood_cost} wood to repair all items."

    if user_data['ingredients'].get('bismuth', 0) < total_bismuth_cost:
        return f"Not enough bismuth. You need {total_bismuth_cost} bismuth to repair all items."

    # Repair items
    for item in items_to_repair:
        item['durability'] = item['max_durability']

    # Deduct costs
    user_data['ingredients']['wood'] -= total_wood_cost
    user_data['ingredients']['bismuth'] -= total_bismuth_cost

    # Update user data
    update_user_data(user=user, updated_values={
        'ingredients': user_data['ingredients'],
        'equipped': user_data['equipped'],
        'unequipped': user_data['unequipped']
    }, user_data_dict=usersdb)

    if items_to_repair:
        return f"Successfully repaired {len(items_to_repair)} items. {total_wood_cost} wood and {total_bismuth_cost} bismuth have been deducted."
    else:
        return "No items needed repair. No resources were deducted."


def repair_item(user, usersdb, mapdb, item_id, wood_cost=2, bismuth_cost=2):
    user_data = usersdb[user]
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    # Check if the user is on a blacksmith tile and controls it
    proper_tile = occupied_by(x_pos, y_pos, what="blacksmith", mapdb=mapdb)
    under_control = owned_by(x_pos, y_pos, control=user, mapdb=mapdb)

    if not proper_tile:
        return "You cannot repair items here, a blacksmith is required"
    elif not under_control:
        return "This blacksmith is not under your control"

    # Find the item in equipped or unequipped items
    item_to_repair = None
    for item in user_data['equipped'] + user_data['unequipped']:
        if str(item.get('id')) == str(item_id):
            item_to_repair = item
            break

    if not item_to_repair:
        return f"Item with ID {item_id} not found."

    if 'durability' not in item_to_repair or 'max_durability' not in item_to_repair:
        return f"The item {item_to_repair['type']} cannot be repaired."

    missing_durability = item_to_repair['max_durability'] - item_to_repair['durability']
    if missing_durability <= 0:
        return f"The item {item_to_repair['type']} is already at full durability."

    wood_cost = missing_durability * wood_cost
    bismuth_cost = missing_durability * bismuth_cost

    if user_data['ingredients'].get('wood', 0) < wood_cost:
        return f"Not enough wood. You need {wood_cost} wood to repair this item."

    if user_data['ingredients'].get('bismuth', 0) < bismuth_cost:
        return f"Not enough bismuth. You need {bismuth_cost} bismuth to repair this item."

    # Repair the item
    item_to_repair['durability'] = item_to_repair['max_durability']

    # Deduct costs
    user_data['ingredients']['wood'] -= wood_cost
    user_data['ingredients']['bismuth'] -= bismuth_cost

    # Update user data
    update_user_data(user=user, updated_values={
        'ingredients': user_data['ingredients'],
        'equipped': user_data['equipped'],
        'unequipped': user_data['unequipped']
    }, user_data_dict=usersdb)

    return f"Successfully repaired {item_to_repair['type']}. {wood_cost} wood and {bismuth_cost} bismuth have been deducted."