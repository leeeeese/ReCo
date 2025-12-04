import { useState } from 'react';
import Navigation from './Navigation';
import Footer from './Footer';
import ProductCard from './ProductCard';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Heart, Clock, MessageSquare, LogOut, Bookmark } from 'lucide-react';

type UserDashboardProps = {
  onNavigate: (page: 'landing' | 'chat' | 'recommendations' | 'about' | 'dashboard') => void;
};

const recentRecommendations = [
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
  }
];

const savedItems = [
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
  }
];

const chatHistory = [
  {
    date: '2025-10-20',
    query: 'iPhone 14 Pro 추천해줘',
    responses: 3
  },
  {
    date: '2025-10-19',
    query: 'MacBook Pro M2 시세가 궁금해',
    responses: 2
  },
  {
    date: '2025-10-18',
    query: '카메라 중고로 사려고 하는데',
    responses: 5
  }
];

export default function UserDashboard({ onNavigate }: UserDashboardProps) {
  const [activeTab, setActiveTab] = useState('recent');

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation onNavigate={onNavigate} currentPage="dashboard" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h1 className="mb-2">내 대시보드</h1>
            <p className="text-gray-600">ReCo와 함께한 중고거래 기록</p>
          </div>
          <Button
            variant="outline"
            className="rounded-2xl"
            onClick={() => {
              alert('로그아웃 되었습니다');
              onNavigate('landing');
            }}
          >
            <LogOut size={20} className="mr-2" />
            로그아웃
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="p-6 rounded-3xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-50 rounded-2xl flex items-center justify-center">
                <Clock size={24} className="text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">총 추천</p>
                <p className="text-2xl">24</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 rounded-3xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-teal-50 rounded-2xl flex items-center justify-center">
                <Heart size={24} className="text-teal-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">관심 상품</p>
                <p className="text-2xl">12</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 rounded-3xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-cyan-50 rounded-2xl flex items-center justify-center">
                <MessageSquare size={24} className="text-cyan-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">대화 수</p>
                <p className="text-2xl">8</p>
              </div>
            </div>
          </Card>

          <Card className="p-6 rounded-3xl">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-50 rounded-2xl flex items-center justify-center">
                <Bookmark size={24} className="text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">절약 금액</p>
                <p className="text-2xl">₩850K</p>
              </div>
            </div>
          </Card>
        </div>

        {/* Tabs Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="w-full md:w-auto mb-8 rounded-2xl p-1">
            <TabsTrigger value="recent" className="rounded-xl">
              <Clock size={16} className="mr-2" />
              최근 추천
            </TabsTrigger>
            <TabsTrigger value="saved" className="rounded-xl">
              <Heart size={16} className="mr-2" />
              관심 상품
            </TabsTrigger>
            <TabsTrigger value="history" className="rounded-xl">
              <MessageSquare size={16} className="mr-2" />
              대화 기록
            </TabsTrigger>
          </TabsList>

          {/* Recent Recommendations */}
          <TabsContent value="recent">
            {recentRecommendations.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {recentRecommendations.map((product, index) => (
                  <ProductCard key={index} {...product} />
                ))}
              </div>
            ) : (
              <Card className="p-12 rounded-3xl text-center">
                <div className="w-20 h-20 bg-gray-100 rounded-full mx-auto mb-6 flex items-center justify-center">
                  <Clock size={32} className="text-gray-400" />
                </div>
                <h3 className="mb-2">추천 내역이 없습니다</h3>
                <p className="text-gray-600 mb-6">
                  ReCo와 대화를 시작해서 상품을 추천받아보세요
                </p>
                <Button
                  onClick={() => onNavigate('chat')}
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl"
                >
                  대화 시작하기
                </Button>
              </Card>
            )}
          </TabsContent>

          {/* Saved Items */}
          <TabsContent value="saved">
            {savedItems.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {savedItems.map((product, index) => (
                  <ProductCard key={index} {...product} />
                ))}
              </div>
            ) : (
              <Card className="p-12 rounded-3xl text-center">
                <div className="w-20 h-20 bg-gray-100 rounded-full mx-auto mb-6 flex items-center justify-center">
                  <Heart size={32} className="text-gray-400" />
                </div>
                <h3 className="mb-2">저장한 상품이 없습니다</h3>
                <p className="text-gray-600">
                  마음에 드는 상품을 저장해보세요
                </p>
              </Card>
            )}
          </TabsContent>

          {/* Chat History */}
          <TabsContent value="history">
            {chatHistory.length > 0 ? (
              <div className="space-y-4">
                {chatHistory.map((chat, index) => (
                  <Card
                    key={index}
                    className="p-6 rounded-3xl hover:shadow-lg transition-shadow cursor-pointer"
                    onClick={() => onNavigate('chat')}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="mb-2">{chat.query}</p>
                        <p className="text-sm text-gray-600">
                          {chat.responses}개의 응답 • {chat.date}
                        </p>
                      </div>
                      <MessageSquare size={24} className="text-gray-400" />
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="p-12 rounded-3xl text-center">
                <div className="w-20 h-20 bg-gray-100 rounded-full mx-auto mb-6 flex items-center justify-center">
                  <MessageSquare size={32} className="text-gray-400" />
                </div>
                <h3 className="mb-2">대화 기록이 없습니다</h3>
                <p className="text-gray-600 mb-6">
                  ReCo와 첫 대화를 시작해보세요
                </p>
                <Button
                  onClick={() => onNavigate('chat')}
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl"
                >
                  대화 시작하기
                </Button>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>

      <Footer />
    </div>
  );
}
