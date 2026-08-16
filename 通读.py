#!/usr/bin/env python3
"""全书通读检查 —— 查四样人眼容易漏、机器查得准的东西：

  1. 数字打架   同一个事实在不同篇里写了不同的数
  2. 引用落空   写着「第 N 篇说过 X」，第 N 篇里根本没有 X
  3. 重复       同一件事在好几篇里各讲了一遍
  4. 生词       术语第一次出现的地方没有解释

查不了的：读起来是不是同一个人写的。那个只有人能判。
"""
import re, html, pathlib, collections

SRC = pathlib.Path(__file__).parent / '源稿.html'

def load():
    s = SRC.read_text('utf-8')
    out = {}
    for name, body in re.findall(r'(前言|第 \d+ 篇) ══════════════ -->(.*?)(?=<!-- ══════════════|\Z)', s, re.S):
        t = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', body, flags=re.S)
        t = re.sub(r'<[^>]+>', '', t)
        out[name] = html.unescape(t)
    return out

def sentences(t):
    for line in t.splitlines():
        for x in re.split(r'(?<=[。！？])', line.strip()):
            x = x.strip()
            if len(x) > 8:
                yield x

# ── 1. 数字打架 ────────────────────────────────────────────
# 把「关键词 + 数字」配对，同一个关键词在全书出现不同数字就报
ANCHORS = [
    ('DSH 星标',        r'DeepSeek Harness[^。]{0,20}星标[^\d]{0,6}([\d,]{3,})|星标是\s*([\d,]{3,})，分叉'),
    ('模型可用工具数',  r'(\d+)\s*(?:个|件)(?:这样的)?工具'),
    ('设计笔记总数',    r'([\d,]{3,})\s*篇设计笔记|仓库里还有\s*([\d,]{3,})\s*篇'),
    ('否决方案篇数',    r'(\d+)\s*篇(?:是)?被否'),
    ('插件清单条数',    r'插件记录[^\d]{0,4}(\d+)|(\d+)\s*条记录，一条记录对应'),
    ('主循环行数',      r'ReactLoopAgent[^\d]{0,20}(\d[\d,]*)\s*行|主循环[^。]{0,12}?(\d{3,})\s*行'),
    ('读一个文件的事件数', r'读一个文件」?[^。]{0,12}(\d+)\s*条|(\d+)\s*条事件记录[^。]{0,8}读'),
    ('整理文件的步数',  r'整理文件[^。]{0,20}1\s*轮\s*(\d)\s*步'),
]

def check_numbers(chs):
    bag = collections.defaultdict(lambda: collections.defaultdict(set))
    for name, t in chs.items():
        for label, pat in ANCHORS:
            for m in re.finditer(pat, t):
                v = next((g for g in m.groups() if g), None)
                if v:
                    bag[label][v.replace(',', '')].add(name)
    bad = []
    for label, vals in bag.items():
        if len(vals) > 1:
            bad.append((label, {v: sorted(w) for v, w in vals.items()}))
    return bad

# ── 2. 引用落空 ────────────────────────────────────────────
# 只查带引号的引用。转述查不了——机器分不清「转述」和「编造」，
# 只有引号声称自己是原话，那才验得动。
QUOTED = re.compile(r'第\s*(\d+)\s*篇[^。]{0,14}?[「『]([^」』]{6,60})[」』]')

def check_refs(chs):
    miss, total = [], 0
    for name, t in chs.items():
        for m in QUOTED.finditer(t):
            no, quote = m.group(1), m.group(2)
            target = f'第 {no} 篇'
            if target not in chs:
                continue
            total += 1
            core = re.sub(r'[，。、！？…\s]', '', quote)
            body = re.sub(r'[，。、！？…\s]', '', chs[target])
            # 引号里的话，取最长的连续片段去被引篇里找
            if core[:12] not in body and core[-12:] not in body:
                miss.append((name, target, quote))
    return miss, total

# ── 3. 重复 ────────────────────────────────────────────────
def check_repeat(chs):
    seen = collections.defaultdict(list)
    for name, t in chs.items():
        for s in sentences(t):
            k = re.sub(r'\s|[，。、「」（）]', '', s)
            if len(k) >= 16:
                seen[k].append(name)
    return [(k, v) for k, v in seen.items() if len(set(v)) > 1]

# ── 4. 生词 ────────────────────────────────────────────────
TERMS = ['上下文窗口', '无状态', '幻觉', '词元', 'turn', 'step', '插件', '预设',
         '子代理', 'subagent', '事件日志', '沙箱', '断言', '压缩', '落盘']
EXPLAIN = r'(叫|指的?是|意思是|就是|也就是|这种|这个上限|这类|——)'

def check_terms(chs):
    order = list(chs.keys())
    out = []
    for term in TERMS:
        for name in order:
            t = chs[name]
            i = t.find(term)
            if i < 0:
                continue
            window = t[max(0, i-70): i+70]
            if not re.search(EXPLAIN, window):
                out.append((term, name, window.replace('\n', ' ').strip()[:80]))
            break
    return out


def main():
    chs = load()
    W = 66
    print('═' * W)
    print(f'  全书通读检查　{len(chs)} 篇')
    print('═' * W)

    nums = check_numbers(chs)
    print(f'\n【1】数字打架　{len(nums)} 处' + ('  ❌' if nums else '  ✅'))
    for label, vals in nums:
        print(f'\n  ── {label} ──')
        for v, where in vals.items():
            print(f'     {v:<10} 出现在 {"、".join(where)}')

    refs, reftotal = check_refs(chs)
    print(f'\n【2】带引号的跨篇引用　查了 {reftotal} 处，对不上 {len(refs)} 处' + ('  ❌' if refs else '  ✅'))
    for a, b, q in refs[:20]:
        print(f'     {a} 引 {b}：「{q}」　← 被引篇里没这句')

    rep = check_repeat(chs)
    print(f'\n【3】整句重复　{len(rep)} 处' + ('  ⚠️' if rep else '  ✅'))
    for k, v in rep[:12]:
        print(f'     {"、".join(sorted(set(v)))}：{k[:44]}…')

    terms = check_terms(chs)
    print(f'\n【4】首次出现没解释　{len(terms)} 处' + ('  ⚠️' if terms else '  ✅'))
    for term, name, ctx in terms:
        print(f'     「{term}」首现于{name}：…{ctx}…')

    print('\n' + '═' * W)
    print('  机器查不了：读起来是不是同一个人写的。')
    print('═' * W)


if __name__ == '__main__':
    main()
