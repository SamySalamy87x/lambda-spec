import json
import threading
from urllib.request import Request, urlopen
from lambda_spec.webapp import create_server


def request_json(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_webapp_health_demo_and_analysis():
    server = create_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, health = request_json(f"{base}/api/health")
        assert status == 200 and health["ok"] is True
        status, demo = request_json(f"{base}/api/demo?name=degradation")
        assert status == 200 and len(demo["rows"]) > 100
        status, analyzed = request_json(f"{base}/api/analyze", demo)
        assert status == 200 and "result" in analyzed
        assert analyzed["result"]["trajectory"]["trend"] in {"weakening", "stable", "strengthening"}
        status, narrative = request_json(f"{base}/api/explain", {"result": analyzed["result"], "lang": "en"})
        assert status == 200 and narrative["narrative"] and narrative["engine"]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
