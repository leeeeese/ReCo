"""
E2E 테스트 (End-to-End)
실제 브라우저를 사용한 전체 플로우 테스트
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
@pytest.mark.slow
class TestE2E:
    """E2E 테스트"""
    
    def test_homepage_loads(self, page: Page):
        """홈페이지 로드 테스트"""
        page.goto("http://localhost:3000")
        expect(page).to_have_title(/ReCo/i)
    
    def test_chat_interface_interaction(self, page: Page):
        """채팅 인터페이스 상호작용 테스트"""
        page.goto("http://localhost:3000")
        
        # 채팅 페이지로 이동
        chat_link = page.get_by_role("link", name=/채팅|Chat/i)
        if chat_link.is_visible():
            chat_link.click()
        
        # 입력 필드 찾기
        input_field = page.get_by_placeholder(/상품명을 입력하거나 질문을 해보세요/i)
        expect(input_field).toBeVisible()
        
        # 메시지 입력
        input_field.fill("아이폰 찾고 있어요")
        
        # 전송 버튼 클릭
        send_button = page.get_by_role("button", name=/전송|Send/i)
        if send_button.is_visible():
            send_button.click()
            
            # 로딩 상태 확인
            expect(page.get_by_text(/분석 중|로딩/i)).toBeVisible(timeout=5000)

