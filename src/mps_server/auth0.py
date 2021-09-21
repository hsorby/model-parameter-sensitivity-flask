import json
from urllib.request import urlopen

import jwt

from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm

from flask import request, session
from functools import wraps
from mps_server.config import Config


# Format error response and append status code.
class AuthError(Exception):
    """
    An AuthError is raised whenever the authentication failed.
    """
    def __init__(self, error, status_code):
        super().__init__()
        self.error = error
        self.status_code = status_code


def get_token_auth_header() -> str:
    """Obtains the access token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                         "description":
                             "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    if len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    if len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Authorization header must be"
                             " Bearer token"}, 401)

    token = parts[1]
    return token


def requires_auth(func):
    """Determines if the access token is valid
    """

    @wraps(func)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen("https://" + Config.AUTH0_DOMAIN + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as jwt_error:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Invalid header. "
                                 "Use an RS256 signed JWT Access Token"}, 401) from jwt_error
        if unverified_header["alg"] == "HS256":
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Invalid header. "
                                 "Use an RS256 signed JWT Access Token"}, 401)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if rsa_key:
            true_rsa_key = RSAAlgorithm.from_jwk(rsa_key)
            public_key_bytes = true_rsa_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)
            try:
                payload = jwt.decode(
                    token,
                    public_key_bytes,
                    algorithms='RS256',
                    audience=Config.AUTH0_AUDIENCE,
                    issuer="https://" + Config.AUTH0_DOMAIN + "/"
                )
            except jwt.ExpiredSignatureError as expired_sign_error:
                raise AuthError({"code": "token_expired",
                                 "description": "token is expired"}, 401) from expired_sign_error
            except jwt.MissingRequiredClaimError as jwt_claims_error:
                raise AuthError({"code": "invalid_claims",
                                 "description":
                                     "incorrect claims,"
                                     " please check the audience and issuer"}, 401) from jwt_claims_error
            except jwt.InvalidTokenError as invalid_token_error:
                raise AuthError({"code": "invalid_token",
                                 "description": "token is invalid"}, 401) from invalid_token_error
            except Exception as exc:
                raise AuthError({"code": "invalid_header",
                                 "description":
                                     "Unable to parse authentication"
                                     " token."}, 401) from exc

            user_id = payload['sub']
            session['user_id'] = user_id
            return func(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)

    return decorated
