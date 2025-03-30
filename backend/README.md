source venv/bin/activate
brew install portaudio

uvicorn app:app --reload --port 5000
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uvicorn app.main:app --reload --host 127.0.0.1 --port 5000



# AI Agent

AI Agent は、ユーザーからの指示を受け取り、タスクを計画、実行、および評価するための **FastAPI** ベースのプロジェクトです。本プロジェクトは、高度なタスク自動化の基礎を提供することを目的としています。

## 特徴

- **タスク自動化**: タスクを分解し順次実行。
- **評価機構**: 実行結果を評価し再計画。
- **SQLite を標準サポート**: 簡易設定で利用可能。

---

## 目次

1. [セットアップ](#セットアップ)
2. [クイックスタート](#クイックスタート)
   - [タスク作成](#タスク作成)
   - [タスク確認](#タスク確認)
   - [タスク実行](#タスク実行)
3. [ディレクトリ構成](#ディレクトリ構成)
4. [テストの実行](#テストの実行)
5. [ドキュメントの参照](#ドキュメントの参照)
6. [貢献ガイドライン](#貢献ガイドライン)

---

## セットアップ

### 必要条件

- Python 3.9 以上
- SQLite データベース

### インストール手順

1. **リポジトリのクローン**
   ```bash
   git clone https://github.com/<あなたのリポジトリ>.git
   cd <クローンしたディレクトリ>
   ```

2. **仮想環境の作成**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
   ```

3. **依存パッケージのインストール**
   ```bash
   pip install -r requirements.txt
   ```

4. **環境変数ファイル（.env）の作成**
   `.env` ファイルをプロジェクトルートに作成し、以下を記載します。
   ```env
   LOG_DIR=./log
   LOG_LEVEL=DEBUG
   DATABASE_URL=sqlite:///./app/tasks.db
   OPENAI_API_KEY=<your API Key>
   GEMINI_API_KEY=<your API Key>
   ```

5. **アプリケーションの起動**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

アプリケーションは `http://localhost:8000` で利用可能です。

---

## クイックスタート

### タスク作成

```bash
curl -X POST "http://localhost:8000/task/create" \
    -H "Content-Type: application/json" \
    -d '{
        "user_goal": "Test Task",
        "user_context": {"priority": "high"},
        "contents": [{"action": "fetch_data", "params": {"url": "https://example.com"}}]
    }'
```

- **出力例**:
  ```json
  {
      "task_id": "<task_id>",
      "contents": [...],
      "current_index": 0,
      "results": [],
      "execute_count": 0,
      "created_at": "2024-01-01T12:00:00",
      "updated_at": "2024-01-01T12:00:00"
  }
  ```

### タスク確認

作成したタスクの進捗や状態を取得します。

```bash
curl -X GET "http://localhost:8000/task/<task_id>"
```

### タスク実行

タスクを順次実行します。

```bash
curl -X POST "http://localhost:8000/task/<task_id>/execute"
```

---

## ディレクトリ構成

本プロジェクトのディレクトリ構成は以下の通りです。

```
<project>/
├── app/
│   ├── api/                # エンドポイントディレクトリ
│   ├── core/               # アプリケーションの設定やロジック
│   ├── db/                 # データベース接続
│   ├── models/             # データベースモデル
│   ├── schemas/            # Pydanticスキーマ
│   ├── services/           # ビジネスロジック
│   ├── utils/              # ヘルパー関数
│   └── main.py             # アプリケーションエントリーポイント
├── docs/                   # MkDocsによるドキュメント
├── tests/                  # pytestによるテストコード
└── requirements.txt        # 必要なパッケージリスト
```

---

## テストの実行

1. **pytestを利用したテストの実行**
   ```bash
   pytest
   pytest tests/test_task.py --maxfail=1 --disable-warnings
   ```

2. **カバレッジレポートの生成**
   ```bash
   pytest --cov=app
   ```

---

## ドキュメントの参照

アプリケーションのAPIや仕様についての詳細な説明は MkDocs で確認可能です。

1. **必要なツールのインストール**
   ```bash
   pip install mkdocs mkdocs-material mkdocstrings mkdocstrings-python mkdocs-toc-md
   ```

2. **ローカルサーバーでドキュメントを表示**
   ```bash
   mkdocs serve
   ```

   デフォルトで `http://localhost:8000` で閲覧可能です。

---

## 貢献ガイドライン

1. **フォーク**
   プロジェクトをフォークし、ローカル環境で開発を行います。

2. **ブランチ作成**
   ```bash
   git checkout -b "feature/新機能名"
   ```

3. **変更内容のコミット**
   適切なコミットメッセージを書きます。
   ```bash
   git commit -m "Add: 新しいエンドポイントを追加"
   ```

4. **プルリクエスト**
   変更内容を記載したプルリクエストを作成します。

---

## ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) のもと提供されます。

---

## 他の参考資料

- **[FastAPI Documentation](https://fastapi.tiangolo.com/)**
- **[SQLAlchemy Documentation](https://docs.sqlalchemy.org/)**

---

**© 2025 AI Agent Project. All rights reserved.**