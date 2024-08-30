import asyncio
import json
import os.path
import signal
import sys
import webbrowser
import os
import re
import inspect
import tornado.ioloop
import tornado.web
import tornado.escape

from buildings import Building
import buildings
from user import User

import entities
from weapons import Weapon
from armor import Armor
from tools import Tool
from chop import chop_forest
from mine import mine_mountain
from conquer import attempt_conquer
from deploy_army import deploy_army, remove_army
from equip import equip_item, unequip_item
from fight import fight, get_fight_preconditions
from login import login, get_leagues
from typing import List, Dict, Any
from turn_engine import TurnEngine
from backend import get_user, update_user_data
from map import (get_tile_map, get_tile_users, get_user_data, strip_usersdb,
                 get_map_data_limit, get_users_data_limit)
from rest import attempt_rest
from move import move, move_to
from build import build
from entity_generator import spawn
from auth import (auth_cookie_get, auth_login_validate, auth_add_user, auth_exists_user, auth_check_users_db)
from sqlite import init_databases, load_users_to_memory, save_users_from_memory, save_map_from_memory, \
    load_map_to_memory
from user import create_user
from wall_generator import generate_multiple_mazes
from upgrade import upgrade
from trash import trash_item, trash_armor, trash_all, trash_weapons
from repair import repair_all_items

max_size = 1000000

# Get all weapon classes dynamically
weapon_classes = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Weapon), inspect.isclass)
                  if issubclass(cls, Weapon) and cls != Weapon}

armor_classes = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Armor), inspect.isclass)
                 if issubclass(cls, Armor) and cls != Armor}

tool_classes = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Tool), inspect.isclass)
                if issubclass(cls, Tool) and cls != Tool}

building_types = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Building), inspect.isclass)
                  if issubclass(cls, Building) and cls != Building}

building_descriptions = {building_type: cls(1).to_dict() for building_type, cls in building_types.items()}


def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)])


# Dynamically gather all entity and building types
entity_types = {cls.__name__.lower(): cls for cls in
                get_all_subclasses(entities.Enemy) | get_all_subclasses(entities.Scenery)}
building_types = {cls.__name__.lower(): cls for cls in get_all_subclasses(buildings.Building)}


def generate_inventory_descriptions(user_data):
    inventory_descriptions = {}
    for item in user_data.get('equipped', []) + user_data.get('unequipped', []):
        item_type = item['type'].lower()
        if item_type in weapon_classes:
            inventory_descriptions[item['id']] = weapon_classes[item_type].DESCRIPTION
        elif item_type in armor_classes:
            inventory_descriptions[item['id']] = armor_classes[item_type].DESCRIPTION
        elif item_type in tool_classes:
            inventory_descriptions[item['id']] = tool_classes[item_type].DESCRIPTION
        else:
            item_id = item.get('id')
            if item_id:
                inventory_descriptions[item_id] = f"A {item['type']} item."
            else:
                inventory_descriptions['unknown_item'] = f"An unknown item."
    return inventory_descriptions


def get_constructor_params(cls):
    return set(inspect.signature(cls.__init__).parameters.keys()) - {'self'}


def get_tile_actions(tile: Any, user: str) -> List[Dict[str, str]]:
    if isinstance(tile, dict):
        tile_type = tile.get('type', '').lower()
        if tile_type in entity_types:
            cls = entity_types[tile_type]
            valid_params = get_constructor_params(cls)
            filtered_tile = {k: v for k, v in tile.items() if k in valid_params}
            tile = cls(**filtered_tile)
        elif tile_type in building_types:
            cls = building_types[tile_type]
            valid_params = get_constructor_params(cls)
            filtered_tile = {k: v for k, v in tile.items() if k in valid_params}
            # Provide a default building_id if it's not present
            if 'building_id' not in filtered_tile:
                filtered_tile['building_id'] = tile.get('id', 1)  # Use 'id' if present, else default to 1
            tile = cls(**filtered_tile)
        elif tile_type == 'player':
            tile = User(**tile)

    if hasattr(tile, 'get_actions'):
        return tile.get_actions(user)
    return []


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_current_league(self):
        return self.get_secure_cookie("league").decode()

    def return_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))

    def write_error(self, status_code, **kwargs):
        self.render("templates/error.html")

    def render_user_panel(self, user, user_data, message="", on_tile_map=None, on_tile_users=None,
                          league=None):
        if on_tile_map is None:
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        if on_tile_users is None:
            on_tile_users = get_tile_users(user_data["x_pos"], user_data["y_pos"], user, usersdb[league])

        # Generate actions for each tile
        tile_actions = {}
        for entry in on_tile_map + on_tile_users:
            coord = list(entry.keys())[0]
            tile = list(entry.values())[0]
            tile_actions[coord] = get_tile_actions(tile, user)

        inventory_descriptions = generate_inventory_descriptions(user_data)

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=tile_actions,
            building_descriptions=building_descriptions,
            inventory_descriptions=inventory_descriptions,
            league=league
        )


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            leagues = get_leagues()  # Get the leagues data
            self.render("templates/login.html", leagues=leagues)  # Pass leagues to the template
        else:
            user = tornado.escape.xhtml_escape(self.current_user)
            league = self.get_current_league()
            data = get_user(user, usersdb[league])
            user_data = data[list(data.keys())[0]]
            self.render_user_panel(user, user_data, message=f"Welcome back, {user}", league=league)


class LogoutHandler(BaseHandler):
    def get(self, data):
        self.clear_all_cookies()
        self.redirect("/")


class MapHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        if not user:
            self.redirect("/")
            return

        visible_distance = 10
        user_data = get_user_data(user, usersdb[league])
        x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
        visible_map_data = get_map_data_limit(x_pos, y_pos, mapdb[league], visible_distance)
        visible_users_data = get_users_data_limit(x_pos, y_pos, strip_usersdb(usersdb[league]), visible_distance)

        # Filter the data to include only essential information
        for username, user_info in visible_users_data.items():
            essential_keys = ["x_pos", "y_pos", "type", "img", "exp", "hp", "armor"]
            visible_users_data[username] = {key: user_info[key] for key in essential_keys if key in user_info}

        for coord, entity in visible_map_data.items():
            filtered_entity = {"type": entity["type"]}
            if "level" in entity:
                filtered_entity["level"] = entity["level"]
            if "control" in entity:
                filtered_entity["control"] = entity["control"]
            if "army" in entity:
                filtered_entity["army"] = entity["army"]
            visible_map_data[coord] = filtered_entity

        # Generate actions for each tile
        tile_actions = {}
        for coord, entity in visible_map_data.items():
            tile_actions[coord] = get_tile_actions(entity, user)
        for coord, user_info in visible_users_data.items():
            user_obj = User(coord, **user_info)
            tile_actions[coord] = user_obj.get_actions(user)

        map_data = {
            "users": visible_users_data,
            "construction": visible_map_data,
            "actions": tile_actions,
            "x_pos": x_pos,
            "y_pos": y_pos
        }
        self.render("templates/map.html", user=user, data=json.dumps(map_data))


class ScoreboardHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.render("templates/scoreboard.html", mapdb=mapdb[league], usersdb=usersdb[league], ensure_ascii=False,
                    user=user)


class UserActionHandler(BaseHandler):
    def perform_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            self.render_user_panel(user, {}, message=f"User {user} not found.", league=league)
            return
        message = action_func(user, user_data, *args, **kwargs)
        user_data = get_user_data(user, usersdb[league])  # Refresh user data
        self.render_user_panel(user, user_data, message=message, league=league)


class EquipHandler(UserActionHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._equip_item, league, id)

    def _equip_item(self, user, user_data, item_id):
        league = self.get_current_league()
        return equip_item(user, usersdb[league], item_id)


class UnequipHandler(UserActionHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._unequip_item, league, id)

    def _unequip_item(self, user, user_data, item_id):
        league = self.get_current_league()
        return unequip_item(user, usersdb[league], item_id)


class RepairHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._repair_items, league)

    def _repair_items(self, user, user_data):
        league = self.get_current_league()
        return repair_all_items(user, usersdb[league])


class TrashHandler(UserActionHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._trash_item, league, id)

    def _trash_item(self, user, user_data, item_id):
        league = self.get_current_league()
        return trash_item(usersdb[league], user, item_id)


class TrashWeaponsHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._trash_weapons, league)

    def _trash_weapons(self, user, user_data):
        league = self.get_current_league()
        return trash_weapons(usersdb[league], user)


class TrashArmorHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._trash_armor, league)

    def _trash_armor(self, user, user_data):
        league = self.get_current_league()
        return trash_armor(usersdb[league], user)


class TrashAllHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._trash_all, league)

    def _trash_all(self, user, user_data):
        league = self.get_current_league()
        return trash_all(usersdb[league], user)

class MoveToHandler(BaseHandler):
    def get(self):
        x = int(self.get_argument("x"))
        y = int(self.get_argument("y"))
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        user_data = get_user_data(user, usersdb=usersdb[league])
        moved = move_to(user, x, y, max_size, user_data, users_dict=usersdb[league], map_dict=mapdb[league])
        user_data = get_user_data(user, usersdb=usersdb[league])  # Refresh user data

        visible_distance = 10
        x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
        visible_map_data = get_map_data_limit(x_pos, y_pos, mapdb[league], visible_distance)
        visible_users_data = get_users_data_limit(x_pos, y_pos, strip_usersdb(usersdb[league]), visible_distance)

        # Filter the data to include only essential information
        filtered_users_data = {}
        for username, user_info in visible_users_data.items():
            essential_keys = ["x_pos", "y_pos", "type", "img", "exp", "hp", "armor"]
            filtered_users_data[username] = {key: user_info[key] for key in essential_keys if key in user_info}

        filtered_map_data = {}
        for coord, entity in visible_map_data.items():
            filtered_entity = {"type": entity["type"]}
            if "level" in entity:
                filtered_entity["level"] = entity["level"]
            if "control" in entity:
                filtered_entity["control"] = entity["control"]
            if "army" in entity:
                filtered_entity["army"] = entity["army"]
            filtered_map_data[coord] = filtered_entity

        tile_actions = {}
        for coord, entity in visible_map_data.items():
            tile_actions[coord] = get_tile_actions(entity, user)
        for coord, user_info in visible_users_data.items():
            user_obj = User(coord, **user_info)
            tile_actions[coord] = user_obj.get_actions(user)

        map_data = {
            "users": filtered_users_data,
            "construction": filtered_map_data,
            "actions": tile_actions,
            "x_pos": x_pos,
            "y_pos": y_pos,
            "message": moved.get("message", "")  # Include the message from the move_to function
        }

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(map_data))


class MoveHandler(UserActionHandler):
    def get(self, data):
        target = self.get_argument("target", default="home")
        entry = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        user_data = get_user_data(user, usersdb=usersdb[league])
        moved = move(user, entry, max_size, user_data, users_dict=usersdb[league], map_dict=mapdb[league])
        user_data = get_user_data(user, usersdb=usersdb[league])  # Refresh user data

        if target == "map":
            visible_distance = 10
            x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
            visible_map_data = get_map_data_limit(x_pos, y_pos, mapdb[league], visible_distance)
            visible_users_data = get_users_data_limit(x_pos, y_pos, strip_usersdb(usersdb[league]), visible_distance)

            # Filter the data to include only essential information
            filtered_users_data = {}
            for username, user_info in visible_users_data.items():
                essential_keys = ["x_pos", "y_pos", "type", "img", "exp", "hp", "armor"]
                filtered_users_data[username] = {key: user_info[key] for key in essential_keys if key in user_info}

            filtered_map_data = {}
            for coord, entity in visible_map_data.items():
                filtered_entity = {"type": entity["type"]}
                if "level" in entity:
                    filtered_entity["level"] = entity["level"]
                if "control" in entity:
                    filtered_entity["control"] = entity["control"]
                if "army" in entity:
                    filtered_entity["army"] = entity["army"]
                filtered_map_data[coord] = filtered_entity

            # Generate actions for each tile
            tile_actions = {}
            for coord, entity in visible_map_data.items():
                tile_actions[coord] = get_tile_actions(entity, user)
            for coord, user_info in visible_users_data.items():
                user_obj = User(coord, **user_info)
                tile_actions[coord] = user_obj.get_actions(user)

            map_data = {
                "users": filtered_users_data,
                "construction": filtered_map_data,
                "actions": tile_actions,
                "x_pos": x_pos,
                "y_pos": y_pos,
                "message": moved["message"]
            }

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(map_data))
        else:
            self.render_user_panel(user, user_data, message=moved["message"], league=self.get_current_league())


class ReviveHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.perform_action(user, self._revive, league)

    def _revive(self, user, user_data):
        league = self.get_current_league()
        if user_data.get("action_points") > 250:
            new_ap = user_data["action_points"] - 250
            update_user_data(user=user, updated_values={"alive": True, "hp": 100, "action_points": new_ap},
                             user_data_dict=usersdb[league])
            message = "You awaken from the dead"
        else:
            message = "You do not have enough action points to revive"
        return message

class RestHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        hours = int(self.get_argument("hours", default="1"))
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_action(user, self._rest, league, hours)
        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _rest(self, user, user_data, hours):
        league = self.get_current_league()
        return attempt_rest(user, user_data, hours, usersdb[league], mapdb[league])

    def return_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
        self.finish()


class FightHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        user_data = get_user_data(user, usersdb[league])
        target = self.get_argument("target")
        target_name = self.get_argument("name", default=None)
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = get_fight_preconditions(user_data)
        if message:
            if return_to_map:
                self.return_json({"message": message})
            else:
                self.render_user_panel(user, user_data, message=message, league=self.get_current_league())
        else:
            fight_result = self._perform_fight(user, user_data, target, target_name, league)
            if return_to_map:
                self.return_json({"message": fight_result.get("message", "Fight completed"),
                                  "battle_data": fight_result["battle_data"]})
            else:
                self.render("templates/fight.html", battle_data=json.dumps(fight_result["battle_data"]),
                            profile_picture=usersdb[league][user]["img"], target_picture=f"img/assets/{target}.png",
                            target=target)  # todo rework

    def _perform_fight(self, user, user_data, target, target_name, league):
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        on_tile_users = get_tile_users(user_data["x_pos"], user_data["y_pos"], user, usersdb[league])
        return fight(target, target_name, on_tile_map, on_tile_users, user_data, user, usersdb[league], mapdb[league])


class ConquerHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        target = self.get_argument("target", default="")
        return_to_map = self.get_argument("return_to_map", default="false") == "true"
        message = self.perform_action(user, self._attempt_conquer, league, target)
        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _attempt_conquer(self, user, user_data, target):
        league = self.get_current_league()
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        return attempt_conquer(user, target, on_tile_map, usersdb[league], mapdb[league], user_data)


class MineHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        mine_amount = int(self.get_argument("amount", default="1"))
        return_to_map = self.get_argument("return_to_map", default="false") == "true"
        message = self.perform_action(user, self._mine_mountain, league, mine_amount)
        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _mine_mountain(self, user, user_data, mine_amount):
        league = self.get_current_league()
        return mine_mountain(user, mine_amount, user_data, usersdb[league], mapdb[league])


class ChopHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        chop_amount = int(self.get_argument("amount", default="1"))
        return_to_map = self.get_argument("return_to_map", default="false") == "true"
        message = self.perform_action(user, self._chop_forest, league, chop_amount)
        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _chop_forest(self, user, user_data, chop_amount):
        league = self.get_current_league()
        return chop_forest(user, chop_amount, user_data, usersdb[league], mapdb[league])


class BuildHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        entity = self.get_argument("entity")
        name = self.get_argument("name")
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_action(user, self._build, league, entity, name)
        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _build(self, user, user_data, entity, name):
        league = self.get_current_league()
        return build(user, user_data, entity, name, mapdb[league], usersdb[league])

    def return_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))
        self.finish()

class UpgradeHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        return_to_map = self.get_argument("return_to_map", default="false") == "true"
        message = self.perform_action(user, self._upgrade, league)
        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _upgrade(self, user, user_data):
        league = self.get_current_league()
        return upgrade(user, mapdb[league], usersdb[league])


class DeployArmyHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        action = self.get_argument("action")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        if action == "add":
            message = self.perform_action(user, self._deploy_army, league)
        elif action == "remove":
            message = self.perform_action(user, self._remove_army, league)
        else:
            message = "No action specified."

        if return_to_map:
            self.return_json({"message": message})
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def _deploy_army(self, user, user_data):
        league = self.get_current_league()
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        return deploy_army(user, on_tile_map, usersdb[league], mapdb[league], user_data)

    def _remove_army(self, user, user_data):
        league = self.get_current_league()
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        return remove_army(user, on_tile_map, usersdb[league], mapdb[league], user_data)


class RedirectToHTTPSHandler(tornado.web.RequestHandler):
    def get(self, parameters):
        self.redirect(self.request.full_url().replace('http://', 'https://'), permanent=True)


class LoginHandler(BaseHandler):
    def post(self, data):
        user = self.get_argument("name")[:16]
        if not re.match("^[a-zA-Z0-9]*$", user):
            self.render("templates/denied.html", message="Username should consist of alphanumericals only!")
            return

        password = self.get_argument("password")
        uploaded_file = self.request.files.get("profile_picture", None)
        league = self.get_argument("league")

        message, user_data = login(password, uploaded_file, auth_exists_user, auth_add_user, create_user,
                                   save_users_from_memory, save_map_from_memory, auth_login_validate,
                                   usersdb, mapdb, user, league)

        if message.startswith("Welcome"):
            self.set_secure_cookie("league", league, expires_days=84)
            self.set_secure_cookie("user", user, expires_days=84)
            if user_data is not None:
                self.render_user_panel(user, user_data, message=message, league=league)
            else:
                self.render("templates/denied.html", message="Error: User data not found after login.")
        else:
            self.render("templates/denied.html", message=message)


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/move_to", MoveToHandler),
        (r"/login(.*)", LoginHandler),
        (r"/logout(.*)", LogoutHandler),
        (r"/move(.*)", MoveHandler),
        (r"/chop(.*)", ChopHandler),
        (r"/mine(.*)", MineHandler),
        (r"/conquer", ConquerHandler),
        (r"/fight", FightHandler),
        (r"/map", MapHandler),
        (r"/rest(.*)", RestHandler),
        (r"/build(.*)", BuildHandler),
        (r"/upgrade", UpgradeHandler),
        (r"/scoreboard", ScoreboardHandler),
        (r"/revive", ReviveHandler),
        (r"/equip", EquipHandler),
        (r"/unequip", UnequipHandler),
        (r"/trash", TrashHandler),
        (r"/trash_weapons", TrashWeaponsHandler),
        (r"/trash_armor", TrashArmorHandler),
        (r"/trash_all", TrashAllHandler),
        (r"/repair", RepairHandler),
        (r"/deploy(.*)", DeployArmyHandler),
        (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "img"}),
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": "css"}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": "js"}),

    ])


async def main():
    with open("config_enclaves.json") as certlocfile:
        contents = json.load(certlocfile)
        certfile = contents["certfile"]
        keyfile = contents["keyfile"]

    ssl_options = {"certfile": certfile, "keyfile": keyfile} if os.path.exists(certfile) else None

    app_redirect = tornado.web.Application([(r"/(.*)", RedirectToHTTPSHandler)])

    app = make_app()
    app.settings["cookie_secret"] = auth_cookie_get()

    app.listen(443, ssl_options=ssl_options)
    app_redirect.listen(80)

    auth_check_users_db()
    webbrowser.open(f"http://127.0.0.1:443")
    print("app starting")

    shutdown_event = asyncio.Event()

    def handle_exit(*args):
        shutdown_event.set()
        turn_engine.stop()
        turn_engine.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    await shutdown_event.wait()


def initialize_map_and_users(league="game"):
    return load_map_to_memory(league), load_users_to_memory(league)


if __name__ == "__main__":
    mapdb = {}
    usersdb = {}

    leagues = ["game", "tour1"]

    for league in leagues:
        print(f"Working on {league}")
        db_status = init_databases(league)
        mapdb[league], usersdb[league] = initialize_map_and_users(league=league)

        print(db_status)
        if not db_status["map_exists"]:
            spawn(mapdb=mapdb[league], entity_class=entities.Forest, probability=1, map_size=200, max_entities=250,
                  level=1,
                  herd_probability=0)
            spawn(mapdb=mapdb[league], entity_class=entities.Mountain, probability=1, map_size=200, max_entities=250,
                  level=1,
                  herd_probability=0)
            spawn(mapdb=mapdb[league], entity_class=entities.Boar, probability=1, herd_size=15, max_entities=50,
                  level=1,
                  herd_probability=1)
            generate_multiple_mazes(mapdb[league], 20, 20, 10, 10, 0.1, 25, 200)

    turn_engine = TurnEngine(usersdb, mapdb)
    turn_engine.start()

    try:
        asyncio.run(main())
    finally:
        print("Application has shut down.")
