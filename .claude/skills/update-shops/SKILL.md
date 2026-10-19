---
name: update-shops
description: スクレイパーリポジトリ（Osaka_eki_bld_Webscraping）の最新データを osaka-ekibiru-data の data/*.json に反映し、更新した店舗の不足情報（tags・description・google_rating）を補完する。「データ更新して」「最新データ反映」などで使う。
---

# 店舗データ更新

作業は Mac と Windows PC の両方で行う。どちらの PC で作業しているかを判定し、パスとコマンドを切り替える。

- 反映先: このリポジトリ（osaka-ekibiru-data）の `data/*.json`
- スクレイパー側: 同じ親フォルダにある `Osaka_eki_bld_Webscraping` の `data/*.json`
  （Mac では `/Users/dan/src/Osaka_eki_bld_Webscraping`）。見つからない場合はユーザーに場所を聞く。まだ clone していなければ `https://github.com/OddMaro/Osaka_eki_bld_Webscraping.git` を clone するか聞く。

| | Mac | Windows |
|---|---|---|
| Python | `python3` | `python`（無ければ `py`） |
| スクレイパーの venv | `.venv/bin/python` | `.venv\Scripts\python.exe` |
| 差分 | `diff -u` | Python の `difflib` で比較する（Windows に `diff` が無い場合があるため） |

Windows では、JSON の読み書きに必ず `encoding="utf-8"` を指定する。コンソール出力が文字化けする場合は `PYTHONIOENCODING=utf-8` を設定する。

## 0. 両方のリポジトリを最新にする

もう一方の PC で更新・push している場合があり、スクレイパー側は GitHub Actions が毎週データを更新しているので、作業前に必ず最新にする。

1. 両方のリポジトリで `git status` を確認する。未コミットの変更があれば、pull する前にユーザーに確認する。
2. 反映先（osaka-ekibiru-data、main ブランチ）で `git pull` を実行する。
3. スクレイパー側（master ブランチ）で `git pull` を実行する。

## 1. 差分を確認する

12ファイルそれぞれを比較し、変化を分類する。

- 店名の入れ替わり（同じ id で name が違う）
- 新規店舗（スクレイパー側にだけある id）
- 閉店（反映先にだけある id。空き区画になったものも含む）
- 空き区画の subcategory の変化だけ → **反映しない**

## 2. 反映する

- 変化のあった店舗だけを書き換える。それ以外の店舗は、反映先にある値（手入力の tags・評価など）をそのまま残す。
- 店舗の並び順はスクレイパー側に合わせる。
- 全店舗が次の11項目をこの順で持つようにする。スクレイパー側に無い項目は既定値で補う。
  `id, name, category, subcategory, url, tags([]), open(""), added_at, google_rating(null), price_range(null), description("")`
- 店名が入れ替わった店舗は、旧店の tags・google_rating・description を引き継がない。
- 空き区画（category `empty`）の subcategory は `""` にする。
- JSON は `ensure_ascii=False, indent=2`、**ファイル末尾に改行を付けない**（既存ファイルの形式）。

## 3. 更新した店舗の不足情報を補完する

- **tags**: 日本語で4つ。他のビルに同じチェーンの店舗があれば、その tags を参考にする。無ければ Web 検索（ホットペッパー等）で業態を調べて付ける。
- **description**: 1〜2文の日本語（例:「髪質改善を専門とする美容室。…」）。調べて確認できた事実だけを書き、推測は書かない。
- **google_rating**: スクレイパー側の `.venv` と `.env` の `GOOGLE_MAPS_API_KEY` を使い（`.env` や `.venv` は git 管理外なので、その PC に無い場合は `null` のままにし、報告で伝える）、Places API (New) の searchText で `"{店名} 大阪駅前第Nビル"` を検索する（短縮形の `1bld` ではなく正式なビル名を使う）。displayName と formattedAddress を出力し、**該当ビルの該当店舗であることを確認できた場合だけ**評価を入れる。別店舗や別のビルの支店がヒットした場合は `null` のままにする。
- **price_range**: 飲食店だけ Places の priceLevel を変換して入れる（`add_shop_details.py` の PRICE_LEVEL_MAP）。飲食店以外は `null`。
- **open**: 空欄のままにする。

## 4. 確認と報告

- `scripts/validate_open.py` を実行する（Mac は `python3`、Windows は `python`）。
- 変更した店舗の一覧、反映しなかった差分とその理由、`null` のまま残した項目とその理由を報告する。
- コミット・push は、ユーザーに指示されるまでしない。
