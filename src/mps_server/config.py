import os
import tempfile


class Config(object):
    AUTH0_AUDIENCE = "https://libcellml.org/mps/api"
    AUTH0_DOMAIN = os.environ.get('MPS_AUTH0_DOMAIN')
    AUTH0_SECRET = os.environ.get('MPS_AUTH0_SECRET')
    CLIENT_ORIGIN_URL = os.environ.get("MPS_CLIENT_ORIGIN_URL", "http://localhost:4040")
    CLIENT_WORKING_DIR = os.environ.get('MPS_CLIENT_WORKING_DIR')
    SIMULATION_DATA_DIR = os.environ.get('SIMULATION_DATA_DIR', os.path.join(tempfile.gettempdir(), 'mps_simulation_data'))
