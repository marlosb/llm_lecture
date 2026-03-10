const languageScreen = document.getElementById("language-screen");
const contentScreen = document.getElementById("content-screen");
const languageMenuButton = document.getElementById("language-menu-button");
const languageMenu = document.getElementById("language-menu");
const currentLanguageFlag = document.getElementById("current-language-flag");

const appTitle = document.getElementById("app-title");
const progressBar = document.getElementById("progress-bar");
const stepCard = document.querySelector(".step-card");
const stepCounter = document.getElementById("step-counter");
const stepTitle = document.getElementById("step-title");
const stepSubtitle = document.getElementById("step-subtitle");
const stepBody = document.getElementById("step-body");
const stepImage = document.getElementById("step-image");
const tokenizerPanel = document.getElementById("tokenizer-panel");
const tokenizerInput = document.getElementById("tokenizer-input");
const tokenizerTokenCount = document.getElementById("tokenizer-token-count");
const tokenizerColoredOutput = document.getElementById("tokenizer-colored-output");
const tokenizerIdsOutput = document.getElementById("tokenizer-ids-output");
const pretrainPanel = document.getElementById("pretrain-panel");
const pretrainInput = document.getElementById("pretrain-input");
const pretrainSubmitButton = document.getElementById("pretrain-submit-button");
const chatPanel = document.getElementById("chat-panel");
const chatThread = document.getElementById("chat-thread");
const chatInput = document.getElementById("chat-input");
const chatSubmitButton = document.getElementById("chat-submit-button");
const backButton = document.getElementById("back-button");
const nextButton = document.getElementById("next-button");
const idleWarningBanner = document.getElementById("idle-warning-banner");
const idleWarningText = document.getElementById("idle-warning-text");
const idleWarningCancel = document.getElementById("idle-warning-cancel");

const languageTriggers = document.querySelectorAll("[data-language]");
const flagByLanguage = {
  "en-us": "/static/images/flags/us-canada-diagonal.svg",
  "pt-br": "/static/images/flags/brazil.svg",
  "es-mx": "/static/images/flags/mexico.svg",
};

const TOTAL_SEGMENTS = 15;
const IDLE_LIMIT_MS = 5 * 60 * 1000;
const AUTO_REFRESH_SECONDS = 30;
const appState = {
  currentLanguage: "pt-br",
  steps: [],
  currentStep: 0,
  chatMessages: [],
  labels: {
    back: "Voltar",
    next: "Avancar",
    counterPrefix: "PARTE",
  },
  ui: {
    progressAriaLabel: "Ir para parte {part}",
    idleWarningMessage: "Página inativa. Atualização automática em {seconds}s.",
    idleWarningCancel: "Cancelar",
    tokenizerLabel: "Digite um texto para tokenizar",
    tokenizerEmptyMessage: "Digite um texto para ver os tokens.",
    tokenizerTotalTokens: "Total de tokens: {count}",
    tokenizerIdsLabel: "IDs",
    pretrainLabel: "Digite o início de um texto",
    pretrainSubmit: "Gerar continuação",
    textCompletionError: "Falha ao gerar continuação.",
    chatSubmit: "Enviar",
    chatWelcome: "Olá! Escreva sua mensagem para começarmos.",
    chatError: "Falha ao gerar resposta do chat.",
    chatFallbackError: "Erro no chat.",
    tokenizerRequestError: "Falha ao tokenizar o texto.",
    tokenizerFallbackError: "Erro ao tokenizar.",
  },
};
const defaultLabels = { ...appState.labels };
const defaultUiLabels = { ...appState.ui };
const TOKEN_COLORS = [
  "#ffd7d7",
  "#ffe9c5",
  "#fff1a8",
  "#d8f5d0",
  "#cdefff",
  "#dfdcff",
  "#f6d8ff",
];
let tokenizerDebounceHandle = null;
let tokenizerRequestCounter = 0;
let idleTimeoutHandle = null;
let autoRefreshTimeoutHandle = null;
let autoRefreshIntervalHandle = null;

const getSegmentClass = (segmentIndex) => {
  const customColor = appState.steps[segmentIndex]?.progressColor;
  if (customColor === "blue") {
    return "segment-blue";
  }
  if (customColor === "primary") {
    return "segment-primary";
  }
  if (customColor === "orange") {
    return "segment-orange";
  }
  if (segmentIndex === 0) {
    return "segment-primary";
  }
  const groupIndex = (segmentIndex - 1) % 6;
  return groupIndex < 3 ? "segment-blue" : "segment-orange";
};

const formatLabel = (template, values = {}) => {
  return Object.entries(values).reduce((accumulator, [key, value]) => {
    return accumulator.replaceAll(`{${key}}`, String(value));
  }, template);
};

const renderStaticUiText = () => {
  idleWarningCancel.textContent = appState.ui.idleWarningCancel;
  const tokenizerLabel = document.querySelector("label[for='tokenizer-input']");
  const pretrainLabel = document.querySelector("label[for='pretrain-input']");
  if (tokenizerLabel) {
    tokenizerLabel.textContent = appState.ui.tokenizerLabel;
  }
  if (pretrainLabel) {
    pretrainLabel.textContent = appState.ui.pretrainLabel;
  }
  pretrainSubmitButton.textContent = appState.ui.pretrainSubmit;
  chatSubmitButton.textContent = appState.ui.chatSubmit;
};

const renderProgress = () => {
  progressBar.innerHTML = "";
  const availableSteps = appState.steps.length;
  for (let index = 0; index < TOTAL_SEGMENTS; index += 1) {
    const segment = document.createElement("button");
    segment.type = "button";
    segment.className = "progress-segment";
    segment.dataset.stepIndex = String(index);
    segment.setAttribute(
      "aria-label",
      formatLabel(appState.ui.progressAriaLabel, { part: index + 1 }),
    );
    segment.disabled = index >= availableSteps;
    if (index <= appState.currentStep) {
      segment.classList.add("active", getSegmentClass(index));
    }
    progressBar.appendChild(segment);
  }
};

const hideIdleWarning = () => {
  idleWarningBanner.classList.add("hidden");
  if (autoRefreshTimeoutHandle) {
    clearTimeout(autoRefreshTimeoutHandle);
    autoRefreshTimeoutHandle = null;
  }
  if (autoRefreshIntervalHandle) {
    clearInterval(autoRefreshIntervalHandle);
    autoRefreshIntervalHandle = null;
  }
};

const startIdleTimer = () => {
  if (idleTimeoutHandle) {
    clearTimeout(idleTimeoutHandle);
  }
  idleTimeoutHandle = setTimeout(() => {
    if (contentScreen.classList.contains("hidden")) {
      startIdleTimer();
      return;
    }

    let remainingSeconds = AUTO_REFRESH_SECONDS;
    idleWarningText.textContent = formatLabel(appState.ui.idleWarningMessage, {
      seconds: remainingSeconds,
    });
    idleWarningBanner.classList.remove("hidden");

    autoRefreshIntervalHandle = setInterval(() => {
      remainingSeconds -= 1;
      if (remainingSeconds <= 0) {
        clearInterval(autoRefreshIntervalHandle);
        autoRefreshIntervalHandle = null;
        return;
      }
      idleWarningText.textContent = formatLabel(appState.ui.idleWarningMessage, {
        seconds: remainingSeconds,
      });
    }, 1000);

    autoRefreshTimeoutHandle = setTimeout(() => {
      window.location.reload();
    }, AUTO_REFRESH_SECONDS * 1000);
  }, IDLE_LIMIT_MS);
};

const markUserActivity = () => {
  if (!idleWarningBanner.classList.contains("hidden")) {
    return;
  }
  startIdleTimer();
};

const clearTokenizerOutputs = (message = "") => {
  tokenizerTokenCount.textContent = message;
  tokenizerColoredOutput.textContent = "";
  tokenizerIdsOutput.textContent = "";
};

const renderTokenizerResult = (result) => {
  tokenizerTokenCount.textContent = formatLabel(appState.ui.tokenizerTotalTokens, {
    count: result.token_ids.length,
  });
  tokenizerColoredOutput.innerHTML = "";
  result.tokens.forEach((token, index) => {
    const tokenSpan = document.createElement("span");
    tokenSpan.className = "token-chip";
    tokenSpan.style.backgroundColor = TOKEN_COLORS[index % TOKEN_COLORS.length];
    tokenSpan.textContent = token.text;
    tokenizerColoredOutput.appendChild(tokenSpan);
  });
  tokenizerIdsOutput.textContent = `${appState.ui.tokenizerIdsLabel}: ${result.token_ids.join(", ")}`;
};

const runTextCompletion = async () => {
  const step = appState.steps[appState.currentStep];
  if (!step || step.interactive !== "text-completion") {
    return;
  }

  const prompt = pretrainInput.value.trim();
  if (!prompt) {
    return;
  }

  pretrainSubmitButton.disabled = true;
  try {
    const response = await fetch("/api/text-complete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: prompt,
        max_new_tokens: step.maxNewTokens || 60,
      }),
    });
    if (!response.ok) {
      let message = appState.ui.textCompletionError;
      try {
        const errorPayload = await response.json();
        if (errorPayload?.detail) {
          message = errorPayload.detail;
        }
      } catch (_unused) {
        // Keep default message when error payload is not JSON.
      }
      throw new Error(message);
    }
    const payload = await response.json();
    pretrainInput.value = payload.full_text;
  } catch (error) {
    // Keep user text unchanged when generation fails.
  } finally {
    pretrainSubmitButton.disabled = false;
  }
};

const renderChatMessages = () => {
  chatThread.innerHTML = "";
  appState.chatMessages.forEach((message) => {
    const bubble = document.createElement("div");
    bubble.className = `chat-message ${message.role}`;
    bubble.textContent = message.text;
    chatThread.appendChild(bubble);
  });
  chatThread.scrollTop = chatThread.scrollHeight;
};

const runChatCompletion = async () => {
  const step = appState.steps[appState.currentStep];
  const isChatStep = step && (step.interactive === "chat-completion" || step.interactive === "reasoning-chat-completion");
  if (!isChatStep) {
    return;
  }

  const prompt = chatInput.value.trim();
  if (!prompt) {
    return;
  }

  appState.chatMessages.push({ role: "user", text: prompt });
  appState.chatMessages.push({ role: "assistant", text: "..." });
  renderChatMessages();
  chatInput.value = "";
  chatSubmitButton.disabled = true;
  try {
    const endpoint = step.interactive === "reasoning-chat-completion"
      ? "/api/reasoning-chat-complete"
      : "/api/chat-complete";
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: prompt,
      }),
    });
    if (!response.ok) {
      let message = appState.ui.chatError;
      try {
        const errorPayload = await response.json();
        if (errorPayload?.detail) {
          message = errorPayload.detail;
        }
      } catch (_unused) {
        // Keep default message when error payload is not JSON.
      }
      throw new Error(message);
    }
    const payload = await response.json();
    appState.chatMessages.pop();
    appState.chatMessages.push({ role: "assistant", text: payload.completion });
    renderChatMessages();
  } catch (error) {
    appState.chatMessages.pop();
    appState.chatMessages.push({
      role: "assistant",
      text: error.message || appState.ui.chatFallbackError,
    });
    renderChatMessages();
  } finally {
    chatSubmitButton.disabled = false;
  }
};

const runTokenizer = async (inputText) => {
  const step = appState.steps[appState.currentStep];
  if (!step || step.interactive !== "tokenizer") {
    return;
  }
  if (inputText.trim() === "") {
    clearTokenizerOutputs(appState.ui.tokenizerEmptyMessage);
    return;
  }

  const requestId = tokenizerRequestCounter + 1;
  tokenizerRequestCounter = requestId;
  try {
    const response = await fetch("/api/tokenize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: inputText }),
    });
    if (!response.ok) {
      throw new Error(appState.ui.tokenizerRequestError);
    }
    const payload = await response.json();
    if (requestId !== tokenizerRequestCounter) {
      return;
    }
    renderTokenizerResult(payload);
  } catch (error) {
    clearTokenizerOutputs(error.message || appState.ui.tokenizerFallbackError);
  }
};

const renderStep = () => {
  const step = appState.steps[appState.currentStep];
  if (!step) {
    return;
  }

  stepCounter.textContent = `${appState.labels.counterPrefix} ${appState.currentStep + 1} / ${appState.steps.length}`;
  stepTitle.textContent = step.title;
  stepSubtitle.textContent = step.subtitle || "";
  stepSubtitle.classList.toggle("hidden", !step.subtitle);
  stepBody.innerHTML = step.body || "";
  stepBody.classList.toggle("hidden", !step.body);
  const useCenterLargeImage = step.imageLayout === "center-large";
  stepCard.classList.toggle("image-center-large", useCenterLargeImage);
  if (step.image) {
    stepImage.src = step.image;
    stepImage.alt = step.imageAlt || step.title;
    stepImage.classList.toggle("step-image-center-large", useCenterLargeImage);
    if (useCenterLargeImage) {
      stepImage.style.margin = "20px auto 0";
      stepImage.style.alignSelf = "center";
      stepImage.style.width = "min(760px, 95%)";
      stepImage.style.maxHeight = "460px";
    } else {
      stepImage.style.margin = "";
      stepImage.style.alignSelf = "";
      stepImage.style.width = "";
      stepImage.style.maxHeight = "";
    }
    stepImage.classList.remove("hidden");
  } else {
    stepImage.classList.add("hidden");
    stepImage.classList.remove("step-image-center-large");
    stepImage.style.margin = "";
    stepImage.style.alignSelf = "";
    stepImage.style.width = "";
    stepImage.style.maxHeight = "";
    stepImage.src = "";
    stepImage.alt = "";
  }
  const tokenizerEnabled = step.interactive === "tokenizer";
  const pretrainEnabled = step.interactive === "text-completion";
  const chatEnabled =
    step.interactive === "chat-completion" ||
    step.interactive === "reasoning-chat-completion";
  tokenizerPanel.classList.toggle("hidden", !tokenizerEnabled);
  pretrainPanel.classList.toggle("hidden", !pretrainEnabled);
  chatPanel.classList.toggle("hidden", !chatEnabled);
  if (tokenizerEnabled) {
    if (step.tokenizerPrompt) {
      tokenizerInput.placeholder = step.tokenizerPrompt;
    }
    if (step.tokenizerSeedText && !tokenizerInput.value) {
      tokenizerInput.value = step.tokenizerSeedText;
    }
    runTokenizer(tokenizerInput.value);
  } else {
    tokenizerInput.value = "";
    clearTokenizerOutputs();
  }

  if (pretrainEnabled) {
    if (step.textPrompt) {
      pretrainInput.placeholder = step.textPrompt;
    }
    if (step.textSeedText) {
      pretrainInput.value = step.textSeedText;
    } else {
      pretrainInput.value = "";
    }
  } else {
    pretrainInput.value = "";
  }

  if (chatEnabled) {
    if (step.chatPrompt) {
      chatInput.placeholder = step.chatPrompt;
    }
    if (step.chatSeedText) {
      chatInput.value = step.chatSeedText;
    } else {
      chatInput.value = "";
    }
    appState.chatMessages = [
      { role: "assistant", text: appState.ui.chatWelcome },
    ];
    renderChatMessages();
  } else {
    chatInput.value = "";
    appState.chatMessages = [];
    renderChatMessages();
  }

  backButton.disabled = appState.currentStep === 0;
  nextButton.disabled = appState.currentStep >= appState.steps.length - 1;
  backButton.textContent = appState.labels.back;
  nextButton.textContent = appState.labels.next;

  renderProgress();
};

const showContentScreen = () => {
  languageScreen.classList.add("hidden");
  contentScreen.classList.remove("hidden");
  hideIdleWarning();
  startIdleTimer();
};

const updateCurrentLanguage = (languageCode) => {
  currentLanguageFlag.src = flagByLanguage[languageCode];
  currentLanguageFlag.alt = `Selected language ${languageCode}`;
};

const closeLanguageMenu = () => {
  languageMenu.classList.add("hidden");
  languageMenuButton.setAttribute("aria-expanded", "false");
};

const loadLanguage = async (languageCode) => {
  const response = await fetch(`/api/content/${languageCode}`);
  if (!response.ok) {
    throw new Error(`Unable to load language ${languageCode}.`);
  }
  const payload = await response.json();
  appState.currentLanguage = languageCode;
  appState.currentStep = 0;
  appState.steps = payload.steps || [
    {
      title: payload.headline || "Conteudo",
      body: payload.description || "Conteudo em preparacao para este idioma.",
    },
  ];
  appState.labels = { ...defaultLabels, ...(payload.navigation || {}) };
  appState.ui = { ...defaultUiLabels, ...(payload.ui || {}) };
  appTitle.textContent = payload.appTitle || "LLM Lecture";

  renderStaticUiText();
  renderStep();
  updateCurrentLanguage(languageCode);
  closeLanguageMenu();
  showContentScreen();
};

languageTriggers.forEach((trigger) => {
  trigger.addEventListener("click", async () => {
    const { language } = trigger.dataset;
    if (!language) {
      return;
    }
    await loadLanguage(language);
  });
});

languageMenuButton.addEventListener("click", () => {
  const expanded = languageMenuButton.getAttribute("aria-expanded") === "true";
  languageMenuButton.setAttribute("aria-expanded", String(!expanded));
  languageMenu.classList.toggle("hidden", expanded);
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".language-switcher")) {
    closeLanguageMenu();
  }
});

backButton.addEventListener("click", () => {
  if (appState.currentStep === 0) {
    return;
  }
  appState.currentStep -= 1;
  renderStep();
});

nextButton.addEventListener("click", () => {
  if (appState.currentStep >= appState.steps.length - 1) {
    return;
  }
  appState.currentStep += 1;
  renderStep();
});

progressBar.addEventListener("click", (event) => {
  const target = event.target.closest(".progress-segment");
  if (!target) {
    return;
  }

  const stepIndex = Number(target.dataset.stepIndex);
  if (!Number.isInteger(stepIndex) || stepIndex < 0) {
    return;
  }
  if (stepIndex >= appState.steps.length) {
    return;
  }

  appState.currentStep = stepIndex;
  renderStep();
});

tokenizerInput.addEventListener("input", () => {
  clearTimeout(tokenizerDebounceHandle);
  tokenizerDebounceHandle = setTimeout(() => {
    runTokenizer(tokenizerInput.value);
  }, 250);
});

pretrainSubmitButton.addEventListener("click", () => {
  runTextCompletion();
});

chatSubmitButton.addEventListener("click", () => {
  runChatCompletion();
});

idleWarningCancel.addEventListener("click", () => {
  hideIdleWarning();
  startIdleTimer();
});

["pointerdown", "pointermove", "keydown", "scroll", "touchstart"].forEach((eventName) => {
  window.addEventListener(eventName, markUserActivity, { passive: true });
});

startIdleTimer();
