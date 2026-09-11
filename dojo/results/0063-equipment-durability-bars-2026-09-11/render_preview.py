import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'plugin-linear-ascent'))
from plugin_linear_ascent import render
items = []
for durability, name in [(0.75,'Green · 75%'),(0.25,'Low · 25%'),(0,'Broken'),(1,'Full')]:
    item = dict(slug='chain_hauberk', name=name, kind='armor', equipped=True,
                dur=durability, dur_left=int(100*durability), dur_max=100,
                stat_val=8, stat_name='DEF')
    items.append('<div class="example">'+render._slot_cell(item)+'<p>'+name+'</p></div>')
for readonly, name in [(False,'Packed ×2'),(True,'Player sheet')]:
    item = dict(slug='chain_hauberk', name=name, kind='armor', equipped=readonly,
                count=2, dur=.75, dur_left=75, dur_max=100)
    items.append('<div class="example">'+render._slot_cell(item,readonly=readonly)+'<p>'+name+'</p></div>')
page = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Equipment durability bars</title><style>'+render.SCENE_CSS+
        'body{margin:24px;background:#000;color:#aaa;font:16px VGA,monospace}'
        '*{box-sizing:border-box}.examples{display:flex;flex-wrap:wrap;gap:24px}'
        '.example{width:110px}p{margin:10px 0}h1{font:20px VGA;margin-bottom:28px}'
        '</style></head><body><h1>Equipment durability bars</h1><div class="examples">'+
        ''.join(items)+'</div><script>'+render.TIP_JS+'</script></body></html>')
Path(__file__).with_name('preview.html').write_text(page)
