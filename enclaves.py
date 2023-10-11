import asyncio
import json
import os.path
import signal
import sys
import webbrowser
import os
import re

import tornado.ioloop
import tornado.web
import tornado.escape

import actions
import descriptions
from chop import chop_forest
from mine import mine_mountain
from conquer import attempt_conquer
from deploy_army import deploy_army, remove_army
from equip import equip_item
from fight import fight, get_fight_preconditions
from login import login
from turn_engine import TurnEngine
from backend import (
    get_user,
    update_user_data,
)
from map import get_tile_map, get_tile_users, get_user_data, get_surrounding_map_and_user_data, create_map_database, \
    save_map_from_memory, load_map_to_memory, strip_usersdb
from rest import attempt_rest
from move import move
from build import build
from entities import Forest, Mountain
from entity_generator import generate_and_save_entities
from auth import (
    auth_cookie_get,
    auth_login_validate,
    auth_add_user,
    auth_exists_user,
    auth_check_users_db,
)
from sqlite import (
    create_game_database,
)
from user import create_users_db, create_user, save_users_from_memory, load_users_to_memory

from wall_generator import generate_multiple_mazes
from upgrade import upgrade
from trash import trash_item

max_size = 1000000


class BaseHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.render("templates/error.html")

    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    def get(self):
        message = self.get_argument("message", default="")
        if not self.current_user:
            self.render("templates/login.html")
        else:
            user = tornado.escape.xhtml_escape(self.current_user)
            message = f"Welcome back, {user}"

            data = get_user(user, usersdb)
            # Get the user's data
            username = list(data.keys())[
                0
            ]  # Get the first (and only) key in the dictionary
            user_data = data[username]  # Get the user's data

            print("usersdb", usersdb)  # debug
            print("mapdb", mapdb)  # debug

            print("data", data)  # debug
            print("user_data", user_data)  # debug
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
            on_tile_users = get_tile_users(
                user_data["x_pos"], user_data["y_pos"], user, usersdb
            )
            print("on_tile_map", on_tile_map)
            print("on_tile_users", on_tile_users)
            self.render(
                "templates/user_panel.html",
                user=user,
                file=user_data,
                message=message,
                on_tile_map=on_tile_map,
                on_tile_users=on_tile_users,
                actions=actions,
                descriptions=descriptions,
            )


class LogoutHandler(BaseHandler):
    def get(self, data):
        self.clear_all_cookies()
        self.redirect("/")


class MapHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)

        data = json.dumps(get_surrounding_map_and_user_data(user, strip_usersdb(usersdb), mapdb, 50))

        print("data", data)  # debug
        self.render("templates/map.html", data=data, ensure_ascii=False, user=user)


class ScoreboardHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)

        self.render("templates/scoreboard.html", mapdb=mapdb, usersdb=usersdb, ensure_ascii=False, user=user)


class EquipHandler(BaseHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb=usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        message = equip_item(usersdb, user, id)

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class TrashHandler(BaseHandler):
    def get(self):
        id = self.get_argument("id")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb=usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        message = trash_item(usersdb, user, id)

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class DeployArmyHandler(BaseHandler):
    def get(self, data):
        type = self.get_argument("type")
        action = self.get_argument("action")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb=usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        if action == "add":
            message = deploy_army(user, on_tile_map, usersdb, mapdb, user_data)
        elif action == "remove":
            message = remove_army(user, on_tile_map, usersdb, mapdb, user_data)
        else:
            message = "No action specified."
        user_data = get_user_data(user, usersdb=usersdb)  # refresh

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class BuildHandler(BaseHandler):
    def get(self, data):
        entity = self.get_argument("entity")
        name = self.get_argument("name")
        user = tornado.escape.xhtml_escape(self.current_user)

        message = build(entity, name, user, mapdb, usersdb=usersdb)

        user_data = get_user_data(user, usersdb=usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class UpgradeHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)

        message = upgrade(user, mapdb, usersdb=usersdb)

        user_data = get_user_data(user, usersdb=usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class MoveHandler(BaseHandler):
    def get(self, data):
        target = self.get_argument("target", default="home")
        entry = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb=usersdb)
        moved = move(user, entry, max_size, user_data, users_dict=usersdb, map_dict=mapdb)
        user_data = get_user_data(user, usersdb=usersdb)  # update

        message = moved["message"]

        if target == "map":
            self.render(
                "templates/map.html",
                user=user,
                data=json.dumps(
                    get_surrounding_map_and_user_data(user, strip_usersdb(usersdb), mapdb, 50)
                ),
                message=message,
            )
        else:
            on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
            on_tile_users = get_tile_users(
                user_data["x_pos"], user_data["y_pos"], user, usersdb
            )

            self.render(
                "templates/user_panel.html",
                user=user,
                file=user_data,
                message=message,
                on_tile_map=on_tile_map,
                on_tile_users=on_tile_users,
                actions=actions,
                descriptions=descriptions,
            )


class ReviveHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)

        if user_data.get("action_points") > 5000:
            new_ap = user_data["action_points"] - 5000

            update_user_data(
                user=user,
                updated_values={"alive": True, "hp": 100, "action_points": new_ap},
                user_data_dict=usersdb,
            )
            message = "You awaken from the dead"
        else:
            message = "There is no way to revive you"

        user_data = get_user_data(user, usersdb)

        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class RestHandler(BaseHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        hours = self.get_argument("hours", default="1")

        message = attempt_rest(user, user_data, hours, usersdb, mapdb)

        user_data = get_user_data(user, usersdb)

        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class FightHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        target = self.get_argument("target")
        target_name = self.get_argument("name", default=None)

        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        message = get_fight_preconditions(user_data)

        if message:
            self.render(
                "templates/user_panel.html",
                user=user,
                file=user_data,
                message=message,
                on_tile_map=on_tile_map,
                on_tile_users=on_tile_users,
                actions=actions,
                descriptions=descriptions,
            )
        else:
            messages = fight(
                target,
                target_name,
                on_tile_map,
                on_tile_users,
                user_data,
                user,
                usersdb,
                mapdb,
            )
            self.render("templates/fight.html", messages=messages)


class ConquerHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        target = self.get_argument("target", default="")

        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)

        message = attempt_conquer(user, target, on_tile_map, usersdb, mapdb, user_data)

        user_data = get_user_data(user, usersdb)  # update
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class MineHandler(BaseHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        chop_amount = int(self.get_argument("amount", default="1"))

        user_data = get_user_data(user, usersdb)

        message = mine_mountain(user, chop_amount, user_data, usersdb, mapdb)

        user_data = get_user_data(user, usersdb)

        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


class ChopHandler(BaseHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        chop_amount = int(self.get_argument("amount", default="1"))

        user_data = get_user_data(user, usersdb)

        message = chop_forest(user, chop_amount, user_data, usersdb, mapdb)

        user_data = get_user_data(user, usersdb)

        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        self.render(
            "templates/user_panel.html",
            user=user,
            file=user_data,
            message=message,
            on_tile_map=on_tile_map,
            on_tile_users=on_tile_users,
            actions=actions,
            descriptions=descriptions,
        )


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

        message, context = login(password, uploaded_file, auth_exists_user, auth_add_user, create_user,
                                 save_users_from_memory, save_map_from_memory, auth_login_validate, get_user_data,
                                 get_tile_map, get_tile_users, actions, descriptions, usersdb, mapdb, user)

        if context:
            self.set_secure_cookie("user", self.get_argument("name"), expires_days=84)
            self.render("templates/user_panel.html", **context)
        else:
            self.render("templates/denied.html", message=message)


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
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
            (r"/trash", TrashHandler),
            (r"/deploy(.*)", DeployArmyHandler),
            (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
            (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "img"}),
            # (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": "graphics"}),
        ]
    )


async def main():
    with open("config_enclaves.json") as certlocfile:
        contents = json.load(certlocfile)
        certfile = contents["certfile"]
        keyfile = contents["keyfile"]

    if os.path.exists(certfile):
        ssl_options = {
            "certfile": certfile,
            "keyfile": keyfile,
        }
    else:
        ssl_options = None

    app_redirect = tornado.web.Application(
        [
            (r"/(.*)", RedirectToHTTPSHandler),
        ]
    )

    app = make_app()
    app.settings["cookie_secret"] = auth_cookie_get()

    app.listen(443, ssl_options=ssl_options)
    app_redirect.listen(80)

    auth_check_users_db()
    webbrowser.open(f"http://127.0.0.1:443")
    print("app starting")

    # Instead of await asyncio.Event().wait(), create an event to listen for shutdown
    shutdown_event = asyncio.Event()

    # Signal handlers to set the event and stop the app
    def handle_exit(*args):
        shutdown_event.set()
        turn_engine.stop()
        turn_engine.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Wait for shutdown signal
    await shutdown_event.wait()
    # After receiving the shutdown signal, stop the TurnEngine thread


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
    mapdb = load_map_to_memory()
    usersdb = load_users_to_memory()

    return mapdb, usersdb


if __name__ == "__main__":
    db_status = init_databases()
    mapdb, usersdb = initialize_map_and_users()

    if not db_status["map_exists"]:
        generate_and_save_entities(
            mapdb=mapdb,
            entity_instance=Forest(),
            probability=1,
            size=200,
            max_entities=250,
            level=1,
            herd_probability=0
        )

        generate_and_save_entities(
            mapdb=mapdb,
            entity_instance=Mountain,
            probability=1,
            size=200,
            max_entities=250,
            level=1,
            herd_probability=0
        )

        generate_multiple_mazes(mapdb, 20, 20, 10, 10, 0.1, 25, 200)

    actions = actions.TileActions()
    descriptions = descriptions.Descriptions()

    turn_engine = TurnEngine(usersdb, mapdb)
    turn_engine.start()

    try:
        asyncio.run(main())
    finally:
        print("Application has shut down.")
