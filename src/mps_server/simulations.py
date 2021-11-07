import atexit
import json
import os
import pickle
import uuid

import multiprocessing as mp
from queue import Empty
from time import sleep

import psutil as psutil
from filelock import FileLock

from mps_server.common import normalise_for_use_as_path
from mps_server.config import Config

SIMULATION_DATA_DIR = Config.SIMULATION_DATA_DIR
SIMULATIONS_DIR_NAME = "simulations"
# simulation_queue = mp.Queue()
# simulation_progress_queue = mp.Queue()
# manager_quit_queue = mp.Queue()

simulation_process = None


def _simulations_dir():
    return os.path.join(SIMULATION_DATA_DIR, SIMULATIONS_DIR_NAME)


def _shared_control_file(name, lock=False):
    return os.path.join(SIMULATION_DATA_DIR, f"{name}.lock" if lock else name)


def _running(lock=False):
    return _shared_control_file('running.txt', lock)


def _stopping(lock=False):
    return _shared_control_file('stopping.txt', lock)


def run_simulation():
    import time
    count = 0
    while count < 50:
        count += 1
        print('simulation running:', count, os.getpid())
        time.sleep(0.25)


def _is_simulation_file(filename):
    if filename.endswith('.lock'):
        return False

    return os.path.isfile(filename)


def simulation_manager():
    print('simulation manager kicking off:', os.getpid())

    simulations_dir = _simulations_dir()
    if not os.path.isdir(simulations_dir):
        os.mkdir(simulations_dir)

    sleep(0.2)
    files = os.listdir(simulations_dir)
    full_path_files = [os.path.join(simulations_dir, f) for f in files if _is_simulation_file(os.path.join(simulations_dir, f))]
    full_path_files.sort(key=lambda x: os.path.getmtime(x))
    simulation = None
    for full_path_file in full_path_files:
        lock = FileLock(f"{full_path_file}.lock")
        with lock:
            with open(full_path_file, 'rb') as f:
                simulation_run = pickle.load(f)

            if simulation_run.status() == Status.PENDING:
                simulation = {
                    'obj': simulation_run,
                    'src': full_path_file,
                }
                break

    if simulation is not None:
        simulation_obj = simulation['obj']
        simulation_src = simulation['src']

        print('process simulation:', simulation_obj.id())
        print('location:', simulation_src)
        simulation_obj.set_status(Status.RUNNING)
        lock = FileLock(f"{simulation_src}.lock")
        with lock:
            with open(simulation_src, 'wb') as f:
                pickle.dump(simulation_obj, f)

        print('running simulation ...', simulation_obj.title())
        print('simulation processed.')

        simulation_obj.set_status(Status.FINISHED)
        lock = FileLock(f"{simulation_src}.lock")
        with lock:
            with open(simulation_src, 'wb') as f:
                pickle.dump(simulation_obj, f)


def _running_manager_pid():
    with open(_running()) as f:
        content = f.read()

    return int(content)


def _is_file_pid_active():
    # Try reading from file to see if pid is alive
    if not os.path.isfile(_running()):
        return False

    return psutil.pid_exists(_running_manager_pid())


def start_simulation_manager_process():
    global simulation_process
    lock = FileLock(_running(lock=True))
    try:
        with lock.acquire(5):
            if not _is_file_pid_active():
                simulation_process = mp.Process(target=simulation_manager)
                simulation_process.start()
                pid = simulation_process.pid
                if pid is not None:
                    with open(_running(), 'w') as f:
                        f.write(str(pid))
    except TimeoutError:
        print('timed out ...')
        # Try reading from file to see if pid is alive
        with open(_running()) as f:
            content = f.read()

        if psutil.pid_exists(content):
            print('simulation process is already running do nothing.')
        else:
            print('lock file exists but the pid is not current.')
            print('can I remove lock file????')


def activate_simulation_runner():
    pass


class Status(object):
    PENDING = 0
    RUNNING = 1
    FINISHED = 2


class SimulationRun(object):

    def __init__(self, properties):
        self._id = normalise_for_use_as_path(properties['user_id'] + '.' + str(uuid.uuid4()))
        self._status = Status.PENDING
        self._model = properties['model']
        self._uncertainties = properties['uncertainties']
        self._settings = properties['settings']
        self._outputs = properties['outputs']

    def id(self):
        return self._id

    def reference(self):
        return self._id.split('_dot_')[1]

    def status(self):
        return self._status

    def set_status(self, status):
        self._status = status

    def title(self):
        return os.path.splitext(self._model)[0]

    def __str__(self):
        return json.dumps(self._outputs)


def queue_simulation(simulation_data):
    start_simulation_manager_process()
    simulation_run = SimulationRun(simulation_data)
    print('putting something in the simulation queue')
    # simulation_queue.put(simulation_run)
    lock = FileLock(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, simulation_run.id()), lock=True))
    with lock:
        with open(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, simulation_run.id())), 'wb') as f:
            pickle.dump(simulation_run, f)

    return {
        "reference": simulation_run.reference(),
        "status": simulation_run.status(),
        "title": simulation_run.title(),
    }


def process_queue():
    print('processing queue')
