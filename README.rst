Model Parameter Sensitivity Backend
===================================

Install the backend with::

 pip install -e .

Set environment variables::

 CLIENT_ORIGIN_URL = os.environ.get("MPS_CLIENT_ORIGIN_URL", "http://localhost:4040")
 CLIENT_WORKING_DIR = os.environ.get('MPS_CLIENT_WORKING_DIR')
 AUTH0_DOMAIN = os.environ.get('MPS_AUTH0_DOMAIN', "auth0.domain")
 AUTH0_SECRET = os.environ.get('MPS_AUTH0_SECRET', 'mps-secret-value')
 SIMULATION_DATA_DIR = os.environ.get('SIMULATION_DATA_DIR', os.path.join(tempfile.gettempdir(), 'mps_simulation_data'))

`MPS_CLIENT_WORKING_DIR`, `MPS_AUTH0_DOMAIN`, `MPS_AUTH0_SECRET` must be set.
`MPS_CLIENT_ORIGIN_URL` has a default value of `http://localhost:4040`.

Run
---

In a file called *.env* set the required environment variables as key/value pairs.
Then run the command to setup the environment for the server::

 export $(grep -v '^#' .env | xargs)

Now, to run the server you can use the command::

 mps-serve

This command will start *Gunicorn* running the *Flask* application.