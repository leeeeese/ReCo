"""OpenAI API 키 테스트 스크립트"""
from openai import OpenAI
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 확인
api_key = os.getenv('OPENAI_API_KEY')
print(f"API 키: {api_key[:20]}...{api_key[-10:] if api_key else 'None'}")

# OpenAI 클라이언트 생성
try:
    client = OpenAI(api_key=api_key)
    print("\n✅ OpenAI 클라이언트 생성 성공")

    # 간단한 테스트 호출
    print("API 호출 테스트 중...")
    response = client.chat.completions.create(
        model='gpt-5-mini',
        messages=[{'role': 'user', 'content': 'Say hello in Korean'}],
        max_completion_tokens=500
    )

    print(f"✅ API 키 정상 작동! 응답: {response.choices[0].message.content}")

except Exception as e:
    print(f"❌ 오류 발생: {e}")
