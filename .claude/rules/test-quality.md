# テスト品質保護ルール

## 原則

**テストは守るもの、改ざんするものではない**

テストが失敗したとき、取るべき行動は以下のいずれかです:

1. **実装コードを修正する** (推奨)
   - テストが正しく、実装に問題がある場合

2. **テストの期待値を更新する**
   - 仕様変更により、期待値が変わった場合
   - 必ず理由を明記する

3. **テストを追加する**
   - カバレッジが不足している場合

## 禁止事項

### ❌ テストを削除・無効化する

```python
# 悪い例: テストをコメントアウト
# def test_user_creation():
#     user = create_user("test")
#     assert user.name == "test"
```

### ❌ テストをスキップする

```python
# 悪い例: 無条件でスキップ
@pytest.mark.skip("動かないから")
def test_important_feature():
    ...
```

### ❌ テストを形骸化する

```python
# 悪い例: 常に通るテスト
def test_calculation():
    result = calculate(1, 2)
    assert True  # 何もチェックしていない
```

### ❌ try-except でエラーを隠す

```python
# 悪い例: エラーを握りつぶす
def test_validation():
    try:
        validate_data(invalid_data)
        assert True
    except:
        pass  # エラーを無視
```

## 良い例

### ✅ 実装を修正する

```python
# テスト (変更なし)
def test_user_creation():
    user = create_user("test")
    assert user.name == "test"

# 実装を修正
def create_user(name):
    return User(name=name)  # バグを修正
```

### ✅ 仕様変更時に理由を明記して更新

```python
# テストを更新 (理由あり)
def test_user_creation():
    # 仕様変更: ユーザー名は大文字で保存する
    user = create_user("test")
    assert user.name == "TEST"  # 期待値を変更
```

### ✅ カバレッジを追加

```python
# 新しいテストケースを追加
def test_user_creation_with_empty_name():
    with pytest.raises(ValueError):
        create_user("")
```

## テスト失敗時のフロー

```
テスト失敗
    ↓
1. エラーメッセージを読む
    ↓
2. 原因を特定する
    ↓
3. 選択肢:
   - 実装にバグ → 実装を修正
   - 仕様変更 → テストを更新 (理由を明記)
   - カバレッジ不足 → テストを追加
    ↓
4. 修正後、再度テストを実行
    ↓
5. 全テストが通ることを確認
```

## 例外ケース

以下の場合のみ、テストをスキップできます:

1. **環境依存のテスト**
   ```python
   @pytest.mark.skipif(sys.platform != "linux", reason="Linux専用機能")
   def test_linux_feature():
       ...
   ```

2. **外部サービス依存のテスト**
   ```python
   @pytest.mark.skipif(not has_api_key(), reason="APIキーが必要")
   def test_external_api():
       ...
   ```

必ず `reason` を明記してください。

## まとめ

- テストが失敗したら、実装を疑う
- テストを削除・無効化・形骸化しない
- 仕様変更時は理由を明記してテストを更新
- カバレッジを追加して品質を向上

**テストはプロジェクトの品質を守る最後の砦です。**
