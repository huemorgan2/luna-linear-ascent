import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from simulation.serve import Server


class GameApiTests(unittest.TestCase):
    def test_actual_run_inspect_download_replay_and_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            server=Server(('127.0.0.1',0),Path(root)/'proposal',Path(root)/'game')
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base='http://127.0.0.1:'+str(server.server_port)
            def call(path,body=None):
                request=Request(base+path,None if body is None else json.dumps(body).encode(),{'Content-Type':'application/json'})
                with urlopen(request,timeout=40) as r:return json.load(r)
            try:
                self.assertIn('engine/core.py',call('/api/game/defaults')['source']['files'])
                a=call('/api/game/inspect',{'seed':10});b=call('/api/game/inspect',{'seed':11})
                a=call('/api/game/inspect',{'session':a['session'],'action':'gate'})
                self.assertEqual(a['player']['location'],'gate')
                b=call('/api/game/inspect',{'session':b['session'],'action':'forge'})
                self.assertEqual(b['player']['location'],'forge')
                with self.assertRaises(HTTPError):call('/api/game/inspect',{'session':a['session'],'action':'invent_loot'})
                with self.assertRaises(HTTPError):call('/api/game/runs',{'group_hp_scale':.5})
                call('/api/game/runs',dict(players=1,days=1,max_floor=3,workers=1,readiness_trials=2,minutes_per_day=1))
                server.jobs.thread.join(timeout=40)
                status=call('/api/status');self.assertEqual(status['status'],'complete',status)
                ident=status['run_id'];data=call('/api/game/runs/'+ident+'.json')
                self.assertEqual(data['backend'],'actual-game-engine')
                self.assertEqual(len(call('/api/game/runs')['runs']),1)
                self.assertEqual(len(call('/api/runs')['runs']),0)
                reports=Path(root)/'game-searches';reports.mkdir()
                report=dict(search_id=ident,status='complete',winner='staff-levels-margin1')
                (reports/(ident+'.json')).write_text(json.dumps(report))
                self.assertEqual(call('/api/game/searches')['searches'],[report])
                self.assertEqual(call('/api/game/searches/'+ident+'.json'),report)
                report.update(status='invalid',trials=[dict(run_id=ident)])
                (reports/(ident+'.json')).write_text(json.dumps(report))
                self.assertTrue(call('/api/game/runs')['runs'][0]['diagnostic'])

                with self.assertRaises(HTTPError):call('/api/game/searches/not-an-id')

                self.assertTrue(call('/api/game/replay',dict(run_id=ident,player=0))['match'])
            finally:
                server.shutdown();server.server_close();thread.join()
                if server.jobs.thread:server.jobs.thread.join(timeout=40)
