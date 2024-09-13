import tornado.websocket
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
import time

from buildings import Building
import buildings
from player import User, calculate_total_hp

import entities
from fish import fish_pond
from demolish import demolish
from leagues import load_leagues
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
from spawner import spawn
from auth import (auth_cookie_get, auth_login_validate, auth_add_user, auth_exists_user, auth_check_users_db)
from sqlite import init_databases, load_users_to_memory, save_users_from_memory, save_map_from_memory, \
    load_map_to_memory, users_db
from player import create_user, calculate_population_limit
from maze_generator import generate_multiple_mazes
from upgrade import upgrade
from trash import trash_item, trash_armor, trash_all, trash_weapons
from repair import repair_all_items
from drag import drag_player

MAX_SIZE = 1000000
DISTANCE = 15

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
    def prepare(self):
        allowed_paths = ["/", "/login"]  # Add any other public paths here
        if not self.current_user and self.request.path not in allowed_paths:
            self.redirect("/")
            return

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_current_league(self):
        return self.get_secure_cookie("league").decode()

    def return_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))

    def write_error(self, status_code, **kwargs):
        self.render("templates/error.html")

    def render_user_panel(self, user, user_data, message="", on_tile_map=None, on_tile_users=None, league=None):
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

        # Calculate current and max total HP
        current_hp = user_data.get("hp", 0)
        exp = user_data.get("exp", 0)
        current_total_hp = calculate_total_hp(current_hp, exp)
        max_total_hp = calculate_total_hp(100, exp)  # Assuming 100 is the base max HP

        #print("user_data", user_data)
        #print("mapdb", mapdb)


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
            league=league,
            current_total_hp=current_total_hp,
            max_total_hp=max_total_hp,
            pop_limit = calculate_population_limit(user_data)
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

        visible_distance = DISTANCE
        user_data = get_user_data(user, usersdb[league])
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
            if "hp" in entity:
                filtered_entity["hp"] = entity["hp"]
            filtered_map_data[coord] = filtered_entity

        # Generate actions for each tile and player
        tile_actions = {}
        for coord, entity in filtered_map_data.items():
            tile_actions[coord] = get_tile_actions(entity, user)

        for username, user_info in filtered_users_data.items():
            if username != user:
                coord = f"{user_info['x_pos']},{user_info['y_pos']}"
                if user_info.get('hp', 0) > 0:  # Alive users have HP > 0
                    tile_actions[coord] = [{
                        "name": "challenge",
                        "action": f"/fight?target=player&name={username}"
                    }]
                else:  # Dead users have HP <= 0
                    tile_actions[coord] = [{
                        "name": "drag",
                        "action": f"/drag?target={username}"
                    }]

        map_data = {
            "users": filtered_users_data,
            "construction": filtered_map_data,
            "actions": tile_actions,
            "x_pos": x_pos,
            "y_pos": y_pos
        }

        # Check if the request wants JSON
        if self.get_argument("format", None) == "json":
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(map_data))
        else:
            self.render("templates/map.html", user=user, data=json.dumps(map_data), timestamp=time.time())


class ScoreboardHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        self.render("templates/scoreboard.html", mapdb=mapdb[league].copy(), usersdb=usersdb[league].copy(), ensure_ascii=False,
                    user=user)


class BestiaryHandler(BaseHandler):
    def get(self):
        enemy_classes = [cls for cls in entities.__dict__.values()
                         if isinstance(cls, type) and issubclass(cls, entities.Enemy) and cls != entities.Enemy]
        enemies = [cls(cls.min_level) for cls in enemy_classes]
        self.render("templates/bestiary.html", enemies=enemies)

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

class MoveHandler(BaseHandler):
    def get(self, direction):
        target = self.get_argument("target", default="home")
        entry = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        user_data = get_user_data(user, usersdb=usersdb[league])
        moved = move(user, entry, MAX_SIZE, user_data, users_dict=usersdb[league], map_dict=mapdb[league])
        user_data = get_user_data(user, usersdb=usersdb[league])  # Refresh user data

        if target == "map":
            visible_distance = DISTANCE
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
                if "hp" in entity:
                    filtered_entity["hp"] = entity["hp"]
                filtered_map_data[coord] = filtered_entity

            # Generate actions for each tile and player
            tile_actions = {}
            for coord, entity in filtered_map_data.items():
                tile_actions[coord] = get_tile_actions(entity, user)

            for username, user_info in filtered_users_data.items():
                if username != user:
                    coord = f"{user_info['x_pos']},{user_info['y_pos']}"
                    if user_info.get('hp', 0) > 0:  # Alive users have HP > 0
                        tile_actions[coord] = [{
                            "name": "challenge",
                            "action": f"/fight?target=player&name={username}"
                        }]
                    else:  # Dead users have HP <= 0
                        tile_actions[coord] = [{
                            "name": "drag",
                            "action": f"/drag?target={username}"
                        }]

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
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
            on_tile_users = get_tile_users(user_data["x_pos"], user_data["y_pos"], user, usersdb[league])
            self.render_user_panel(user, user_data, message=moved["message"], on_tile_map=on_tile_map, on_tile_users=on_tile_users, league=league)


class MoveToHandler(BaseHandler):
    def get(self):
        x = int(self.get_argument("x"))
        y = int(self.get_argument("y"))
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        user_data = get_user_data(user, usersdb=usersdb[league])

        # Proximity check
        current_x, current_y = user_data["x_pos"], user_data["y_pos"]
        max_move_distance = DISTANCE  # Define the maximum allowed move distance
        if abs(x - current_x) > max_move_distance or abs(y - current_y) > max_move_distance:
            self.write(json.dumps({"error": "Invalid move. Target location is too far."}))
            return

        moved = move_to(user, x, y, MAX_SIZE, user_data, users_dict=usersdb[league], map_dict=mapdb[league])
        user_data = get_user_data(user, usersdb=usersdb[league])  # Refresh user data

        visible_distance = DISTANCE
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
            if "hp" in entity:
                filtered_entity["hp"] = entity["hp"]
            filtered_map_data[coord] = filtered_entity

        # Generate actions for each tile and player
        tile_actions = {}
        for coord, entity in filtered_map_data.items():
            tile_actions[coord] = get_tile_actions(entity, user)

        for username, user_info in filtered_users_data.items():
            if username != user:
                coord = f"{user_info['x_pos']},{user_info['y_pos']}"
                if user_info.get('hp', 0) > 0:  # Alive users have HP > 0
                    tile_actions[coord] = [{
                        "name": "challenge",
                        "action": f"/fight?target=player&name={username}"
                    }]
                else:  # Dead users have HP <= 0
                    tile_actions[coord] = [{
                        "name": "drag",
                        "action": f"/drag?target={username}"
                    }]

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

class DragHandler(BaseHandler):
    def get(self):
        target = self.get_argument("target")
        direction = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            message = f"User {user} not found."
        else:
            message, new_x, new_y = drag_player(target, direction, league, usersdb, mapdb, MAX_SIZE)
            if new_x is not None and new_y is not None:
                # Move the dragging player to the new position
                move_to(user, new_x, new_y, MAX_SIZE, user_data, users_dict=usersdb[league], map_dict=mapdb[league])
            # Refresh user data after dragging
            user_data = get_user_data(user, usersdb[league])

        if return_to_map:
            # Prepare map data for JSON response
            visible_distance = 10
            x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
            visible_map_data = get_map_data_limit(x_pos, y_pos, mapdb[league], visible_distance)
            visible_users_data = get_users_data_limit(x_pos, y_pos, strip_usersdb(usersdb[league]), visible_distance)

            # Filter and prepare data as in MapHandler
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
                if "hp" in entity:
                    filtered_entity["hp"] = entity["hp"]
                filtered_map_data[coord] = filtered_entity

            # Generate actions for each tile and player
            tile_actions = {}
            for coord, entity in filtered_map_data.items():
                tile_actions[coord] = get_tile_actions(entity, user)

            for username, user_info in filtered_users_data.items():
                if username != user:
                    coord = f"{user_info['x_pos']},{user_info['y_pos']}"
                    if user_info.get('hp', 0) > 0:  # Alive users have HP > 0
                        tile_actions[coord] = [{
                            "name": "challenge",
                            "action": f"/fight?target=player&name={username}"
                        }]
                    else:  # Dead users have HP <= 0
                        tile_actions[coord] = [{
                            "name": "drag",
                            "action": f"/drag?target={username}"
                        }]

            map_data = {
                "users": filtered_users_data,
                "construction": filtered_map_data,
                "actions": tile_actions,
                "x_pos": x_pos,
                "y_pos": y_pos,
                "message": message
            }

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(map_data))
        else:
            # Refresh on_tile_map and on_tile_users
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
            on_tile_users = get_tile_users(user_data["x_pos"], user_data["y_pos"], user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, on_tile_map=on_tile_map, on_tile_users=on_tile_users, league=league)



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
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        hours = int(self.get_argument("hours", default="1"))
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_rest_action(user, self._rest, league, hours)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_rest_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

    def _rest(self, user, user_data, hours):
        league = self.get_current_league()
        result = attempt_rest(user, user_data, hours, usersdb[league], mapdb[league])
        return result if isinstance(result, str) else result.get("message", "Rest action completed")


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
            print("fight_result", fight_result)
            if return_to_map:
                self.return_json({"message": fight_result.get("message", "Fight completed"),
                                  "battle_data": fight_result["battle_data"]})
            else:
                # For player targets, use the target's image from usersdb
                if target.lower() == "player" and target_name in usersdb[league]:
                    target_picture = usersdb[league][target_name]["img"]
                else:
                    target_picture = f"img/assets/{target}.png"


                self.render("templates/fight.html",
                            battle_data=json.dumps(fight_result["battle_data"]),
                            profile_picture=user_data["img"],
                            target_picture=target_picture,
                            target=target,
                            timestamp=int(time.time()))  # Add this line

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

        message = self.perform_conquer_action(user, self._attempt_conquer, league, target)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_conquer_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

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

        message = self.perform_mine_action(user, self._mine_mountain, league, mine_amount)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_mine_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

    def _mine_mountain(self, user, user_data, mine_amount):
        league = self.get_current_league()
        return mine_mountain(user, mine_amount, user_data, usersdb[league], mapdb[league])

class FishHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_fish_action(user, self._fish_pond, league)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_fish_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

    def _fish_pond(self, user, user_data):
        league = self.get_current_league()
        return fish_pond(user, user_data, usersdb[league], mapdb[league])

class ChopHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        chop_amount = int(self.get_argument("amount", default="1"))
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_chop_action(user, self._chop_forest, league, chop_amount)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_chop_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

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

        message = self.perform_build_action(user, self._build, league, entity, name)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_build_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

    def _build(self, user, user_data, entity, name):
        league = self.get_current_league()
        return build(user, user_data, entity, name, mapdb[league], usersdb[league])


class UpgradeHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_upgrade_action(user, self._upgrade, league)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_upgrade_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

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
            message = self.perform_deploy_action(user, self._deploy_army, league)
        elif action == "remove":
            message = self.perform_deploy_action(user, self._remove_army, league)
        else:
            message = "No action specified."

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_deploy_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

    def _deploy_army(self, user, user_data):
        league = self.get_current_league()
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        return deploy_army(user, on_tile_map, usersdb[league], mapdb[league], user_data)

    def _remove_army(self, user, user_data):
        league = self.get_current_league()
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb[league])
        return remove_army(user, on_tile_map, usersdb[league], mapdb[league], user_data)




class DemolishHandler(UserActionHandler):
    def get(self, *args, **kwargs):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        return_to_map = self.get_argument("return_to_map", default="false") == "true"

        message = self.perform_demolish_action(user, self._demolish, league)

        if return_to_map:
            self.set_header("Content-Type", "application/json")
            self.write(json.dumps({"message": message}))
        else:
            user_data = get_user_data(user, usersdb[league])
            self.render_user_panel(user, user_data, message=message, league=league)

    def perform_demolish_action(self, user, action_func, league, *args, **kwargs):
        user_data = get_user_data(user, usersdb[league])
        if user_data is None:
            return f"User {user} not found."
        return action_func(user, user_data, *args, **kwargs)

    def _demolish(self, user, user_data):
        league = self.get_current_league()
        return demolish(user, user_data, usersdb[league], mapdb[league])

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

class ChatHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        league = self.get_current_league()
        if not user:
            self.redirect("/")
            return
        chat_history = self.get_chat_history(league)
        self.render("templates/chat.html", user=user, league=league, chat_history=chat_history)

    def get_chat_history(self, league):
        chat_history_file = f"chat_history_{league}.json"
        if os.path.exists(chat_history_file):
            with open(chat_history_file, "r") as file:
                chat_history = json.load(file)
        else:
            chat_history = []
        return chat_history

class ChatWebSocketHandler(tornado.websocket.WebSocketHandler):
    connections = set()

    def open(self):
        ChatWebSocketHandler.connections.add(self)

    def on_message(self, message):
        user = tornado.escape.xhtml_escape(self.get_secure_cookie("user").decode())
        league = self.get_secure_cookie("league").decode()
        message_data = json.loads(message)  # Parse the received message as JSON
        message_data["user"] = user  # Add the user to the message data
        self.store_chat_message(league, message_data)
        for connection in ChatWebSocketHandler.connections:
            connection.write_message(json.dumps(message_data))

    def on_close(self):
        ChatWebSocketHandler.connections.remove(self)

    def store_chat_message(self, league, message_data):
        chat_history_file = f"chat_history_{league}.json"
        if os.path.exists(chat_history_file):
            with open(chat_history_file, "r") as file:
                chat_history = json.load(file)
        else:
            chat_history = []
        chat_history.append(message_data)
        with open(chat_history_file, "w") as file:
            json.dump(chat_history, file)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/move_to", MoveToHandler),
        (r"/login(.*)", LoginHandler),
        (r"/logout(.*)", LogoutHandler),
        (r"/move(.*)", MoveHandler),
        (r"/chop(.*)", ChopHandler),
        (r"/fish(.*)", FishHandler),
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
        (r"/drag", DragHandler),
        (r"/trash", TrashHandler),
        (r"/demolish", DemolishHandler),
        (r"/trash_weapons", TrashWeaponsHandler),
        (r"/trash_armor", TrashArmorHandler),
        (r"/trash_all", TrashAllHandler),
        (r"/repair", RepairHandler),
        (r"/deploy(.*)", DeployArmyHandler),
        (r"/bestiary", BestiaryHandler),
        (r"/chat", ChatHandler),
        (r"/ws/chat", ChatWebSocketHandler),
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

    leagues = load_leagues()

    for league in leagues:
        print(f"Working on {league}")
        db_status = init_databases(league)
        mapdb[league], usersdb[league] = initialize_map_and_users(league=league)

        print(db_status)
        if not db_status["map_exists"]:
            print("Fresh start")
            # First, spawn the biomes
            spawn(mapdb=mapdb[league], entity_class=entities.Cavern, probability=1, map_size=1000, max_entities=250,
                  herd_probability=0, is_biome_generation=True)
            spawn(mapdb=mapdb[league], entity_class=entities.Forest, probability=1, map_size=1000, max_entities=250,
                  herd_probability=0, is_biome_generation=True)
            spawn(mapdb=mapdb[league], entity_class=entities.Pond, probability=1, map_size=1000, max_entities=100,
                  herd_probability=0, is_biome_generation=True)
            spawn(mapdb=mapdb[league], entity_class=entities.Mountain, probability=1, map_size=1000, max_entities=200,
                  herd_probability=0, is_biome_generation=True)
            spawn(mapdb=mapdb[league], entity_class=entities.Graveyard, probability=1, map_size=1000, max_entities=200,
                  herd_probability=0, is_biome_generation=True)
            spawn(mapdb=mapdb[league], entity_class=entities.Desert, probability=1, map_size=1000, max_entities=200,
                  herd_probability=0, is_biome_generation=True)
            spawn(mapdb=mapdb[league], entity_class=entities.Gnomes, probability=1, map_size=1000, max_entities=200,
                  herd_probability=0, is_biome_generation=True)

            spawn(mapdb=mapdb[league], entity_class=entities.Rat, probability=1, map_size=1000, max_entities=200,
                  herd_probability=1)
            spawn(mapdb=mapdb[league], entity_class=entities.Boar, probability=1, map_size=1000, max_entities=200,
                  herd_probability=1)
            spawn(mapdb=mapdb[league], entity_class=entities.Wolf, probability=1, map_size=1000, max_entities=200,
                  herd_probability=1)

            # Generate mazes (if you still want to include them)
            generate_multiple_mazes(mapdb[league], 51, 51, 10, 10, 0.1, 500, 1000)

    turn_engine = TurnEngine(usersdb, mapdb)
    turn_engine.start()

    try:
        asyncio.run(main())
    finally:
        print("Application has shut down.")
