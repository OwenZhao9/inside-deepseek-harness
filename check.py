#!/usr/bin/env python3
"""
书稿校验工序 —— 用法：python3 check.py 稿子.md

分两类输出：
  【自动判定】机器能直接判对错的（文件路径、行号、语气违规）
  【需人工核】机器只能标出来、必须回原文看的（推论句、命令、数字）

设计原则：你读这份报告，不读全文。
"""
import re, sys, os, pathlib

REPO = pathlib.Path.home() / 'askAnything/harness-0to1/dsh-repo'

# ── 语气违规词表（来自定好的语气十条）──────────────────────
TONE = [
    ('拟人俏皮动词', r'躺在|趴在|静静地|悄悄地|默默地'),
    ('无信息引导词', r'更值得看的是|更值得注意的是|有意思的是|真正的关键在于|值得注意的是|而这恰恰|不得不说'),
    ('爹味/预告好坏', r'很妙|非常妙|是不是很|咱们一起|咱们来|你也试试|让我们|不妨试试|相信你'),
    ('假第一人称经历', r'我敲下|我数了|我熬|我试了一下|我亲自|我花了.{0,4}小时'),
    ('评价同行', r'没人说得清|大博主|某些博主|那些自媒体'),
    # ── 第 13 条：不解释读者本来就会的事 ──
    # 判据：这句话对一个会用手机、会上网的成年人是不是废话？
    # 他不懂的是 AI 和这个软件，不是互联网。
    ('俯视/解释常识', r'不用注册|跟平时上网|跟平常上网|就是那个|双击就行|粘进去|'
                     r'一看就懂|谁都会|很简单|非常简单|超级简单|按一下回车|复制粘贴就'),
    # ── 作者给自己留后路，不是读者需要的 ──
    ('免责声明', r'是正常的|对不上.{0,6}正常|以实际.{0,4}为准|仅供参考|可能会有出入'),
    # ── 第 14 条：讲东西，别讲这篇文章 ──
    # 判据：这句话给的是关于「东西」的信息，还是关于「文章」的信息？后者删。
    # 而且本书每篇独立成文，「前面几篇」这种话连前提都不成立。
    ('目录式过渡', r'前面.{0,4}篇(讲|说|介绍)|这一篇(讲的是|先说|要说|把它)|本篇(讲|将)|'
                  r'先看一眼|接下来(我们|要讲)|上一节(讲|说)|读完这一篇(你|就)'),
]

# ── 推论句标记词：这类句子机器判不了对错，必须回原文核 ──────
INFER = r'因为|所以|这说明|这意味着|正是|恰恰|之所以|原因是|可见|因此|于是|表明|导致|印证|证明了|说明了'

# ── 看着像文件路径的东西 ────────────────────────────────
PATH_RE = re.compile(r'`([\w.@/-]+\.(?:ts|tsx|js|md|yml|yaml|json|py|sh|txt)(?::\d+)?)`')
# ── 中文行号写法：`某文件.md` …… 第 67 行 ─────────────────
CN_LINE_RE = re.compile(
    r'`([\w.@/-]+\.(?:ts|tsx|js|md|yml|yaml|json|py|sh|txt))`[^\n。]{0,12}?第\s*(\d+)\s*行')
# ── 看着像命令的东西 ────────────────────────────────────
CMD_RE = re.compile(r'^\s*(npx|npm|curl|gh|git|node|python3?|ls|find|grep|zstd|open|export|echo|mkdir|mv|rm)\b')


def split_sentences(text):
    """按中文标点断句，保留行号。"""
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith(('```', '|', '>')):
            continue
        for s in re.split(r'(?<=[。！？])', line):
            s = s.strip()
            if len(s) > 6:
                out.append((lineno, s))
    return out


def check(path):
    text = pathlib.Path(path).read_text(encoding='utf-8')
    lines = text.splitlines()
    name = os.path.basename(path)

    # 1. 文件路径与行号
    good, bad, lineref = [], [], []
    for m in PATH_RE.finditer(text):
        raw = m.group(1)
        p, _, ln = raw.partition(':')
        f = REPO / p
        if not f.is_file():
            bad.append(raw)
            continue
        good.append(raw)
        if ln.isdigit():
            total = sum(1 for _ in f.open(encoding='utf-8', errors='ignore'))
            lineref.append((raw, int(ln) <= total, total))

    # 1b. 中文写法的行号引用：`x.md` 的第 67 行
    for m in CN_LINE_RE.finditer(text):
        p, ln = m.group(1), int(m.group(2))
        f = REPO / p
        if not f.is_file():
            bad.append(f'{p}（第{ln}行）')
            continue
        total = sum(1 for _ in f.open(encoding='utf-8', errors='ignore'))
        lineref.append((f'{p} 第{ln}行', ln <= total, total))

    # 2. 语气违规
    tone_hits = []
    for lineno, line in enumerate(lines, 1):
        for label, pat in TONE:
            for m in re.finditer(pat, line):
                tone_hits.append((lineno, label, m.group(0), line.strip()[:46]))

    # 3. 推论句
    infers = [(n, s) for n, s in split_sentences(text) if re.search(INFER, s)]

    # 4. 命令
    cmds = [(n, l.strip()) for n, l in enumerate(lines, 1) if CMD_RE.match(l)]

    # 5. 数字断言（3 位以上的数，或带单位的）
    nums = []
    for lineno, line in enumerate(lines, 1):
        for m in re.finditer(r'(\d[\d,]{2,}|\d+\s*(?:篇|条|个|行|秒|分钟|小时|万|亿|%|MB|KB|GB))', line):
            nums.append((lineno, m.group(0)))

    # ── 输出 ──────────────────────────────────────────
    W = 58
    print('═' * W)
    print(f'  校验报告：{name}   {len(lines)} 行 / {len(text)} 字')
    print('═' * W)
    bad_ln = [r for r, ok, _ in lineref if not ok]
    print('\n【自动判定】')
    print(f'  文件路径    {len(good)+len(bad):>3} 条  →  {len(good)} 存在, {len(bad)} 不存在'
          + ('  ❌' if bad else '  ✅'))
    print(f'  行号引用    {len(lineref):>3} 条  →  {len(lineref)-len(bad_ln)} 有效, {len(bad_ln)} 越界'
          + ('  ❌' if bad_ln else '  ✅'))
    print(f'  语气违规    {len(tone_hits):>3} 处'
          + ('  ⚠️' if tone_hits else '  ✅'))

    print('\n【需人工核】')
    print(f'  推论句      {len(infers):>3} 条   ← 逐条回原文核，这是错误高发区')
    print(f'  可执行命令  {len(cmds):>3} 条   ← 抽验能不能跑')
    print(f'  数字断言    {len(nums):>3} 处   ← 每个都要有来源')

    if bad:
        print('\n──── ❌ 不存在的路径 ────')
        for r in bad:
            print(f'  {r}')
    if bad_ln:
        print('\n──── ❌ 行号越界 ────')
        for r, ok, total in lineref:
            if not ok:
                print(f'  {r}  实际只有 {total} 行')
    if tone_hits:
        print('\n──── ⚠️ 语气违规 ────')
        for n, label, word, ctx in tone_hits:
            print(f'  L{n:<4} [{label}] 「{word}」')
            print(f'        {ctx}…')
    if infers:
        print('\n──── 推论句（必须逐条回原文核）────')
        for n, s in infers:
            print(f'  L{n:<4} {s[:70]}')
    if cmds:
        print('\n──── 可执行命令 ────')
        for n, c in cmds:
            print(f'  L{n:<4} {c[:70]}')

    print()
    fail = bool(bad or bad_ln)
    print('═' * W)
    print('  结论：' + ('❌ 有硬错误，先修' if fail
                      else '⚠️ 自动检查通过，推论句待人工核' if infers
                      else '✅ 全部通过'))
    print('═' * W)
    return 1 if fail else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python3 check.py 稿子.md')
        sys.exit(2)
    sys.exit(max(check(p) for p in sys.argv[1:]))
