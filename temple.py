from backend import update_user_data
from map import occupied_by, owned_by, get_user_data
from spells import spell_types
from typing import Dict, Any, List, Tuple


def check_temple_access(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any]) -> Tuple[bool, str]:
    user_data = get_user_data(user, usersdb)
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    proper_tile = occupied_by(x_pos, y_pos, what="temple", mapdb=mapdb)
    under_control = owned_by(x_pos, y_pos, control=user, mapdb=mapdb)

    if not proper_tile:
        return False, "You cannot access temple functions here. A temple is required."
    elif not under_control:
        return False, "This temple is not under your control."

    return True, ""


def get_temple_info(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any]) -> Tuple[bool, str, List[Any]]:
    access_granted, message = check_temple_access(user, usersdb, mapdb)
    if not access_granted:
        return False, message, []

    available_spells = [spell_class(spell_id=i) for i, spell_class in enumerate(spell_types.values())]
    return True, "Temple access granted", available_spells


def learn_spell(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any], spell_type: str) -> Tuple[bool, str]:
    access_granted, message = check_temple_access(user, usersdb, mapdb)
    if not access_granted:
        return False, message

    user_data = get_user_data(user, usersdb)

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


def update_spell_queue(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any], spell_queue: List[str]) -> Tuple[
    bool, str]:
    access_granted, message = check_temple_access(user, usersdb, mapdb)
    if not access_granted:
        return False, message

    user_data = get_user_data(user, usersdb)
    user_data['spell_queue'] = spell_queue
    update_user_data(user, user_data, usersdb)
    return True, "Spell queue updated successfully"