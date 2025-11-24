import Navigation from './Navigation';
import Footer from './Footer';
import { Card } from './ui/card';
import { Brain, Search, Star, Zap, Users, Target } from 'lucide-react';

type AboutPageProps = {
  onNavigate: (page: 'landing' | 'chat' | 'recommendations' | 'about' | 'dashboard') => void;
};

export default function AboutPage({ onNavigate }: AboutPageProps) {
  const teamMembers = [
    {
      icon: <Brain size={32} className="text-emerald-600" />,
      role: 'Main Agent',
      description: '사용자 의도를 파악하고 전체 프로세스를 조율합니다'
    },
    {
      icon: <Search size={32} className="text-teal-600" />,
      role: 'Search Agent',
      description: '여러 플랫폼에서 상품 정보를 수집하고 필터링합니다'
    },
    {
      icon: <Star size={32} className="text-cyan-600" />,
      role: 'Scoring Agent',
      description: '상품의 가치를 분석하고 추천 점수를 산정합니다'
    },
    {
      icon: <Zap size={32} className="text-lime-600" />,
      role: 'Postprocessor',
      description: '최종 결과를 정제하고 최적의 추천을 제공합니다'
    }
  ];

  const features = [
    {
      icon: <Users size={24} />,
      title: '멀티 플랫폼 지원',
      description: '중고나라, 당근마켓, 번개장터 등 주요 플랫폼을 한 번에'
    },
    {
      icon: <Target size={24} />,
      title: '정확한 가격 예측',
      description: '빅데이터 분석을 통한 실시간 시세 정보 제공'
    },
    {
      icon: <Brain size={24} />,
      title: 'AI 기반 추천',
      description: '사용자 패턴을 학습하여 맞춤형 상품 추천'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation onNavigate={onNavigate} currentPage="about" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="mb-6">
            ReCo는 <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">AI Agent</span>입니다
          </h1>
          <p className="text-gray-600 max-w-3xl mx-auto">
            ReCo는 복잡한 중고거래 과정을 단순화하고, 최적의 선택을 도와주는 
            AI 기반 추천 시스템입니다. 여러 개의 전문화된 에이전트가 협력하여 
            가장 합리적인 거래를 찾아드립니다.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {features.map((feature, index) => (
            <Card key={index} className="p-6 rounded-3xl hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl flex items-center justify-center mb-4 text-emerald-600">
                {feature.icon}
              </div>
              <h3 className="mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </Card>
          ))}
        </div>

        {/* Architecture Section */}
        <div className="mb-16">
          <div className="text-center mb-12">
            <h2 className="mb-4">AI Agent Architecture</h2>
            <p className="text-gray-600">
              ReCo의 멀티 에이전트 시스템은 각 단계별로 전문화된 AI가 협력합니다
            </p>
          </div>

          {/* Architecture Diagram */}
          <Card className="p-8 rounded-3xl bg-gradient-to-br from-emerald-50 to-teal-50 mb-8">
            <div className="flex flex-col md:flex-row items-center justify-center gap-6">
              <div className="flex flex-col items-center">
                <div className="w-24 h-24 bg-white rounded-3xl shadow-lg flex items-center justify-center mb-3">
                  <Users size={40} className="text-emerald-600" />
                </div>
                <span>사용자 입력</span>
              </div>

              <div className="hidden md:block text-4xl text-gray-300">→</div>

              <div className="flex flex-col items-center">
                <div className="w-24 h-24 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-3xl shadow-lg flex items-center justify-center mb-3">
                  <Brain size={40} className="text-white" />
                </div>
                <span>Main Agent</span>
              </div>

              <div className="hidden md:block text-4xl text-gray-300">→</div>

              <div className="grid grid-cols-1 gap-4">
                <div className="flex items-center gap-3">
                  <div className="w-16 h-16 bg-white rounded-2xl shadow flex items-center justify-center">
                    <Search size={24} className="text-teal-600" />
                  </div>
                  <span className="text-sm">Search</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-16 h-16 bg-white rounded-2xl shadow flex items-center justify-center">
                    <Star size={24} className="text-cyan-600" />
                  </div>
                  <span className="text-sm">Scoring</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-16 h-16 bg-white rounded-2xl shadow flex items-center justify-center">
                    <Zap size={24} className="text-lime-600" />
                  </div>
                  <span className="text-sm">Process</span>
                </div>
              </div>

              <div className="hidden md:block text-4xl text-gray-300">→</div>

              <div className="flex flex-col items-center">
                <div className="w-24 h-24 bg-white rounded-3xl shadow-lg flex items-center justify-center mb-3">
                  <Target size={40} className="text-emerald-600" />
                </div>
                <span>추천 결과</span>
              </div>
            </div>
          </Card>

          {/* Team Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {teamMembers.map((member, index) => (
              <Card key={index} className="p-6 rounded-3xl hover:shadow-lg transition-shadow border-2 hover:border-emerald-200">
                <div className="w-16 h-16 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-2xl flex items-center justify-center mb-4">
                  {member.icon}
                </div>
                <h3 className="mb-2">{member.role}</h3>
                <p className="text-sm text-gray-600">{member.description}</p>
              </Card>
            ))}
          </div>
        </div>

        {/* Mission Section */}
        <Card className="p-12 rounded-3xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white text-center">
          <h2 className="text-white mb-4">우리의 미션</h2>
          <p className="text-emerald-50 max-w-3xl mx-auto">
            ReCo는 중고거래의 정보 비대칭을 해소하고, 모든 사람이 공정하고 
            합리적인 가격으로 거래할 수 있는 환경을 만들어갑니다. AI 기술을 
            통해 더 스마트하고 안전한 중고거래 생태계를 구축하는 것이 우리의 목표입니다.
          </p>
        </Card>
      </div>

      <Footer />
    </div>
  );
}
