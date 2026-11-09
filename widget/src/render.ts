export interface Citation {
  id: string;
  kind: string;
}

export interface ApiResponse {
  answer: string;
  citations: Citation[];
  deflected: boolean;
}

export interface RenderedMessage {
  text: string;
  citations: Citation[];
}

export const FALLBACK_MESSAGE = "I'm not able to help with that here, but our support team can.";

export function toRenderedMessage(response: ApiResponse): RenderedMessage {
  if (response.deflected) {
    return { text: FALLBACK_MESSAGE, citations: [] };
  }
  return { text: response.answer, citations: response.citations };
}
