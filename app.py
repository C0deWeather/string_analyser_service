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

@app.get('/strings')
def list_analysed_strings():
    """
    This endpoint lists all analysed strings
    """
    if not request.args:
        records = storage.get_all_analysed_strings()
        data = [AnalysedString(record).to_dict() for record in records]
        response = {
            "data": data,
            "count": len(data),
            "filters_applied": None
        }
        return jsonify(response), 200

    # --- Extract and validate query params ---
    try:
        is_palindrome = request.args.get('is_palindrome')
        min_length = request.args.get('min_length', type=int)
        max_length = request.args.get('max_length', type=int)
        word_count = request.args.get('word_count', type=int)
        contains_character = request.args.get('contains_character')

        filters = []
        params = []

        if is_palindrome is not None:
            if is_palindrome.lower() not in ('true', 'false'):
                return jsonify({"error": "Invalid is_palindrome value"}), 400
            filters.append("is_palindrome = ?")
            params.append(is_palindrome.lower() == 'true')

        if min_length is not None:
            filters.append("length >= ?")
            params.append(min_length)

        if max_length is not None:
            filters.append("length <= ?")
            params.append(max_length)

        if word_count is not None:
            filters.append("word_count = ?")
            params.append(word_count)

        if contains_character:
            filters.append("value LIKE ?")
            params.append(f"%{contains_character}%")

        where_clause = " AND ".join(filters) if filters else "1=1"


        query = f"""
            SELECT string_properties.id
            FROM string_properties
            JOIN string_properties
            ON analysed_strings.id = string_properties.string_id
            WHERE {where_clause};
        """
        rows = storage.fetchall(query, tuple(params))
        # --- Format response ---
        data = []
        for row in rows:
            data.append({
                "id": row["id"],
                "value": row["value"],
                "properties": {
                    "length": row["length"],
                    "is_palindrome": bool(row["is_palindrome"]),
                    "unique_characters": row["unique_characters"],
                    "word_count": row["word_count"]
                },
                "created_at": row["created_at"]
            })

        return jsonify({
            "data": data,
            "count": len(data),
            "filters_applied": {
                "is_palindrome": is_palindrome,
                "min_length": min_length,
                "max_length": max_length,
                "word_count": word_count,
                "contains_character": contains_character
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


  
    is_palindrome = request.args.get('is_palindrome')
    min_length = request.args.get('min_length', type=int)
    max_length = request.args.get('max_length', type=int)
    word_count = request.args.get('word_count', type=int)
    contains_character = request.args.get('contains_character')
    if any(filter is None for filter in [min_length, max_length, word_count]):
        abort(
            400,
            description="Invalid query parameter values or types")
    elif is_palindrome not in ['true', 'false']:
        abort(
            400,
            description="Invalid query parameter values or types")
    elif not isinstance(contains_character, str) and len(contains_character) != 1:
        abort(
            400,
            description="Invalid query parameter values or types")

    if is_palindrome == 'true':
        is_palindrome = True
    else:
        is_palindrome = False
    
    filters = {
        "is_palindrome": is_palindrome,
        "min_length": min_length,
        "max_length": max_length,
        "word_count": word_count,
        "contains_character": contains_character
    }
    records = storage.get_all_analysed_strings()
    response = [AnalysedString(record).to_dict() for record in records]
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