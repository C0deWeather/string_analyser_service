#!/usr/bin/env python3
from datetime import datetime
from flask import Flask, jsonify, abort
from flask import request
from models.analysed_string import AnalysedString
from models.storage import DBStorage


app = Flask(__name__)
storage = DBStorage()

# do not sort JSON keys
app.json.sort_keys = False


@app.post('/strings')
def analyse_string():
    """
    This endpoint analyses a string sent via a POST request
    """
    # check if request body is JSON and has "value" field
    if not request.is_json or "value" not in request.json:
        abort(
            400,
            description="Invalid request body or missing \"value\" field")
    # check if "value" field is a string
    elif not isinstance(request.json["value"], str):
        abort(
            422,
            description="Invalid data type for \"value\" (must be string)")
    # check if string already exists in db
    string_value = request.json["value"]
    record = storage.get_analysed_string_by_value(string_value)
    if record:
        abort(
            409,
            description="String already exists in the system")
    # create AnalysedString object and store in db
    analysed_string = AnalysedString(string_value)
    response = analysed_string.to_dict()
    storage.insert(analysed_string)
    return jsonify(response), 201

@app.get('/strings/<string_value>')
def get_analysed_string(string_value):
    """
    This endpoint retrieves the analysis of a previously analysed string
    """
    record = storage.get_analysed_string_by_value(string_value)
    if not record:
        abort(
            404,
            description="String does not exist in the system")
    # reconstruct AnalysedString object from db record
    analysed_string = AnalysedString(record)
    response = analysed_string.to_dict()
    return jsonify(response), 200

def error_response(code, e):
    response = {}
    response["status"] = "success"
    response["user"] = user
    response["timestamp"] = datetime.utcnow().isoformat() + "Z"
    response["fact"] = f"could not retrieve cat fact: {str(e)}"
    return jsonify(response), code


@app.errorhandler(504)
def handle_504_error(e):
    return error_response(504, e)


@app.errorhandler(502)
def handle_502_error(e):
    return error_response(502, e)


@app.errorhandler(500)
def handle_500_error(e):
    return error_response(500, e)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)