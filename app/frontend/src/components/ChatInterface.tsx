import React, { useState, useRef, useEffect } from 'react';
import Navigation from './Navigation';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Send, Mic, Sparkles, Loader2 } from 'lucide-react';
import ProductCard from './ProductCard';
import { ImageWithFallback } from './figma/ImageWithFallback';
import logo from './ReCo Logo.png';
import { apiClient, type RecommendationResult } from '../utils/api';

type ChatInterfaceProps = {
  onNavigate: (page: 'landing' | 'chat' | 'recommendations' | 'about' | 'dashboard') => void;
};

type Message = {
  id: string;
  type: 'user' | 'bot';
  text?: string;
  products?: Array<{
    image: string;
    name: string;
    price: string;
    avgPrice?: string;
    score: number;
    reason?: string;
    site: string;
    link: string;
  }>;
};

const categories = ['전자기기', '패션', '가전', '가구', '스포츠', '기타'];

const mockProducts = [
  {
    image: 'https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzbWFydHBob25lJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjA5NTUxMjZ8MA&ixlib=rb-4.1.0&q=80&w=1080',
    name: 'iPhone 14 Pro 256GB',
    price: '₩850,000',
    avgPrice: '₩950,000',
    score: 92,
    reason: '상태가 매우 좋고 시세보다 10% 저렴합니다. 판매자 평점도 높아 신뢰할 수 있습니다.',
    site: '중고나라',
    link: '#'
  },
  {
    image: 'https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzbWFydHBob25lJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjA5NTUxMjZ8MA&ixlib=rb-4.1.0&q=80&w=1080',
    name: 'iPhone 14 Pro 128GB',
    price: '₩750,000',
    avgPrice: '₩850,000',
    score: 88,
    reason: '배터리 효율 95% 이상, 액정 상태 양호합니다. 합리적인 가격대입니다.',
    site: '당근마켓',
    link: '#'
  }
];

export default function ChatInterface({ onNavigate }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      text: '안녕하세요! ReCo입니다. 어떤 중고 상품을 찾고 계신가요? 상품명을 입력하거나 질문을 해주세요.'
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([
    'MacBook Pro 2023',
    'Canon EOS R6',
    '에어팟 프로 2세대'
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [loadingMessageId, setLoadingMessageId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(() => {
    // localStorage에서 세션 ID 복원 또는 새로 생성
    const saved = localStorage.getItem('reco_session_id');
    return saved || null;
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 컴포넌트 언마운트 시 EventSource 정리
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // API 응답을 ProductCard 형식으로 변환
  const convertToProductCard = (result: any) => {
    // 백엔드 응답 구조에 맞게 필드 추출
    const rankingFactors = result.ranking_factors || {};
    
    // 추천 이유 추출 (여러 소스에서 시도)
    // 1. 판매자 추천 이유 (seller_final_reasoning, combination_explanation 등)
    // 2. 상품 매칭 점수 기반 설명
    // 3. 기본 메시지
    let reasonValue = 
      result.final_reasoning || 
      result.seller_final_reasoning ||
      result.combination_explanation ||
      result.reasoning ||
      rankingFactors.reasoning || 
      rankingFactors.reason;
    
    // 추천 이유가 없으면 점수 기반으로 생성
    if (!reasonValue) {
      const matchScore = result.match_score;
      const sellerScore = result.seller_final_score;
      
      if (matchScore && !isNaN(matchScore)) {
        const scorePercent = Math.round(matchScore * 100);
        reasonValue = `매칭 점수 ${scorePercent}점`;
        if (sellerScore && !isNaN(sellerScore)) {
          reasonValue += ` (판매자 점수: ${Math.round(sellerScore * 100)}점)`;
        }
      } else if (sellerScore && !isNaN(sellerScore)) {
        reasonValue = `판매자 추천 점수: ${Math.round(sellerScore * 100)}점`;
      } else {
        reasonValue = '추천 상품입니다.';
      }
    }
    
    const reason =
      typeof reasonValue === 'string' ? reasonValue : JSON.stringify(reasonValue);
    
    // 점수 계산 (NaN 방지)
    const finalScore = result.final_score || result.match_score || 0;
    const score = finalScore && !isNaN(finalScore) && finalScore > 0 ? Math.round(finalScore * 100) : undefined;
    
    return {
      image: `https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&w=400`,
      name: result.title || result.name || '상품명 없음',
      price: `₩${(result.price || 0).toLocaleString()}`,
      avgPrice: rankingFactors.market_avg ? `₩${Math.round(rankingFactors.market_avg).toLocaleString()}` : undefined,
      score: score && score > 0 ? score : undefined, // NaN이거나 0이면 표시하지 않음
      reason,
      site: result.seller_name || '중고나라',
      link: '#'
    };
  };

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      text: inputValue
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Add to recent searches if not already there
    if (!recentSearches.includes(inputValue)) {
      setRecentSearches(prev => [inputValue, ...prev.slice(0, 4)]);
    }

    const searchQuery = inputValue;
    setInputValue('');
    setIsLoading(true);
    setProgress(0);
    setProgressMessage('워크플로우 시작');

    // 로딩 메시지 추가
    const loadingMessageId = (Date.now() + 1).toString();
    const loadingMessage: Message = {
      id: loadingMessageId,
      type: 'bot',
      text: '분석 중입니다... 잠시만 기다려주세요.'
    };
    setLoadingMessageId(loadingMessageId);
    setMessages(prev => [...prev, loadingMessage]);

    // 기존 EventSource가 있으면 닫기
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
      const userInput = {
        search_query: searchQuery,
        trust_safety: 50,
        quality_condition: 50,
        remote_transaction: 50,
        activity_responsiveness: 50,
        price_flexibility: 50,
        category: selectedCategories.length > 0 ? selectedCategories[0] : null,
        location: null,
        price_min: null,
        price_max: null,
        session_id: sessionId,  // 세션 ID 전달
      };

      // POST 요청으로 SSE 엔드포인트 호출
      const response = await fetch(`${API_BASE_URL}/api/v1/recommend/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userInput),
      });

      if (!response.ok) {
        throw new Error(`SSE 연결 실패 (status: ${response.status})`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('스트림을 읽을 수 없습니다.');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'progress') {
                setProgress(data.progress);
                setProgressMessage(data.message);
                // 로딩 메시지 업데이트
                if (loadingMessageId) {
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === loadingMessageId 
                        ? { ...msg, text: `${data.message} (${data.progress}%)` }
                        : msg
                    )
                  );
                }
              } else if (data.type === 'complete') {
                setProgress(100);
                setProgressMessage('추천 완료');
                
                // 세션 ID 저장
                if (data.session_id && data.session_id !== sessionId) {
                  setSessionId(data.session_id);
                  localStorage.setItem('reco_session_id', data.session_id);
                }
                
                // 로딩 메시지 제거
                setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
                setLoadingMessageId(null);

                // 응답 처리
                const finalItems = data.final_item_scores || [];
                
                if (finalItems.length > 0) {
                  const products = finalItems.map(convertToProductCard);
                  const botMessage: Message = {
                    id: (Date.now() + 2).toString(),
                    type: 'bot',
                    text: `"${searchQuery}"에 대한 검색 결과를 찾았습니다. ${finalItems.length}개의 상품을 추천드립니다:`,
                    products: products
                  };
                  setMessages(prev => [...prev, botMessage]);
                } else {
                  const botMessage: Message = {
                    id: (Date.now() + 2).toString(),
                    type: 'bot',
                    text: `죄송합니다. "${searchQuery}"에 대한 추천 상품을 찾지 못했습니다. 다른 키워드로 검색해보시겠어요?`
                  };
                  setMessages(prev => [...prev, botMessage]);
                }
                setIsLoading(false);
                return;
              } else if (data.type === 'error') {
                // 로딩 메시지 제거
                setMessages(prev => prev.filter(msg => msg.id !== loadingMessageId));
                setLoadingMessageId(null);
                
                const errorMessage: Message = {
                  id: (Date.now() + 2).toString(),
                  type: 'bot',
                  text: data.error_message || '오류가 발생했습니다.'
                };
                setMessages(prev => [...prev, errorMessage]);
                setIsLoading(false);
                return;
              }
            } catch (e) {
              console.error('SSE 데이터 파싱 오류:', e);
            }
          }
        }
      }
    } catch (error) {
      // 로딩 메시지 제거
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
      
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: 'bot',
        text:
          error instanceof Error
            ? error.message
            : '오류가 발생했습니다. 서버 연결을 확인해주세요.'
      };
      setMessages(prev => [...prev, errorMessage]);
      console.error('SSE 연결 오류:', error);
    } finally {
      setIsLoading(false);
      setProgress(0);
      setProgressMessage('');
    }
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navigation onNavigate={onNavigate} currentPage="chat" />

      <div className="flex-1 flex">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full">
          {/* Chat Header */}
          <div className="bg-white border-b px-6 py-4 flex items-center gap-3">
            <ImageWithFallback 
              src={logo} 
              alt="ReCo Logo" 
              className="w-10 h-10 rounded-full object-cover"
            />
            <div>
              <h3>ReCo와 대화 중</h3>
              <p className="text-sm text-gray-600">AI 기반 중고거래 추천 서비스</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map(message => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-2xl ${message.type === 'user' ? 'w-auto' : 'w-full'}`}>
                  {message.type === 'bot' && (
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-full flex items-center justify-center">
                        <Sparkles size={16} className="text-white" />
                      </div>
                      <span className="text-sm">ReCo</span>
                    </div>
                  )}
                  
                  {message.text && (
                    <div
                      className={`rounded-3xl px-6 py-4 ${
                        message.type === 'user'
                          ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white'
                          : 'bg-white border'
                      }`}
                    >
                      <p>{message.text}</p>
                      {message.type === 'bot' && isLoading && message.id === loadingMessageId && progress > 0 && (
                        <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-emerald-600 to-teal-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {message.products && (
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {message.products.map((product, index) => (
                        <ProductCard key={index} {...product} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-white border-t p-6">
            <div className="flex gap-3">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="상품명을 입력하거나 질문을 해보세요"
                className="flex-1 rounded-2xl border-gray-300"
              />
              <Button
                onClick={handleSend}
                disabled={isLoading}
                className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl px-6"
              >
                {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
              </Button>
              <Button
                variant="outline"
                className="rounded-2xl px-6"
              >
                <Mic size={20} />
              </Button>
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className="hidden lg:block w-80 bg-white border-l p-6">
          {/* Recent Searches */}
          <div className="mb-8">
            <h3 className="mb-4">최근 검색</h3>
            <div className="space-y-2">
              {recentSearches.length > 0 ? (
                recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => setInputValue(search)}
                    className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-2xl transition-colors"
                  >
                    {search}
                  </button>
                ))
              ) : (
                <p className="text-sm text-gray-500 text-center py-8">
                  아직 검색한 상품이 없어요
                </p>
              )}
            </div>
          </div>

          {/* Categories */}
          <div>
            <h3 className="mb-4">관심 카테고리</h3>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <Badge
                  key={category}
                  onClick={() => toggleCategory(category)}
                  className={`cursor-pointer rounded-xl px-4 py-2 ${
                    selectedCategories.includes(category)
                      ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {category}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}