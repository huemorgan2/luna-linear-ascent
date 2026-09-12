#!/usr/bin/env python3
"""Local simulation explorer. No packages or production services required."""
from pathlib import Path
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import re
import sys
import threading
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulation.model import Config, POLICIES, ROOT
from simulation.results import available_cpus, save_run, simulate, validate_run
from simulation.experiments import run_study,plan,VARIANTS

RUN_ID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\Z")


class Jobs:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.state = dict(status="idle")
        self.thread = None
        self.cache = {}

    def status(self):
        with self.lock:
            return dict(self.state)

    def start(self, settings, study=False):
        config = Config.from_dict(settings.get("base",{}) if study and isinstance(settings,dict) else settings)
        if study:
            plan(config.to_dict(),settings.get("seeds",[1601,1602,1603]),settings.get("variants",list(VARIANTS)))
        with self.lock:
            if self.state["status"] == "running":
                raise RuntimeError("A simulation is already running. Wait for it to finish.")
            self.state = dict(status="running", stage="starting", fraction=0,
                workers=min(config.workers or available_cpus(), max(config.players, config.max_floor)))
            self.thread = threading.Thread(target=self._study if study else self._run,
                args=(config,settings) if study else (config,), name="simulation-run")
            self.thread.start()
            return dict(self.state)

    def _run(self, config):
        def progress(event):
            with self.lock:
                self.state.update(event)
        try:
            result = simulate(config, progress)
            save_run(result, self.directory)
            with self.lock:
                self.state.update(status="complete", fraction=1, run_id=result["run_id"], seconds=result["duration_seconds"])
        except Exception as error:
            with self.lock:
                self.state.update(status="error", error=f"{type(error).__name__}: {error}")

    def _study(self, config, settings):
        def progress(event):
            with self.lock:self.state.update(event)
        try:
            result,path=run_study(config.to_dict(),settings.get("seeds"),settings.get("variants"),
                run_directory=self.directory,progress=progress)
            with self.lock:self.state.update(status="complete",fraction=1,study_id=result["study_id"],
                run_id=result["completed"][-1]["run_id"],seconds=sum(v["seconds"] for v in result["analysis"]["variants"].values()))
        except Exception as error:
            with self.lock:self.state.update(status="error",error=f"{type(error).__name__}: {error}")

    def manifest(self):
        rows, errors = [], []
        for path in sorted(self.directory.glob("*.json"), reverse=True):
            if not RUN_ID.fullmatch(path.stem):
                continue
            stamp = (path.stat().st_mtime_ns, path.stat().st_size)
            cached = self.cache.get(path.name)
            if not cached or cached[0] != stamp:
                try:
                    data = validate_run(json.loads(path.read_text()))
                    if data["run_id"] != path.stem:
                        raise ValueError("Run ID does not match filename")
                    item = {k:data.get(k) for k in ("run_id", "created_at", "config", "duration_seconds", "deterministic_sha256", "execution")}
                    cached = (stamp, item, None)
                except (OSError, ValueError, KeyError, TypeError) as error:
                    cached = (stamp, None, f"{path.name}: {error}")
                self.cache[path.name] = cached
            if cached[2]:
                errors.append(cached[2])
            else:
                rows.append(cached[1])
        return dict(runs=rows, errors=errors)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, directory=None):
        self.jobs = Jobs(directory or ROOT / "runs")
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send_bytes(self, body, code=200, mime="application/json", filename=None):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def json(self, data, code=200):
        self.send_bytes(json.dumps(data, allow_nan=False).encode(), code)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/defaults":
            return self.json(dict(config=Config().to_dict(), policies=POLICIES, cpus=available_cpus()))
        if path == "/api/status":
            return self.json(self.server.jobs.status())
        if path == "/api/studies":
            studies=[]
            for p in sorted((ROOT/"studies").glob("*.json"),reverse=True):
                try:
                    data=json.loads(p.read_text());studies.append({k:data.get(k) for k in ("study_id","created_at","status","seeds","variants","analysis")})
                except (OSError,ValueError):continue
            return self.json(dict(studies=studies))
        if path.startswith("/api/studies/"):
            ident=path.removeprefix("/api/studies/")
            if not RUN_ID.fullmatch(ident):return self.json(dict(error="Invalid study ID"),400)
            target=ROOT/"studies"/(ident+".json")
            if not target.is_file():return self.json(dict(error="Study not found"),404)
            return self.send_bytes(target.read_bytes())
        if path == "/api/runs":
            return self.json(self.server.jobs.manifest())
        if path.startswith("/api/runs/"):
            ident = path.removeprefix("/api/runs/")
            download = ident.endswith(".json")
            if download:
                ident = ident[:-5]
            if not RUN_ID.fullmatch(ident):
                return self.json(dict(error="Invalid run ID"), 400)
            target = self.server.jobs.directory / (ident+".json")
            if not target.is_file():
                return self.json(dict(error="Run not found"), 404)
            return self.send_bytes(target.read_bytes(), filename=target.name if download else None)
        assets = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/style.css": "style.css",
            "/WebPlus_IBM_VGA_8x16.woff": "WebPlus_IBM_VGA_8x16.woff", "/FONT-LICENSE.txt": "FONT-LICENSE.txt"}
        if path == "/model":
            return self.send_bytes((ROOT / "MODEL.md").read_bytes(), mime="text/plain; charset=utf-8")
        if path == "/audit":
            return self.send_bytes((ROOT.parent/"research/simulation-audit/AUDIT.md").read_bytes(),mime="text/plain; charset=utf-8")
        if path in assets:
            target = ROOT / "web" / assets[path]
            mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            return self.send_bytes(target.read_bytes(), mime=mime)
        return self.json(dict(error="Not found"), 404)

    def do_POST(self):
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        origin = self.headers.get("Origin")
        if host not in allowed or (origin and origin != "http://"+host):
            return self.json(dict(error="Run creation requires the local explorer origin"), 403)
        route=urlparse(self.path).path
        if route not in ("/api/runs","/api/studies"):
            return self.json(dict(error="Not found"), 404)
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            return self.json(dict(error="Expected application/json"), 415)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                return self.json(dict(error="Settings body must be 1–65536 bytes"), 413)
            settings = json.loads(self.rfile.read(length))
            return self.json(self.server.jobs.start(settings,study=route=="/api/studies"), 202)
        except (ValueError, UnicodeError) as error:
            return self.json(dict(error=str(error)), 400)
        except RuntimeError as error:
            return self.json(dict(error=str(error)), 409)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--runs-dir", type=Path)
    args = parser.parse_args()
    server = Server(("127.0.0.1", args.port), args.runs_dir)
    print(f"Simulation lab: http://127.0.0.1:{server.server_port} · {available_cpus()} available CPUs", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if server.jobs.thread and server.jobs.thread.is_alive():
            print("Finishing the current simulation before exit…", flush=True)
            server.jobs.thread.join()


if __name__ == "__main__":
    main()
