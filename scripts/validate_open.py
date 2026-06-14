#!/usr/bin/env python3
"""open（営業時間）フィールドの形式チェック。

アプリ側パーサー（lib/models/opening_hours.dart）と同じ文法で検証する。
使い方: リポジトリルートで `python3 scripts/validate_open.py`
不正な記入があればファイル名・店舗ID・内容を表示して exit 1。
"""
import glob
import json
import re
import sys

DAY_CHARS = '月火水木金土日'

# 全角→半角などの正規化テーブル
TRANS = str.maketrans(
    {
        '：': ':', '；': ';', '、': ',', '，': ',',
        '〜': '-', '～': '-', '−': '-', '–': '-', '―': '-', '　': ' ',
        **{chr(0xFF10 + i): str(i) for i in range(10)},
    }
)

RANGE_RE = re.compile(r'^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$')


def strip_parens(s: str) -> str:
    out, depth = [], 0
    for c in s:
        if c in '(（':
            depth += 1
        elif c in ')）':
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(c)
    return ''.join(out)


def parse_days(spec: str):
    """曜日集合を返す。空指定→空集合、不正→None"""
    days = set()
    s = spec.replace(' ', '').replace(',', '').replace('・', '')
    i = 0
    while i < len(s):
        c = s[i]
        if c == '祝':
            i += 1
            continue
        if c not in DAY_CHARS:
            return None
        frm = DAY_CHARS.index(c)
        if i + 2 < len(s) and s[i + 1] == '-':
            if s[i + 2] not in DAY_CHARS:
                return None
            to = DAY_CHARS.index(s[i + 2])
            d = frm
            while True:
                days.add(d)
                if d == to:
                    break
                d = (d + 1) % 7
            i += 3
        else:
            days.add(frm)
            i += 1
    return days


def parse_ranges(spec: str):
    """時間帯リストを返す。休→[]、不正→None"""
    s = spec.strip()
    if '休' in s:
        return []
    if '24時間' in s:
        return [(0, 1440)]
    ranges = []
    for part in s.split(','):
        p = part.strip()
        if not p:
            continue
        m = RANGE_RE.match(p)
        if not m:
            return None
        sh, sm, eh, em = (int(g) for g in m.groups())
        if sh > 24 or eh > 29 or sm > 59 or em > 59:
            return None
        start, end = sh * 60 + sm, eh * 60 + em
        if end <= start:
            end += 1440
        if start >= 1440 or end > start + 1440:
            return None
        ranges.append((start, end))
    return ranges or None


def is_valid(raw: str) -> bool:
    text = strip_parens(raw).translate(TRANS)
    if not text.strip():
        return False
    assigned = False
    for section in text.split(';'):
        s = section.strip()
        if not s:
            continue
        i = 0
        while i < len(s) and not (s[i].isdigit() or s[i] == '休'):
            i += 1
        day_spec, time_spec = s[:i].strip(), s[i:].strip()
        days = parse_days(day_spec)
        if days is None:
            return False
        if not time_spec:
            if not days:
                continue
            return False
        if parse_ranges(time_spec) is None:
            return False
        if day_spec and not days:  # 祝のみ → 無視
            continue
        assigned = True
    return assigned


def main() -> int:
    errors = []
    filled = total = 0
    for path in sorted(glob.glob('data/*.json')):
        if '_nav' in path:
            continue
        with open(path) as f:
            doc = json.load(f)
        for shop in doc.get('shops', []):
            total += 1
            raw = shop.get('open', '')
            if not raw:
                continue
            filled += 1
            if not is_valid(raw):
                errors.append((path, shop.get('id'), shop.get('name'), raw))

    print(f'記入済み: {filled} / {total} 店舗')
    if errors:
        print(f'\nNG: {len(errors)} 件（アプリでは原文表示のみ・フィルター対象外になります）')
        for path, sid, name, raw in errors:
            print(f'  {path} {sid} {name}: "{raw}"')
        print('\n書き方は docs/open_format.md を参照してください。')
        return 1
    print('OK: すべて正しい形式です')
    return 0


if __name__ == '__main__':
    sys.exit(main())
