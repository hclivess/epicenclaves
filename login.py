import io

from PIL import Image


def login(password, uploaded_file, auth_exists_user, auth_add_user, create_user, save_users_from_memory,
          save_map_from_memory, auth_login_validate, get_user_data, get_tile_map, get_tile_users, actions, descriptions,
          usersdb, mapdb, user):
    profile_pic_path = "img/pps/default.png"

    if uploaded_file:
        uploaded_file = uploaded_file[0]
        if len(uploaded_file["body"]) > 50 * 1024:
            return "Profile picture size should be less than 50 KB!", None

        file_extension = os.path.splitext(uploaded_file["filename"])[-1].lower()
        if file_extension not in [".jpg", ".jpeg", ".png", ".gif"]:
            return "Invalid file type!", None

        try:
            Image.open(io.BytesIO(uploaded_file["body"]))
        except Exception as e:
            return f"Uploaded file is not a valid image: {e}!", None

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
        user_data = get_user_data(user, usersdb)
        on_tile_map = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)
        on_tile_users = get_tile_users(
            user_data["x_pos"], user_data["y_pos"], user, usersdb
        )
        return f"Welcome, {user}!", {
            'user': user,
            'file': user_data,
            'message': f"Welcome, {user}!",
            'on_tile_map': on_tile_map,
            'on_tile_users': on_tile_users,
            'actions': actions,
            'descriptions': descriptions,
        }
    else:
        return "Wrong password", None
