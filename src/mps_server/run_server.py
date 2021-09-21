import subprocess


def run(*args, **kwargs):
    run_args = ['--reload']
    run_args.extend(['-w', '2'])
    run_args.append('mps_server.main:app')
    run_args.extend(['--bind', 'localhost:6060'])
    subprocess.run(['gunicorn'] + run_args)


def main():
    run()


if __name__ == "__main__":
    main()
