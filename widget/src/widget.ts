import { ApiResponse, formatCitation, toRenderedMessage } from "./render.js";

const DEFAULT_API_BASE = "/api";

function getApiBase(): string {
  const script = document.currentScript;
  const configured = script instanceof HTMLElement ? script.dataset.apiBase : null;
  return configured ?? DEFAULT_API_BASE;
}

function injectStyles(): void {
  const style = document.createElement("style");
  style.textContent = `
    .sa-widget-launcher {
      position: fixed;
      bottom: 1rem;
      right: 1rem;
      width: 3.5rem;
      height: 3.5rem;
      border-radius: 50%;
      border: none;
      background: #111827;
      color: #fff;
      font-size: 1.5rem;
      cursor: pointer;
      z-index: 2147483000;
    }
    .sa-widget-panel {
      position: fixed;
      bottom: 1rem;
      right: 1rem;
      width: min(22rem, calc(100vw - 2rem));
      height: min(32rem, calc(100vh - 6rem));
      display: flex;
      flex-direction: column;
      background: #fff;
      border-radius: 0.75rem;
      box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.25);
      overflow: hidden;
      z-index: 2147483000;
      font-family: system-ui, sans-serif;
    }
    .sa-widget-panel[hidden] {
      display: none;
    }
    .sa-widget-header {
      padding: 0.75rem 1rem;
      background: #111827;
      color: #fff;
      font-weight: 600;
    }
    .sa-widget-history {
      flex: 1;
      overflow-y: auto;
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }
    .sa-widget-message {
      max-width: 85%;
      padding: 0.5rem 0.75rem;
      border-radius: 0.75rem;
      font-size: 0.9rem;
      line-height: 1.3;
      white-space: pre-wrap;
    }
    .sa-widget-message.user {
      align-self: flex-end;
      background: #2563eb;
      color: #fff;
    }
    .sa-widget-message.assistant {
      align-self: flex-start;
      background: #f3f4f6;
      color: #111827;
    }
    .sa-widget-citations {
      margin-top: 0.35rem;
      font-size: 0.75rem;
      opacity: 0.7;
    }
    .sa-widget-form {
      display: flex;
      gap: 0.5rem;
      padding: 0.75rem;
      border-top: 1px solid #e5e7eb;
    }
    .sa-widget-input {
      flex: 1;
      padding: 0.5rem 0.75rem;
      border: 1px solid #d1d5db;
      border-radius: 0.5rem;
      font-size: 0.9rem;
    }
    .sa-widget-submit {
      padding: 0.5rem 0.9rem;
      border: none;
      border-radius: 0.5rem;
      background: #2563eb;
      color: #fff;
      cursor: pointer;
    }
    @media (max-width: 30rem) {
      .sa-widget-panel {
        bottom: 0;
        right: 0;
        width: 100vw;
        height: 100vh;
        border-radius: 0;
      }
    }
  `;
  document.head.appendChild(style);
}

function appendMessage(history: HTMLElement, role: "user" | "assistant", text: string, citationLabels: string[]): void {
  const message = document.createElement("div");
  message.className = `sa-widget-message ${role}`;
  message.textContent = text;

  for (const label of citationLabels) {
    const citation = document.createElement("div");
    citation.className = "sa-widget-citations";
    citation.textContent = label;
    message.appendChild(citation);
  }

  history.appendChild(message);
  history.scrollTop = history.scrollHeight;
}

async function askQuestion(apiBase: string, question: string): Promise<ApiResponse> {
  const response = await fetch(apiBase, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  return (await response.json()) as ApiResponse;
}

export function mount(): void {
  const apiBase = getApiBase();
  injectStyles();

  const launcher = document.createElement("button");
  launcher.className = "sa-widget-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", "Open chat");
  launcher.textContent = "💬";

  const panel = document.createElement("div");
  panel.className = "sa-widget-panel";
  panel.hidden = true;

  const header = document.createElement("div");
  header.className = "sa-widget-header";
  header.textContent = "Ask us anything";

  const history = document.createElement("div");
  history.className = "sa-widget-history";

  const form = document.createElement("form");
  form.className = "sa-widget-form";

  const input = document.createElement("input");
  input.className = "sa-widget-input";
  input.type = "text";
  input.placeholder = "Ask a question…";
  input.setAttribute("aria-label", "Ask a question");

  const submit = document.createElement("button");
  submit.className = "sa-widget-submit";
  submit.type = "submit";
  submit.textContent = "Send";

  form.appendChild(input);
  form.appendChild(submit);
  panel.appendChild(header);
  panel.appendChild(history);
  panel.appendChild(form);

  launcher.addEventListener("click", () => {
    panel.hidden = !panel.hidden;
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question) {
      return;
    }

    appendMessage(history, "user", question, []);
    input.value = "";
    submit.disabled = true;

    askQuestion(apiBase, question)
      .then((response) => {
        const rendered = toRenderedMessage(response);
        appendMessage(history, "assistant", rendered.text, rendered.citations.map(formatCitation));
      })
      .catch(() => {
        appendMessage(history, "assistant", "Something went wrong. Please try again.", []);
      })
      .finally(() => {
        submit.disabled = false;
      });
  });

  document.body.appendChild(launcher);
  document.body.appendChild(panel);
}

mount();
