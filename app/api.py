from flask import Flask, jsonify, request
import json
from .db import get_db
from .tools import run_query
from .agent import Agent

def create_app():
    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/agent/query", methods=["POST"])
    def agent_query():
        data = request.get_json(force=True) or {}
        question = data.get("question", "")

        # Create and run agent
        agent = Agent()
        result = agent.query(question)

        # Build response including sql_used
        response = {
            "request_id": agent.request_id,
            "question": question,
            "answer": result.get("answer", []),
            "num_rows": result.get("num_rows", 0),
            "status": result.get("status", "unknown"),
            "sql_used": result.get("sql_used", "")
        }

        return jsonify(response), 200

    @app.route("/agent/trace/<request_id>", methods=["GET"])
    def agent_trace(request_id):
        """Return the full agent trace for a request."""
        from pathlib import Path
        trace_path = Path(__file__).resolve().parent.parent / "logs" / f"{request_id}.json"

        if trace_path.exists():
            with open(trace_path, "r") as f:
                trace = json.load(f)
            return jsonify(trace), 200
        else:
            return jsonify({"error": "Trace not found"}), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
