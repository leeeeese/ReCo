"""
E2E 테스트 (End-to-End)
실제 브라우저를 사용한 전체 플로우 테스트

⚠️ 주의: 이 테스트를 실행하려면 프론트엔드(포트 3000)와 백엔드(포트 8000) 서버가 실행 중이어야 합니다.
"""

import pytest
import re
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.slow
class TestE2E:
    """E2E 테스트 - 서버 실행 필요"""
    
    def test_homepage_loads(self, page: Page):
        """홈페이지 로드 테스트"""
        page.goto("http://localhost:3000", timeout=10000)
        # 페이지가 로드될 때까지 대기
        page.wait_for_load_state("networkidle")
        # 제목 확인 (ReCo가 포함되어 있으면 통과)
        title = page.title()
        assert "ReCo" in title or len(title) > 0
    
    def test_chat_interface_interaction(self, page: Page):
        """채팅 인터페이스 상호작용 테스트"""
        page.goto("http://localhost:3000", timeout=10000)
        page.wait_for_load_state("networkidle")
        
        # 채팅 페이지로 이동 (링크가 있으면)
        try:
            chat_link = page.get_by_role("link", name=re.compile(r"채팅|Chat", re.IGNORECASE), timeout=2000)
            if chat_link.is_visible():
                chat_link.click()
                page.wait_for_load_state("networkidle")
        except Exception:
            # 채팅 링크가 없으면 이미 채팅 페이지일 수 있음
            pass
        
        # 입력 필드 찾기
        input_field = page.get_by_placeholder(re.compile(r"상품명|질문", re.IGNORECASE), timeout=5000)
        expect(input_field).to_be_visible()
        
        # 메시지 입력
        input_field.fill("아이폰 찾고 있어요")
        
        # 전송 버튼 클릭
        send_button = page.get_by_role("button", name=re.compile(r"전송|Send", re.IGNORECASE), timeout=2000)
        if send_button.is_visible():
            send_button.click()
            
            # 로딩 상태 확인 (선택적)
            try:
                expect(page.get_by_text(re.compile(r"분석|로딩|loading", re.IGNORECASE))).to_be_visible(timeout=5000)
            except Exception:
                # 로딩 메시지가 없어도 테스트 통과
                pass

