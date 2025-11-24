import { useState } from 'react';
import Navigation from './Navigation';
import Footer from './Footer';
import ProductCard from './ProductCard';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Card } from './ui/card';
import { Filter, X } from 'lucide-react';

type RecommendationPageProps = {
  onNavigate: (page: 'landing' | 'chat' | 'recommendations' | 'about' | 'dashboard') => void;
};

const mockRecommendations = [
  {
    image: 'https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzbWFydHBob25lJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjA5NTUxMjZ8MA&ixlib=rb-4.1.0&q=80&w=1080',
    name: 'iPhone 14 Pro 256GB',
    price: '₩850,000',
    avgPrice: '₩950,000',
    score: 92,
    reason: '상태가 매우 좋고 시세보다 10% 저렴합니다.',
    site: '중고나라',
    link: '#'
  },
  {
    image: 'https://images.unsplash.com/photo-1511385348-a52b4a160dc2?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsYXB0b3AlMjBjb21wdXRlcnxlbnwxfHx8fDE3NjEwMjMxOTh8MA&ixlib=rb-4.1.0&q=80&w=1080',
    name: 'MacBook Pro M2 2023',
    price: '₩1,800,000',
    avgPrice: '₩2,000,000',
    score: 95,
    reason: '거의 새 제품 수준이며 가격도 합리적입니다.',
    site: '당근마켓',
    link: '#'
  },
  {
    image: 'https://images.unsplash.com/photo-1512025316832-8658f04f8a83?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjYW1lcmElMjBlcXVpcG1lbnR8ZW58MXx8fHwxNzYwOTE3ODQ0fDA&ixlib=rb-4.1.0&q=80&w=1080',
    name: 'Canon EOS R6 미러리스',
    price: '₩2,200,000',
    avgPrice: '₩2,500,000',
    score: 88,
    reason: '셔터 수가 적고 관리가 잘 되어있습니다.',
    site: '번개장터',
    link: '#'
  },
  {
    image: 'https://images.unsplash.com/photo-1558756520-22cfe5d382ca?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxoZWFkcGhvbmVzJTIwYXVkaW98ZW58MXx8fHwxNzYwOTM5NTQwfDA&ixlib=rb-4.1.0&q=80&w=1080',
    name: '에어팟 맥스 스페이스 그레이',
    price: '₩450,000',
    avgPrice: '₩520,000',
    score: 90,
    reason: '사용감 거의 없고 박스 포함 풀구성입니다.',
    site: '중고나라',
    link: '#'
  },
  {
    image: 'https://images.unsplash.com/photo-1532453288672-3a27e9be9efd?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmYXNoaW9uJTIwY2xvdGhpbmd8ZW58MXx8fHwxNzYwOTI0NzE3fDA&ixlib=rb-4.1.0&q=80&w=1080',
    name: 'Supreme Box Logo 후디',
    price: '₩380,000',
    avgPrice: '₩450,000',
    score: 85,
    reason: '정품 인증 완료, 상태 양호합니다.',
    site: '크림',
    link: '#'
  }
];

export default function RecommendationPage({ onNavigate }: RecommendationPageProps) {
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('score');
  const [priceRange, setPriceRange] = useState([0, 5000000]);
  const [showFilters, setShowFilters] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation onNavigate={onNavigate} currentPage="recommendations" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="mb-4">ReCo의 추천 결과</h1>
          <p className="text-gray-600">
            AI가 분석한 최적의 중고 상품을 확인해보세요
          </p>
        </div>

        {/* Filter Bar */}
        <Card className="p-6 rounded-3xl mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Category Filter */}
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger className="rounded-2xl">
                  <SelectValue placeholder="카테고리" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="electronics">전자기기</SelectItem>
                  <SelectItem value="fashion">패션</SelectItem>
                  <SelectItem value="appliances">가전</SelectItem>
                  <SelectItem value="furniture">가구</SelectItem>
                  <SelectItem value="sports">스포츠</SelectItem>
                </SelectContent>
              </Select>

              {/* Sort Filter */}
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="rounded-2xl">
                  <SelectValue placeholder="정렬" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="score">추천 점수순</SelectItem>
                  <SelectItem value="price-low">낮은 가격순</SelectItem>
                  <SelectItem value="price-high">높은 가격순</SelectItem>
                  <SelectItem value="recent">최신순</SelectItem>
                </SelectContent>
              </Select>

              {/* Mobile Filter Toggle */}
              <Button
                variant="outline"
                className="rounded-2xl lg:hidden"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter size={20} className="mr-2" />
                가격 필터
              </Button>

              {/* Desktop Price Range */}
              <div className="hidden lg:flex flex-col gap-2">
                <label className="text-sm">가격 범위</label>
                <Slider
                  value={priceRange}
                  onValueChange={setPriceRange}
                  min={0}
                  max={5000000}
                  step={100000}
                  className="flex-1"
                />
                <div className="flex justify-between text-sm text-gray-600">
                  <span>₩{(priceRange[0] / 10000).toFixed(0)}만</span>
                  <span>₩{(priceRange[1] / 10000).toFixed(0)}만</span>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Price Range */}
          {showFilters && (
            <div className="lg:hidden mt-4 pt-4 border-t">
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm">가격 범위</label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFilters(false)}
                >
                  <X size={16} />
                </Button>
              </div>
              <Slider
                value={priceRange}
                onValueChange={setPriceRange}
                min={0}
                max={5000000}
                step={100000}
              />
              <div className="flex justify-between text-sm text-gray-600 mt-2">
                <span>₩{(priceRange[0] / 10000).toFixed(0)}만</span>
                <span>₩{(priceRange[1] / 10000).toFixed(0)}만</span>
              </div>
            </div>
          )}
        </Card>

        {/* Product Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {mockRecommendations.map((product, index) => (
            <ProductCard key={index} {...product} />
          ))}
        </div>

        {/* Empty State (Hidden by default) */}
        <div className="hidden">
          <Card className="p-12 rounded-3xl text-center">
            <div className="w-20 h-20 bg-gray-100 rounded-full mx-auto mb-6 flex items-center justify-center">
              <Filter size={32} className="text-gray-400" />
            </div>
            <h3 className="mb-2">아직 검색한 상품이 없어요</h3>
            <p className="text-gray-600 mb-6">
              ReCo와 대화를 시작해서 원하는 상품을 찾아보세요
            </p>
            <Button
              onClick={() => onNavigate('chat')}
              className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl"
            >
              대화 시작하기
            </Button>
          </Card>
        </div>
      </div>

      <Footer />
    </div>
  );
}
