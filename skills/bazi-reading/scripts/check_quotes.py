#!/usr/bin/env python3
"""核對解讀稿中的原文引用是否真的出現在 references/ 的原文檔案裡。

用法：
    python3 scripts/check_quotes.py 解讀稿.md
    或  cat 解讀稿.md | python3 scripts/check_quotes.py -
    python3 scripts/check_quotes.py 解讀稿.md --packet 審稿包.md
        另外產生「審稿包」：每段引文在稿中的論點、出處檔名與行號、原文前後文，
        給審稿員直接閱讀，不必自己到原書裡搜尋。

規則：稿中每一個「〔書名・章名〕「原文」」或單獨的「原文」引號片段，都拿去 references/ 底下所有原典的全文中比對。
比對前會去掉標點與空白，所以斷句、逗號寫法不同不影響；但字要一樣（多數原典是簡體錄入本，照檔案原字引用）。
輸出每一段引文是「找到」還是「找不到」，以及找到時的檔名。找不到的引文要修正或改標為〔推論〕。
"""
import os, re, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references')
PUNCT = re.compile(r'[\s，。、；：？！「」『』（）()《》〈〉〔〕﹐﹑﹕﹖﹔．,.;:?!…—\-\'"“”‘’\[\]【】<>／/|・·]')


def norm(s):
    return PUNCT.sub('', s)


def load():
    docs = []
    for sub in sorted(x for x in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, x))):
        d = os.path.join(BASE, sub)
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.md'):
                raw = open(os.path.join(d, fn), encoding='utf8').read()
                title = raw.split('\n', 1)[0].lstrip('# ').strip()
                docs.append((f'{sub}/{fn}（{title}）', norm(raw), raw))
    return docs


def context(raw, nq, before=350, after=250):
    """回傳引文在原檔的行號，以及前後文（以原始文字擷取，保留標點）。"""
    idx = [i for i, ch in enumerate(raw) if not PUNCT.match(ch)]
    body = ''.join(raw[i] for i in idx)
    k = body.find(nq)
    if k < 0:
        return None, ''
    a, b = idx[k], idx[k + len(nq) - 1] + 1
    line = raw.count('\n', 0, a) + 1
    s, e = max(0, a - before), min(len(raw), b + after)
    snip = ('…' if s > 0 else '') + raw[s:a] + '【' + raw[a:b] + '】' + raw[b:e] + ('…' if e < len(raw) else '')
    return line, snip.strip()


def claim_of(text, q):
    """稿中包含這段引文的那一行（論點），過長時截斷。"""
    for ln in text.split('\n'):
        if '「' + q + '」' in ln:
            ln = ln.strip()
            return ln if len(ln) <= 400 else ln[:400] + '…'
    return ''


def main():
    args = sys.argv[1:]
    packet = None
    if '--packet' in args:
        i = args.index('--packet'); packet = args[i + 1]; del args[i:i + 2]
    src = args[0] if args else '-'
    text = sys.stdin.read() if src == '-' else open(src, encoding='utf8').read()
    quotes = [q for q in re.findall(r'「([^「」]{4,200})」', text)]
    if not quotes:
        print('稿中沒有找到任何「」引文。每個論點都應附上原文引文。')
        return 1
    docs = load()
    bad = 0
    pk = []
    for q in dict.fromkeys(quotes):
        nq = norm(q)
        if len(nq) < 4:
            continue
        hit = [(fn, raw) for fn, body, raw in docs if nq in body]
        if hit:
            print(f'找到　「{q}」 → {hit[0][0]}' + (f' 等 {len(hit)} 處' if len(hit) > 1 else ''))
            if packet is not None:
                line, snip = context(hit[0][1], nq)
                more = '、'.join(h[0].split('（')[0] for h in hit[1:4])
                pk.append(f'### Q{len(pk) + 1}\n- 稿中論點：{claim_of(text, q)}\n- 出處：{hit[0][0]} 第 {line} 行' + (f'（另見 {more}）' if more else '') + f'\n- 原文前後文（【】內是引文）：\n\n' + '\n'.join('> ' + x for x in snip.split('\n') if x.strip()) + '\n')
        else:
            bad += 1
            # 退而求其次：找最長的連續片段，幫忙定位
            best = ''
            for fn, body, _ in docs:
                for k in range(len(nq), 5, -1):
                    if k <= len(best):
                        break
                    for st in range(0, len(nq) - k + 1):
                        if nq[st:st + k] in body:
                            best, where = nq[st:st + k], fn
                            break
                    if len(best) == k:
                        break
            hint = f'（最接近的片段「{best}」在 {where}）' if len(best) >= 6 else ''
            print(f'找不到「{q}」{hint}')
    print(f'\n共 {len(dict.fromkeys(quotes))} 段引文，找不到 {bad} 段。')
    if packet is not None:
        head = ('# 審稿包\n\n每段引文：稿中的論點、出處（檔名與行號）、原文前後文。'
                '審稿時先讀這份，判斷原文的前提和這張盤是否相符；前後文不夠判斷時，再照行號打開原檔讀整段。'
                + (f'\n\n注意：另有 {bad} 段引文在原書找不到，不在這份清單內。' if bad else '') + '\n\n')
        open(packet, 'w', encoding='utf8').write(head + '\n'.join(pk))
        print(f'審稿包已寫入 {packet}（{len(pk)} 段）')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
