import os
import subprocess
import tempfile


def run(*args, **kwargs):
    run_args = ['--reload', '--preload']
    run_args.extend(['-w', '1'])
    run_args.append('mps_server.main:app')
    run_args.extend(['--bind', 'localhost:6060'])
    subprocess.run(['gunicorn'] + run_args)


def setup():
    # Putting sticky tape over the safety light.
    # os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
    simulation_data_dir = os.environ.get('SIMULATION_DATA_DIR', os.path.join(tempfile.gettempdir(), 'mps_simulation_data'))
    if not os.path.isdir(simulation_data_dir):
        os.mkdir(simulation_data_dir)


def main():
    setup()
    run()


if __name__ == "__main__":
    main()
