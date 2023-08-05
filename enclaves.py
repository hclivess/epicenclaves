import asyncio
import json
import os.path
import webbrowser

import tornado.ioloop
import tornado.web
import tornado.escape

import backend
from backend import cookie_get, tile_occupied, build, occupied_by, generate_entities
from sqlite import create_map_table, has_item, update_map_data, create_user_file, load_user_data, login_validate, \
    update_user_data, remove_construction, add_user, exists_user, load_all_map_data, check_users_db

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

            file = load_user_data(user)
            print("file", file)  # debug
            occupied = tile_occupied(file["x_pos"], file["y_pos"])
            print("occupied", occupied)  # debug

            if file["action_points"] < 1:
                message = f"You have action points left for this turn"

            self.render("templates/user_panel.html",
                        user=user,
                        file=file,
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

        data = json.dumps(load_all_map_data())
        print("data", data)  # debug
        self.render("templates/map.html",
                    data=data,
                    ensure_ascii=False)


class BuildHandler(BaseHandler):
    def get(self, data):
        entity = self.get_argument("entity")
        name = self.get_argument("name")
        user = tornado.escape.xhtml_escape(self.current_user)

        user_data = load_user_data(user)
        occupied = tile_occupied(user_data["x_pos"], user_data["y_pos"])

        if occupied["type"] == "empty":
            message = "Building procedure not yet defined"

            if entity == "house":
                if user_data["wood"] >= 50:
                    update_user_data(user=user,
                                     updated_values={"pop_lim": user_data["pop_lim"] + 10,
                                                     "wood": user_data["wood"] - 50})
                    build(entity=entity,
                          name=name,
                          user=user,
                          user_data=user_data)

                    message = f"Successfully built {entity}"
                else:
                    message = f"Not enough wood to build {entity}"

            elif entity == "inn":
                if user_data["wood"] >= 50:
                    update_user_data(user=user,
                                     updated_values={"pop_lim": user_data["pop_lim"] + 10,
                                                     "wood": user_data["wood"] - 50})
                    build(entity=entity,
                          name=name,
                          user=user,
                          user_data=user_data)

                    message = f"Successfully built {entity}"
                else:
                    message = f"Not enough wood to build {entity}"

        else:
            message = "Cannot build here"

        user_data = load_user_data(user)
        occupied = tile_occupied(user_data["x_pos"], user_data["y_pos"])

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

        def move(user, direction, axis_key, axis_limit):
            file = load_user_data(user)
            new_pos = file[axis_key] + direction

            # Check if the action points are more than 0 before allowing movement
            if file["action_points"] > 0 and 1 <= new_pos <= axis_limit:
                # Update both the position and the action points in one go
                update_user_data(user, {axis_key: new_pos, "action_points": file["action_points"] - 1})
                return True
            return False

        if entry == "left":
            moved = move(user, -1, "x_pos", max_size)
        elif entry == "right":
            moved = move(user, 1, "x_pos", max_size)
        elif entry == "down":
            moved = move(user, 1, "y_pos", max_size)
        elif entry == "up":
            moved = move(user, -1, "y_pos", max_size)
        else:
            moved = False
        message = "Moved" if moved else "Moved out of bounds or no action points left"

        if target == "map":

            self.render("templates/map.html",
                        user=user,
                        data=json.dumps(load_all_map_data()),
                        message=message)
        else:
            file = load_user_data(user)
            occupied = tile_occupied(file["x_pos"], file["y_pos"])

            self.render("templates/user_panel.html",
                        user=user,
                        file=file,
                        message=message,
                        on_tile=occupied,
                        actions=actions,
                        descriptions=descriptions)


class RestHandler(BaseHandler):
    def get(self, parameters):
        user = tornado.escape.xhtml_escape(self.current_user)
        file = load_user_data(user)
        hours = self.get_argument("hours", default="1")

        proper_tile = occupied_by(file["x_pos"], file["y_pos"], what="inn")

        if proper_tile and file["action_points"] > 0 and file["hp"] < 99:
            new_hp = file["hp"] + int(hours)
            new_ap = file["action_points"] - int(hours)
            if new_hp > 100:
                new_hp = 100

            update_user_data(user=user, updated_values={"hp": new_hp})
            update_user_data(user=user, updated_values={"action_points": new_ap})

            message = "You feel more rested"

        elif file["hp"] > 99:
            message = "You are already fully rested"

        elif not proper_tile:
            message = "You cannot rest here, inn required"

        else:
            message = "Out of action points to rest"

        file = load_user_data(user)
        occupied = tile_occupied(file["x_pos"], file["y_pos"])

        self.render("templates/user_panel.html",
                    user=user,
                    file=file,
                    message=message,
                    on_tile=occupied,
                    actions=actions,
                    descriptions=descriptions)


class ConquerHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        file = load_user_data(user)
        this_tile = tile_occupied(file["x_pos"], file["y_pos"])

        owner = this_tile["control"]

        if owner == user:
            message = "You already own this tile"

        elif this_tile["type"] != "empty" and file["action_points"] > 0:
            remove_construction(owner, {"x_pos": file["x_pos"], "y_pos": file["y_pos"]})

            update_user_data(user=user,
                             updated_values={"construction": this_tile, "action_points": file["action_points"] - 1})

            update_map_data({"x_pos": file["x_pos"], "y_pos": file["y_pos"], "data": {"control": user}})
            message = "Takeover successful"
        else:
            message = "Cannot acquire an empty tile"

        file = load_user_data(user)
        occupied = tile_occupied(file["x_pos"], file["y_pos"])

        self.render("templates/user_panel.html",
                    user=user,
                    file=file,
                    message=message,
                    on_tile=occupied,
                    actions=actions,
                    descriptions=descriptions)


class ChopHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        file = load_user_data(user)
        proper_tile = occupied_by(file["x_pos"], file["y_pos"], what="forest")
        item = "axe"

        if not has_item(user, item):
            message = f"You have no {item} at hand"

        elif proper_tile and file["action_points"] > 0:
            new_wood = file["wood"] + 1
            new_ap = file["action_points"] - 1

            update_user_data(user=user, updated_values={"wood": new_wood})
            update_user_data(user=user, updated_values={"action_points": new_ap})

            message = "Chopping successful"

        elif not proper_tile:
            message = "Not on a forest tile"

        else:
            message = "Out of action points to chop"

        file = load_user_data(user)
        occupied = tile_occupied(file["x_pos"], file["y_pos"])

        self.render("templates/user_panel.html",
                    user=user,
                    file=file,
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
            create_user_file(user)
        if login_validate(user, password):
            self.set_secure_cookie("user", self.get_argument("name"), expires_days=84)

            message = f"Welcome, {user}!"

            file = load_user_data(user)
            occupied = tile_occupied(file["x_pos"], file["y_pos"])

            self.render("templates/user_panel.html",
                        user=user,
                        file=file,
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

    await asyncio.Event().wait()


if __name__ == "__main__":
    if not os.path.exists("db/map_data.db"):
        create_map_table()

        generate_entities(entity_type="forest",
                          probability=0.25,
                          additional_entity_data={"control": "nobody",
                                                  "hp": 100},
                          size=101,
                          every=5)

    actions = backend.Actions()
    descriptions = backend.Descriptions()
    asyncio.run(main())
    # If you want to add a test user after starting the server, you can call add_user here
    # add_user("testuser", "testpass")
