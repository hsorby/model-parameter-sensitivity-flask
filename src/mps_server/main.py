import os

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from mps_server.auth0 import requires_auth, AuthError
from mps_server.config import Config
from mps_server.management import store_cellml_file, list_model_files, model_parameter_information, store_parameter_uncertainties_file, \
    parameter_uncertainty_distribution_information, list_uncertainty_definitions_files, list_output_parameter_files, output_parameters_information, store_output_parameters_file
from mps_server.simulations import queue_simulation

app = Flask(__name__)
app.secret_key = os.environ.get('MPS_SECRET_KEY', 'secret-key-value')

CORS(app)


@app.errorhandler(AuthError)
def handle_auth_error(ex: AuthError):
    """
    serializes the given AuthError as json and sets the response status code accordingly.
    :param ex: an auth error
    :return: json serialized ex response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


@app.route("/api/v1/messages/public-message")
def public_message():
    return {"message": "Hello, the public API is working!"}


@app.route("/api/v1/messages/protected-message")
@requires_auth
def protected_message():
    return {"message": "Hello, the protected API is working!"}


@app.route("/api/v1/info/model-parameters")
@requires_auth
def parameter_info():
    filename = request.args.get('filename')

    parameter_information = model_parameter_information(Config.CLIENT_WORKING_DIR, session['user_id'], filename)
    return jsonify({'parameter_information': parameter_information})


@app.route("/api/v1/info/parameter-uncertainty-distributions")
@requires_auth
def parameter_uncertainty_distribution_info():
    filename = request.args.get('filename')
    associated_model = request.args.get('model')

    parameter_uncertainty_information = parameter_uncertainty_distribution_information(Config.CLIENT_WORKING_DIR, session['user_id'], associated_model, filename)
    return jsonify({'parameter_uncertainty_information': parameter_uncertainty_information})


@app.route("/api/v1/info/output-parameters")
@requires_auth
def output_parameters_info():
    filename = request.args.get('filename')
    associated_model = request.args.get('model')

    output_information = output_parameters_information(Config.CLIENT_WORKING_DIR, session['user_id'], associated_model, filename)
    return jsonify({'output_parameters_information': output_information})


@app.route("/api/v1/user/list-models")
@requires_auth
def user_models():
    model_files = list_model_files(Config.CLIENT_WORKING_DIR, session['user_id'])
    return jsonify({'model_files': model_files})


@app.route("/api/v1/user/list-parameter-uncertainties")
@requires_auth
def user_uncertainty_definitions():
    associated_model = request.args.get('model')
    model_files = list_uncertainty_definitions_files(Config.CLIENT_WORKING_DIR, session['user_id'], associated_model)
    return jsonify({'uncertainty_definitions': model_files})


@app.route("/api/v1/user/list-output-parameters")
@requires_auth
def user_output_parameters():
    associated_model = request.args.get('model')
    model_files = list_output_parameter_files(Config.CLIENT_WORKING_DIR, session['user_id'], associated_model)
    return jsonify({'output_parameters': model_files})


@app.route("/api/v1/upload", methods=['POST'])
@requires_auth
def upload():
    content = request.files.to_dict()
    result = -1
    if len(content) == 1 and 'file' in content:
        file_uploaded = content['file']
        result = store_cellml_file({'id': session['user_id']}, {'base_dir': Config.CLIENT_WORKING_DIR, 'file': file_uploaded})
        if result == 0:
            return jsonify({"message": "File upload success"})

    message = 'Something went wrong with upload'
    if result == 1:
        message = 'File upload error'
    elif result == 2:
        message = 'Uploaded file is not CellML 2.0'

    response = jsonify({'message': message})
    response.status_code = 400
    return response


@app.route("/api/v1/store/parameter-uncertainties", methods=['POST'])
@requires_auth
def store_uncertainty_definitions():
    filename = request.args.get('filename')
    model = request.args.get('model')

    result = store_parameter_uncertainties_file(
        {
            'base_dir': Config.CLIENT_WORKING_DIR,
            'user_id': session['user_id'],
            'filename': filename,
            'associated_model': model
        }, request.json)
    if result == 0:
        return jsonify({'message': 'Uncertainty definitions saved successfully'})

    response = jsonify({'message': 'An error occurred while trying to save uncertainty definitions'})
    response.status_code = 400
    return response


@app.route("/api/v1/store/output-parameters", methods=['POST'])
@requires_auth
def store_output_parameters():
    filename = request.args.get('filename')
    model = request.args.get('model')

    result = store_output_parameters_file(
        {
            'base_dir': Config.CLIENT_WORKING_DIR,
            'user_id': session['user_id'],
            'filename': filename,
            'associated_model': model
        }, request.json)
    if result == 0:
        return jsonify({'message': 'Output parameters saved successfully'})

    response = jsonify({'message': 'An error occurred while trying to save output parameters'})
    response.status_code = 400
    return response


@app.route("/api/v1/simulation/submit", methods=['POST'])
@requires_auth
def submit_simulation():
    simulation_data = request.json
    simulation_data['user_id'] = session['user_id']
    result = queue_simulation(simulation_data)
    if result is not None:
        return jsonify({'message': 'Job submitted successfully', **result})

    response = jsonify({'message': 'An error occurred while trying to submit job'})
    response.status_code = 400
    return response
