"""The public guide must keep its 425 species and progression tied to the engine."""
import importlib.util
import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

WORLD = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gen_wiki', WORLD / 'tools/gen_wiki.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_baked_wiki_matches_deployed_content_and_all_species():
    baked = json.loads((gen.OUT / 'data.json').read_text())
    assert baked == gen.make_data()
    assert [f['floor'] for f in baked['floors']] == list(range(1, 101))
    monsters = [m for f in baked['floors'] for m in f['monsters']]
    assert len(monsters) == len({m['id'] for m in monsters}) == 425
    assert baked['uniqueImages'] == 425
    assert baked['maxImageReuse'] <= 3
    for f in baked['floors']:
        authored = gen.schema.get_floor(f['floor'])
        assert [m['id'] for m in f['monsters']] == [e.id for e in authored.encounters]
        for m in f['monsters']:
            atk, defense, hp = gen.economy.creature_stats(f['floor'], m['traits'])
            if 'bulwark' in m['traits']:
                hp = round(hp * gen.economy.BULWARK_HP_MULT)
            assert (m['atk'], m['defense'], m['hp']) == (atk, defense, hp)
            for name, setting in gen.economy.SPECIMENS.items():
                assert m['specimenStats'][name]['hp'] == round(hp * setting['hp'])
                assert m['specimenStats'][name]['deepAtk'] == round(round(atk * setting['atk']) * 1.2)
            assert m['deepEligible'] == (f['floor'] >= 4 and not {'frail', 'feeble'}.intersection(m['traits']))
    assert next(m for m in baked['floors'][2]['monsters'] if m['name'] == 'Marsh adder')['id'] == 'reed_adder'


def test_neutral_upgrade_reference_preserves_existing_power_at_every_gate():
    upgrades = gen.make_data()['upgrades']
    assert len(upgrades) == 84
    for gi in range(4):
        rows = [s for s in upgrades if s['gi'] == gi]
        assert [r['level'] for r in rows] == list(range(21))
        for a, b in zip(rows, rows[1:]):
            assert a['floor'] < b['floor'] and a['q'] < b['q']
            if a['level'] > 0:  # base acquisition is not an upgrade fee
                assert a['gold'] < b['gold']
            assert a['dur'] < b['dur'] and a['atk'] <= b['atk']
        for r in rows:
            assert r['atk'] == gen.economy.honed_bonus(gen.economy._reference_bonus(r['floor'], 'weapon'), gen.economy.reference_hone(r['floor']))
    for floor in range(1, 101):
        available = max((r for r in upgrades if r['floor'] <= floor), key=lambda r: r['floor'])
        assert available['atk'] == gen.economy.honed_bonus(gen.economy._reference_bonus(floor, 'weapon'), gen.economy.reference_hone(floor))
    assert next(r for r in upgrades if r['gi'] == 3 and r['level'] == 6)['floor'] == 84


@pytest.mark.asyncio
async def test_public_wiki_routes_assets_and_home_link_need_no_account():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        for route in ('/wiki', '/wiki/'):
            response = await client.get(route)
            assert response.status_code == 200
            assert 'data-wiki-revision="089.1"' in response.text
            assert 'set-cookie' not in response.headers
        assert 'href="/wiki"' in (await client.get('/')).text
        for path in ('wiki.mjs', 'wiki.css', 'data.json'):
            assert (await client.get('/static/site/wiki/' + path)).status_code == 200
        assert (await client.get('/static/site/fonts/WebPlus_IBM_VGA_8x16.woff')).status_code == 200
