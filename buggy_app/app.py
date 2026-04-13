from flask import Flask, jsonify, request
import logging
from pathlib import Path

app = Flask(__name__)

LOG_FILE = Path(__file__).resolve().parent / "logs" / "app.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/calculate')
def calculate():
    try:
        x = int(request.args.get('x', 10))
        y = int(request.args.get('y', 0))
    except (TypeError, ValueError):
        return jsonify({"error": "x and y must be valid integers"}), 400

    if y == 0:
        logger.warning("Invalid input for /calculate: x=%s y=%s", x, y)
        return jsonify({"error": "y must not be zero"}), 400

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
    if user is None:
        logger.info("User not found for user_id=%s", user_id)
        return jsonify({"error": "user not found"}), 404
    return jsonify({"name": user["name"]})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
