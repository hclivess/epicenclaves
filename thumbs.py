import os
from PIL import Image


def convert_png_to_jpg_thumbnail(source_folder, target_folder, size=(150, 150)):
    # Create the target folder if it doesn't exist
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    # Loop through all files in the source folder
    for filename in os.listdir(source_folder):
        if filename.lower().endswith('.png'):
            # Generate the new filename
            new_filename = os.path.splitext(filename)[0] + '.jpg'
            target_path = os.path.join(target_folder, new_filename)

            # Skip if the file already exists
            if os.path.exists(target_path):
                print(f"Skipping {filename} - thumbnail already exists")
                continue

            # Open the image
            with Image.open(os.path.join(source_folder, filename)) as img:
                # Convert to RGB (in case of transparency)
                img = img.convert('RGB')

                # Resize the image
                img.thumbnail(size)

                # Save the image as JPG
                img.save(target_path, 'JPEG', quality=85, optimize=True)

                print(f"Converted {filename} to {new_filename}")

# Usage
source_folder = 'img/assets'  # Current directory
target_folder = 'img/assets/thumbs'  # Subfolder named 'thumbs'
convert_png_to_jpg_thumbnail(source_folder, target_folder)