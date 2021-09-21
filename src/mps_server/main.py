import os

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from mps_server.auth0 import requires_auth, AuthError
from mps_server.config import Config
from mps_server.management import store_cellml_file, list_model_files, model_parameter_information

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


@app.route("/api/v1/parameter-info")
@requires_auth
def parameter_info():
    filename = request.args.get('filename')

    parameter_information = model_parameter_information(Config.CLIENT_WORKING_DIR, session['user_id'], filename)
    return jsonify({'parameter_information': parameter_information})


@app.route("/api/v1/user-models")
@requires_auth
def user_models():
    model_files = list_model_files(session['user_id'], Config.CLIENT_WORKING_DIR)
    return jsonify({'model_files': model_files})


@app.route("/api/v1/upload", methods=['POST'])
@requires_auth
def upload():
    content = request.files.to_dict()
    if len(content) == 1 and 'file' in content:
        file_uploaded = content['file']
        result = store_cellml_file({'id': session['user_id']}, {'base_dir': Config.CLIENT_WORKING_DIR, 'file': file_uploaded})
        if result == 0:
            return jsonify({"message": "File upload success"})

    response = jsonify({'message': 'File upload error'})
    response.status_code = 400
    return response
