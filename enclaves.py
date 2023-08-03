import asyncio
import json
import os.path
from backend import exists_user, add_user, check_users_db, login_validate, cookie_get, create_user_file, load_user_file, \
    on_tile, load_files, build, update_user_file, hashify, occupied_by, has_item, generate_entities, has_ap
import tornado.ioloop
import tornado.web
import webbrowser

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

            file = load_user_file(user)
            occupied = on_tile(file["x_pos"], file["y_pos"])

            if file["action_points"] < 1:
                message = f"You have action points left for this turn"

            self.render("templates/user_panel.html",
                        user=user,
                        file=load_user_file(user),
                        message=message,
                        on_tile=occupied)


class LogoutHandler(BaseHandler):
    def get(self, data):
        self.clear_all_cookies()
        self.redirect("/")


class MapHandler(BaseHandler):
    def get(self):
        data = json.dumps(load_files())
        print(data)
        self.render("templates/map.html",
                    data=data,
                    ensure_ascii=False)


class BuildHandler(BaseHandler):
    def get(self, data):
        entity = self.get_argument("entity")
        name = self.get_argument("name")
        user = tornado.escape.xhtml_escape(self.current_user)

        file = load_user_file(user)
        occupied = on_tile(file["x_pos"], file["y_pos"])

        if not occupied:
            build(entity=entity,
                  name=name,
                  user=user,
                  file=file)

            message = f"Successfully built {entity}"
        else:
            message = "Cannot build here"

        file = load_user_file(user)
        occupied = on_tile(file["x_pos"], file["y_pos"])

        self.render("templates/user_panel.html",
                    user=user,
                    file=load_user_file(user),
                    message=message,
                    on_tile=occupied)


class MoveHandler(BaseHandler):
    def get(self, data):
        target = self.get_argument("target", default="home")
        entry = self.get_argument("direction")
        user = tornado.escape.xhtml_escape(self.current_user)

        def update_user_file(user, key, updated_value):
            file_path = f"users/{hashify(user)}.json"
            with open(file_path, "r") as infile:
                file = json.load(infile)
            file[key] = updated_value
            with open(file_path, "w") as outfile:
                json.dump(file, outfile, indent=2)

        def move(user, direction, axis_key, axis_limit):
            file = load_user_file(user)
            new_pos = file[axis_key] + direction

            # Check if the action points are more than 0 before allowing movement
            if file["action_points"] > 0 and 1 <= new_pos <= axis_limit:
                update_user_file(user, axis_key, new_pos)
                new_ap = file["action_points"] - 1
                update_user_file(user, "action_points", new_ap)
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
                        data=json.dumps(load_files()),
                        message=message)
        else:
            file = load_user_file(user)
            occupied = on_tile(file["x_pos"], file["y_pos"])

            self.render("templates/user_panel.html",
                        user=user,
                        file=load_user_file(user),
                        message=message,
                        on_tile=occupied)


class ChopHandler(BaseHandler):
    def get(self):
        user = tornado.escape.xhtml_escape(self.current_user)
        file = load_user_file(user)
        proper_tile = occupied_by(file["x_pos"], file["y_pos"], what="forest")
        item = "axe"

        if not has_item(user, item):
            message = f"You have no {item} at hand"

        elif proper_tile:
            new_wood = file["resources"]["wood"] + 1
            new_ap = file["action_points"] - 1

            updated_values = {
                "resources": {"wood": new_wood},
                "action_points": new_ap
            }

            update_user_file(user, updated_values)
            message = "Chopping successful"

        else:
            message = "Not on a forest tile"

        file = load_user_file(user)
        occupied = on_tile(file["x_pos"], file["y_pos"])

        self.render("templates/user_panel.html",
                    user=user,
                    file=load_user_file(user),
                    message=message,
                    on_tile=occupied)


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

            file = load_user_file(user)
            occupied = on_tile(file["x_pos"], file["y_pos"])

            self.render("templates/user_panel.html",
                        user=user,
                        file=load_user_file(user),
                        message=message,
                        on_tile=occupied)
        else:
            self.render("templates/notfound.html")


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/login(.*)", LoginHandler),
        (r"/logout(.*)", LogoutHandler),
        (r"/move(.*)", MoveHandler),
        (r"/chop", ChopHandler),
        (r"/map", MapHandler),
        (r"/build(.*)", BuildHandler),
        (r"/assets/(.*)", tornado.web.StaticFileHandler, {"path": "assets"}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": "img"}),
        (r'/(favicon.ico)', tornado.web.StaticFileHandler, {"path": "graphics"}),
    ])


async def main():
    app = make_app()
    port = 8888
    app.listen(port)
    app.settings["cookie_secret"] = cookie_get()
    check_users_db()
    webbrowser.open(f"http://127.0.0.1:{port}")

    if not os.path.exists("environment"):
        os.mkdir("environment")

    generate_entities(entity_type="forest",
                      probability=0.25,
                      additional_entity_data={"actions": ["chop"]})

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
    # If you want to add a test user after starting the server, you can call add_user here
    # add_user("testuser", "testpass")
