let conversation = [];

const make = (tag, className, text) => {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
};

function appendMessage(container, role, text) {
  const message = make("article", `chat-message ${role === "user" ? "chat-user" : "chat-model"}`);
  const avatar = make("span", "chat-avatar", role === "user" ? "You" : "G");
  avatar.setAttribute("aria-hidden", "true");

  const body = make("div", "chat-message-body");
  const header = make("div", "chat-message-header");
  header.append(
    make("strong", "", role === "user" ? "You" : "Gemini 3.6 Flash"),
    make("time", "", new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })),
  );
  body.append(header, make("p", "chat-message-text", text));
  message.append(avatar, body);
  container.append(message);
  container.scrollTop = container.scrollHeight;
  return message;
}

function addWelcome(container) {
  const welcome = make("div", "chat-welcome");
  const icon = make("span", "chat-welcome-icon", "G");
  icon.setAttribute("aria-hidden", "true");
  welcome.append(
    icon,
    make("h3", "", "Start a conversation"),
    make("p", "", "Send a message to Gemini 3.6 Flash. Replies will appear here, and follow-up messages include recent chat context."),
  );
  container.append(welcome);
}

function accessView(user, onSignIn) {
  const section = make("section", "chat-access panel");
  const icon = make("div", "chat-access-icon", "G");
  const title = user ? "Administrator access required" : "Sign in to use Gemini chat";
  const detail = user
    ? "This test can call an external AI service, so only administrators can use it."
    : "Sign in with an administrator account to send prompts and view model responses.";
  section.append(icon, make("h2", "", title), make("p", "", detail));
  const button = make("button", "button primary", user ? "Switch account" : "Sign in");
  button.type = "button";
  button.addEventListener("click", onSignIn);
  section.append(button);
  return section;
}

export function clearGeminiChat() {
  conversation = [];
}

export function createGeminiChatView({ request, user, onSignIn }) {
  if (user?.role !== "admin") return accessView(user, onSignIn);

  const layout = make("div", "gemini-layout");
  const chatPanel = make("section", "panel gemini-chat-panel");
  const chatHeader = make("div", "gemini-chat-header");
  const heading = make("div");
  heading.append(
    make("h2", "", "Gemini conversation"),
    make("p", "", "A private, temporary chat for testing model responses."),
  );
  const clearButton = make("button", "button secondary", "New chat");
  clearButton.type = "button";
  clearButton.addEventListener("click", () => {
    conversation = [];
    renderHistory();
    input.focus();
  });
  chatHeader.append(heading, clearButton);

  const transcript = make("div", "chat-transcript");
  transcript.setAttribute("role", "log");
  transcript.setAttribute("aria-label", "Gemini chat messages");
  transcript.setAttribute("aria-live", "polite");

  function renderHistory() {
    transcript.replaceChildren();
    if (conversation.length === 0) {
      addWelcome(transcript);
      return;
    }
    for (const message of conversation) appendMessage(transcript, message.role, message.text);
  }

  const status = make("p", "chat-status");
  status.setAttribute("role", "status");
  status.hidden = true;

  const form = make("form", "chat-composer");
  const inputLabel = make("label", "visually-hidden", "Message Gemini");
  const input = make("textarea");
  input.id = "gemini-message";
  input.name = "message";
  input.maxLength = 1000;
  input.rows = 2;
  input.placeholder = "Ask Gemini something…";
  input.required = true;
  inputLabel.htmlFor = input.id;
  input.setAttribute("aria-describedby", "gemini-message-help");

  const composerFooter = make("div", "chat-composer-footer");
  const helper = make("span", "chat-helper", "Enter to send · Shift+Enter for a new line");
  helper.id = "gemini-message-help";
  const sendArea = make("div", "chat-send-area");
  const counter = make("span", "chat-counter", "0 / 1000");
  const sendButton = make("button", "button primary chat-send", "Send");
  sendButton.type = "submit";
  sendButton.disabled = true;
  sendArea.append(counter, sendButton);
  composerFooter.append(helper, sendArea);
  form.append(inputLabel, input, composerFooter);

  const setupMessage = "To enable Gemini, set GEMINI_API_KEY in the server’s .env file, restart the backend, and refresh this page.";
  let configured = false;
  async function checkConfiguration() {
    status.textContent = "Checking Gemini configuration…";
    status.hidden = false;
    try {
      const result = await request("/gemini/status");
      configured = result.configured === true;
      sendButton.disabled = !configured;
      status.hidden = configured;
      if (!configured) status.textContent = setupMessage;
    } catch (error) {
      status.textContent = `Could not check Gemini configuration: ${error.message}. Refresh to try again.`;
    }
  }

  input.addEventListener("input", () => {
    counter.textContent = `${input.value.length} / 1000`;
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const draft = input.value;
    const text = draft.trim();
    if (!text || sendButton.disabled) return;

    input.value = "";
    counter.textContent = "0 / 1000";
    const pendingMessage = appendMessage(transcript, "user", text);
    const messages = [...conversation, { role: "user", text }].slice(-12);
    if (messages[0]?.role === "model") messages.shift();

    sendButton.disabled = true;
    input.disabled = true;
    clearButton.disabled = true;
    status.hidden = true;
    const typing = make("div", "chat-typing");
    typing.setAttribute("role", "status");
    typing.append(make("span"), make("span"), make("span"), make("span", "", "Gemini is thinking…"));
    transcript.append(typing);
    transcript.scrollTop = transcript.scrollHeight;

    try {
      const result = await request("/gemini/chat", {
        method: "POST",
        body: { messages },
      });
      conversation = [...messages, { role: "model", text: result.response }].slice(-12);
      if (conversation[0]?.role === "model") conversation.shift();
      typing.remove();
      appendMessage(transcript, "model", result.response);
      status.textContent = `Response received from ${result.model}.`;
      status.className = "chat-status success";
      status.hidden = false;
    } catch (error) {
      typing.remove();
      pendingMessage.remove();
      input.value = draft;
      counter.textContent = `${draft.length} / 1000`;
      if (error.message === "GEMINI_API_KEY is not configured") configured = false;
      status.textContent = !configured
        ? setupMessage
        : `Unable to get a response: ${error.message}. Your draft is ready to resend.`;
      status.className = "chat-status error";
      status.hidden = false;
    } finally {
      sendButton.disabled = !configured;
      input.disabled = false;
      clearButton.disabled = false;
      input.focus();
    }
  });

  renderHistory();
  chatPanel.append(chatHeader, transcript, status, form);

  const guidance = make("aside", "panel chat-guidance");
  const modelCard = make("div", "chat-model-card");
  modelCard.append(make("span", "chat-model-mark", "G"), make("div", "", "Gemini 3.6 Flash"));
  modelCard.lastElementChild.append(make("small", "", "Stable text generation model"));
  guidance.append(modelCard);
  guidance.append(
    make("h3", "", "About this chat"),
    make("p", "", "This interface sends your message and recent conversation turns to Gemini. Chat history stays in this browser session and is not saved to the hospital database."),
    make("h3", "", "Before you send"),
    make("p", "", "Use synthetic, non-sensitive test prompts only. Do not enter patient names, health details, credentials, or other confidential information."),
  );
  const modelDetails = make("dl", "chat-details");
  modelDetails.append(
    make("dt", "", "Model"), make("dd", "", "gemini-3.6-flash"),
    make("dt", "", "Access"), make("dd", "", "Administrator only"),
    make("dt", "", "Context"), make("dd", "", "Up to 12 messages"),
  );
  guidance.append(modelDetails);

  layout.append(chatPanel, guidance);
  void checkConfiguration();
  return layout;
}
