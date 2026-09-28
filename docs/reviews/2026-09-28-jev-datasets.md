# レビュー: Jev による要確認データセットの判定（2026-09-28）

エージェント（Jev の組み合わせ判定, spec 0009 §7.2）がルールの「要確認」を採用・不採用に振り分けた結果。
違和感のあるものは `data/manifests/overrides.json` で上書きする（`<feature>/<datasetId>`）。

## 採用（3 件）

| feature | 組織 | データセット | Jev | 確信度 | 一覧 |
| --- | --- | --- | --- | --- | --- |
| park | 葛飾区 | [区内施設一覧](https://catalog.data.metro.tokyo.lg.jp/dataset/t131229d0000000002) | mixed | 0.99 | 0.89 |
| publicFacility | 町田市 | [中規模集会施設](https://catalog.data.metro.tokyo.lg.jp/dataset/t132098d0000000012) | publicFacility | 1.00 | 0.90 |
| tourism | 葛飾区 | [区内施設一覧](https://catalog.data.metro.tokyo.lg.jp/dataset/t131229d0000000002) | mixed | 0.99 | 0.89 |

## 不採用（92 件）

ほぼすべて統計・利用集計・調査報告・資料集（「一覧」の値が低い）。

| feature | 組織 | データセット | Jev | 確信度 | 一覧 |
| --- | --- | --- | --- | --- | --- |
| culture | 東京都交通局 | [都営バス　バスのりば](https://catalog.data.metro.tokyo.lg.jp/dataset/t000018d0000000043) | none | 0.99 | 0.42 |
| culture | 東京都総務局 | [くらしと統計2025](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d2000000338) | none | 1.00 | 0.03 |
| culture | 大田区 | [郷土博物館の入館者](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000236) | culture | 0.97 | 0.18 |
| culture | 大田区 | [令和5年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000270) | none | 1.00 | 0.08 |
| culture | 大田区 | [令和4年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000373) | none | 1.00 | 0.06 |
| culture | 大田区 | [郷土博物館の入館者](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000195) | culture | 0.97 | 0.18 |
| culture | 大田区 | [令和6年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000224) | none | 1.00 | 0.06 |
| culture | 東京都保健医療局 | [TOKYO WALKING MAP](https://catalog.data.metro.tokyo.lg.jp/dataset/t000055d0000000363) | none | 0.81 | 0.25 |
| culture | 八王子市 | [統計八王子関連オープンデータ一覧（平成27年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132012d0000000006) | none | 1.00 | 0.03 |
| culture | 八王子市 | [統計八王子関連オープンデータ一覧（平成28年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132012d0000000007) | none | 1.00 | 0.03 |
| culture | 調布市 | [博物館収蔵資料保管庫(施設カルテ)](https://catalog.data.metro.tokyo.lg.jp/dataset/t132080d3100000279) | culture | 0.85 | 0.29 |
| culture | 東京都環境局 | [都内中小規模事業所を対象とした「東京都地球温暖化対策報告書制度」＿低炭素ベンチマーク[2012年度実績改訂版〕](https://catalog.data.metro.tokyo.lg.jp/dataset/t000009d0000000020) | none | 1.00 | 0.13 |
| library | 大田区 | [令和5年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000270) | none | 1.00 | 0.08 |
| library | 大田区 | [令和4年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000373) | none | 1.00 | 0.06 |
| library | 大田区 | [令和6年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000224) | none | 1.00 | 0.06 |
| library | 八王子市 | [統計八王子関連オープンデータ一覧（平成27年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132012d0000000006) | none | 1.00 | 0.03 |
| library | 八王子市 | [統計八王子関連オープンデータ一覧（平成28年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132012d0000000007) | none | 1.00 | 0.03 |
| library | 東京都教育庁 | [都立中央図書館　利用案内_開架新聞のリスト](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000163) | library | 0.73 | 0.10 |
| library | 練馬区 | [図書館所蔵資料数](https://catalog.data.metro.tokyo.lg.jp/dataset/t131202d0000000034) | library | 0.96 | 0.16 |
| library | 東京都教育庁 | [東京都公立図書館調査　平成29年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d0000000019) | library | 1.00 | 0.16 |
| library | 東京都教育庁 | [東京都公立図書館調査　平成31年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d0000000020) | library | 1.00 | 0.16 |
| library | 東京都教育庁 | [東京都公立図書館調査　令和2年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d0000000021) | library | 1.00 | 0.15 |
| library | 東京都教育庁 | [東京都公立図書館調査　平成28年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d0000000022) | library | 0.99 | 0.17 |
| library | 東京都教育庁 | [都内公立図書館インターネット等サービス状況](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d0000000023) | library | 1.00 | 0.11 |
| library | 東京都教育庁 | [東京都公立図書館調査　令和3年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d0000000024) | library | 1.00 | 0.16 |
| library | 東京都教育庁 | [東京都公立図書館調査　平成30年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d1700000001) | library | 1.00 | 0.17 |
| library | 東京都教育庁 | [東京都公立図書館調査　令和4年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000181) | library | 0.96 | 0.11 |
| library | 東京都教育庁 | [東京都公立図書館調査　令和5年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000182) | library | 0.97 | 0.12 |
| library | 東京都教育庁 | [東京都公立図書館調査　令和6年度](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000183) | library | 0.96 | 0.12 |
| library | 港区 | [港区の図書館利用集計](https://catalog.data.metro.tokyo.lg.jp/dataset/t131032d0000000277) | library | 0.93 | 0.05 |
| library | 狛江市 | [図書館登録者数の状況（図書館）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132195d0000000243) | library | 0.95 | 0.06 |
| library | 東京都環境局 | [都内中小規模事業所を対象とした「東京都地球温暖化対策報告書制度」＿低炭素ベンチマーク[2012年度実績改訂版〕](https://catalog.data.metro.tokyo.lg.jp/dataset/t000009d0000000020) | none | 1.00 | 0.13 |
| library | 府中市 | [府中市統計書オープンデータ_民生](https://catalog.data.metro.tokyo.lg.jp/dataset/t132063d0000000006) | library | 0.80 | 0.08 |
| library | 狛江市 | [図書館登録者数の状況（図書館）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132195d0000000061) | library | 0.95 | 0.06 |
| library | 東京都教育庁 | [読書状況調査集計結果_平成２７年度_【調査２】学校における読書活動等に関する取組状況の調査（p.30）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000026) | none | 0.98 | 0.03 |
| library | 東京都教育庁 | [平成19年度調査研究報告_参考文献（PDF：813KB）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000028) | library | 0.98 | 0.09 |
| library | 東京都教育庁 | [教員の職のあり方検討委員会報告について_「これからの教員の任用制度について～新たな職の視点から～」](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000029) | none | 0.99 | 0.03 |
| library | 東京都教育庁 | [教育管理職等の任用・育成のあり方検討委員会第１次報告について_これからの教育管理職・指導主事の選考・育成制度について](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000030) | none | 1.00 | 0.02 |
| library | 東京都教育庁 | [教育管理職等の任用・育成のあり方検討委員会 第２次報告について_「副校長・主幹教諭の育成及び職のあり方について」～教育管理職等の任用･育成のあり方検討委員会　第２次報告～](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000031) | none | 1.00 | 0.02 |
| library | 東京都教育庁 | [教育管理職等の任用・育成のあり方検討委員会最終報告について_「これからの教育管理職等の任用･育成及び職のあり方について」～教育管理職等の任用・育成のあり方検討委員会　最終報告～](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000032) | none | 0.89 | 0.05 |
| library | 東京都教育庁 | [都立高等学校補欠募集の一層の活用・推進〔生徒の進路変更の希望に応え、再チャレンジを支援する仕組みの強化〕に向けて_都立高等学校補欠募集の実施に関するガイドライン](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000033) | none | 1.00 | 0.05 |
| library | 東京都教育庁 | [平成30年度東京都立高等学校入学者選抜検討委員会報告について_平成30年度東京都立高等学校入学者選抜検討委員会報告書](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000034) | none | 1.00 | 0.03 |
| library | 東京都教育庁 | [読書状況調査集計結果_平成２７年度_【調査２】学校における読書活動等に関する取組状況の調査（p.30）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000021d2000000168) | none | 0.96 | 0.04 |
| park | 大田区 | [令和5年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000270) | none | 1.00 | 0.08 |
| park | 大田区 | [令和4年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000373) | none | 1.00 | 0.06 |
| park | 大田区 | [令和6年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000224) | none | 1.00 | 0.06 |
| park | 東京都保健医療局 | [TOKYO WALKING MAP](https://catalog.data.metro.tokyo.lg.jp/dataset/t000055d0000000363) | none | 0.81 | 0.25 |
| park | 八王子市 | [統計八王子関連オープンデータ一覧（平成27年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132012d0000000006) | none | 1.00 | 0.03 |
| park | 八王子市 | [統計八王子関連オープンデータ一覧（平成28年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t132012d0000000007) | none | 1.00 | 0.03 |
| park | 調布市 | [しばさき公園北第1・第2学童クラブ(施設カルテ)](https://catalog.data.metro.tokyo.lg.jp/dataset/t132080d3100000035) | none | 0.83 | 0.24 |
| park | 東京都都市整備局 | [東京の土地２０２３（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d0000000040) | none | 1.00 | 0.06 |
| park | 東京都都市整備局 | [東京の土地２０２４（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d2000000023) | none | 1.00 | 0.06 |
| park | 東京都都市整備局 | [東京の土地２０２０（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d0000000034) | none | 1.00 | 0.07 |
| park | 東京都交通局 | [都営バス　バスのりば](https://catalog.data.metro.tokyo.lg.jp/dataset/t000018d0000000043) | none | 0.99 | 0.21 |
| park | 東京都総務局 | [三宅島噴火災害誌 資料編_資料2 平成18年版 管内概要 東京都三宅支庁](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000021) | none | 1.00 | 0.06 |
| park | 東京都総務局 | [東京の防災プラン進捗レポート2017 【第2部】◆ 震災対策（区部・多摩地域における地震）_３　出火・延焼の抑制](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000051) | none | 0.97 | 0.08 |
| park | 東京都総務局 | [東京の防災プラン進捗レポート2017 【第2部】◆ 震災対策（区部・多摩地域における地震）_４　安全で迅速な避難の実現](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000052) | none | 0.98 | 0.06 |
| park | 東京都総務局 | [東京の防災プラン進捗レポート2017 【第2部】◆ 震災対策（区部・多摩地域における地震）_９　公助による救出救助活動の展開](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000057) | none | 0.98 | 0.06 |
| park | 東京都都市整備局 | [東京の土地２０２１（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d0000000036) | none | 1.00 | 0.06 |
| park | 東京都都市整備局 | [東京の土地２０２２（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d0000000039) | none | 1.00 | 0.09 |
| park | 府中市 | [府中市統計書オープンデータ_民生](https://catalog.data.metro.tokyo.lg.jp/dataset/t132063d0000000006) | none | 1.00 | 0.03 |
| park | 府中市 | [府中市統計書オープンデータ_建設・住居](https://catalog.data.metro.tokyo.lg.jp/dataset/t132063d0000000007) | park | 0.94 | 0.09 |
| park | 東京都総務局 | [若者へのオンラインアンケート調査結果](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d2000001056) | none | 1.00 | 0.05 |
| park | 東京都都市整備局 | [東京の土地２０１８（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d0000000032) | none | 1.00 | 0.06 |
| park | 東京都都市整備局 | [東京の土地２０１９（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d0000000033) | none | 1.00 | 0.07 |
| park | 東京都都市整備局 | [東京の土地２０１７（土地関係資料集）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d1800000013) | none | 1.00 | 0.06 |
| park | 東京都都市整備局 | [みどりの新戦略ガイドライン【本文】　資料編](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d1900000007) | none | 0.78 | 0.05 |
| park | 東京都建設局 | [主要事業の用地取得進捗状況等](https://catalog.data.metro.tokyo.lg.jp/dataset/t000014d1700000024) | none | 0.86 | 0.29 |
| park | 東京都建設局 | [「パークマネジメントマスタープラン」策定（平成１６年度）_本文 [1,424KB]](https://catalog.data.metro.tokyo.lg.jp/dataset/t000014d2000000008) | park | 0.79 | 0.08 |
| publicFacility | 町田市 | [地質調査地点一覧](https://catalog.data.metro.tokyo.lg.jp/dataset/t132098d0000000026) | none | 0.81 | 0.78 |
| publicFacility | 町田市 | [市民バス・コミュニティバス](https://catalog.data.metro.tokyo.lg.jp/dataset/t132098d0000000081) | none | 0.96 | 0.67 |
| publicFacility | 東京都財務局 | [令和５年度　決算の状況](https://catalog.data.metro.tokyo.lg.jp/dataset/t000004d2000000033) | none | 1.00 | 0.02 |
| publicFacility | 東京都財務局 | [令和６年度　決算の状況](https://catalog.data.metro.tokyo.lg.jp/dataset/t000004d2000000035) | none | 1.00 | 0.02 |
| publicFacility | 大田区 | [区民センターの利用](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000182) | publicFacility | 0.98 | 0.29 |
| publicFacility | 大田区 | [令和5年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000270) | none | 1.00 | 0.08 |
| publicFacility | 大田区 | [令和4年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000373) | none | 1.00 | 0.06 |
| publicFacility | 大田区 | [区民センターの利用](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000142) | publicFacility | 0.98 | 0.29 |
| publicFacility | 大田区 | [令和6年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000224) | none | 1.00 | 0.06 |
| publicFacility | 東京都財務局 | [令和４年度　決算の状況](https://catalog.data.metro.tokyo.lg.jp/dataset/t000004d2000000022) | none | 1.00 | 0.02 |
| publicFacility | 世田谷区 | [公衆無線LANアクセスポイント一覧](https://catalog.data.metro.tokyo.lg.jp/dataset/t131121d0000000004) | none | 0.96 | 0.56 |
| publicFacility | 品川区 | [戸籍窓口関係証明の発行枚数](https://catalog.data.metro.tokyo.lg.jp/dataset/t131091d3100000003) | none | 0.98 | 0.12 |
| publicFacility | 東京都都市整備局 | [防災街区整備事業](https://catalog.data.metro.tokyo.lg.jp/dataset/t000008d1700000003) | none | 0.97 | 0.27 |
| tourism | 東京都総務局 | [三宅支庁管内概要（令和６年版）](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d2000001097) | none | 1.00 | 0.05 |
| tourism | 大田区 | [令和5年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d0000000270) | none | 1.00 | 0.08 |
| tourism | 大田区 | [令和6年度区政ファイルデータ](https://catalog.data.metro.tokyo.lg.jp/dataset/t131113d3100000224) | none | 1.00 | 0.06 |
| tourism | 東京都保健医療局 | [TOKYO WALKING MAP](https://catalog.data.metro.tokyo.lg.jp/dataset/t000055d0000000363) | none | 0.81 | 0.25 |
| tourism | 東京都総務局 | [三宅島噴火災害誌 資料編_資料2 平成18年版 管内概要 東京都三宅支庁](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000021) | none | 1.00 | 0.06 |
| tourism | 東京都総務局 | [南海トラフ巨大地震等による東京の被害想定（平成25年5月14日公表）_第1部 被害想定結果](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000042) | none | 1.00 | 0.24 |
| tourism | 東京都総務局 | [東京の防災プラン進捗レポート2017 【第2部】◆ 震災対策（区部・多摩地域における地震）_５　各種情報の的確な発信](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000053) | none | 1.00 | 0.04 |
| tourism | 東京都総務局 | [東京の防災プラン進捗レポート2017 【第2部】 ◆ 震災対策(島しょ地域における地震)_２　島しょ地域における備蓄・輸送体制の確保](https://catalog.data.metro.tokyo.lg.jp/dataset/t000003d1700000059) | none | 0.98 | 0.06 |
| tourism | 東京都環境局 | [観光バスの環境性能表示に係るガイドライン](https://catalog.data.metro.tokyo.lg.jp/dataset/t000009d1800000011) | none | 0.98 | 0.03 |
| tourism | 東大和市 | [オープンデータ一覧](https://catalog.data.metro.tokyo.lg.jp/dataset/t132209d0000000005) | tourism | 0.92 | 0.24 |
