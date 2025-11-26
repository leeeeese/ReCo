/**
 * ChatInterface 컴포넌트 테스트
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChatInterface from '../../components/ChatInterface';

// API 모킹
vi.mock('../../utils/api', () => ({
  apiClient: {
    recommendProducts: vi.fn(),
  },
}));

describe('ChatInterface', () => {
  const mockOnNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('초기 렌더링 시 환영 메시지 표시', () => {
    render(<ChatInterface onNavigate={mockOnNavigate} />);
    
    expect(screen.getByText(/안녕하세요! ReCo입니다/i)).toBeInTheDocument();
  });

  it('사용자 입력 필드 렌더링', () => {
    render(<ChatInterface onNavigate={mockOnNavigate} />);
    
    const input = screen.getByPlaceholderText(/상품명을 입력하거나 질문을 해보세요/i);
    expect(input).toBeInTheDocument();
  });

  it('메시지 입력 및 전송 버튼 클릭', async () => {
    const user = userEvent.setup();
    render(<ChatInterface onNavigate={mockOnNavigate} />);
    
    const input = screen.getByPlaceholderText(/상품명을 입력하거나 질문을 해보세요/i);
    const sendButton = screen.getByRole('button', { name: /전송/i });
    
    await user.type(input, '아이폰 찾고 있어요');
    await user.click(sendButton);
    
    // 사용자 메시지가 표시되는지 확인
    await waitFor(() => {
      expect(screen.getByText('아이폰 찾고 있어요')).toBeInTheDocument();
    });
  });

  it('로딩 중일 때 전송 버튼 비활성화', async () => {
    const user = userEvent.setup();
    render(<ChatInterface onNavigate={mockOnNavigate} />);
    
    const input = screen.getByPlaceholderText(/상품명을 입력하거나 질문을 해보세요/i);
    const sendButton = screen.getByRole('button', { name: /전송/i });
    
    await user.type(input, '테스트');
    await user.click(sendButton);
    
    // 로딩 중에는 버튼이 비활성화되어야 함
    expect(sendButton).toBeDisabled();
  });
});

