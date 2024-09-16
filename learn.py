from backend import update_user_data
from map import occupied_by

def learn_spell(user, usersdb, mapdb, spell_type, spell_types):
    user_data = usersdb[user]
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    # Check if the user is on a temple tile
    proper_tile = occupied_by(x_pos, y_pos, what="temple", mapdb=mapdb)

    if not proper_tile:
        return False, "You cannot learn spells here, a temple is required"

    if spell_type in user_data.get('spells', []):
        return False, "You have already learned this spell"

    spell_class = spell_types.get(spell_type.lower())
    if spell_class is None:
        return False, "Spell not found"

    spell = spell_class(spell_id=len(user_data['spells']))
    cost = spell.COST.get('research', 0)

    if user_data['research'] >= cost:
        user_data['research'] -= cost
        user_data['spells'].append(spell_type)  # Only store the spell type
        update_user_data(user, user_data, usersdb)
        return True, f"Learned {spell.DISPLAY_NAME}"
    else:
        return False, "Not enough research points"