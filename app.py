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
    analysed_string = AnalysedString(string_value)
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
    print("i dey inside app.py/get_analysed_string o", record)
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

    # --- Extract and validate query params ---
    try:
        print("i am being tried...")

        is_palindrome = request.args.get('is_palindrome')
        min_length = request.args.get('min_length', type=int)
        max_length = request.args.get('max_length', type=int)
        word_count = request.args.get('word_count', type=int)
        contains_character = request.args.get('contains_character')

        filters = []
        params = []

        if is_palindrome is not None:
            if is_palindrome.lower() not in ('true', 'false'):
                abort(
            400,
            description="Invalid query parameter values or types")
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
            SELECT analysed_strings.*
            FROM analysed_strings
            JOIN string_properties
            ON analysed_strings.id = string_properties.string_id
            WHERE {where_clause};
        """

        rows = storage.fetchall(query, tuple(params))
        print("Query result: ", rows)
        # --- Format response ---
        data = []
        for row in rows:
            print(row)
            data.append(AnalysedString(row).to_dict())

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
        abort(500, description=str(e))




@app.get('/strings/filter-by-natural-language')
def filter_by_natural_language():
    storage.reload()

    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

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

        # --- Build WHERE clause dynamically ---
        filters = []
        params = []
        if "is_palindrome" in parsed_filters:
            filters.append("is_palindrome = ?")
            params.append(True)
        if "min_length" in parsed_filters:
            filters.append("length >= ?")
            params.append(parsed_filters["min_length"])
        if "max_length" in parsed_filters:
            filters.append("length <= ?")
            params.append(parsed_filters["max_length"])
        if "word_count" in parsed_filters:
            filters.append("word_count = ?")
            params.append(parsed_filters["word_count"])
        if "contains_character" in parsed_filters:
            filters.append("value LIKE ?")
            params.append(f"%{parsed_filters['contains_character']}%")

        where_clause = " AND ".join(filters)

        query = f"""
            SELECT string_properties.id                          FROM string_properties                               JOIN character_frequency_map
            ON string_properties.string_id = character_frequency_map.string_id                                        WHERE {where_clause};
        """
        rows = storage.fetchall(query, tuple(params))        # --- Format response ---
        data = []
        for row in rows:
            rec = storage.get_analysed_string_by_value(row['id'])
            data.append(AnalysedString(rec[1]).to_dict())

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

    record = storage.get_string_by_value(string_value)
    if not record:
        abort(404, description='String not found')

    storage.delete_string(record['id'])
    return '', 204

def error_response(code, e):
    response = {}
    response["status"] = "error"
    response["message"] = f"Error: {str(e)}"
    return jsonify(response), code

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
