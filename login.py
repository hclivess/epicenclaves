import io
import os
from PIL import Image


def login(password, uploaded_file, auth_exists_user, auth_add_user, create_user, save_users_from_memory,
          save_map_from_memory, auth_login_validate, usersdb, mapdb, user, league="game"):
    profile_pic_path = "img/pps/default.png"

    if uploaded_file:
        uploaded_file = uploaded_file[0]
        if len(uploaded_file["body"]) > 500 * 1024:
            return "Profile picture size should be less than 500 KB!"

        file_extension = os.path.splitext(uploaded_file["filename"])[-1].lower()
        if file_extension not in [".jpg", ".jpeg", ".png", ".gif"]:
            return "Invalid file type!"

        try:
            Image.open(io.BytesIO(uploaded_file["body"]))
        except Exception as e:
            return f"Uploaded file is not a valid image: {e}!"

        save_dir = "img/pps/"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        save_path = f"img/pps/{user}{file_extension}"
        with open(save_path, "wb") as f:
            f.write(uploaded_file["body"])

        profile_pic_path = save_path

    if not auth_exists_user(user):
        auth_add_user(user, password)
        create_user(user_data_dict=usersdb, user=user, profile_pic=profile_pic_path, mapdb=mapdb, league=league)

    save_users_from_memory(usersdb, league=league)
    save_map_from_memory(mapdb, league=league)

    if auth_login_validate(user, password):
        return f"Welcome, {user}!"
    else:
        return "Wrong password"