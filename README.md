# 麻雀牌キーホルダー

**日本語 | [English](README.en.md)**

Git branch、GitHub Invertocat、發＋4列×3行のコントリビューショングリッド、**赤い中＋赤い円形Invertocat**の4種類です。中の字形はそのままに、下の絵柄を既存ロゴ牌と同じ公式SVGの輪郭へ差し替えました。ロゴの変形や描き直しは行わず、等比縮小して落ち着いた赤の平面インレイにしています。GitHub公式・公認商品ではありません。**Bambu Lab P1S・0.2 mmノズル・AMS・PLA用の設定済みプロジェクト3MF**を収録し、パーツの塗り直しは不要です。

[日本語で360°ビューを開く](https://ktanino10.github.io/github-mahjong-keychains/#ja) · [Open viewer in English](https://ktanino10.github.io/github-mahjong-keychains/#en) · [オフラインHTMLをダウンロード](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/docs/index.html)

![4種類のキーホルダーとボールチェーンの参考CG](docs/images/keychains-studio.png)

## ダウンロード

| プロジェクト | 印刷パーツ数 | 使用する色 |
| --- | ---: | --- |
| [既存3種類セット（変更なし）](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/all-three-P1S-0.2-AMS-PLA.3mf) | 10 | 白・黒・緑・薄緑 |
| [中（独立した新プロジェクト）](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/chun-P1S-0.2-AMS-PLA.3mf) | 3 | 白・黒・赤 |
| [Git branch](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/git-branch-P1S-0.2-AMS-PLA.3mf) | 3 | 白・黒・緑 |
| [Invertocat](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/invertocat-P1S-0.2-AMS-PLA.3mf) | 3 | 白・黒 |
| [發](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/print-package/projects/hatsu-P1S-0.2-AMS-PLA.3mf) | 4 | 白・黒・緑・薄緑 |

[印刷用一式ZIP（5プロジェクト・13 STL・日英説明・オフラインHTML）](https://github.com/ktanino10/github-mahjong-keychains/raw/refs/heads/main/docs/downloads/github-mahjong-keychains-P1S-0.2-AMS-PLA.zip)

**既存3種の4色セットと、中の3色は別の印刷プロジェクトです。** 全4種では白・黒・緑・薄緑・赤の計5色になるため、1台の4スロットAMSで同時には扱えません。全4種をまとめた5色の印刷プロジェクトは配布していません。中の印刷時は、必要に応じて緑系スプールを赤へ差し替え、プロジェクトの赤を実際のAMSスプールへ対応付けてください。既存4ファイルの色割当とURLは維持しています。

これらは表示色だけを付けた汎用3MFではありません。プリンター、工程、PLA設定、パーツのフィラメント番号、配置、パージ量を保存したBambu Studioプロジェクトです。金属チェーンやフックはSTL・3MFに含みません。印刷機へそのまま送るG-codeは配布していません。

## 印刷手順

1. **Bambu Studio 02.09.01.70**で3MFを「プロジェクト」として開きます。形状のみの読み込みや、パーツの個別自動配置はしないでください。
2. プリンターが **Bambu Lab P1S 0.2 nozzle**、PLAが下記の番号になっていることを確認します。既存3種用の4ファイルは共通の4色パレット、中だけは独立した白・黒・赤の3色パレットです。
3. 実際のAMSに入れたPLAスプールを、印刷ダイアログで対応させます。**プロジェクトの色番号は設定済みですが、物理的なAMSスロットとの対応は機器側の確認が必要です。** 実ノズルが0.2 mmであることも確認してください。
4. 設定済みのプレートは **Textured PEI Plate**、PLA温度はノズル220 °C・ベッド55 °Cです。実際に使用するプレートとスプールの指定温度が異なる場合は、実物に合わせてから再スライスしてください。
5. まず単品プロジェクトで試作し、プレビューの耳・インレイ・各色割当・パージタワーを確認します。印刷後は穴、積層の接合、欠け、色移りを確認してから金具を取り付けてください。

本リポジトリの生成・検証処理はプリンターに接続せず、送信や印刷開始を行いません。

### 色番号

**既存3種用の4プロジェクト：従来の共通パレット**

| プロジェクト番号 | 色 | 表示用RGB | 割当 |
| ---: | --- | --- | --- |
| 1 | 白 | `#F6F5EE` | 各牌の白い本体 |
| 2 | 黒 | `#161616` | 背面・耳全体・Invertocatインレイ |
| 3 | 緑 | `#238636` | Git branch・發・濃緑のグリッド |
| 4 | 薄緑 | `#9DD96C` | 發の薄緑のグリッド |

**中の専用プロジェクト：独立した3色パレット**

| プロジェクト番号 | 色 | 表示用RGB | 割当 |
| ---: | --- | --- | --- |
| 1 | 白 | `#F6F5EE` | 白い本体 |
| 2 | 黒 | `#161616` | 共通の背面・耳全体 |
| 3 | 赤 | `#B33220` | 中と公式SVG由来の円形Invertocat |

赤のSTLは、離れた中の字形と円形ロゴの2つの閉じた立体を1つの色パーツとして保持します。白い本体のくぼみに同じ座標で収まり、別々に自動配置する必要はありません。グラデーション印刷は使いません。赤は本作品の指定色であり、公式ロゴの標準色や一般的な改変・商品化許可を示すものではありません。

RGBは画面表示の目安で、特定メーカーのPLA色を保証するものではありません。[パーツ別対応表](print-package/parts-and-colors.csv)も収録しています。

### 保存済みの造形設定

積層・初層とも0.10 mm、外周6周、上下8層、充填100%（Rectilinear）、サポートなし、背面を下にした配置、パージタワーあり。外壁40 mm/s、内壁60 mm/s、上面30 mm/sとし、Generic PLAの0.2 mm用流量上限1.6 mm³/sを維持しています。色の混入を避けるため、モデルや充填へのフラッシュは無効です。

機種の親設定は公式のP1S 0.2 mmです。工程の親名は `0.10mm Standard @BBL X1C 0.2 nozzle` ですが、これは**公式P1S 0.2 mmプロファイル自身が既定として指定する共通工程**で、X1への機種変更ではありません。全フィラメントとも公式 `Generic PLA @0.2 nozzle` が親設定です。[設定と出典](validation/profile-provenance.json)

パージ量は濃色から淡色を多めにした初期値です。実際の顔料による色移りは試作で確認してください。既存3種類同時のスライサー推定は約11時間12分・約54 g、中単品は約4時間13分・20.4 g（いずれもパージ・タワー込み）です。実測値ではありません。

## 寸法と取付金具

| 項目 | 寸法 |
| --- | --- |
| 牌本体：高さ × 幅 × 厚み | **28 × 21 × 16.5 mm** |
| 耳を含む全高 | 36 mm |
| 耳の厚み / 穴径 | 5 mm / Ø4.6 mm |
| 本体の黒い背面 / 白い側面 | 5.5 mm / 11 mm |
| 黒白の共通境界 | z = 5.5 mm |
| 表面のインレイ | z = 15.7〜16.5 mm |

既存10個の印刷用STLと4つのプロジェクト3MFはバイト単位で変更していません。新しい中は同じ共通本体に3パーツを追加し、黒い背面・耳のSTLは既存品とバイト単位で同一です。耳の輪郭、本体サイズ、表裏の比率、既存ロゴ、發、グリッドは変更せず、本体を横断する穴も追加していません。AMOS SMARTとの一致は[掲載外寸](https://www.alban.co.jp/products/detail/682)のみで、材質・重量・強度の同等性を意味しません。

**標準表示：購入品を参考にしたボールチェーン。** [商品表記](https://www.amazon.co.jp/dp/B0DN6JW6LK)の球径2.4 mm・長さ120 mmを使用し、既存の耳を通るループを表示します。ピッチ、球数、コネクター寸法、垂れ方は概略です。銀色は表示例で、購入色を推定していません。コネクターを外し、球の付いた自由端を穴へ通して再接続する想定です。コネクター自体を穴に押し込まないでください。

**切替表示：回転カン付きワイヤーゲートフック。** [商品形状](https://www.amazon.co.jp/dp/B0FX47WYC4)を参考に、丸いフック、細いゲート、短い回転軸、下部丸カンを表示します。掲載寸法はタイトル42 mm、説明44 × 18 mmと差があり、内部比率は概略です。下部丸カンの内径・線径が不明のため**取付適合は未確認の参考表示**です。ボールチェーン取付を先行する設計方針は変えていません。商品画像や注文情報は配布していません。

**実機印刷・実物金具の適合・強度試験は未実施です。** PLAは高温で変形し得ます。耳を強く引かず、欠けや積層剥離があれば使用を止めてください。荷重を支える用途や安全に関わる用途には使わないでください。

## HTMLの使い方

ページ右上の **日本語 / English** で、設定、注意書き、動的状態、エラー、読み上げラベルまで切り替えられます。ダウンロードした `index.html` をブラウザで開けば、モデル、Three.js、フォント、画像を含め**外部通信なし**で表示します。「HTMLを保存」は選択中の言語を保持した単独ファイルを保存します。3MFへのダウンロードリンクはオンライン時に使用してください。

ドラッグ・1本指・矢印キーで回転、スクロール・ピンチ・`+` / `-` で拡大縮小、`Home` で全体表示。絵柄、表・裏・側面・斜め、金具の表示／非表示、金具の種類、自動回転を切り替えられます。自動回転は初期状態では停止しています。

4種類を並べて**見る**ことと、同じAMSで一度に**印刷する**ことは別です。中を選ぶと白・黒・赤だけが表示され、全4種では計5色と別プロジェクトの注意が表示されます。[日本語スクリーンショット](docs/images/viewer-ja-chun.png) · [English screenshot](docs/images/viewer-en-chun.png)

## 検証と再生成

中の完成3MFを**追加の設定ファイルを渡さず、公式Bambu Studio 02.09.01.70のCLIで再読込・スライス**しました。165層でプレートの警告欄は空、白・黒・赤の3色が実際に使われています。1〜55層は黒、56〜157層は白、158〜165層は白と赤です。個人設定・プリンター・アカウントを使わない隔離設定で実施しました。既存4ファイルは変更せず、同じ公式版で行った再読込・スライスの検証結果をSHA-256照合のうえ保持しています。

中の3パーツと2つの赤い連結成分は閉じた正体積のメッシュです。合計体積は共通の確定ブランクと一致し、ブール演算でも体積のある重複・欠落はありません（STL精度の照合許容差0.00002 mm）。頂点対応、全三角形の接続と向き、寸法、配置も3MF・GLBと照合しました。[中の形状検証](validation/validation-chun.json)

上の中は前版と同じSVGパス・位置・三角形接続を保持しています。下の円形Invertocatは既存ロゴ牌の輪郭と等比縮小後の頂点・側壁が一致し、赤い成分は中とロゴの2つだけです。旧猫頭の輪郭は残っていません。等比縮小時に平坦面の三角形分割は変わりますが、ロゴ輪郭は変更していません。`prepare_assets.py` は既存の公式SVGから下のロゴを再構成し、上の字形を保持します。

[スライサー検証](validation/slicer-checks.json) · [元STLのSHA-256](validation/accepted-meshes.json) · [ブラウザ検証](validation/browser-checks.json) · [配布ファイルのSHA-256](https://github.com/ktanino10/github-mahjong-keychains/blob/main/validation/deliverables.json)

デスクトップ版CLIは、任意の展開済みプロファイル検索や既存パージ行列に関する紛らわしい診断行を出します。これらを隠さず検証JSONに分類し、実際の保存色・使用フィラメント・全層と、空のプレート警告欄を別途確認しています。「全ログに警告が一切ない」という意味ではありません。

開発用にはPython 3.13、Node.js、Blender、上記Bambu Studioを使用します。印刷するだけなら再生成は不要です。

```sh
python3.13 -m pip install -r requirements.txt
python3.13 scripts/prepare_assets.py
python3.13 scripts/build_variant.py chun
python3.13 -m unittest discover -s scripts -p test_projects.py
python3.13 scripts/package_models.py --only chun --bambu "$BAMBU" --profiles "$BBL_PROFILES"
python3.13 scripts/validate_projects.py --only chun --bambu "$BAMBU"
"$BLENDER" --background --factory-startup --python scripts/render_scene.py
"$BLENDER" --background --factory-startup --python viewer/export_viewer.py
python3.13 viewer/check_geometry.py
python3.13 scripts/make_deliverables.py --poster-only
cd viewer
npm ci
npm run build
npm test
cd ..
python3.13 scripts/make_deliverables.py
python3.13 scripts/audit_public.py
```

`BAMBU` / `BLENDER` / `OPENSCAD` は実行ファイル、`BBL_PROFILES` は**アプリ同梱**の `Resources/profiles/BBL` ディレクトリです。個人のプリンター設定フォルダーは使いません。中間ファイルは `.work/` に保存します。上の例は中だけを再生成し、既存10 STL・4プロジェクトを保持します。全プロジェクトを再スライスして確認する場合のみ、検証コマンドの `--only chun` を外してください。印刷・再梱包だけならSTL再生成は不要です。

GitHub公式商品ではありません。**コードのMITライセンスはロゴ・字形・派生モデルを一括して自由利用可能にするものではありません。** [素材別の権利・ライセンス](ASSET-LICENSES.md)を確認してください。
