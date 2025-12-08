import { useState } from "react";
import LandingPage from "./components/LandingPage";
import ChatInterface from "./components/ChatInterface";
import RecommendationPage from "./components/RecommendationPage";
import AboutPage from "./components/AboutPage";
import UserDashboard from "./components/UserDashboard";

export default function App() {
  const [currentPage, setCurrentPage] = useState<
    "landing" | "chat" | "recommendations" | "about" | "dashboard"
  >("landing");

  const renderPage = () => {
    switch (currentPage) {
      case "landing":
        return <LandingPage onNavigate={setCurrentPage} />;
      case "chat":
        return <ChatInterface onNavigate={setCurrentPage} />;
      case "recommendations":
        return <RecommendationPage onNavigate={setCurrentPage} />;
      case "about":
        return <AboutPage onNavigate={setCurrentPage} />;
      case "dashboard":
        return <UserDashboard onNavigate={setCurrentPage} />;
      default:
        return <LandingPage onNavigate={setCurrentPage} />;
    }
  };

  return <div className="min-h-screen bg-gray-50">{renderPage()}</div>;
}
