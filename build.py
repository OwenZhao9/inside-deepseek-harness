#!/usr/bin/env python3
"""把书稿源文件生成两份：

  书稿.html        本地看的。图用相对路径，几十 KB，双击秒开。
  书稿-打包.html   要发给别人时用的。图 base64 内嵌，一个文件走天下。

用法：python3 build.py [--打包]
"""
import base64, pathlib, re, sys

HOME = pathlib.Path.home() / 'askAnything/harness-0to1'
SRC = pathlib.Path(__file__).parent / '源稿.html'
SHOTS = HOME / 'capture/shots'
IMGS = {
    'IMG_5_1': '5-1-home.png',
    'IMG_5_2': '5-2-conversation.png',
    'IMG_5_3': '5-3-trace.png',
    'IMG_6_1': '6-1-organize.png',
    'IMG_7_1': '7-1-merge.png',
    'IMG_9_1': '9-1-sandbox.png',
    'IMG_WX': '公众号.png',
}

SHELL = ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,initial-scale=1">'
         '<style>*{margin:0;padding:0}</style></head><body>\n{BODY}\n</body></html>')


def build(pack=False):
    s = SRC.read_text('utf-8')
    for key, fn in IMGS.items():
        if key not in s:
            continue
        f = SHOTS / fn
        if pack:
            src = 'data:image/png;base64,' + base64.b64encode(f.read_bytes()).decode()
        else:
            src = f'capture/shots/{fn}'
        s = s.replace(key, src)

    out = HOME / ('书稿-打包.html' if pack else '书稿.html')
    out.write_text(SHELL.replace('{BODY}', s), 'utf-8')

    chaps = re.findall(r'(前言|结语|第 \d+ 篇) ══════════════ -->(.*?)(?=<!-- ══════════════|\Z)', s, re.S)
    total = 0
    for no, part in chaps:
        n = len(re.sub(r'\s', '', re.sub(r'<[^>]+>', '', part)))
        total += n
        print(f'  {no:<8} {n:>5} 字')
    print(f'  {"合计":<8} {total:>5} 字')
    print(f'\n  → {out}   {out.stat().st_size/1024:.0f} KB')
    return out


if __name__ == '__main__':
    build(pack='--打包' in sys.argv)
