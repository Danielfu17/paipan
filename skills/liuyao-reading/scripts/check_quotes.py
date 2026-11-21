#!/usr/bin/env python3
"""核對解讀稿中的原文引用是否真的出現在 references/ 的原文檔案裡。

用法：
    python3 scripts/check_quotes.py 解讀稿.md
    或  cat 解讀稿.md | python3 scripts/check_quotes.py -

規則：稿中每一個「〔書名・章名〕「原文」」或單獨的「原文」引號片段，都拿去兩部書的全文中比對。
比對前會去掉標點與空白，所以斷句、逗號寫法不同不影響；但字要一樣（《卜筮正宗》是簡體）。
輸出每一段引文是「找到」還是「找不到」，以及找到時的檔名。找不到的引文要修正或改標為〔推論〕。
"""
import os, re, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references')
PUNCT = re.compile(r'[\s，。、；：？！「」『』（）()《》〈〉〔〕﹐﹑﹕﹖﹔．,.;:?!…—\-\'"“”‘’\[\]【】<>／/|・·]')


def norm(s):
    return PUNCT.sub('', s)


def load():
    docs = []
    for sub in ('zengshan', 'zhengzong'):
        d = os.path.join(BASE, sub)
        for fn in sorted(os.listdir(d)):
            if fn.endswith('.md'):
                raw = open(os.path.join(d, fn), encoding='utf8').read()
                title = raw.split('\n', 1)[0].lstrip('# ').strip()
                docs.append((f'{sub}/{fn}（{title}）', norm(raw)))
    return docs


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '-'
    text = sys.stdin.read() if src == '-' else open(src, encoding='utf8').read()
    quotes = [q for q in re.findall(r'「([^「」]{4,200})」', text)]
    if not quotes:
        print('稿中沒有找到任何「」引文。每個論點都應附上原文引文。')
        return 1
    docs = load()
    bad = 0
    for q in dict.fromkeys(quotes):
        nq = norm(q)
        if len(nq) < 4:
            continue
        hit = [fn for fn, body in docs if nq in body]
        if hit:
            print(f'找到　「{q}」 → {hit[0]}' + (f' 等 {len(hit)} 處' if len(hit) > 1 else ''))
        else:
            bad += 1
            # 退而求其次：找最長的連續片段，幫忙定位
            best = ''
            for fn, body in docs:
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
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
