# -*- coding: utf-8 -*-
"""
見積・回答FAX用 西濃運賃ルックアップ（式を再実装しない・公開ツールの値をそのまま返す）

  python unchin_lookup.py 愛知 2 2        # 県 長さ(m) 束数 → 税抜/税込
  python unchin_lookup.py 愛知 2 1-20     # 範囲で表
  python unchin_lookup.py 新潟 4 5 --json
  python unchin_lookup.py 山梨 2 --set 10 --iri 20   # EC「20枚入り×10セット」→ 束数に換算して引く
  python unchin_lookup.py 山梨 2 --mai 200           # 枚数で指定（束数はツールが換算）
  python unchin_lookup.py 山梨 2 10 --mai 200        # 束数と枚数の両方→食い違いを検査

【毎回の妥当性チェック】（2026-11-12 追加：楽天 20枚入り×10セットを10束で引いた事故の再発防止）
  束あたり標準入数 = 2m 8〜10枚 / 3m 10枚 / 4m 8枚（運賃ツール index.html と同じ）
  ・枚数(--mai / --set×--iri)があれば、枚数÷束数=1束の枚数 が標準から外れたら 🔴
  ・1枚あたり送料が「その県・その長さ」の普通の範囲（1〜20束）から外れたら 🔴
  ・1束あたり送料を全国の平均レンジ（10〜90%点）と並べて表示

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

IRI = {2: (8, 10), 3: (10, 10), 4: (8, 8)}   # 1束の標準枚数(最小,最大)。index.html updateQtyLabel と同じ

def band(data, pref, length, upto=20):
    """その県・長さの1束あたり税込(1〜upto束)と、全国の10〜90%点"""
    def per(arr):
        return [round(z*1.1)/q for q, z in enumerate(arr[:upto], 1) if z is not None]
    mine = per(data["single"][pref][str(length)])
    allv = sorted(v for pv in data["single"].values() for v in per(pv.get(str(length)) or []))
    pick = lambda x: allv[int(x*(len(allv)-1))]
    return (min(mine), max(mine)) if mine else None, (pick(.1), pick(.9))

def check(data, r, mai):
    """r=lookup結果。NG文言のリスト（空ならOK）と表示行を返す"""
    ng, lines = [], []
    lo_i, hi_i = IRI[r["length"]]
    mine, (p10, p90) = band(data, r["pref"], r["length"])
    per_taba = r["zeikomi"] / r["qty"]
    lines.append(f"  1束あたり 税込{per_taba:,.0f}円 ／ {r['pref']}{r['length']}m の普通の範囲 {mine[0]:,.0f}〜{mine[1]:,.0f}円 ／ 全国の平均レンジ {p10:,.0f}〜{p90:,.0f}円")
    if not (mine[0]-1 <= per_taba <= mine[1]+1):
        ng.append("1束あたりがこの県・長さの範囲外")
    if mai:
        iri = mai / r["qty"]
        per_mai = r["zeikomi"] / mai
        mlo, mhi = mine[0]/hi_i, mine[1]/min(lo_i, iri)   # 端数束(例 2m15枚=2束)は1束の枚数が少ない分だけ上限を広げる
        lines.append(f"  {mai}枚 ÷ {r['qty']}束 = 1束{iri:.1f}枚（標準 {lo_i}〜{hi_i}枚）／1枚あたり 税込{per_mai:,.0f}円（普通 {mlo:,.0f}〜{mhi:,.0f}円）")
        if not (lo_i - 0.5 <= iri <= hi_i + 0.5) and not (iri < lo_i and r["qty"] == -(-mai // lo_i)):
            ng.append(f"1束{iri:.1f}枚になっている（標準{lo_i}〜{hi_i}枚）→束数の換算ミスの疑い")
        if not (mlo*0.98 <= per_mai <= mhi*1.02):
            ng.append(f"1枚あたり{per_mai:,.0f}円が普通の範囲外")
    return ng, lines

def main():
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    argv = sys.argv[1:]
    def opt(name):
        if name in argv:
            i = argv.index(name); v = argv[i+1]; del argv[i:i+2]; return int(v)
        return None
    mai, nset, iri = opt("--mai"), opt("--set"), opt("--iri")
    as_json = "--json" in argv
    a = [x for x in argv if not x.startswith("--")]
    if nset is not None:
        if iri is None:
            print("--set を使う時は --iri（1セットの枚数）も指定"); sys.exit(1)
        mai = nset * iri
    if len(a) < 2 or (len(a) < 3 and mai is None):
        print(__doc__); sys.exit(1)
    pref, length = a[0], int(a[1].replace("m",""))
    if len(a) >= 3:
        lo, hi = (map(int, a[2].split("-")) if "-" in a[2] else (int(a[2]), int(a[2])))
    else:
        lo_i, hi_i = IRI[length]
        lo = hi = -(-mai // hi_i)   # 標準入数(多い方)で切上げ。2mは8〜10枚なので「10枚束」換算
        if lo_i != hi_i:
            print(f"※{length}mの束は{lo_i}〜{hi_i}枚。{mai}枚÷{hi_i}枚＝{lo}束で換算（8枚束の商品なら束数を直接指定）", file=sys.stderr)
    try:
        data = load_live(); src = "live"
    except Exception as e:
        data = load_local(); src = f"local(fallback: {e})"
        if data is None: raise
    loc = load_local()
    if src == "live" and loc and loc.get("single") != data.get("single"):
        print("⚠ ローカル soryo_table.json が本番と不一致（git pull か node gen_soryo_table.js を確認）", file=sys.stderr)
    rows = [lookup(data, pref, length, q) for q in range(lo, hi+1)]
    single = lo == hi and rows[0] is not None
    ng, lines = check(data, rows[0], mai) if single else ([], [])
    if as_json:
        if single:
            rows[0]["check"] = {"ok": not ng, "ng": ng, "mai": mai}
        print(json.dumps(rows, ensure_ascii=False)); return
    head = f"[{src}] {pref} {length}m  法人宛車上渡し・段ボール込み"
    if nset is not None:
        head += f"  （{nset}セット×{iri}枚＝{mai}枚）"
    print(head)
    for r, q in zip(rows, range(lo, hi+1)):
        print(f"{q:>2}束  税抜 {'個別見積' if r is None else format(r['zeinuki'],',')}  税込 {'-' if r is None else format(r['zeikomi'],',')}")
    if single:
        for ln in lines:
            print(ln)
        if ng:
            print("🔴 要確認: " + " / ".join(ng)); sys.exit(2)
        print("✅ 範囲内" + ("" if mai else "（枚数未指定＝束数換算は未検査。EC品は --set/--iri か --mai を付ける）"))

if __name__ == "__main__":
    main()
