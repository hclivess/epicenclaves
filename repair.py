from backend import update_user_data


def repair_all_items(user, usersdb):
    user_data = usersdb[user]

    items_to_repair = []

    # Count items that need repair
    for item in user_data['equipped'] + user_data['unequipped']:
        if 'durability' in item and 'max_durability' in item:
            if item['durability'] < item['max_durability']:
                items_to_repair.append(item)

    total_wood_cost = len(items_to_repair) * 100
    total_bismuth_cost = len(items_to_repair) * 50

    if user_data['wood'] < total_wood_cost:
        return f"Not enough wood. You need {total_wood_cost} wood to repair all items."

    if user_data['bismuth'] < total_bismuth_cost:
        return f"Not enough bismuth. You need {total_bismuth_cost} bismuth to repair all items."

    # Repair items
    for item in items_to_repair:
        item['durability'] = item['max_durability']

    # Deduct costs
    user_data['wood'] -= total_wood_cost
    user_data['bismuth'] -= total_bismuth_cost

    # Update user data
    update_user_data(user=user, updated_values={
        'wood': user_data['wood'],
        'bismuth': user_data['bismuth'],
        'equipped': user_data['equipped'],
        'unequipped': user_data['unequipped']
    }, user_data_dict=usersdb)

    if items_to_repair:
        return f"Successfully repaired {len(items_to_repair)} items. {total_wood_cost} wood and {total_bismuth_cost} bismuth have been deducted."
    else:
        return "No items needed repair. No resources were deducted."