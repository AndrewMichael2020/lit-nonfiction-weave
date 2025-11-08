setup:
pip install -r requirements.txt


lab:
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser


test:
pytest -q
