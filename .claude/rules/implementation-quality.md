# 実装品質保護ルール

## 原則

**動作するコードを書く、見せかけだけの実装をしない**

## 禁止事項

### ❌ 形骸化実装

```python
# 悪い例: 何もしない関数
def validate_user(user):
    pass  # TODO: 実装する

# 悪い例: 常に成功を返す
def save_to_database(data):
    return True  # 実際には保存していない
```

### ❌ ハードコードされた値を返す

```python
# 悪い例: 固定値を返す
def get_user_count():
    return 42  # 実際のカウントではない

# 悪い例: ダミーデータ
def fetch_users():
    return [{"id": 1, "name": "dummy"}]  # モックのまま
```

### ❌ エラーを握りつぶす

```python
# 悪い例: エラーを無視
def process_data(data):
    try:
        # 複雑な処理
        risky_operation(data)
    except:
        pass  # エラーを無視
```

### ❌ コメントで実装を済ませる

```python
# 悪い例: コメントだけ
def complex_calculation(x, y):
    # ここで複雑な計算をする
    # 1. xとyを検証
    # 2. 計算を実行
    # 3. 結果を返す
    return 0  # 実装なし
```

### ❌ 見せかけだけの条件分岐

```python
# 悪い例: 条件に関係なく同じ結果
def get_status(user):
    if user.is_active:
        return "active"
    else:
        return "active"  # 同じ値を返している
```

## 良い例

### ✅ 実際に動作する実装

```python
# 良い例: 本当に検証する
def validate_user(user):
    if not user.email:
        raise ValueError("メールアドレスが必要です")
    if not user.name:
        raise ValueError("名前が必要です")
    return True
```

### ✅ 実データを扱う

```python
# 良い例: 実際にカウントする
def get_user_count():
    return db.query(User).count()

# 良い例: 実データを取得
def fetch_users():
    return db.query(User).all()
```

### ✅ 適切なエラーハンドリング

```python
# 良い例: エラーを適切に処理
def process_data(data):
    try:
        risky_operation(data)
    except ValueError as e:
        logger.error(f"データ検証エラー: {e}")
        raise
    except DatabaseError as e:
        logger.error(f"データベースエラー: {e}")
        return None
```

### ✅ 実装を伴うコメント

```python
# 良い例: コメント + 実装
def complex_calculation(x, y):
    # 1. 入力値を検証
    if x < 0 or y < 0:
        raise ValueError("負の値は受け付けません")

    # 2. 計算を実行
    result = (x ** 2 + y ** 2) ** 0.5

    # 3. 結果を返す
    return round(result, 2)
```

### ✅ 意味のある条件分岐

```python
# 良い例: 条件によって異なる結果
def get_status(user):
    if user.is_active:
        return "active"
    else:
        return "inactive"
```

## 段階的実装のガイドライン

実装が複雑で一度に完成できない場合:

1. **明示的にマークする**
   ```python
   def advanced_feature():
       # FIXME: 現在は基本機能のみ実装
       # TODO: 高度な機能を追加する必要あり
       return basic_implementation()
   ```

2. **動作する最小限の機能を実装**
   ```python
   def search_users(query):
       # 現在は名前のみで検索
       # TODO: メールアドレス、電話番号での検索も追加
       return User.query.filter(User.name.contains(query)).all()
   ```

3. **Plans.md にタスクを追加**
   ```markdown
   - [ ] search_users に複数フィールドでの検索機能を追加
   ```

## 実装の優先順位

1. **動作するコード** > 完璧なコード
2. **テストが通る** > 美しいコード
3. **エラーが出ない** > 最適化されたコード

まず動くものを作り、その後で改善する。

## レビュー時のチェックリスト

- [ ] 関数は実際に動作するか?
- [ ] ハードコードされた値はないか?
- [ ] エラーを握りつぶしていないか?
- [ ] TODO/FIXME がある場合、Plans.md に追加されているか?
- [ ] テストが実際の機能をチェックしているか?

## まとめ

- 動作するコードを書く
- ハードコードやダミーデータを避ける
- エラーを適切に処理する
- 段階的実装でも、動く最小限の機能を実装する
- TODO は Plans.md で管理する

**動かないコードは、ないのと同じです。**
