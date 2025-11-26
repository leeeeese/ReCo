/**
 * ProductCard 컴포넌트 테스트
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ProductCard from '../../components/ProductCard';

describe('ProductCard', () => {
  const mockProduct = {
    image: 'https://example.com/image.jpg',
    name: '아이폰 14 프로',
    price: '₩850,000',
    avgPrice: '₩950,000',
    score: 92,
    reason: '상태가 매우 좋고 시세보다 10% 저렴합니다.',
    site: '중고나라',
    link: '#',
  };

  it('상품 정보 렌더링', () => {
    render(<ProductCard {...mockProduct} />);
    
    expect(screen.getByText('아이폰 14 프로')).toBeInTheDocument();
    expect(screen.getByText('₩850,000')).toBeInTheDocument();
    expect(screen.getByText('₩950,000')).toBeInTheDocument();
    expect(screen.getByText(/상태가 매우 좋고/i)).toBeInTheDocument();
  });

  it('점수 표시', () => {
    render(<ProductCard {...mockProduct} />);
    
    expect(screen.getByText('92')).toBeInTheDocument();
  });

  it('avgPrice가 없을 때 처리', () => {
    const productWithoutAvg = { ...mockProduct, avgPrice: undefined };
    render(<ProductCard {...productWithoutAvg} />);
    
    expect(screen.getByText('아이폰 14 프로')).toBeInTheDocument();
    expect(screen.queryByText('₩950,000')).not.toBeInTheDocument();
  });
});

