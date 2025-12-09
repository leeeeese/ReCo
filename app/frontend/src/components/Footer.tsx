import { Facebook, Twitter, Instagram, Linkedin } from 'lucide-react';
import logo from '../assets/be4e933247d398b35fc960ad2df357273b46c0e1.png';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300 py-12 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center mb-4">
              <img src={logo} alt="ReCo Logo" className="h-10 brightness-0 invert" />
            </div>
            <p className="text-sm mb-4">
              스마트한 중고거래를 위한 AI 추천 플랫폼
            </p>
            <div className="flex gap-4">
              <button className="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center hover:bg-gray-700 transition-colors">
                <Facebook size={20} />
              </button>
              <button className="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center hover:bg-gray-700 transition-colors">
                <Twitter size={20} />
              </button>
              <button className="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center hover:bg-gray-700 transition-colors">
                <Instagram size={20} />
              </button>
              <button className="w-10 h-10 bg-gray-800 rounded-xl flex items-center justify-center hover:bg-gray-700 transition-colors">
                <Linkedin size={20} />
              </button>
            </div>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-white mb-4">서비스</h3>
            <ul className="space-y-2 text-sm">
              <li><button className="hover:text-white transition-colors">가격 분석</button></li>
              <li><button className="hover:text-white transition-colors">대화형 상담</button></li>
              <li><button className="hover:text-white transition-colors">중고 상품 조회</button></li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white mb-4">법적 고지</h3>
            <ul className="space-y-2 text-sm">
              <li><button className="hover:text-white transition-colors">이용약관</button></li>
              <li><button className="hover:text-white transition-colors">개인정보 처리방침</button></li>
              <li><button className="hover:text-white transition-colors">고객센터</button></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
          <p>&copy; 2025 ReCo. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}