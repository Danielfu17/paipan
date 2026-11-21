#!/usr/bin/env python3
"""拿資料包的盤面，核對解讀稿裡的事實陳述有沒有寫錯。

用法：
    python3 scripts/check_qimen.py 資料包.md 解讀稿.md

檢查四件事：
1. 吉凶分類：稿中寫「某門／某星／某神」後面緊跟吉、凶、中平等字樣時，是否和《神奇之門》的分類一致。
2. 落宮：稿中寫「乙（兌七）」「庚在巽四」「驚門落兌七」這類寫法時，是否和資料包的天盤位置一致。
3. 一句話裡同時提到某幾宮、又說它們「都」是吉門（或凶門）時，逐宮核對那幾宮的門。
4. 用神宮（用神、日干、時干、年命所在的宮）的門、星、神是否都有寫到。請對最終版執行。
只抓得到常見寫法；列出的每一條都要回稿中確認，沒列出的也不代表都對。
"""
import re, sys

GATE = {'開門': '大吉', '生門': '大吉', '休門': '吉', '杜門': '中平', '景門': '中平', '死門': '凶', '驚門': '凶', '傷門': '凶'}
STAR = {'天心': '吉', '天任': '吉', '天禽': '吉', '天輔': '吉', '天沖': '次吉', '天蓬': '凶', '天芮': '凶', '天柱': '凶', '天英': '中平'}
GOD = {'值符': '吉', '太陰': '吉', '六合': '吉', '九地': '吉', '九天': '吉', '白虎': '凶', '玄武': '凶', '螣蛇': '偏凶', '騰蛇': '偏凶'}
PAL = {'坎一': 1, '坤二': 2, '震三': 3, '巽四': 4, '中五': 5, '乾六': 6, '兌七': 7, '艮八': 8, '離九': 9}
PALNAME = {v: k for k, v in PAL.items()}
GOOD = {'大吉', '吉'}
BAD = {'凶'}


def parse_pack(t):
    cells = {}
    for line in t.split('\n'):
        m = re.match(r'^(坎一|坤二|震三|巽四|中五|乾六|兌七|艮八|離九)宮（[^）]*）｜(.*)$', line.strip())
        if not m:
            continue
        p, rest = PAL[m.group(1)], m.group(2)
        g = re.search(r'八門 (\S{2})', rest)
        s = re.search(r'九星 (天\S)', rest)
        d = re.search(r'八神 (\S{2})', rest)
        tian = re.search(r'天盤干 ([^｜]+)', rest)
        cells[p] = {'gate': g.group(1) if g else None, 'star': s.group(1) if s else None, 'god': d.group(1) if d else None,
                    'tian': re.findall(r'[甲乙丙丁戊己庚辛壬癸]', re.sub(r'（[^）]*）', '', tian.group(1))) if tian else [], 'stars': re.findall(r'天[蓬芮沖輔禽心柱任英]', rest)}
    return cells


def judge_word(s):
    for w in ('大吉', '次吉', '偏凶', '中平', '小吉', '小凶', '大凶', '吉', '凶'):
        if s.startswith(w):
            return w
    return None


def same(claim, real):
    if claim == real:
        return True
    if claim in ('吉', '大吉', '小吉') and real in ('吉', '大吉', '次吉'):
        return True
    if claim in ('凶', '大凶', '小凶') and real in ('凶', '偏凶'):
        return True
    return False


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    pack = open(sys.argv[1], encoding='utf8').read()
    text = open(sys.argv[2], encoding='utf8').read()
    cells = parse_pack(pack)
    if not cells:
        print('資料包裡找不到九宮盤面，無法核對。')
        return 2
    where = {}
    for p, c in cells.items():
        for g in c['tian']:
            where.setdefault(g, set()).add(p)
        for k in ('gate', 'god'):
            if c[k]:
                where.setdefault(c[k], set()).add(p)
        for st in c['stars']:
            where.setdefault(st, set()).add(p)
    issues, n = [], 0
    names = list(GATE) + list(STAR) + list(GOD)
    # 1. 吉凶分類
    for nm in names:
        for m in re.finditer(nm, text):
            tail = text[m.end():m.end() + 6]
            tail = re.sub(r'^[（(「『\s是為屬，、]*', '', tail)
            w = judge_word(tail)
            if not w:
                continue
            real = GATE.get(nm) or STAR.get(nm) or GOD.get(nm)
            n += 1
            if not same(w, real):
                issues.append(f'吉凶分類：「{text[max(0, m.start() - 6):m.end() + 8]}」把{nm}寫成「{w}」，依《神奇之門》分類是「{real}」。')
    # 2. 落宮
    for m in re.finditer(r'([甲乙丙丁戊己庚辛壬癸]|天[蓬芮沖輔禽心柱任英]|[開休生傷杜景死驚]門|值符|螣蛇|太陰|六合|白虎|玄武|九地|九天)[（(]?(?:在|落|落在|位於|於)?(坎一|坤二|震三|巽四|乾六|兌七|艮八|離九)', text):
        sym, pal = m.group(1), PAL[m.group(2)]
        if sym not in where:
            continue
        n += 1
        if pal not in where[sym]:
            real = '、'.join(PALNAME[p] for p in sorted(where[sym]))
            issues.append(f'落宮：「{m.group(0)}」，但資料包裡{sym}在{real}。')
    # 3. 「都是吉門／凶門」的整句核對
    for sent in re.split(r'[。；\n]', text):
        kind = '吉門' if '吉門' in sent else ('凶門' if '凶門' in sent else None)
        if not kind or not re.search(r'都|皆|均|同樣', sent):
            continue
        pals = [PAL[x] for x in re.findall(r'(坎一|坤二|震三|巽四|乾六|兌七|艮八|離九)', sent)]
        for p in dict.fromkeys(pals):
            g = cells.get(p, {}).get('gate')
            if not g:
                continue
            n += 1
            ok = GATE[g] in GOOD if kind == '吉門' else GATE[g] in BAD
            if not ok:
                issues.append(f'整句：「{sent.strip()[:60]}」說是{kind}，但{PALNAME[p]}宮是{g}（{GATE[g]}）。')
    # 4. 用神宮的門、星、神是否都寫到（只列一邊會讓結論偏掉）
    yong = set()
    for m in re.finditer(r'天盤在(坎一|坤二|震三|巽四|乾六|兌七|艮八|離九)宮', pack):
        yong.add(PAL[m.group(1)])
    for m in re.finditer(r'^[^\n｜]*（[^）\n]*）：落(坎一|坤二|震三|巽四|乾六|兌七|艮八|離九)宮', pack, re.M):
        yong.add(PAL[m.group(1)])
    missing = []
    for p in sorted(yong):
        c = cells.get(p)
        if not c:
            continue
        need = [x for x in [c['gate'], c['god']] + c['stars'] if x]
        lack = [x for x in need if x not in text and not (x == '螣蛇' and '騰蛇' in text)]
        if lack:
            missing.append(f'{PALNAME[p]}宮缺：{"、".join(lack)}')
    for x in missing:
        issues.append(f'用神宮沒有寫全：{x}。吉象與凶象都要列出。')
    for x in dict.fromkeys(issues):
        print('有誤', x)
    print(f'\n檢查了 {n} 處事實寫法，疑似有誤 {len(dict.fromkeys(issues))} 處。')
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
