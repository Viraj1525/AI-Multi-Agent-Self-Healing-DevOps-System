from flask import Flask, jsonify, request
import logging
import random

app = Flask(__name__)
logging.basicConfig(
    filename='buggy_app/logs/app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/calculate')
def calculate():
    x = int(request.args.get('x', 10))
    y = int(request.args.get('y', 0))
    try:
        result = x / y
        return jsonify({"result": result})
    except ZeroDivisionError as e:
        logger.error(f"ZeroDivisionError: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/user/<user_id>')
def get_user(user_id):
    users = {"1": {"name": "Alice"}}
    user = users.get(user_id)
    try:
        return jsonify({"name": user["name"]})
    except TypeError as e:
        logger.error(f"NullPointerError for user_id={user_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)