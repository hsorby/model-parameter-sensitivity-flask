import json
import os

from cellsolvertools.utilities import is_cellml_file
from mps_server.libcellml_tools import get_parameters_from_model


def _normalise_to_path(data_in):
    """Normalise the 'data_in' so it can be used as part of a path."""
    return data_in.replace('|', '_').replace('.', '_dot_')


def _create_output_dir(required_dir):
    """Create an output directory at the given location if one does not yet exist there."""
    if not os.path.isdir(required_dir):
        os.makedirs(required_dir)


def _model_files_dir(base_dir, user_id):
    user_path = _normalise_to_path(user_id)
    return os.path.join(base_dir, user_path, 'model_files')


def _output_parameter_files_dir(base_dir, user_id, associated_model):
    user_path = _normalise_to_path(user_id)
    model_path = _normalise_to_path(associated_model)
    return os.path.join(base_dir, user_path, 'output_parameter_files', model_path)


def _uncertainty_definitions_files_dir(base_dir, user_id, associated_model):
    user_path = _normalise_to_path(user_id)
    model_path = _normalise_to_path(associated_model)
    return os.path.join(base_dir, user_path, 'uncertainty_definition_files', model_path)


def list_uncertainty_definitions_files(base_dir, user_id, associated_model):
    files_dir = _uncertainty_definitions_files_dir(base_dir, user_id, associated_model)
    _create_output_dir(files_dir)
    return os.listdir(files_dir)


def list_output_parameter_files(base_dir, user_id, associated_model):
    files_dir = _output_parameter_files_dir(base_dir, user_id, associated_model)
    _create_output_dir(files_dir)
    return os.listdir(files_dir)


def list_model_files(base_dir, user_id):
    files_dir = _model_files_dir(base_dir, user_id)
    _create_output_dir(files_dir)
    return os.listdir(files_dir)


def store_output_parameters_file(file_info, data):
    output_dir = _output_parameter_files_dir(file_info['base_dir'], file_info['user_id'], file_info['associated_model'])
    target_location = os.path.join(output_dir, file_info['filename'])
    json_string = json.dumps(data)
    try:
        with open(target_location, 'w') as f:
            f.write(json_string)

    except OSError:
        return 1

    return 0


def store_parameter_uncertainties_file(file_info, data):
    output_dir = _uncertainty_definitions_files_dir(file_info['base_dir'], file_info['user_id'], file_info['associated_model'])
    target_location = os.path.join(output_dir, file_info['filename'])
    json_string = json.dumps(data)
    try:
        with open(target_location, 'w') as f:
            f.write(json_string)

    except OSError:
        return 1

    return 0


def store_cellml_file(user_info, file_info):
    file = file_info['file']
    output_dir = _model_files_dir(file_info['base_dir'], user_info['id'])
    target_location = os.path.join(output_dir, file.filename)
    test_location = target_location + '.test'
    try:
        with open(test_location, 'wb') as fb:
            file.save(fb)

        if is_cellml_file(test_location):
            os.rename(test_location, target_location)
        else:
            os.remove(test_location)
            return 2
    except OSError:
        return 1

    return 0


def model_parameter_information(base_dir, user_id, model_filename):
    target_location = os.path.join(_model_files_dir(base_dir, user_id), model_filename)
    return get_parameters_from_model(target_location)


def parameter_uncertainty_distribution_information(base_dir, user_id, associated_model, filename):
    file_dir = _uncertainty_definitions_files_dir(base_dir, user_id, associated_model)
    target_location = os.path.join(file_dir, filename)
    with open(target_location) as f:
        content = f.read()

    return json.loads(content)


def output_parameters_information(base_dir, user_id, associated_model, filename):
    file_dir = _output_parameter_files_dir(base_dir, user_id, associated_model)
    target_location = os.path.join(file_dir, filename)
    with open(target_location) as f:
        content = f.read()

    return json.loads(content)
