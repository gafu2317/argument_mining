import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

class LLMClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # キーがない場合はエラーを出さずに、UI側でハンドリングさせるためにNoneにしておく
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)

    def fetch_json(self, system_prompt: str, user_text: str) -> dict:
        """
        LLMにプロンプトを投げ、JSONオブジェクト(dict)として返す。
        """
        if not self.client:
            raise ValueError("API Key is missing. Please set OPENAI_API_KEY in .env file.")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text}
                ],
                response_format={"type": "json_object"},  # 強制的にJSONを出力させる
                temperature=0  # 毎回同じ結果になるようにランダム性を排除
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            print(f"LLM Error: {e}")
            raise e