import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from simulation.serve import Jobs, Server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.server = Server(("127.0.0.1", 0), self.directory.name, Path(self.directory.name)/"game")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        if self.server.jobs.thread:
            self.server.jobs.thread.join(timeout=20)
        self.directory.cleanup()

    def get(self, path):
        with urlopen(self.base+path, timeout=20) as response:
            return json.load(response)

    def post(self, data, origin=None):
        headers = {"Content-Type": "application/json"}
        if origin:
            headers["Origin"] = origin
        request = Request(self.base+"/api/runs", json.dumps(data).encode(), headers)
        with urlopen(request, timeout=20) as response:
            return response.status, json.load(response)

    def test_assets_and_input_errors(self):
        with urlopen(self.base) as response:
            self.assertIn(b"Run the actual engine", response.read())
        self.assertGreaterEqual(self.get("/api/defaults")["cpus"], 1)
        for body in ({"players":0}, {"workers":-1}, {"policies":[{}]}, [], {"players":True}, {"unknown":3}):
            with self.assertRaises(HTTPError) as caught:
                self.post(body)
            self.assertEqual(caught.exception.code, 400)
        with self.assertRaises(HTTPError) as caught:
            self.post({}, "https://another-site.invalid")
        self.assertEqual(caught.exception.code, 403)
        for path in ("/api/runs/../model.py", "/../model.py", "/data/inputs.json"):
            with self.assertRaises(HTTPError):
                self.get(path)

    def test_background_parallel_run_saved_and_downloadable(self):
        settings = dict(players=6, days=2, max_floor=3, workers=2, readiness_trials=4, warden_trials=1)
        self.assertEqual(self.post(settings)[0], 202)
        deadline = time.monotonic()+20
        while time.monotonic() < deadline:
            status = self.get("/api/status")
            if status["status"] != "running":
                break
            time.sleep(.02)
        self.assertEqual(status["status"], "complete", status)
        first_id = status["run_id"]
        result = self.get("/api/runs/"+first_id)
        self.assertEqual(result["execution"]["workers"], 2)
        with urlopen(self.base+"/api/runs/"+first_id+".json") as response:
            self.assertIn("attachment", response.headers["Content-Disposition"])
            self.assertEqual(json.load(response), result)
        self.assertEqual(self.get("/api/runs")["runs"][0]["run_id"], first_id)
        self.post({**settings, "seed":99})
        self.server.jobs.thread.join(timeout=20)
        self.assertEqual(self.server.jobs.status()["status"], "complete")
        self.assertEqual(len(self.get("/api/runs")["runs"]), 2)
        self.assertTrue((Path(self.directory.name)/(first_id+".json")).is_file())

    def test_busy_and_worker_failure_visible(self):
        jobs = self.server.jobs
        entered, release = threading.Event(), threading.Event()
        def failure(*args):
            entered.set()
            release.wait(timeout=5)
            raise ValueError("Injected worker failure")
        with patch("simulation.serve.simulate", side_effect=failure):
            self.post({"players":1})
            self.assertTrue(entered.wait(timeout=3))
            with self.assertRaises(HTTPError) as caught:
                self.post({"players":1})
            self.assertEqual(caught.exception.code, 409)
            release.set()
            jobs.thread.join(timeout=3)
        self.assertEqual(jobs.status()["status"], "error")
        self.assertIn("Injected worker failure", jobs.status()["error"])
        self.assertEqual(jobs.manifest()["runs"], [])


if __name__ == "__main__":
    unittest.main()
