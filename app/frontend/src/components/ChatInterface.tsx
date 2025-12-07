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
import logo from "./ReCo Logo.png";

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

  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      text: inputValue,
    };

    setMessages((prev) => [...prev, userMessage]);

    // Add to recent searches if not already there
    if (!recentSearches.includes(inputValue)) {
      setRecentSearches((prev) => [inputValue, ...prev.slice(0, 4)]);
    }

    setInputValue("");

    // Simulate bot response
    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "bot",
        text: `"${inputValue}"에 대한 검색 결과를 찾았습니다. 다음 상품들을 추천드립니다:`,
        products: mockProducts,
      };
      setMessages((prev) => [...prev, botMessage]);
    }, 1000);
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
