import os
import re
import codecs

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


setup(
    name='model-parameter-sensitivity-backend',
    version=find_version('src', 'mps_server', '__init__.py'),
    packages=['mps_server'],
    package_dir={'': 'src'},
    url='https://github.com/hsorby/model-parameter-sensitivity-flask',
    license='Apache 2.0',
    author='Hugh Sorby',
    author_email='h.sorby@auckland.ac.nz',
    description='A Flask backend for the model-parameter-sensitivity Vue frontend.',
    install_requires=['Flask', 'Flask-Cors', 'gunicorn', 'pyjwt', 'cryptography', 'libcellml', 'FileLock', 'psutil'],
    entry_points={
        'console_scripts': ['mps-serve=mps_server.run_server:main'],
    }
)
