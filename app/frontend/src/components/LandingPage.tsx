import Navigation from './Navigation';
import Footer from './Footer';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Brain, TrendingUp, MessageSquare, ArrowRight } from 'lucide-react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import logo from 'figma:asset/be4e933247d398b35fc960ad2df357273b46c0e1.png';

type LandingPageProps = {
  onNavigate: (page: 'landing' | 'chat' | 'recommendations' | 'about' | 'dashboard') => void;
};

export default function LandingPage({ onNavigate }: LandingPageProps) {
  const features = [
    {
      icon: <Brain size={32} className="text-emerald-600" />,
      title: '중고 상품 조회',
      description: '지금 ReCo가 알려주는 인기 중고 상품을 조회해 보세요!'
    },
    {
      icon: <TrendingUp size={32} className="text-teal-600" />,
      title: '가격 분석',
      description: '평균 시세를 예측하고 가격 트렌드를 분석합니다. 합리적인 가격으로 거래할 수 있도록 도와드립니다.'
    },
    {
      icon: <MessageSquare size={32} className="text-green-600" />,
      title: '대화형 인터페이스',
      description: '자연스러운 대화로 상담이 가능합니다. 궁금한 점을 물어보면 ReCo가 친절하게 답변해드립니다.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <Navigation onNavigate={onNavigate} currentPage="landing" />

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="mb-6 text-5xl font-black">
              스마트한 중고거래,<br />
              <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                ReCo
              </span>와 함께
            </h1>
            <p className="text-gray-600 mb-8">
              AI 기술로 중고 상품을 추천받고, 가격을 비교하며, 
              자연스러운 대화를 통해 최적의 거래를 경험하세요.
            </p>
            <Button 
              onClick={() => onNavigate('chat')}
              className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl px-6 py-3 font-bold"
            >
              지금 시작하기
              <ArrowRight size={20} className="ml-2" />
            </Button>
          </div>

          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full opacity-20 blur-3xl"></div>
              <ImageWithFallback 
                src={logo}
                alt="ReCo Logo"
                className="relative w-full max-w-md rounded-3xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="mb-4 text-3xl font-normal">주요 기능</h2>
          <p className="text-gray-600">ReCo가 제공하는 스마트한 중고거래 솔루션</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <Card key={index} className="p-8 rounded-3xl hover:shadow-lg transition-shadow border-2 hover:border-emerald-200">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl flex items-center justify-center mb-6">
                {feature.icon}
              </div>
              <h3 className="mb-3 text-xl font-bold">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 mb-16">
        <Card className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white p-12 rounded-3xl text-center">
          <h2 className="text-white mb-4 text-[20px]">지금 바로 시작해보세요</h2>
          <p className="mb-8 text-emerald-50 text-[20px]">
            ReCo와 함께라면 중고거래가 더욱 쉽고 안전해집니다
          </p>
          <Button 
            onClick={() => onNavigate('chat')}
            className="bg-white text-emerald-700 hover:bg-gray-100 rounded-2xl px-8 py-6 text-[20px] font-bold"
          >
            ReCo 시작하기
            <ArrowRight size={20} className="ml-2" />
          </Button>
        </Card>
      </section>

      <Footer />
    </div>
  );
}