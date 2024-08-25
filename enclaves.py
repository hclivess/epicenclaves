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

import actions
import descriptions
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
from login import login
from turn_engine import TurnEngine
from backend import get_user, update_user_data
from map import (get_tile_map, get_tile_users, get_user_data, get_surrounding_map_and_user_data,
                 create_map_database, save_map_from_memory, load_map_to_memory, strip_usersdb,
                 get_map_data_limit, get_users_data_limit)
from rest import attempt_rest
from move import move, move_to
from build import build
from entity_generator import spawn
from auth import (auth_cookie_get, auth_login_validate, auth_add_user, auth_exists_user, auth_check_users_db)
from sqlite import create_game_database
from user import create_users_db, create_user, save_users_from_memory, load_users_to_memory
from wall_generator import generate_multiple_mazes
from upgrade import upgrade
from trash import trash_item

max_size = 1000000

# Get all weapon classes dynamically
weapon_classes = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Weapon), inspect.isclass)
                  if issubclass(cls, Weapon) and cls != Weapon}

armor_classes = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Armor), inspect.isclass)
                 if issubclass(cls, Armor) and cls != Armor}

tool_classes = {name.lower(): cls for name, cls in inspect.getmembers(inspect.getmodule(Tool), inspect.isclass)
                if issubclass(cls, Tool) and cls != Tool}


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


class BaseHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.render("templates/error.html")

    def get_current_user(self):
        return self.get_secure_cookie("user")

    def render_user_panel(self, user, user_data, message="", on_tile_map=None, on_tile_users=None):
        if on_tile_map is None:
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        if on_tile_users is None:
            on_tile_users = get_tile_users(user_data["x_pos"], user_data["y_pos"], user, usersdb)

        inventory_descriptions = generate_inventory_descriptions(user_data)
        print(inventory_descriptions)

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
            inventory_descriptions=inventory_descriptions
        )


class MainHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.render("templates/login.html")
        else:
            user = tornado.escape.xhtml_escape(self.current_user)
            data = get_user(user, usersdb)
            user_data = data[list(data.keys())[0]]
            self.render_user_panel(user, user_data, message=f"Welcome back, {user}")


class LogoutHandler(BaseHandler):
    def get(self, data):
        self.clear_all_cookies()
        self.redirect("/")


class MapHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        if not user:
            self.redirect("/")
            return

        visible_distance = 5
        data = get_surrounding_map_and_user_data(
            user=user,
            user_data_dict=usersdb,
            map_data_dict=mapdb,
            distance=visible_distance
        )
        self.render("templates/map.html", data=json.dumps(data), user=user)


class ScoreboardHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        self.render("templates/scoreboard.html", mapdb=mapdb, usersdb=usersdb, ensure_ascii=False, user=user)


class UserActionHandler(BaseHandler):
    def perform_action(self, user, action_func, *args, **kwargs):
        user_data = get_user_data(user, usersdb)
        if user_data is None:
            self.render_user_panel(user, {}, message=f"User {user} not found.")
            return
        message = action_func(user, user_data, *args, **kwargs)
        user_data = get_user_data(user, usersdb)  # Refresh user data
        self.render_user_panel(user, user_data, message=message)


class EquipHandler(UserActionHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)
        self.perform_action(user, self._equip_item, id)

    def _equip_item(self, user, user_data, item_id):
        return equip_item(user, usersdb, item_id)


class UnequipHandler(UserActionHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)
        self.perform_action(user, self._unequip_item, id)

    def _unequip_item(self, user, user_data, item_id):
        return unequip_item(user, usersdb, item_id)


class TrashHandler(UserActionHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)
        self.perform_action(user, self._trash_item, id)

    def _trash_item(self, user, user_data, item_id):
        return trash_item(usersdb, user, item_id)


class DeployArmyHandler(UserActionHandler):
    def get(self, data):
        action = self.get_argument("action")
        user = tornado.escape.xhtml_escape(self.current_user)

        if action == "add":
            self.perform_action(user, self._deploy_army, mapdb, usersdb)
        elif action == "remove":
            self.perform_action(user, self._remove_army, mapdb, usersdb)
        else:
            user_data = get_user_data(user, usersdb=usersdb)
            self.render_user_panel(user, user_data, message="No action specified.")

    def _deploy_army(self, user, user_data, mapdb, usersdb):
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        return deploy_army(user, on_tile_map, usersdb, mapdb, user_data)

    def _remove_army(self, user, user_data, mapdb, usersdb):
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        return remove_army(user, on_tile_map, usersdb, mapdb, user_data)


class BuildHandler(UserActionHandler):
    def get(self, data):
        user = tornado.escape.xhtml_escape(self.current_user)
        entity = self.get_argument("entity")
        name = self.get_argument("name")
        self.perform_action(user, build, entity, name, mapdb, usersdb)


class UserActionHandler(BaseHandler):
    def perform_action(self, user, action_func, *args, **kwargs):
        user_data = get_user_data(user, usersdb)
        if user_data is None:
            self.render_user_panel(user, {}, message=f"User {user} not found.")
            return
        message = action_func(user, user_data, *args, **kwargs)
        user_data = get_user_data(user, usersdb)  # Refresh user data
        self.render_user_panel(user, user_data, message=message)


class UpgradeHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        self.perform_action(user, self._upgrade)

    def _upgrade(self, user, user_data):
        return upgrade(user, mapdb, usersdb)


class MoveToHandler(BaseHandler):
    def get(self):
        x = int(self.get_argument("x"))
        y = int(self.get_argument("y"))
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb=usersdb)
        moved = move_to(user, x, y, max_size, user_data, users_dict=usersdb, map_dict=mapdb)
        user_data = get_user_data(user, usersdb=usersdb)  # Refresh user data

        visible_distance = 5
        x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
        visible_map_data = get_map_data_limit(x_pos, y_pos, mapdb, visible_distance)
        visible_users_data = get_users_data_limit(x_pos, y_pos, strip_usersdb(usersdb), visible_distance)

        map_data = {
            "users": visible_users_data,
            "construction": visible_map_data,
            "message": moved["message"]
        }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(map_data))


class MoveHandler(UserActionHandler):
    def get(self, data):
        target = self.get_argument("target", default="home")
        entry = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb=usersdb)
        moved = move(user, entry, max_size, user_data, users_dict=usersdb, map_dict=mapdb)
        user_data = get_user_data(user, usersdb=usersdb)  # Refresh user data

        if target == "map":
            visible_distance = 5
            x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
            visible_map_data = get_map_data_limit(x_pos, y_pos, mapdb, visible_distance)
            visible_users_data = get_users_data_limit(x_pos, y_pos, strip_usersdb(usersdb), visible_distance)
            map_data = {"users": visible_users_data, "construction": visible_map_data}
            self.render("templates/map.html", user=user, data=json.dumps(map_data), message=moved["message"])
        else:
            self.render_user_panel(user, user_data, message=moved["message"])


class ReviveHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        if user_data.get("action_points") > 5000:
            new_ap = user_data["action_points"] - 5000
            update_user_data(user=user, updated_values={"alive": True, "hp": 100, "action_points": new_ap},
                             user_data_dict=usersdb)
            message = "You awaken from the dead"
        else:
            message = "There is no way to revive you"
        user_data = get_user_data(user, usersdb)
        self.render_user_panel(user, user_data, message=message)


class RestHandler(UserActionHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        hours = self.get_argument("hours", default="1")
        self.perform_action(user, attempt_rest, hours, usersdb, mapdb)


class FightHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        target = self.get_argument("target")
        target_name = self.get_argument("name", default=None)

        message = get_fight_preconditions(user_data)
        if message:
            self.render_user_panel(user, user_data, message=message)
        else:
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
            on_tile_users = get_tile_users(user_data["x_pos"], user_data["y_pos"], user, usersdb)
            fight_result = fight(target, target_name, on_tile_map, on_tile_users, user_data, user, usersdb, mapdb)
            self.render("templates/fight.html", battle_data=json.dumps(fight_result["battle_data"]),
                        profile_picture=usersdb[user]["img"], target=target)


class ConquerHandler(UserActionHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        target = self.get_argument("target", default="")
        self.perform_action(user, self._attempt_conquer, target)

    def _attempt_conquer(self, user, user_data, target):
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        return attempt_conquer(user, target, on_tile_map, usersdb, mapdb, user_data)


class MineHandler(UserActionHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        chop_amount = int(self.get_argument("amount", default="1"))
        self.perform_action(user, mine_mountain, chop_amount, usersdb, mapdb)


class ChopHandler(UserActionHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        chop_amount = int(self.get_argument("amount", default="1"))
        self.perform_action(user, chop_forest, chop_amount, usersdb, mapdb)


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

        message = login(password, uploaded_file, auth_exists_user, auth_add_user, create_user,
                        save_users_from_memory, save_map_from_memory, auth_login_validate, usersdb, mapdb, user)

        if message.startswith("Welcome"):
            self.set_secure_cookie("user", self.get_argument("name"), expires_days=84)
            user_data = get_user_data(user, usersdb)
            self.render_user_panel(user, user_data, message=message)
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
        (r"/deploy(.*)", DeployArmyHandler),
        (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "img"}),
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


def init_databases():
    map_exists = os.path.exists("db/map_data.db")
    game_exists = os.path.exists("db/game_data.db")
    user_exists = os.path.exists("db/user_data.db")

    if not map_exists:
        create_map_database()
    if not game_exists:
        create_game_database()
    if not user_exists:
        create_users_db()

    return {"map_exists": map_exists}


def initialize_map_and_users():
    return load_map_to_memory(), load_users_to_memory()


if __name__ == "__main__":
    db_status = init_databases()
    mapdb, usersdb = initialize_map_and_users()

    if not db_status["map_exists"]:
        spawn(mapdb=mapdb, entity_class=entities.Forest, probability=1, map_size=200, max_entities=250, level=1,
              herd_probability=0)
        spawn(mapdb=mapdb, entity_class=entities.Mountain, probability=1, map_size=200, max_entities=250, level=1,
              herd_probability=0)
        spawn(mapdb=mapdb, entity_class=entities.Boar, probability=1, herd_size=15, max_entities=50, level=1,
              herd_probability=1)
        generate_multiple_mazes(mapdb, 20, 20, 10, 10, 0.1, 25, 200)

    actions = actions.TileActions()
    descriptions = descriptions.Descriptions()

    turn_engine = TurnEngine(usersdb, mapdb)
    turn_engine.start()

    try:
        asyncio.run(main())
    finally:
        print("Application has shut down.")
