"""Disposable local setup only. Never use a real player or another DB."""
import asyncio
import json
import sys
import asyncpg

URL = 'postgresql://ascent_qa:ascent_qa_only@127.0.0.1:55440/ascent_maps_browser'

async def main():
    conn = await asyncpg.connect(URL)
    assert await conn.fetchval('SELECT current_database()') == 'ascent_maps_browser'
    row = await conn.fetchrow("SELECT doc FROM ascent_players WHERE tenant='web' AND player='mapsqa85'")
    doc = json.loads(row['doc'])
    if len(sys.argv) > 1:
        floor = int(sys.argv[1])
        assert 1 <= floor <= 11
        doc.update(floor=floor, location='gate_town', stage='playing', encounter=None)
        doc['hp'] = int(sys.argv[2]) if len(sys.argv) > 2 else 80
        doc['labs'] = {'floormap': False}
        doc['flags'].update({f'floor_seen_{n}': True for n in range(1,12)})
        for key in ('movie_floor','movie_beat','movie_teaser','gate_from','kill_receipt'):
            doc.pop(key,None)
        await conn.execute("UPDATE ascent_players SET doc=$1::jsonb WHERE tenant='web' AND player='mapsqa85'",json.dumps(doc))
    print(json.dumps({k:doc.get(k) for k in ('floor','location','hp','gold','energy_val','act_seq','encounter','labs')}))
    await conn.close()

asyncio.run(main())
