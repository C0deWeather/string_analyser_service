#!/usr/bin/env python3
from flask import Flask, jsonify, abort, request
from models.analysed_string import AnalysedString
from models import storage
import os
import re


app = Flask(__name__)
# do not sort JSON keys
app.json.sort_keys = False


@app.post('/strings')
def analyse_string():
    """
    This endpoint analyses a string sent via a POST request
    """
    storage.reload()
    # check if request body is JSON and has "value" field
    if not request.is_json and "value" not in request.json:
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
    analysed_string = AnalysedString(string=string_value)
    response = analysed_string.to_dict()
    storage.insert(analysed_string)
    return jsonify(response), 201

@app.get('/strings/<string_value>')
def get_analysed_string(string_value):
    """
    This endpoint retrieves the analysis of a previously analysed string
    """
    storage.reload()
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
    storage.reload()
    if not request.args:
        records = storage.get_all_analysed_strings()
        data = [AnalysedString(record).to_dict() for record in records]
        response = {
            "data": data,
            "count": len(data),
            "filters_applied": None
        }
        return jsonify(response), 200

    data = get_data(request.args)

    return jsonify({
        "data": data,
        "count": len(data),
        "filters_applied": {
            "is_palindrome": request.args.get('is_palindrome'),
            "min_length": request.args.get("min_length"),
            "max_length": request.args.get('max_length'),
            "word_count": request.args.get('word_count'),
            "contains_character": request.args.get('contains_character')
        }
    }), 200

@app.get('/strings/filter-by-natural-language')
def filter_by_natural_language():
    storage.reload()

    query = request.args.get('query', '').strip().lower()
    if not query:
        abort(400, description="Missing 'query' parameter")

    parsed_filters = {}

    try:
        # --- NLP Heuristics ---
        if "palindromic" in query or "palindrome" in query:
            parsed_filters["is_palindrome"] = True

        if "single word" in query or "one word" in query:
            parsed_filters["word_count"] = 1

        match_len = re.search(r'longer than (\d+)', query)
        if match_len:
            parsed_filters["min_length"] = int(match_len.group(1)) + 1

        match_len_max = re.search(r'shorter than (\d+)', query)
        if match_len_max:
            parsed_filters["max_length"] = int(match_len_max.group(1)) - 1

        match_contains = re.search(r'contain(?:ing)? the letter (\w)', query)
        if match_contains:
            parsed_filters["contains_character"] = match_contains.group(1)

        # fallback heuristic for “first vowel”
        if "first vowel" in query:
            parsed_filters["contains_character"] = 'a'

        if not parsed_filters:
            abort(400, description = "Unable to parse natural language query")

        # Get data based on parsed filters
        data = get_data(parsed_filters)

        return jsonify({
            "data": data,
            "count": len(data),
            "interpreted_query": {
                "original": query,
                "parsed_filters": parsed_filters
            }
        }), 200

    except Exception as e:
        abort(422, description=str(e))


@app.delete('/strings/<string_value>')
def delete_string(string_value):
    """Delete a string and all its related data."""
    storage.reload()

    record = storage.get_analysed_string_by_value(string_value)
    if not record:
        abort(404, description='String not found')

    storage.delete_string(record[0])  # record[0] is the id
    return '', 204

def error_response(code, e):
    response = {}
    response["status"] = "error"
    response["message"] = f"Error: {str(e)}"
    return jsonify(response), code

def get_data(req_args):
    """
    Build SQL query based on provided filters, execute query and return results.
    """
    filters = []
    params = []

    try:
        is_palindrome = req_args.get('is_palindrome')
        min_length = req_args.get('min_length')
        max_length = req_args.get('max_length')
        word_count = req_args.get('word_count')
        contains_character = req_args.get('contains_character')

        if is_palindrome is not None:
            if is_palindrome not in (True, False):
                abort(
                    400,
                    description="Invalid query parameter values or types")
            filters.append("is_palindrome = ?")
            params.append(is_palindrome)

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
            SELECT analysed_strings.*
            FROM analysed_strings
            JOIN string_properties
            ON analysed_strings.id = string_properties.string_id
            WHERE {where_clause};
        """

        print(query)
        rows = storage.fetchall(query, tuple(params))
        data = [AnalysedString(row).to_dict() for row in rows]
        
        return data

    except Exception as e:
        abort(422, description=str(e))

@app.errorhandler(400)
def handle_400_error(e):
    return error_response(400, e)

@app.errorhandler(409)
def handle_409_error(e):
    return error_response(409, e)

@app.errorhandler(422)
def handle_422_error(e):
    return error_response(422, e)

@app.errorhandler(500)
def handle_500_error(e):
    return error_response(500, e)

@app.teardown_appcontext
def close_db_connection(exception=None):
    storage.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
