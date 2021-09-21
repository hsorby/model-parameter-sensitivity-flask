import os

from cellsolvertools.utilities import is_cellml_file
from mps_server.libcellml_tools import get_parameters_from_model


def _normalise_to_path(data_in):
    """Normalise the 'data_in' so it can be used as part of a path."""
    return data_in.replace('|', '_')


def _create_output_dir(required_dir):
    """Create an output directory at the given location if one does not yet exist there."""
    if not os.path.isdir(required_dir):
        os.makedirs(required_dir)


def list_model_files(user_id, base_dir):
    user_path = _normalise_to_path(user_id)
    files_dir = os.path.join(base_dir, user_path, 'model_files')
    listing = os.listdir(files_dir)
    return listing


def store_cellml_file(user_info, file_info):
    user_path = _normalise_to_path(user_info['id'])
    file = file_info['file']
    output_dir = os.path.join(file_info['base_dir'], user_path)
    _create_output_dir(output_dir)
    target_location = os.path.join(output_dir, 'model_files', file.filename)
    if os.path.isfile(target_location):
        return 0
    else:
        try:
            with open(target_location, 'wb') as fb:
                file.save(fb)

            if not is_cellml_file(target_location):
                os.remove(target_location)
                return 1
        except OSError:
            return 1

    return 0


def model_parameter_information(base_dir, user_id, model_filename):
    user_dir = _normalise_to_path(user_id)
    target_location = os.path.join(base_dir, user_dir, 'model_files', model_filename)
    return get_parameters_from_model(target_location)
