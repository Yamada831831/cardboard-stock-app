📘 段ボール在庫管理システムについて（README）
このシステムは、段ボールの在庫を管理するために構築されたWebアプリケーションです。PC・スマートフォンのどちらでも利用でき、現場での操作性を重視して設計されています。

🖥 使用技術
区分	使用技術
フロントエンド	HTML / JavaScript（Bootstrap 5）
バックエンド	Python（Flask）
データベース	PostgreSQL（NeonクラウドDB）
デプロイ	Render（無料プラン）
外部連携	n8n（Webhookでログ保存）
🔧 主な機能
段ボールの種類登録・編集・削除

在庫数の入荷（追加）・使用（減少）処理

シーズンオフの段ボールを一覧から非表示にできる

操作ログの記録（使用・戻し・数量・操作端末・コメント付き）

操作ログはCSV形式でダウンロード可能

🔐 ユーザー識別
ログイン機能はありません。

ブラウザのlocalStorageを利用して、端末ごとに自動で固有IDを割り当てています。

固有IDには任意の表示名（ニックネーム）を紐づけることができ、管理者がデータベース上で設定します。

🧾 データベース構成（主要テーブル）
テーブル名	内容
cardboard_types	段ボールの種類（名前・サイズ・備考）
cardboard_stock	在庫（数量、シーズンオフ設定、種類ID）
stock_operation_logs	操作履歴（使用・戻し・コメント等）
operator_aliases	固有IDと表示名の紐づけ管理
🗃 データのリセット・削除方法
操作ログをリセットする場合（NeonのSQLエディタから実行）：

sql
コピーする
編集する
TRUNCATE TABLE stock_operation_logs RESTART IDENTITY;
🛠 補足事項
操作ログはFlaskとn8nの両方で記録されています。

ログイン不要のため、端末識別と表示名の登録を適切に行うことが重要です。

デプロイ後はRenderのダッシュボードで状態を確認してください。

n8nはRenderでホストされており、Webhook URLは /webhook/operation_logs です。

📂 その他
Gitリポジトリやコードを引き継ぐ場合は、app.py、templates/、static/、requirements.txt を含めてください。

データベースURLやWebhook URL、Render環境の情報は安全な場所に保存しておいてください。

ご不明点やトラブルがあれば、Flask、PostgreSQL、n8n、Renderの各公式ドキュメントをご参照ください。

