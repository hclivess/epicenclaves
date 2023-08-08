import asyncio
import json
import os.path
import signal
import webbrowser

import tornado.ioloop
import tornado.web
import tornado.escape

from turn_engine import TurnEngine
import backend
from backend import cookie_get, build, occupied_by, generate_entities, get_user_data, move, attempt_rest, \
    Boar, death_roll, get_tile
from sqlite import create_map_database, has_item, update_map_data, create_user, update_user_data, login_validate, \
    remove_from_user, add_user, exists_user, get_surrounding_map_and_user_data, check_users_db, \
    create_user_db, create_game_database, remove_from_map, load_map_to_memory, load_users_to_memory, get_user

max_size = 1000


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
            username = list(data.keys())[0]  # Get the first (and only) key in the dictionary
            user_data = data[username]  # Get the user's data

            print("data", data)  # debug
            print("user_data", user_data)  # debug
            occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)
            print("occupied", occupied)  # debug

            if user_data["action_points"] < 1:
                message = f"You have action points left for this turn"

            self.render("templates/user_panel.html",
                        user=user,
                        file=user_data,
                        message=message,
                        on_tile=occupied,
                        actions=actions,
                        descriptions=descriptions)


class LogoutHandler(BaseHandler):
    def get(self, data):
        self.clear_all_cookies()
        self.redirect("/")


class MapHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)

        data = json.dumps(get_surrounding_map_and_user_data(user, usersdb, mapdb))

        print("data", data)  # debug
        self.render("templates/map.html",
                    data=data,
                    ensure_ascii=False)


class BuildHandler(BaseHandler):
    def get(self, data):
        entity = self.get_argument("entity")
        name = self.get_argument("name")
        user = tornado.escape.xhtml_escape(self.current_user)

        message = build(entity, name, user, mapdb, usersdb=usersdb)

        user_data = get_user_data(user, usersdb=usersdb)
        occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)

        self.render("templates/user_panel.html",
                    user=user,
                    file=user_data,
                    message=message,
                    on_tile=occupied,
                    actions=actions,
                    descriptions=descriptions)


class MoveHandler(BaseHandler):
    def get(self, data):
        target = self.get_argument("target", default="home")
        entry = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb=usersdb)
        moved = move(user, entry, max_size, user_data, users_dict=usersdb)
        user_data = get_user_data(user, usersdb=usersdb)  # update

        message = "Moved" if moved else "Moved out of bounds or no action points left"

        if target == "map":
            self.render(
                "templates/map.html",
                user=user,
                data=json.dumps(get_surrounding_map_and_user_data(user, usersdb, mapdb)),
                message=message
            )
        else:
            occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)
            self.render(
                "templates/user_panel.html",
                user=user,
                file=user_data,
                message=message,
                on_tile=occupied,
                actions=actions,
                descriptions=descriptions
            )


class RestHandler(BaseHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        hours = self.get_argument("hours", default="1")

        message = attempt_rest(user, user_data, hours, usersdb, mapdb)

        user_data = get_user_data(user, usersdb)  # update

        x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
        occupied = get_tile(x_pos, y_pos, mapdb)

        self.render("templates/user_panel.html",
                    user=user,
                    file=user_data,
                    message=message,
                    on_tile=occupied,
                    actions=actions,
                    descriptions=descriptions)


class FightHandler(BaseHandler):

    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        target = self.get_argument("target")

        this_tile = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)
        print("this_tile", this_tile)
        occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)

        user_data = get_user_data(user, usersdb)

        message = None
        if user_data["action_points"] < 1:
            message = "Not enough action points to slay"
        if not user_data["alive"]:
            message = "You are dead"

        if message:
            self.render("templates/user_panel.html",
                        user=user,
                        file=user_data,
                        message=message,
                        on_tile=occupied,
                        actions=actions,
                        descriptions=descriptions)

        else:
            for entry in this_tile:
                if target == list(entry.values())[0].get("type") == "boar":

                    messages = []

                    boar = Boar()  # local instance is sufficient, also should be used in generator!

                    escaped = False
                    while boar.alive and user_data["alive"] and not escaped:
                        if boar.hp < 1:
                            messages.append("The boar is dead")
                            boar.alive = False
                            remove_from_map(entity_type="boar", coords=list(entry.keys())[0], map_data_dict=mapdb)
                            update_user_data(user=user,
                                             updated_values={"action_points": user_data["action_points"] - 1,
                                                             "exp": user_data["exp"] + 1,
                                                             "food": user_data["food"] + 1,
                                                             "hp": user_data["hp"]},
                                             user_data_dict=usersdb)

                        elif user_data["hp"] < 1:
                            if death_roll(boar.kill_chance):
                                messages.append("You died")
                                user_data["alive"] = False
                                update_user_data(user=user,
                                                 updated_values={"alive": user_data["alive"],
                                                                 "hp": user_data["hp"]},
                                                 user_data_dict=usersdb)
                            else:
                                messages.append("You are almost dead but managed to escape")
                                escaped = True
                                update_user_data(user=user,
                                                 updated_values={"action_points": user_data["action_points"] - 1,
                                                                 "hp": 1},
                                                 user_data_dict=usersdb)

                        else:
                            boar.hp -= 1
                            messages.append(f"The boar takes 1 damage and is left with {boar.hp} hp")
                            messages.append(f"You take 1 damage and are left with {user_data['hp']} hp")
                            user_data["hp"] = user_data["hp"] - 1

                    self.render("templates/fight.html",
                                messages=messages)


class ConquerHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        user_data = get_user_data(user, usersdb)
        target = self.get_argument("target", default="home")

        this_tile = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)
        print("this_tile", this_tile)

        for entry in this_tile:
            print("entry", entry)
            owner = list(entry.values())[0].get("control")

            if owner == user:
                message = "You already own this tile"

            elif list(entry.values())[0].get("type") == target and user_data["action_points"] > 0:
                remove_from_user(owner, {"x_pos": user_data["x_pos"], "y_pos": user_data["y_pos"]}, usersdb)

                # Update the "control" attribute
                key = list(entry.keys())[0]
                entry[key]['control'] = user

                # Construct the updated data for the specific position
                updated_data = entry

                update_map_data(updated_data, mapdb)

                # Call the update function
                update_user_data(user=user,
                                 updated_values={"construction": updated_data,
                                                 "action_points": user_data["action_points"] - 1},
                                 user_data_dict=usersdb)

                message = "Takeover successful"
            else:
                message = "Cannot acquire an empty tile"

            user_data = get_user_data(user, usersdb)

            occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)

            self.render("templates/user_panel.html",
                        user=user,
                        file=user_data,
                        message=message,
                        on_tile=occupied,
                        actions=actions,
                        descriptions=descriptions)


class ChopHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = get_user_data(user, usersdb)

        proper_tile = occupied_by(user_data["x_pos"],
                                  user_data["y_pos"],
                                  what="forest",
                                  mapdb=mapdb)
        item = "axe"

        if not has_item(user, item):
            message = f"You have no {item} at hand"

        elif proper_tile and user_data["action_points"] > 0:
            new_wood = user_data["wood"] + 1
            new_ap = user_data["action_points"] - 1

            update_user_data(user=user,
                             updated_values={"action_points": new_ap,
                                             "wood": new_wood},
                             user_data_dict=usersdb)

            message = "Chopping successful"

        elif not proper_tile:
            message = "Not on a forest tile"

        else:
            message = "Out of action points to chop"

        user_data = get_user_data(user, usersdb)

        occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)

        self.render("templates/user_panel.html",
                    user=user,
                    file=user_data,
                    message=message,
                    on_tile=occupied,
                    actions=actions,
                    descriptions=descriptions)


class LoginHandler(BaseHandler):
    def post(self, data):
        user = self.get_argument("name")[:8]
        password = self.get_argument("password")

        if not exists_user(user):
            add_user(user, password)
            create_user(user_data_dict=usersdb, user=user)
        if login_validate(user, password):
            self.set_secure_cookie("user", self.get_argument("name"), expires_days=84)

            message = f"Welcome, {user}!"

            user_data = get_user_data(user, usersdb)

            occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)

            self.render("templates/user_panel.html",
                        user=user,
                        file=user_data,
                        message=message,
                        on_tile=occupied,
                        actions=actions,
                        descriptions=descriptions)
        else:
            self.render("templates/notfound.html")


def make_app():
    return tornado.web.Application([
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
        (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "img"}),
        # (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": "graphics"}),
    ])


async def main():
    app = make_app()
    port = 8888
    app.listen(port)
    app.settings["cookie_secret"] = cookie_get()
    check_users_db()
    webbrowser.open(f"http://127.0.0.1:{port}")
    print("app starting")

    # Instead of await asyncio.Event().wait(), create an event to listen for shutdown
    shutdown_event = asyncio.Event()

    # Signal handlers to set the event and stop the app
    def handle_exit(*args):
        shutdown_event.set()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Wait for shutdown signal
    await shutdown_event.wait()
    # After receiving the shutdown signal, stop the TurnEngine thread
    turn_engine.stop()
    turn_engine.join()


def init_databases():
    if not os.path.exists("db/map_data.db"):
        create_map_database()

    if not os.path.exists("db/game_data.db"):
        create_game_database()

    if not os.path.exists("db/user_data.db"):
        create_user_db()


def initialize_map_and_users():
    mapdb = load_map_to_memory()
    usersdb = load_users_to_memory()

    if not os.path.exists("db/map_data.db"):
        generate_entities(mapdb=mapdb,
                          entity_type="forest",
                          probability=0.50,
                          additional_entity_data={"control": "nobody",
                                                  "hp": 100},
                          size=25,
                          every=5)
    return mapdb, usersdb


if __name__ == "__main__":
    init_databases()
    mapdb, usersdb = initialize_map_and_users()

    actions = backend.TileActions()
    descriptions = backend.Descriptions()

    turn_engine = TurnEngine(usersdb, mapdb)  # reference to memory dict will be added here
    turn_engine.start()

    try:
        asyncio.run(main())
    finally:
        print("Application has shut down.")

