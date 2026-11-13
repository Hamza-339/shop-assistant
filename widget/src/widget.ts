import {
  ApiResponse,
  Citation,
  citationUrl,
  formatCitation,
  mapErrorToMessage,
  parseChips,
  renderMarkdown,
  toRenderedMessage,
  WELCOME_MESSAGE,
} from "./render.js";

const DEFAULT_API_BASE = "/api";
const DEFAULT_COLOR = "#2563eb";

function getApiBase(): string {
  const script = document.currentScript;
  const configured = script instanceof HTMLElement ? script.dataset.apiBase : null;
  return configured ?? DEFAULT_API_BASE;
}

function getBrandColor(): string {
  const script = document.currentScript;
  const configured = script instanceof HTMLElement ? script.dataset.color : null;
  return configured ?? DEFAULT_COLOR;
}

function getChips(): readonly string[] {
  const script = document.currentScript;
  const configured = script instanceof HTMLElement ? script.dataset.chips : null;
  return parseChips(configured);
}

function injectStyles(): void {
  const style = document.createElement("style");
  style.textContent = `
    .sa-widget-root {
      --sa-brand: ${DEFAULT_COLOR};
    }
    .sa-widget-launcher {
      position: fixed;
      bottom: 1rem;
      right: 1rem;
      width: 3.5rem;
      height: 3.5rem;
      border-radius: 50%;
      border: none;
      background: var(--sa-brand);
      color: #fff;
      font-size: 1.5rem;
      cursor: pointer;
      box-shadow: 0 0.25rem 0.75rem rgba(0, 0, 0, 0.25);
      z-index: 2147483000;
    }
    .sa-widget-panel {
      position: fixed;
      bottom: 1rem;
      right: 1rem;
      width: min(24rem, calc(100vw - 2rem));
      height: min(34rem, calc(100vh - 6rem));
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
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: var(--sa-brand);
      color: #fff;
    }
    .sa-widget-header-text {
      display: flex;
      flex-direction: column;
      gap: 0.1rem;
      min-width: 0;
    }
    .sa-widget-title {
      font-weight: 600;
      font-size: 0.95rem;
    }
    .sa-widget-subtitle {
      font-size: 0.7rem;
      opacity: 0.85;
    }
    .sa-widget-close {
      flex-shrink: 0;
      border: none;
      background: transparent;
      color: #fff;
      font-size: 1.25rem;
      line-height: 1;
      cursor: pointer;
      padding: 0.25rem;
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
      line-height: 1.4;
    }
    .sa-widget-message p {
      margin: 0 0 0.5rem;
    }
    .sa-widget-message p:last-child {
      margin-bottom: 0;
    }
    .sa-widget-message ul,
    .sa-widget-message ol {
      margin: 0 0 0.5rem;
      padding-left: 1.25rem;
    }
    .sa-widget-message h1,
    .sa-widget-message h2,
    .sa-widget-message h3 {
      margin: 0 0 0.35rem;
      font-size: 1em;
    }
    .sa-widget-message a {
      color: inherit;
      text-decoration: underline;
    }
    .sa-widget-message.user {
      align-self: flex-end;
      background: var(--sa-brand);
      color: #fff;
      white-space: pre-wrap;
    }
    .sa-widget-message.assistant {
      align-self: flex-start;
      background: #f3f4f6;
      color: #111827;
    }
    .sa-widget-typing {
      align-self: flex-start;
      background: #f3f4f6;
      color: #6b7280;
      padding: 0.5rem 0.75rem;
      border-radius: 0.75rem;
      font-size: 0.9rem;
    }
    .sa-widget-citations {
      margin-top: 0.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
    }
    .sa-widget-citation-chip {
      display: inline-block;
      font-size: 0.7rem;
      padding: 0.2rem 0.5rem;
      border-radius: 999px;
      background: rgba(0, 0, 0, 0.06);
      color: inherit;
      text-decoration: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 12rem;
    }
    .sa-widget-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
      padding: 0 0.75rem 0.5rem;
    }
    .sa-widget-chip {
      border: 1px solid var(--sa-brand);
      color: var(--sa-brand);
      background: #fff;
      border-radius: 999px;
      padding: 0.35rem 0.7rem;
      font-size: 0.8rem;
      cursor: pointer;
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
      background: var(--sa-brand);
      color: #fff;
      cursor: pointer;
    }
    .sa-widget-submit:disabled {
      opacity: 0.6;
      cursor: default;
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

function appendAssistantMessage(history: HTMLElement, text: string, citations: Citation[]): void {
  const message = document.createElement("div");
  message.className = "sa-widget-message assistant";
  message.innerHTML = renderMarkdown(text);

  if (citations.length > 0) {
    const wrapper = document.createElement("div");
    wrapper.className = "sa-widget-citations";

    for (const citation of citations) {
      const link = document.createElement("a");
      link.className = "sa-widget-citation-chip";
      link.href = citationUrl(citation);
      link.textContent = formatCitation(citation);
      wrapper.appendChild(link);
    }

    message.appendChild(wrapper);
  }

  history.appendChild(message);
  history.scrollTop = history.scrollHeight;
}

function appendUserMessage(history: HTMLElement, text: string): void {
  const message = document.createElement("div");
  message.className = "sa-widget-message user";
  message.textContent = text;
  history.appendChild(message);
  history.scrollTop = history.scrollHeight;
}

function appendWelcome(
  history: HTMLElement,
  chipQuestions: readonly string[],
  onChipClick: (question: string) => void,
): void {
  appendAssistantMessage(history, WELCOME_MESSAGE, []);

  const chips = document.createElement("div");
  chips.className = "sa-widget-chips";

  for (const question of chipQuestions) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "sa-widget-chip";
    chip.textContent = question;
    chip.addEventListener("click", () => onChipClick(question));
    chips.appendChild(chip);
  }

  history.appendChild(chips);
}

async function askQuestion(apiBase: string, question: string): Promise<ApiResponse> {
  const response = await fetch(apiBase, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw { status: response.status };
  }
  return (await response.json()) as ApiResponse;
}

export function mount(): void {
  const apiBase = getApiBase();
  const brandColor = getBrandColor();
  const chipQuestions = getChips();
  injectStyles();

  const root = document.createElement("div");
  root.className = "sa-widget-root";
  root.style.setProperty("--sa-brand", brandColor);

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

  const headerText = document.createElement("div");
  headerText.className = "sa-widget-header-text";

  const title = document.createElement("span");
  title.className = "sa-widget-title";
  title.textContent = "Shop Assistant";

  const subtitle = document.createElement("span");
  subtitle.className = "sa-widget-subtitle";
  subtitle.textContent = "AI assistant";

  headerText.appendChild(title);
  headerText.appendChild(subtitle);

  const closeButton = document.createElement("button");
  closeButton.type = "button";
  closeButton.className = "sa-widget-close";
  closeButton.setAttribute("aria-label", "Close chat");
  closeButton.textContent = "×";

  header.appendChild(headerText);
  header.appendChild(closeButton);

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

  root.appendChild(launcher);
  root.appendChild(panel);

  function openPanel(): void {
    if (panel.hidden) {
      panel.hidden = false;
      if (history.childElementCount === 0) {
        appendWelcome(history, chipQuestions, submitQuestion);
      }
    }
  }

  function closePanel(): void {
    panel.hidden = true;
  }

  launcher.addEventListener("click", () => {
    if (panel.hidden) {
      openPanel();
    } else {
      closePanel();
    }
  });

  closeButton.addEventListener("click", closePanel);

  function submitQuestion(question: string): void {
    if (submit.disabled) {
      return;
    }

    appendUserMessage(history, question);
    submit.disabled = true;

    const typing = document.createElement("div");
    typing.className = "sa-widget-typing";
    typing.textContent = "…";
    history.appendChild(typing);
    history.scrollTop = history.scrollHeight;

    askQuestion(apiBase, question)
      .then((response) => {
        const rendered = toRenderedMessage(response);
        typing.remove();
        appendAssistantMessage(history, rendered.text, rendered.citations);
      })
      .catch((failure: unknown) => {
        typing.remove();
        const status = typeof failure === "object" && failure !== null && "status" in failure
          ? (failure as { status?: number }).status
          : undefined;
        appendAssistantMessage(history, mapErrorToMessage({ status, error: failure }), []);
      })
      .finally(() => {
        submit.disabled = false;
      });
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question || submit.disabled) {
      return;
    }
    input.value = "";
    submitQuestion(question);
  });

  document.body.appendChild(root);
}

mount();
