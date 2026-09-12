"""Headless host for the *imported game*. No game rule is implemented here."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO/'worldd'))
from app.gamepath import ensure_game_importable
ensure_game_importable()
import plugin_linear_ascent
from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import core, state, combat

EPOCH = dt.datetime(2026, 1, 2, 6, tzinfo=dt.timezone.utc)
_AT = ContextVar('ascent_simulation_clock', default=None)
_REAL_NOW = state.now


def _clock():
    at = _AT.get()
    return _REAL_NOW() if at is None else at


# Only the external clock is replaced. Context-local values isolate HTTP
# inspector threads; each CPU worker also has its own imported module.
state.now = _clock


@contextmanager
def at_time(seconds):
    token = _AT.set(EPOCH + dt.timedelta(seconds=seconds))
    try:
        yield
    finally:
        _AT.reset(token)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def engine_source():
    root = Path(plugin_linear_ascent.__file__).resolve().parent
    files = {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.py','.yaml','.yml','.json')}
    files['@host/gamepath.py'] = hashlib.sha256((REPO/'worldd/app/gamepath.py').read_bytes()).hexdigest()
    from plugin_linear_ascent.version import VERSION
    return dict(engine='plugin_linear_ascent.engine.core.apply_choice',version=VERSION,
        package_path=str(root),files=files,sha256=digest(files),
        host='isolated local engine documents; no worldd database or multiplayer services',
        virtual_epoch=EPOCH.isoformat())


class GameSession:
    """Synthetic persistence + clock. All player choices go through core."""
    def __init__(self, key, *, seconds=0, document=None, capture=True):
        self.key,self.seconds,self.capture = key,float(seconds),capture
        self.trace=[]
        self.events=[]
        with at_time(self.seconds):
            self.doc=deepcopy(document) if document is not None else state.new_player(key)
        self.scene=None
        self.look()

    def _finish(self, scene, option, text):
        # Like worldd: drain the per-request ledger into host storage.
        self.events=self.doc.pop('_ledger',[])
        effects=self.doc.pop('_effects',[])
        if effects:
            raise RuntimeError('This action requires worldd services: '+','.join(e['kind'] for e in effects))
        self.scene=scene
        self.doc['scene']=scene.to_dict()
        if self.capture:self.trace.append([self.seconds,option,text])
        return scene

    def look(self, seconds=None):
        if seconds is not None:self.advance(seconds)
        with at_time(self.seconds):return self._finish(core.current_scene(self.doc),None,'')

    def advance(self, seconds):
        if seconds < self.seconds:raise ValueError('Virtual time cannot move backwards')
        self.seconds=float(seconds)

    def act(self, option, text='', *, seconds=None):
        if seconds is not None:self.advance(seconds)
        with at_time(self.seconds):return self._finish(core.apply_choice(self.doc,option,text),option,text)

    def legal(self):
        return [o for o in self.scene.options if not o.locked]

    def state_hash(self):
        return digest(self.doc)

    def meters(self):
        with at_time(self.seconds):return combat.meters(self.doc).__dict__


def replay(key, trace, *, expected_source=None, expected_state=None):
    source=engine_source()
    if expected_source and source['sha256']!=expected_source:raise ValueError('Engine source changed; checkout the recorded revision before replay')
    s=GameSession(key,capture=False)
    # Constructor's look is itself part of a saved trace. Start again from
    # new_player so replay does not introduce an extra engine read.
    with at_time(0):s.doc=state.new_player(key)
    for seconds,option,text in trace:
        if option is None:s.look(seconds)
        else:s.act(option,text,seconds=seconds)
    match=expected_state is None or s.state_hash()==expected_state
    return s,dict(match=match,state_sha256=s.state_hash(),engine_sha256=source['sha256'],actions=len(trace))
