/**
 * FastAPI 백엔드와 연동하는 API 클라이언트
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface UserInput {
  search_query: string;
  trust_safety?: number;
  quality_condition?: number;
  remote_transaction?: number;
  activity_responsiveness?: number;
  price_flexibility?: number;
  category?: string | null;
  location?: string | null;
  price_min?: number | null;
  price_max?: number | null;
}

export interface RecommendationResult {
  product_id: number;
  seller_id: number;
  title: string;
  price: number;
  final_score: number;
  ranking_factors: Record<string, any>;
  seller_name: string;
  category: string;
  condition: string;
  location: string;
}

export interface RecommendationResponse {
  status: string;
  message?: string;
  persona_classification?: {
    persona_type?: string;
  };
  final_item_scores?: RecommendationResult[];
  ranked_products?: RecommendationResult[];
  error_message?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async recommendProducts(userInput: UserInput): Promise<RecommendationResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userInput),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API 호출 실패:', error);
      throw error;
    }
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/health`, {
        method: 'GET',
      });
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

export const apiClient = new ApiClient();

