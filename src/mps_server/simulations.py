import json
import multiprocessing
import os
import pickle
import subprocess
import uuid

import multiprocessing as mp
from time import sleep, time

import psutil as psutil
from filelock import FileLock

# import argparse
# import json
# import math
# import os

# from cellsolvertools.generate_code import ModelGenerationError, return_generated_python_code
# from cellsolvertools.utilities import import_code
# import pandas as pd

from cellsolvertools.generate_code import generate_c_code
from cellsolvertools.common import construct_application_config
from cellsolvertools.investigate_output_data import extract_result_for_config

from mps_server.config import Config
from mps_server.management import get_model_file

SIMULATIONS_DIR_NAME = "simulations"
SIMULATIONS_OUTPUT_DIR = "output"


def _simulations_dir():
    return os.path.join(Config.SIMULATION_DATA_DIR, SIMULATIONS_DIR_NAME)


def _output_dir():
    return os.path.join(Config.SIMULATION_RUN_DIR, SIMULATIONS_OUTPUT_DIR)


def _shared_control_file(name, lock=False):
    return os.path.join(Config.SIMULATION_DATA_DIR, f"{name}.lock" if lock else name)


def _running(lock=False):
    return _shared_control_file('running.txt', lock)


def _stopping(lock=False):
    return _shared_control_file('stopping.txt', lock)


def _is_simulation_file(filename):
    if filename.endswith('.lock'):
        return False

    return os.path.isfile(filename)


def _convert_solver_config(in_config):
    return {
        "MaximumNumberOfSteps": in_config["maxNumSteps"],
        "RelativeTolerance": in_config["relativeTolerance"],
        "AbsoluteTolerance": in_config["absoluteTolerance"],
        "IntegrationMethod": in_config["intMethod"],
        "IterationType": in_config["iterationType"],
        "InterpolateSolution": in_config["interpolate"],
        "LinearSolver": in_config["linearSolver"],
        "MaximumStep": float(in_config["maxStep"]),
    }


def _convert_simulation_config(in_config):
    return {
        "StartingPoint": float(in_config["timeStart"]),
        "EndingPoint": float(in_config["timeStop"]),
        "PointInterval": float(in_config["pointInterval"]),
    }


def simulation_manager():
    simulations_dir = _simulations_dir()
    if not os.path.isdir(simulations_dir):
        os.mkdir(simulations_dir)

    sleep(0.2)
    pid = os.getpid()
    all_simulations_run = False
    start_time = time()
    while not all_simulations_run:
        simulation = None
        files = os.listdir(simulations_dir)
        full_path_files = [os.path.join(simulations_dir, f) for f in files if _is_simulation_file(os.path.join(simulations_dir, f))]
        full_path_files.sort(key=lambda x: os.path.getmtime(x))
        if (time() - start_time) > 2:
            print('alive', pid)
            start_time = time()
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

        if simulation is None:
            all_simulations_run = True
        else:
            simulation_obj = simulation['obj']
            simulation_src = simulation['src']

            simulation_obj.set_status(Status.RUNNING)
            lock = FileLock(f"{simulation_src}.lock")
            with lock:
                with open(simulation_src, 'wb') as f:
                    pickle.dump(simulation_obj, f)

            model_file = get_model_file(Config.CLIENT_WORKING_DIR, simulation_obj.user_id(), simulation_obj.model())
            settings = simulation_obj.settings()
            solver_config = settings['solver']
            simulation_config = settings['simulation']
            code_generation_config = {'external_variables': simulation_obj.uncertainties()}
            config = {
                'uncertainties': simulation_obj.uncertainties(),
                'solver': _convert_solver_config(solver_config),
                'simulation': _convert_simulation_config(simulation_config),
                'workers': multiprocessing.cpu_count(),
                'num_trials': simulation_config['numberTrials'],
                'application': construct_application_config(Config.SIMULATION_RUN_DIR, Config.SUNDIALS_CMAKE_CONFIG_DIR)
            }

            generate_c_code(model_file, os.path.join(Config.SIMULATION_RUN_DIR, 'build-simple-sundials-solver', 'src'), code_generation_config)

            # Save config to simulation run dir
            simulation_run_config = os.path.join(Config.SIMULATION_RUN_DIR, 'simulation-run.config')
            with open(simulation_run_config, 'w') as f:
                f.write(json.dumps(config))

            simulation_outputs_config = os.path.join(Config.SIMULATION_RUN_DIR, 'simulation-outputs.config')
            with open(simulation_outputs_config, 'w') as f:
                f.write(json.dumps(simulation_obj.outputs()))

            result = subprocess.run(["simple-sundials-solver-manager", "--simulation-config", simulation_run_config])
            if result.returncode != 0:
                print('**********************************************')
                print("something went very wrong.")

            # Cannot run this from a forked process?
            # entry_point(config)

            simulation_obj.set_status(Status.FINISHED)
            lock = FileLock(f"{simulation_src}.lock")
            with lock:
                with open(simulation_src, 'wb') as f:
                    pickle.dump(simulation_obj, f)

    print('dead', pid)


def _running_manager_pid():
    with open(_running()) as f:
        content = f.read()

    return int(content)


def _is_running_pid_active():
    # Try reading from file to see if pid is alive
    if not os.path.isfile(_running()):
        return False

    return psutil.pid_exists(_running_manager_pid())


def _is_running_pid_zombie():
    try:
        p = psutil.Process(_running_manager_pid())
        print(p.status == psutil.STATUS_ZOMBIE)
        print(p.ppid(), os.getpid())

    except psutil.NoSuchProcess:
        return False

    return p.status == psutil.STATUS_ZOMBIE


def start_simulation_manager_process():
    print('===============================')
    print('pid stuff')
    print(os.getpid())
    print(os.getppid())
    print(mp.current_process())
    print(mp.parent_process())
    print(mp.active_children())
    lock = FileLock(_running(lock=True))
    print('go time')
    try:
        with lock.acquire(5):
            print('lock acquired', _running_manager_pid(), _is_running_pid_active())
            simulation_process = None
            if _is_running_pid_zombie():
                print('Zombie manager process')
            if not _is_running_pid_active():
                print('running pid is not active')
                simulation_process = mp.Process(target=simulation_manager)
                simulation_process.start()
                pid = simulation_process.pid
                print('parent', os.getpid())
                print('child pid', pid)
                if pid is not None:
                    with open(_running(), 'w') as f:
                        f.write(str(pid))

            print('simulation process', os.getpid(), simulation_process)
    except TimeoutError:
        print('**********************************************')
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
    PENDING = 'pending'
    RUNNING = 'running'
    FINISHED = 'finished'


class SimulationRun(object):

    def __init__(self, properties):
        self._user_id = properties['user_id']
        self._id = str(uuid.uuid4())
        self._status = Status.PENDING
        self._model = properties['model']
        self._distributions = properties['uncertainties']
        self._settings = properties['settings']
        self._outputs = properties['outputs']

    def id(self):
        return self._id

    def user_id(self):
        return self._user_id

    def reference(self):
        return self._id

    def status(self):
        return self._status

    def set_status(self, status):
        self._status = status

    def title(self):
        return os.path.splitext(self._model)[0]

    def model(self):
        return self._model

    def uncertainties(self):
        values = {}
        for distribution_dict in self._distributions:
            values[distribution_dict['id']] = _convert_distribution_definition(distribution_dict['distribution'])

        return values

    def settings(self):
        return self._settings

    def outputs(self):
        return self._outputs

    def __str__(self):
        return json.dumps(self._outputs)


def _convert_distribution_definition(distribution):
    parameters = {}
    for index, v in enumerate(distribution['parameters']['values']):
        parameters[f"p{index + 1}"] = v

    return {
        'distribution': distribution['name'],
        **parameters
    }


def get_simulation_result(reference):
    result = None
    lock = FileLock(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, reference), lock=True))
    with lock:
        try:
            with open(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, reference)), 'rb') as f:
                simulation_run = pickle.load(f)

            outputs = simulation_run.outputs()
            model_file = get_model_file(Config.CLIENT_WORKING_DIR, simulation_run.user_id(), simulation_run.model())
            data = extract_result_for_config(model_file, outputs, _output_dir())
            result = data.to_dict(orient='list')

        except OSError:
            pass

    return result


def get_simulation_info(reference):
    info = {}
    # reference = simulation['reference']
    lock = FileLock(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, reference), lock=True))
    with lock:
        try:
            with open(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, reference)), 'rb') as f:
                simulation_run = pickle.load(f)

            info['status'] = simulation_run.status()
            info['reference'] = reference
            info['title'] = simulation_run.title()

        except OSError:
            pass

    return info


def queue_simulation(simulation_data):
    start_simulation_manager_process()
    simulation_run = SimulationRun(simulation_data)
    lock = FileLock(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, simulation_run.id()), lock=True))
    with lock:
        with open(_shared_control_file(os.path.join(SIMULATIONS_DIR_NAME, simulation_run.id())), 'wb') as f:
            pickle.dump(simulation_run, f)

    return {
        "reference": simulation_run.reference(),
        "status": simulation_run.status(),
        "title": simulation_run.title(),
    }
