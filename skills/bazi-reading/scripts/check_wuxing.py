#!/usr/bin/env python3
"""檢查解讀稿裡「X生Y」「X克Y」的五行方向有沒有寫反。

用法：
    python3 scripts/check_wuxing.py 解讀稿.md

它會找出像「午日克亥水」「酉金克寅木」「亥水生寅木」這類緊鄰的寫法，
把兩邊的地支、天干或五行換成五行，對照
  相生：金生水，水生木，木生火，火生土，土生金
  相克：金克木，木克土，土克水，水克火，火克金
寫反或不成立的會列出來。「不克」「不生」會反過來檢查。
它只看緊鄰的字，抓不到所有寫法；列出來的每一條都要回原稿確認。
"""
import re, sys

WX = {}
for chars, e in (('寅卯甲乙木', '木'), ('巳午丙丁火', '火'), ('申酉庚辛金', '金'), ('亥子壬癸水', '水'), ('辰戌丑未戊己土', '土')):
    for c in chars:
        WX[c] = e
GEN = {'金': '水', '水': '木', '木': '火', '火': '土', '土': '金'}
KE = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
TOK = '子丑寅卯辰巳午未申酉戌亥甲乙丙丁戊己庚辛壬癸金木水火土'
PAT = re.compile(rf'([{TOK}])([日月爻{TOK}]?)(不能|不)?(克|剋|尅|生)([{TOK}])')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    text = open(sys.argv[1], encoding='utf8').read()
    # 宮名換成該宮五行，例如「兌七宮（金，她）克巽四宮（木）」→「金克木」
    PW = {'坎一': '水', '坤二': '土', '震三': '木', '巽四': '木', '中五': '土', '乾六': '金', '兌七': '金', '艮八': '土', '離九': '火'}
    text = re.sub(r'(坎一|坤二|震三|巽四|中五|乾六|兌七|艮八|離九)宮?(?:[（(][^）)]*[）)])?', lambda m: PW[m.group(1)], text)
    bad, n = [], 0
    for m in PAT.finditer(text):
        a1, a2, neg, op, b = m.groups()
        before = text[max(0, m.start() - 1):m.start()]
        if before in ('長', '所'):
            continue
        left = a2 if a2 and a2 in WX else a1
        ea, eb = WX[left], WX[b]
        holds = (GEN if op == '生' else KE)[ea] == eb
        n += 1
        if holds == bool(neg):
            ctx = text[max(0, m.start() - 12):m.end() + 8].replace('\n', ' ')
            real = f'{ea}生{eb}' if GEN[ea] == eb else f'{ea}克{eb}' if KE[ea] == eb else f'{eb}生{ea}' if GEN[eb] == ea else f'{eb}克{ea}' if KE[eb] == ea else f'{ea}{eb}同類比和'
            bad.append(f'「{m.group(0)}」：實際是「{real}」，不能寫成「{ea}{"不" if neg else ""}{op}{eb}」。上下文：…{ctx}…')
    for x in bad:
        print('方向有誤', x)
    print(f'\n檢查了 {n} 處生克寫法，疑似寫反 {len(bad)} 處。')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
