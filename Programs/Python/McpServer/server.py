from flask import Flask, request, Response
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Replace with your actual paid keys from Stripe
VALID_KEYS = {"user_premium_888"}

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    data = request.json
    req_id = data.get("id")
    method = data.get("method")
    params = data.get("params", {})
    
    # 1. Auth Check (The Monetization Gate)
    api_key = params.get("arguments", {}).get("api_key")
    if method == "tools/call" and api_key not in VALID_KEYS:
        return json.dumps({
            "jsonrpc": "2.0", "id": req_id,
            "error": {"code": -32000, "message": "Invalid API Key. Pay at your-site.com"}
        })

    # 2. Logic (Simplified for brevity)
    if method == "initialize":
        res = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "Termux-Paid-Server", "version": "1.0"}}
    elif method == "tools/list":
        res = {"tools": [{"name": "security_scan", "description": "Run audit", "inputSchema": {"type": "object", "properties": {"target": {"type": "string"}, "api_key": {"type": "string"}}}}]}
    else:
        res = {"content": [{"type": "text", "text": "Scan complete for " + params.get("arguments", {}).get("target", "unknown")}]}

    return json.dumps({"jsonrpc": "2.0", "id": req_id, "result": res})

"""
if __name__ == "__main__":
    app.run(port=5000)
"""
if __name__ == "__main__":
    # Use 0.0.0.0 to ensure Termux internal networking can find it
    app.run(host='0.0.0.0', port=5000, debug=True)

