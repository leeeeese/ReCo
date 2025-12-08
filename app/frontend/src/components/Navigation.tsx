import { Button } from './ui/button';
import { Menu, X } from 'lucide-react';
import { useState } from 'react';
import logo from './ReCo Logo.png';

type NavigationProps = {
  onNavigate: (page: 'landing' | 'chat' | 'recommendations' | 'about' | 'dashboard') => void;
  currentPage?: string;
};

export default function Navigation({ onNavigate, currentPage }: NavigationProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="bg-white shadow-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <button 
            onClick={() => onNavigate('landing')}
            className="flex items-center hover:opacity-80 transition-opacity"
          >
            <img src={logo} alt="ReCo Logo" className="h-10" />
          </button>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            <button 
              onClick={() => onNavigate('about')}
              className="text-gray-700 hover:text-emerald-600 transition-colors"
            >
              About
            </button>
            <button 
              onClick={() => onNavigate('recommendations')}
              className="text-gray-700 hover:text-emerald-600 transition-colors"
            >
              Features
            </button>
            <button 
              onClick={() => onNavigate('dashboard')}
              className="text-gray-700 hover:text-emerald-600 transition-colors"
            >
              Dashboard
            </button>
            <Button 
              onClick={() => onNavigate('chat')}
              className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl"
            >
              Start
            </Button>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 space-y-4">
            <button 
              onClick={() => {
                onNavigate('about');
                setMobileMenuOpen(false);
              }}
              className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-xl"
            >
              About
            </button>
            <button 
              onClick={() => {
                onNavigate('recommendations');
                setMobileMenuOpen(false);
              }}
              className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-xl"
            >
              Features
            </button>
            <button 
              onClick={() => {
                onNavigate('dashboard');
                setMobileMenuOpen(false);
              }}
              className="block w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-xl"
            >
              Dashboard
            </button>
            <Button 
              onClick={() => {
                onNavigate('chat');
                setMobileMenuOpen(false);
              }}
              className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 rounded-2xl"
            >
              Start
            </Button>
          </div>
        )}
      </div>
    </nav>
  );
}
