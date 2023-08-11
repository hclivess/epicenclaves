python3.10 -m venv ee_venv
cd ee
source ee_venv/bin/activate
pip install --upgrade pip
pip install tornado Pillow requests
python enclaves.py