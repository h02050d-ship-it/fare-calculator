// FAX用 送料ご案内PDFのHTMLを生成（soryo_table.jsonから早見表を作る）
const fs = require('fs');
const D = JSON.parse(fs.readFileSync(__dirname + '/soryo_table.json', 'utf8'));
const URL = 'https://h02050d-ship-it.github.io/fare-calculator/soryo.html';
// QRはローカルqr.pngをdata URIで埋め込み（headless描画時の外部取得を回避）
let QR = '';
try { QR = 'data:image/png;base64,' + fs.readFileSync(__dirname + '/qr.png').toString('base64'); }
catch(e){ QR = 'https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=0&data=' + encodeURIComponent(URL); }

// 代表都道府県（地域別に1つ）
const ROWS = [
  ['北海道','北海道'], ['宮城','東北'], ['東京','関東'], ['新潟','北陸・信越'],
  ['静岡','東海'], ['大阪','近畿'], ['広島','中国'], ['香川','四国'], ['福岡','九州'], ['沖縄','沖縄']
];
const yen = n => '¥' + n.toLocaleString();
// 上段=税込／下段=税抜（税抜は税込÷1.1の逆算）
const cell = (p,len,q) => {
  const a = D.single[p] && D.single[p][len];
  const incl = a ? a[q-1] : null;
  if (incl==null) return `<td class="q">別途</td>`;
  const ex = Math.round(incl/1.1);
  return `<td>${yen(incl)}<span class="ex">税抜 ${yen(ex)}</span></td>`;
};

let body = '';
for (const [p,region] of ROWS){
  const quote = (D.single[p] && D.single[p][2][0]===null);
  if (quote){
    body += `<tr><td class="pf">${p}<span class="rg">${region}</span></td>`
          + `<td class="q" colspan="6">別途お見積り（便ごとに運賃が変わるため）</td></tr>`;
    continue;
  }
  body += `<tr><td class="pf">${p}<span class="rg">${region}</span></td>`
        + `${cell(p,'2',5)}${cell(p,'2',10)}`
        + `${cell(p,'3',5)}${cell(p,'3',10)}`
        + `${cell(p,'4',5)}${cell(p,'4',10)}</tr>`;
}

const html = `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<style>
  @page { size: A4 portrait; margin: 9mm 10mm; }
  * { box-sizing: border-box; margin:0; padding:0; -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  body { font-family:'Meiryo','Hiragino Sans',sans-serif; color:#111; font-size:9.5pt; line-height:1.35; }
  .head { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:2.5px solid #111; padding-bottom:4px; }
  .head .co { font-size:11pt; font-weight:bold; }
  .head .co small { font-weight:normal; font-size:8.5pt; color:#444; }
  .head .date { font-size:8.5pt; color:#444; text-align:right; }
  h1 { font-size:15pt; text-align:center; margin:7px 0 2px; letter-spacing:.03em; }
  .sub { text-align:center; font-size:9pt; color:#333; margin-bottom:7px; }
  .urlbox { display:flex; gap:11px; align-items:center; border:2px solid #111; border-radius:7px; padding:7px 10px; margin-bottom:8px; }
  .urlbox .qr { width:84px; height:84px; flex:0 0 84px; border:1px solid #ccc; }
  .urlbox .qr img { width:100%; height:100%; display:block; }
  .urlbox .ut { flex:1; }
  .urlbox .ut .lead { font-size:9.5pt; font-weight:bold; margin-bottom:2px; }
  .urlbox .ut .url { font-size:11pt; font-weight:bold; color:#1a5e2a; word-break:break-all; }
  .urlbox .ut .steps { font-size:8.5pt; color:#333; margin-top:4px; }
  h2 { font-size:10.5pt; margin:3px 0 4px; padding-left:7px; border-left:4px solid #1a5e2a; }
  table { width:100%; border-collapse:collapse; }
  th, td { border:1px solid #888; padding:2.5px 2px; text-align:center; font-size:9pt; font-weight:bold; }
  thead th { background:#eee; font-size:8.5pt; }
  .grp { background:#f3f3f3; }
  td .ex { display:block; font-size:7pt; color:#777; font-weight:normal; }
  td.pf { text-align:left; font-weight:bold; white-space:nowrap; background:#fafafa; font-size:8.5pt; }
  td.pf .rg { display:block; font-weight:normal; font-size:7pt; color:#777; }
  td.q { color:#9a6b00; font-weight:bold; }
  .note { font-size:8.3pt; color:#333; margin-top:7px; border:1px dashed #999; border-radius:6px; padding:7px 9px; line-height:1.5; }
  .note b { color:#111; }
  .note .ttl { font-weight:bold; margin-bottom:2px; }
  .foot { margin-top:7px; border-top:2px solid #111; padding-top:4px; font-size:8.7pt; display:flex; justify-content:space-between; align-items:flex-end; }
  .foot .tel { font-size:12pt; font-weight:bold; }
</style></head><body>
  <div class="head">
    <div class="co">株式会社 林材木店　<small>無垢ヒノキ専門</small></div>
    <div class="date">2026年6月25日<br>送料のご案内（市場のお取引先様へ）</div>
  </div>

  <h1>📦 送料がその場でわかります</h1>
  <div class="sub">お届け先・長さ・数量を選ぶだけ。スマートフォン・パソコンでご利用いただけます。</div>

  <div class="urlbox">
    <div class="qr"><img src="${QR}" alt="QR"></div>
    <div class="ut">
      <div class="lead">▼ 送料かんたん計算（携帯のカメラでQRを読み取り）</div>
      <div class="url">${URL}</div>
      <div class="steps">① お届け先（都道府県）　② 長さ（2m／3m／4m）　③ 数量（束）　→　送料（税込）が表示されます<br>
      ・住所を貼り付けると都道府県が自動入力　・長さ違いの「混載」や大口（21束以上）にも対応</div>
    </div>
  </div>

  <h2>送料早見表（主要地域）　<span style="font-size:9pt;font-weight:normal;color:#444;">上段＝税込／下段＝税抜　・　配送：西濃運輸　・　法人様宛ての価格</span></h2>
  <table>
    <thead>
      <tr><th rowspan="2">お届け先</th><th colspan="2" class="grp">2m材</th><th colspan="2" class="grp">3m材</th><th colspan="2" class="grp">4m材</th></tr>
      <tr><th>5束</th><th>10束</th><th>5束</th><th>10束</th><th>5束</th><th>10束</th></tr>
    </thead>
    <tbody>${body}</tbody>
  </table>

  <div class="note">
    <div class="ttl">ご確認ください（基本のお取り扱い）</div>
    ・表示は<b>法人様宛て</b>の基本価格です（配送：<b>西濃運輸</b>／金額は税抜・税込を併記）。商品代金は含みません。1束＝<b>2m・4mは8枚／3mは10枚</b>です。<br>
    ・<b>個人のお客様は西濃運輸の支店止め</b>（最寄り支店でのお受け取り）となります。<br>
    ・<b>現場でのお降ろし（現場渡し）は別途費用</b>がかかります。<br>
    ・上表は主要地域の代表例です。<b>全都道府県・全数量・混載は上記URL（QR）でその場で計算</b>できます。<br>
    ・<b>北海道・沖縄・離島</b>は別途お見積り。<b>20束超</b>は複数便に分かれ到着日が分かれる場合があります。<br>
    ・数量・梱包状況により実際の送料が前後する場合があります。最終金額は請求書・見積書でご確認ください。
  </div>

  <div class="foot">
    <div>
      <b>株式会社 林材木店</b>　〒437-1203 静岡県磐田市福田 5490-47<br>
      MAIL：info@hayazai.com　／　HP：https://hayazai.com
    </div>
    <div class="tel">TEL 0538-58-2395</div>
  </div>
</body></html>`;

fs.writeFileSync(__dirname + '/fax_soryo.html', html);
console.log('fax_soryo.html を生成しました（行数:', ROWS.length, '）');
