import { useState, useRef, useEffect } from "react";
import Navigation from "./Navigation";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Slider } from "./ui/slider";
import { Send, Mic, Sparkles } from "lucide-react";
import ProductCard from "./ProductCard";
import { ImageWithFallback } from "./figma/ImageWithFallback";
import logo from "../assets/be4e933247d398b35fc960ad2df357273b46c0e1.png";
import { apiClient } from "../utils/api";

type ChatInterfaceProps = {
  onNavigate: (
    page: "landing" | "chat" | "recommendations" | "about" | "dashboard"
  ) => void;
};

type Message = {
  id: string;
  type: "user" | "bot";
  text?: string;
  products?: Array<{
    image: string;
    name: string;
    price: string;
    avgPrice: string;
    score: number;
    reason: string;
    site: string;
    link: string;
  }>;
};

const categories = ["전자기기", "패션", "가전", "가구", "스포츠", "기타"];

const mockProducts = [
  {
    image:
      "https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzbWFydHBob25lJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjA5NTUxMjZ8MA&ixlib=rb-4.1.0&q=80&w=1080",
    name: "iPhone 14 Pro 256GB",
    price: "₩850,000",
    avgPrice: "₩950,000",
    score: 92,
    reason:
      "상태가 매우 좋고 시세보다 10% 저렴합니다. 판매자 평점도 높아 신뢰할 수 있습니다.",
    site: "중고나라",
    link: "#",
  },
  {
    image:
      "https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzbWFydHBob25lJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjA5NTUxMjZ8MA&ixlib=rb-4.1.0&q=80&w=1080",
    name: "iPhone 14 Pro 128GB",
    price: "₩750,000",
    avgPrice: "₩850,000",
    score: 88,
    reason:
      "배터리 효율 95% 이상, 액정 상태 양호합니다. 합리적인 가격대입니다.",
    site: "당근마켓",
    link: "#",
  },
];

export default function ChatInterface({ onNavigate }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      type: "bot",
      text: "안녕하세요! ReCo입니다. 어떤 중고 상품을 찾고 계신가요? 상품명을 입력하거나 질문을 해주세요.",
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [minPrice, setMinPrice] = useState<number>(0);
  const [maxPrice, setMaxPrice] = useState<number>(5000000);
  const [recentSearches, setRecentSearches] = useState<string[]>([
    "MacBook Pro 2023",
    "Canon EOS R6",
    "에어팟 프로 2세대",
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 일반 대화인지 판단하는 함수
  const isGeneralChat = (text: string): boolean => {
    const lowerText = text.toLowerCase().trim();
    const greetings = [
      "안녕",
      "안녕하세요",
      "안녕하셔",
      "하이",
      "hi",
      "hello",
      "헬로",
      "반가워",
      "반갑습니다",
      "좋은 아침",
      "좋은 저녁",
      "좋은 오후",
      "고마워",
      "고마워요",
      "감사",
      "감사합니다",
      "고맙습니다",
      "뭐해",
      "뭐하세요",
      "뭐하니",
      "뭐하냐",
      "누구야",
      "누구세요",
      "누구니",
      "도와줘",
      "도와주세요",
      "도움",
      "help",
    ];

    // 인사말이거나 짧은 문장(10자 이하)이면 일반 대화로 판단
    if (greetings.some((greeting) => lowerText.includes(greeting))) {
      return true;
    }

    // 질문 패턴 체크
    const questionPatterns = [
      /^[가-힣\s]{0,10}[?？]/,
      /^[가-힣\s]{0,10}인가요/,
      /^[가-힣\s]{0,10}인가\?/,
      /^[가-힣\s]{0,10}인지/,
    ];

    if (questionPatterns.some((pattern) => pattern.test(text))) {
      return true;
    }

    // 너무 짧은 문장 (3자 이하)은 일반 대화로 판단
    if (text.length <= 3) {
      return true;
    }

    return false;
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      text: inputValue,
    };

    setMessages((prev) => [...prev, userMessage]);

    const query = inputValue;
    setInputValue("");

    // 일반 대화인지 확인
    if (isGeneralChat(query)) {
      // 로딩 메시지 추가
      const loadingMessageId = (Date.now() + 1).toString();
      const loadingMessage: Message = {
        id: loadingMessageId,
        type: "bot",
        text: "응답 중...",
      };
      setMessages((prev) => [...prev, loadingMessage]);

      try {
        // 일반 대화 API 호출
        const response = await apiClient.chat(query);

        // 로딩 메시지 제거
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== loadingMessageId)
        );

        const botMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: "bot",
          text: response.response || "안녕하세요! 무엇을 도와드릴까요?",
        };
        setMessages((prev) => [...prev, botMessage]);
      } catch (error) {
        // 로딩 메시지 제거
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== loadingMessageId)
        );

        console.error("대화 API 호출 오류:", error);

        let errorText = "대화 처리 중 오류가 발생했습니다.";
        if (error instanceof Error) {
          errorText = error.message;
          // 네트워크 오류인 경우
          if (
            error.message.includes("Failed to fetch") ||
            error.message.includes("연결할 수 없습니다")
          ) {
            errorText =
              "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.";
          }
          // 타임아웃 오류인 경우
          if (error.message.includes("시간이 초과")) {
            errorText =
              "요청 시간이 초과되었습니다. 백엔드 서버가 실행 중인지 확인해주세요.";
          }
        }

        const errorMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: "bot",
          text: errorText,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
      return;
    }

    // Add to recent searches if not already there
    if (!recentSearches.includes(query)) {
      setRecentSearches((prev) => [query, ...prev.slice(0, 4)]);
    }

    // 로딩 메시지 추가
    const loadingMessageId = (Date.now() + 1).toString();
    const loadingMessage: Message = {
      id: loadingMessageId,
      type: "bot",
      text: "AI가 상품을 분석하고 추천 중입니다. 잠시만 기다려주세요...",
    };
    setMessages((prev) => [...prev, loadingMessage]);

    try {
      // 상품 추천 API 호출
      const response = await apiClient.recommendProducts({
        search_query: query,
        price_min: minPrice > 0 ? minPrice : null,
        price_max: maxPrice < 5000000 ? maxPrice : null,
        category: selectedCategories.length > 0 ? selectedCategories[0] : null,
        trust_safety: 50,
        quality_condition: 50,
        remote_transaction: 50,
        activity_responsiveness: 50,
        price_flexibility: 50,
      });

      // 로딩 메시지 제거
      setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));

      // 에러 응답 확인
      if (response.status === "error" || response.error_message) {
        throw new Error(
          response.error_message || "서버에서 오류가 발생했습니다."
        );
      }

      // 응답 처리
      const products =
        response.ranked_products || response.final_item_scores || [];

      if (!products || products.length === 0) {
        const botMessage: Message = {
          id: (Date.now() + 2).toString(),
          type: "bot",
          text: `"${query}"에 대한 검색 결과를 찾지 못했습니다. 다른 검색어를 시도해보세요.`,
        };
        setMessages((prev) => [...prev, botMessage]);
        return;
      }

      // 실행 시간 로깅 (개발 환경)
      const executionTime = response.execution_time;
      if (executionTime != null && typeof executionTime === "number") {
        console.log(`워크플로우 실행 시간: ${executionTime.toFixed(2)}초`);
      }

      const formattedProducts = products.map((product: any) => ({
        image:
          "https://images.unsplash.com/photo-1557817683-5cfe3620b05c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzbWFydHBob25lJTIwdGVjaG5vbG9neXxlbnwxfHx8fDE3NjA5NTUxMjZ8MA&ixlib=rb-4.1.0&q=80&w=1080",
        name: product.title || "상품명 없음",
        price: `₩${product.price?.toLocaleString() || "0"}`,
        avgPrice: `₩${(product.price * 1.1)?.toLocaleString() || "0"}`,
        score: Math.round((product.final_score || 0) * 100),
        reason:
          product.ranking_factors?.reasoning ||
          product.final_reasoning ||
          "추천 상품입니다.",
        site: "중고나라",
        link: "#",
      }));

      const botMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: "bot",
        text: `"${query}"에 대한 검색 결과를 찾았습니다. 다음 상품들을 추천드립니다:`,
        products: formattedProducts,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      // 로딩 메시지 제거
      setMessages((prev) => prev.filter((msg) => msg.id !== loadingMessageId));

      // 에러 로깅
      console.error("API 호출 오류:", error);

      let errorText = "알 수 없는 오류가 발생했습니다.";
      if (error instanceof Error) {
        errorText = error.message;
        // 네트워크 오류인 경우
        if (
          error.message.includes("Failed to fetch") ||
          error.message.includes("network")
        ) {
          errorText =
            "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.";
        }
        // 타임아웃 오류인 경우
        if (
          error.message.includes("시간이 초과") ||
          error.message.includes("timeout")
        ) {
          errorText = "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.";
        }
      }

      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: "bot",
        text: `오류가 발생했습니다: ${errorText}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  const formatPrice = (price: number) => {
    if (price >= 1000000) {
      return `${(price / 1000000).toFixed(0)}M`;
    } else if (price >= 1000) {
      return `${(price / 1000).toFixed(0)}K`;
    }
    return price.toString();
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
              <p className="text-sm text-gray-600">
                AI 기반 중고거래 추천 서비스
              </p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.type === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-2xl ${
                    message.type === "user" ? "w-auto" : "w-full"
                  }`}
                >
                  {message.type === "bot" && (
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
                        message.type === "user"
                          ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white"
                          : "bg-white border"
                      }`}
                    >
                      <p>{message.text}</p>
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
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                placeholder="상품명을 입력하거나 질문을 해보세요"
                className="flex-1 rounded-2xl border-gray-300"
              />
              <Button
                onClick={handleSend}
                className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl px-6"
              >
                <Send size={20} />
              </Button>
              <Button variant="outline" className="rounded-2xl px-6">
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
                      ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  {category}
                </Badge>
              ))}
            </div>
          </div>

          {/* Price Range */}
          <div className="mt-8">
            <h3 className="mb-4">가격 범위</h3>

            {/* Price Display */}
            <div className="flex justify-between items-center mb-4">
              <div className="flex-1">
                <label className="text-xs text-gray-600 mb-1 block">
                  최소 가격
                </label>
                <Input
                  type="number"
                  value={minPrice}
                  onChange={(e) => setMinPrice(Number(e.target.value))}
                  className="rounded-xl"
                  placeholder="0"
                />
              </div>
              <div className="px-3 pt-6">-</div>
              <div className="flex-1">
                <label className="text-xs text-gray-600 mb-1 block">
                  최대 가격
                </label>
                <Input
                  type="number"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(Number(e.target.value))}
                  className="rounded-xl"
                  placeholder="5000000"
                />
              </div>
            </div>

            {/* Slider */}
            <div className="space-y-2">
              <Slider
                min={0}
                max={5000000}
                step={10000}
                value={[minPrice, maxPrice]}
                onValueChange={([min, max]) => {
                  setMinPrice(min);
                  setMaxPrice(max);
                }}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>₩{formatPrice(minPrice)}</span>
                <span>₩{formatPrice(maxPrice)}</span>
              </div>
            </div>

            {/* Quick Price Presets */}
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={() => {
                  setMinPrice(0);
                  setMaxPrice(500000);
                }}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm transition-colors"
              >
                ~50만
              </button>
              <button
                onClick={() => {
                  setMinPrice(500000);
                  setMaxPrice(1000000);
                }}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm transition-colors"
              >
                50만~100만
              </button>
              <button
                onClick={() => {
                  setMinPrice(1000000);
                  setMaxPrice(3000000);
                }}
                className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm transition-colors"
              >
                100만~300만
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
