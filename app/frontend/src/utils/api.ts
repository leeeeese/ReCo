/**
 * FastAPI 백엔드와 연동하는 API 클라이언트
 */

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 300000); // 300초 (LLM 처리 시간 고려)

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
  execution_time?: number;
  session_id?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async recommendProducts(
    userInput: UserInput
  ): Promise<RecommendationResponse> {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      API_TIMEOUT_MS
    );

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/recommend`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userInput),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`추천 API 호출 실패 (status: ${response.status})`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new Error(
          "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
        );
      }
      console.error("API 호출 실패:", error);
      throw error instanceof Error
        ? error
        : new Error("알 수 없는 오류가 발생했습니다.");
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  async healthCheck(): Promise<boolean> {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      Math.min(API_TIMEOUT_MS, 5000)
    );

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/health`, {
        method: "GET",
        signal: controller.signal,
      });
      return response.ok;
    } catch (error) {
      return false;
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  async chat(message: string): Promise<{ response: string }> {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(
      () => controller.abort(),
      35000 // 일반 대화 타임아웃 35초 (백엔드 LLM 30초 + 버퍼 5초)
    );

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`대화 API 호출 실패 (status: ${response.status})`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new Error(
          "요청 시간이 초과되었습니다. 백엔드 서버가 실행 중인지 확인해주세요."
        );
      }
      console.error("대화 API 호출 실패:", error);

      // 네트워크 오류인 경우 더 명확한 메시지
      if (
        error instanceof TypeError &&
        error.message.includes("Failed to fetch")
      ) {
        throw new Error(
          "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
        );
      }

      throw error instanceof Error
        ? error
        : new Error("알 수 없는 오류가 발생했습니다.");
    } finally {
      window.clearTimeout(timeoutId);
    }
  }
}

export const apiClient = new ApiClient();
