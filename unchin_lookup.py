# -*- coding: utf-8 -*-
"""
見積・回答FAX用 西濃運賃ルックアップ（式を再実装しない・公開ツールの値をそのまま返す）

  python unchin_lookup.py 愛知 2 2        # 県 長さ(m) 束数 → 税抜/税込
  python unchin_lookup.py 愛知 2 1-20     # 範囲で表
  python unchin_lookup.py 新潟 4 5 --json

値の出どころ = 本番 https://h02050d-ship-it.github.io/fare-calculator/soryo.html に埋め込まれた
DATA.single[県][長さ][束数-1]（税抜・法人宛車上渡し・段ボール込み）。税込 = 税抜×1.1。
取引先が見る数字と必ず一致する。ローカル soryo_table.json と食い違えば警告を出す。
"""
import sys, re, json, os, urllib.request

LIVE = "https://h02050d-ship-it.github.io/fare-calculator/soryo.html"
HERE = os.path.dirname(os.path.abspath(__file__))

def load_live():
    html = urllib.request.urlopen(LIVE, timeout=20).read().decode("utf-8")
    i = html.find('const DATA = {')
    if i < 0:
        raise RuntimeError("soryo.html から DATA を抽出できません")
    start = html.index("{", i)
    data, _ = json.JSONDecoder().raw_decode(html[start:])
    return data

def load_local():
    p = os.path.join(HERE, "soryo_table.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None

def lookup(data, pref, length, qty):
    pref = pref.replace("県","").replace("府","").replace("都","")
    if pref == "北海":
        pref = "北海道"
    single = data["single"]
    if pref not in single:
        raise KeyError(f"県名が不正: {pref}")
    arr = single[pref].get(str(length))
    if arr is None:
        raise KeyError(f"長さは 2/3/4 のみ: {length}")
    if not (1 <= qty <= len(arr)):
        raise KeyError(f"束数は 1〜{len(arr)}: {qty}")
    z = arr[qty-1]
    if z is None:
        return None  # 個別見積(北海道・沖縄・離島)
    return {"pref": pref, "length": length, "qty": qty, "zeinuki": z, "zeikomi": round(z*1.1)}

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    as_json = "--json" in sys.argv
    if len(a) < 3:
        print(__doc__); sys.exit(1)
    pref, length = a[0], int(a[1].replace("m",""))
    lo, hi = (map(int, a[2].split("-")) if "-" in a[2] else (int(a[2]), int(a[2])))
    try:
        data = load_live(); src = "live"
    except Exception as e:
        data = load_local(); src = f"local(fallback: {e})"
        if data is None: raise
    loc = load_local()
    if src == "live" and loc and loc.get("single") != data.get("single"):
        print("⚠ ローカル soryo_table.json が本番と不一致（git pull か node gen_soryo_table.js を確認）", file=sys.stderr)
    rows = [lookup(data, pref, length, q) for q in range(lo, hi+1)]
    if as_json:
        print(json.dumps(rows, ensure_ascii=False)); return
    print(f"[{src}] {pref} {length}m  法人宛車上渡し・段ボール込み")
    for r, q in zip(rows, range(lo, hi+1)):
        print(f"{q:>2}束  税抜 {'個別見積' if r is None else format(r['zeinuki'],',')}  税込 {'-' if r is None else format(r['zeikomi'],',')}")

if __name__ == "__main__":
    main()
