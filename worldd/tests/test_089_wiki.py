"""The public guide must keep its 425 species and progression tied to the engine."""
import importlib.util
import hashlib
import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

WORLD = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gen_wiki', WORLD / 'tools/gen_wiki.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_every_weapon_grade_has_a_separate_existing_drawing():
    data = gen.make_data()
    files, contents = set(), set()
    for weapon in data['model']['weapons']:
        assert 'image' not in weapon and 'art' not in weapon
        assert set(weapon['images']) == set(data['model']['grades'])
        for grade, image in weapon['images'].items():
            url = image['src'].split('?')[0]
            path = (gen.ART / url.removeprefix('/static/laart/')) if url.startswith('/static/laart/') else (gen.OUT / url.removeprefix('/static/site/wiki/'))
            raw = path.read_bytes()
            assert raw.startswith(b'\x89PNG\r\n\x1a\n')
            assert image['description'] == weapon['artByGrade'][grade]['description']
            assert len(image['description']) > 20
            files.add(path)
            contents.add(hashlib.sha256(raw).digest())
    assert len(files) == len(contents) == 64


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
            actual = gen.bestiary.profile(f['floor'], m['id'])
            assert (m['atk'],m['defense'],m['hp']) == (actual['atk'],actual['defense'],actual['hp'])
            assert m['type']==actual['type'] and m['traits']==actual['traits']
            assert m['familyWeights']==gen.bestiary.family_weights(actual)
            for name in gen.economy.SPECIMENS:
                normal=gen.bestiary.specimen_profile(actual,name)
                deep=gen.bestiary.specimen_profile(actual,name,deep=True)
                assert m['specimenStats'][name]['hp']==normal['hp']
                assert m['specimenStats'][name]['deepAtk']==deep['atk']
                for mode in ('normal','deep'):
                    got=m['lootByMode'][mode][name]
                    expected=gen.bestiary.drop_rates(f['floor'],m['traits'],specimen=name,deep=mode=='deep')
                    assert got['material']==[expected['material'][grade] if got['eligible'] else 0 for grade in gen.collection.GRADES]
            assert m['deepEligible'] == (f['floor']>=4 and not {'frail','feeble'}.intersection(m['traits']))
    assert next(m for m in baked['floors'][2]['monsters'] if m['name'] == 'Marsh adder')['id'] == 'reed_adder'


def test_neutral_upgrade_reference_preserves_existing_power_at_every_gate():
    upgrades = gen.make_data()['upgrades']
    assert len(upgrades) == 84
    for gi in range(4):
        rows = [s for s in upgrades if s['gi'] == gi]
        assert [r['level'] for r in rows] == list(range(21))
        for a, b in zip(rows, rows[1:]):
            assert a['floor'] < b['floor']
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
            assert 'data-wiki-revision="collection-2"' in response.text
            assert 'set-cookie' not in response.headers
        assert 'href="/wiki"' in (await client.get('/')).text
        for path in ('wiki.mjs', 'wiki.css', 'data.json'):
            assert (await client.get('/static/site/wiki/' + path)).status_code == 200
        for weapon in gen.make_data()['model']['weapons']:
            for image in weapon['images'].values():
                response = await client.get(image['src'])
                assert response.status_code == 200
                assert response.headers['content-type'] == 'image/png'
        assert (await client.get('/static/site/fonts/WebPlus_IBM_VGA_8x16.woff')).status_code == 200


def test_every_family_state_and_acquisition_is_an_exact_runtime_quote():
    data=gen.make_data()
    for family in data['model']['weapons']:
        for grade in gen.collection.GRADES:
            assert family['sources'][grade]==gen.sources(family['id'],grade)
            states=family['states'][grade]
            assert len(states)==21
            for record in states:
                current=gen.item(family['id'],grade,record['level'])
                assert record['atk']==gen.collection.stats(current)['attack']
                quote=gen.workshop.acquisition_quote(family['id'],grade,'craft') if record['level']==0 else gen.collection.upgrade_quote(gen.item(family['id'],grade,record['level']-1))
                assert (record['gold'],record['materials'])==(quote['gold'],quote['materials'])
    assert len(data['sites'])==8
    for s in data['sites']:
        assert s['floor']==gen.gathering.SITES[s['id']]['floor']
        assert s['yield_amount']==gen.gathering.SITES[s['id']]['yield_amount']
    for row in data['shieldExamples']:
        actual=gen.battle_rules.incoming(row['raw'],row['armorDef'],row['shieldDef'],guard=row['guard'])
        assert all(row[k]==v for k,v in actual.items())
    assert len(set(data['icons'][key] for key in data['materialIcons'].values()))==8
