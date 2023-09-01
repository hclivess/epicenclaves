import asyncio
import json
import os.path
import signal
import sys
import webbrowser
import os
import re
import io
from PIL import Image

import tornado.ioloop
import tornado.web
import tornado.escape

import actions
import descriptions
from chop import chop_forest
from conquer import attempt_conquer
from deploy_army import deploy_army
from equip import equip_item
from fight import fight, get_fight_preconditions
from turn_engine import TurnEngine
from backend import (
    get_user,
    update_user_data,
)
from map import get_tile_map, get_tile_users, get_user_data, get_surrounding_map_and_user_data, create_map_database, \
    save_map_from_memory, load_map_to_memory
from rest import attempt_rest
from move import move
from build import build
from entities import Tree
from entity_generator import spawn_entity
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
from entities import Wall

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

        data = json.dumps(get_surrounding_map_and_user_data(user, usersdb, mapdb))

        print("data", data)  # debug
        self.render("templates/map.html", data=data, ensure_ascii=False, user=user)


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


class DeployArmyHandler(BaseHandler):
    def get(self, data):
        type = self.get_argument("type")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb=usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )

        message = deploy_army(user, on_tile_map, usersdb, mapdb, user_data)
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
                    get_surrounding_map_and_user_data(user, usersdb, mapdb)
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


class ChopHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb)

        message = chop_forest(user, user_data, usersdb, mapdb)

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


class LoginHandler(BaseHandler):
    def post(self, data):
        user = self.get_argument("name")[:16]

        # Sanity check for username
        if not re.match("^[a-zA-Z0-9]*$", user):
            self.render(
                "templates/denied.html",
                message="Username should consist of alphanumericals only!",
            )
            return

        password = self.get_argument("password")

        uploaded_file = self.request.files.get("profile_picture", None)
        profile_pic_path = "img/pps/default.png"

        if uploaded_file:
            uploaded_file = uploaded_file[0]
            file_size = len(uploaded_file["body"])
            if file_size > 50 * 1024:
                self.render(
                    "templates/denied.html",
                    message="Profile picture size should be less than 50 KB!",
                )
                return

            # Check file extension
            filename = uploaded_file["filename"]
            file_extension = os.path.splitext(filename)[-1].lower()

            if file_extension not in [".jpg", ".jpeg", ".png", ".gif"]:
                self.render("templates/denied.html", message="Invalid file type!")
                return

            # Attempt to open the image using PIL
            try:
                Image.open(io.BytesIO(uploaded_file["body"]))
            except Exception as e:
                self.render(
                    "templates/denied.html",
                    message=f"Uploaded file is not a valid image: {e}!",
                )
                return

            save_dir = "img/pps/"
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            save_path = f"img/pps/{user}{file_extension}"

            with open(save_path, "wb") as f:
                f.write(uploaded_file["body"])

            profile_pic_path = save_path

        if not auth_exists_user(user):
            auth_add_user(user, password)
            create_user(user_data_dict=usersdb, user=user, profile_pic=profile_pic_path, mapdb=mapdb)

            save_users_from_memory(usersdb)
            save_map_from_memory(mapdb)

        if auth_login_validate(user, password):
            self.set_secure_cookie("user", self.get_argument("name"), expires_days=84)
            message = f"Welcome, {user}!"
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
        else:
            self.render("templates/denied.html", message="Wrong password")


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/login(.*)", LoginHandler),
            (r"/logout(.*)", LogoutHandler),
            (r"/move(.*)", MoveHandler),
            (r"/chop", ChopHandler),
            (r"/conquer", ConquerHandler),
            (r"/fight", FightHandler),
            (r"/map", MapHandler),
            (r"/rest(.*)", RestHandler),
            (r"/build(.*)", BuildHandler),
            (r"/revive", ReviveHandler),
            (r"/equip", EquipHandler),
            (r"/deploy(.*)", DeployArmyHandler),
            (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
            (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "img"}),
            # (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": "graphics"}),
        ]
    )


async def main():
    app = make_app()
    port = 8888
    app.listen(port)
    app.settings["cookie_secret"] = auth_cookie_get()
    auth_check_users_db()
    webbrowser.open(f"http://127.0.0.1:{port}")
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
        spawn_entity(
            mapdb=mapdb,
            entity_class=Tree,
            probability=0.5,
            size=200,
            every=10,
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
