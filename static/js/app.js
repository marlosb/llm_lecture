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
const SHARED_STEP_MEDIA = {
  0: {
    image: "/static/images/step1.png",
    imageAlt: "Abstract blocks representing model construction",
    imageLayout: "right-with-text",
  },
  2: {
    image: "/static/images/tokens.png",
    imageAlt: "Tokenization examples",
    imageLayout: "center-large",
  },
  5: {
    inlineBodyImage: {
      src: "/static/images/step6.png",
      alt: "Books, newspapers and magazines used as training data",
      afterParagraph: 1,
    },
  },
  8: {
    image: "/static/images/step9.png",
    imageAlt: "Transition from text completion to chat interaction",
    imageLayout: "left-with-text",
  },
  12: {
    image: "/static/images/step13.png",
    imageAlt: "Reasoning workflow leading to improved outcomes",
    imageLayout: "left-with-text",
  },
  14: {
    image: "/static/images/step15.png",
    imageAlt: "Overview of LLM journey from data to aligned chat behavior",
    imageLayout: "below-centered",
  },
};
let tokenizerDebounceHandle = null;
let tokenizerRequestCounter = 0;
let idleTimeoutHandle = null;
let autoRefreshTimeoutHandle = null;
let autoRefreshIntervalHandle = null;
let tokenizerWatchIntervalHandle = null;
let tokenizerLastObservedValue = "";
let kioskboardHasRun = false;

const KIOSKBOARD_INPUT_SELECTOR = ".js-kioskboard-input";
const KIOSKBOARD_CLOSE_BUTTON_CLASS = "kioskboard-close-button";
const KIOSKBOARD_KEYS_BY_LANGUAGE = {
  "en-us": [
    { 0: "Q", 1: "W", 2: "E", 3: "R", 4: "T", 5: "Y", 6: "U", 7: "I", 8: "O", 9: "P" },
    { 0: "A", 1: "S", 2: "D", 3: "F", 4: "G", 5: "H", 6: "J", 7: "K", 8: "L" },
    { 0: "Z", 1: "X", 2: "C", 3: "V", 4: "B", 5: "N", 6: "M" },
  ],
  "pt-br": [
    { 0: "Q", 1: "W", 2: "E", 3: "R", 4: "T", 5: "Y", 6: "U", 7: "I", 8: "O", 9: "P" },
    { 0: "A", 1: "S", 2: "D", 3: "F", 4: "G", 5: "H", 6: "J", 7: "K", 8: "L", 9: "Ç" },
    { 0: "Z", 1: "X", 2: "C", 3: "V", 4: "B", 5: "N", 6: "M" },
  ],
  "es-mx": [
    { 0: "Q", 1: "W", 2: "E", 3: "R", 4: "T", 5: "Y", 6: "U", 7: "I", 8: "O", 9: "P" },
    { 0: "A", 1: "S", 2: "D", 3: "F", 4: "G", 5: "H", 6: "J", 7: "K", 8: "L", 9: "Ñ" },
    { 0: "Z", 1: "X", 2: "C", 3: "V", 4: "B", 5: "N", 6: "M" },
  ],
};

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

const getKioskboardSpaceText = () => {
  if (appState.currentLanguage === "es-mx") {
    return "Espacio";
  }
  if (appState.currentLanguage === "pt-br") {
    return "Espaço";
  }
  return "Space";
};

const getKioskboardCloseText = () => {
  if (appState.currentLanguage === "es-mx") {
    return "Cerrar";
  }
  if (appState.currentLanguage === "pt-br") {
    return "Fechar";
  }
  return "Close";
};

const closeKioskboard = () => {
  const activeElement = document.activeElement;
  if (activeElement instanceof HTMLElement && activeElement.matches(KIOSKBOARD_INPUT_SELECTOR)) {
    activeElement.blur();
  }

  const keyboardElement = document.getElementById("KioskBoard-VirtualKeyboard");
  if (keyboardElement) {
    keyboardElement.remove();
  }
  syncKioskboardBodyState();
};

const ensureKioskboardCloseButton = () => {
  const keyboardElement = document.getElementById("KioskBoard-VirtualKeyboard");
  if (!keyboardElement) {
    return;
  }

  let closeButton = keyboardElement.querySelector(`.${KIOSKBOARD_CLOSE_BUTTON_CLASS}`);
  if (!(closeButton instanceof HTMLButtonElement)) {
    closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = KIOSKBOARD_CLOSE_BUTTON_CLASS;
    closeButton.textContent = "×";
    closeButton.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeKioskboard();
    });
    keyboardElement.appendChild(closeButton);
  }

  closeButton.setAttribute("aria-label", getKioskboardCloseText());
  closeButton.title = getKioskboardCloseText();
};

const ensureFocusedInputVisibleAboveKeyboard = () => {
  const activeElement = document.activeElement;
  const keyboardElement = document.getElementById("KioskBoard-VirtualKeyboard");
  if (!(activeElement instanceof HTMLElement) || !activeElement.matches(KIOSKBOARD_INPUT_SELECTOR) || !keyboardElement) {
    return;
  }
  const keyboardTop = keyboardElement.getBoundingClientRect().top;
  const inputRect = activeElement.getBoundingClientRect();
  if (inputRect.bottom > keyboardTop - 10) {
    window.scrollBy({
      top: inputRect.bottom - keyboardTop + 28,
      behavior: "smooth",
    });
  }
};

const syncKioskboardBodyState = () => {
  const keyboardElement = document.getElementById("KioskBoard-VirtualKeyboard");
  const keyboardVisible = Boolean(keyboardElement);
  document.body.classList.toggle("kioskboard-visible", keyboardVisible);
  if (keyboardVisible) {
    ensureKioskboardCloseButton();
    ensureFocusedInputVisibleAboveKeyboard();
  }
};

const initKioskBoard = () => {
  if (!window.KioskBoard) {
    return;
  }
  const keysArrayOfObjects = KIOSKBOARD_KEYS_BY_LANGUAGE[appState.currentLanguage] || KIOSKBOARD_KEYS_BY_LANGUAGE["en-us"];
  window.KioskBoard.init({
    keysArrayOfObjects,
    keysJsonUrl: null,
    keysSpecialCharsArrayOfStrings: [
      "á", "à", "â", "ã", "ä",
      "é", "è", "ê", "ë",
      "í", "ì", "î", "ï",
      "ó", "ò", "ô", "õ", "ö",
      "ú", "ù", "û", "ü",
      "ç", "ñ",
      "Á", "À", "Â", "Ã", "Ä",
      "É", "È", "Ê", "Ë",
      "Í", "Ì", "Î", "Ï",
      "Ó", "Ò", "Ô", "Õ", "Ö",
      "Ú", "Ù", "Û", "Ü",
      "Ç", "Ñ",
    ],
    keysNumpadArrayOfNumbers: null,
    language: "en",
    theme: "light",
    autoScroll: true,
    capsLockActive: false,
    allowRealKeyboard: false,
    allowMobileKeyboard: false,
    cssAnimations: true,
    cssAnimationsDuration: 360,
    cssAnimationsStyle: "slide",
    keysAllowSpacebar: true,
    keysSpacebarText: getKioskboardSpaceText(),
    keysFontFamily: "Segoe UI, Arial, sans-serif",
    keysFontSize: "20px",
    keysFontWeight: "normal",
    keysIconSize: "22px",
    keysEnterText: "Enter",
    keysEnterCallback: () => {
      ensureFocusedInputVisibleAboveKeyboard();
    },
    keysEnterCanClose: false,
  });
  if (!kioskboardHasRun) {
    window.KioskBoard.run(KIOSKBOARD_INPUT_SELECTOR);
    kioskboardHasRun = true;
  }
  syncKioskboardBodyState();
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

const renderStepBody = (stepBodyHtml, inlineBodyImageConfig) => {
  stepBody.innerHTML = "";
  if (!stepBodyHtml) {
    return;
  }

  const paragraphs = stepBodyHtml.split(/\n\s*\n/);
  const insertAfter = Number.isInteger(inlineBodyImageConfig?.afterParagraph)
    ? inlineBodyImageConfig.afterParagraph
    : -1;

  paragraphs.forEach((paragraphHtml, index) => {
    const paragraph = document.createElement("p");
    paragraph.className = "step-body-paragraph";
    paragraph.innerHTML = paragraphHtml.trim();
    stepBody.appendChild(paragraph);

    if (index === insertAfter && inlineBodyImageConfig?.src) {
      const inlineImage = document.createElement("img");
      inlineImage.className = "step-inline-image";
      inlineImage.src = inlineBodyImageConfig.src;
      inlineImage.alt = inlineBodyImageConfig.alt || "";
      stepBody.appendChild(inlineImage);
    }
  });
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
      const rawErrorBody = await response.text();
      let backendMessage = "";
      if (rawErrorBody) {
        try {
          const errorPayload = JSON.parse(rawErrorBody);
          if (errorPayload && typeof errorPayload.detail === "string") {
            backendMessage = errorPayload.detail;
          }
        } catch (parseError) {
          backendMessage = rawErrorBody.trim();
        }
      }
      throw new Error(backendMessage || appState.ui.tokenizerRequestError);
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
  const stepMedia = SHARED_STEP_MEDIA[appState.currentStep] || {};
  renderStepBody(step.body || "", stepMedia.inlineBodyImage);
  stepBody.classList.toggle("hidden", !step.body);
  const stepImageSource = stepMedia.image || step.image;
  const stepImageAlt = stepMedia.imageAlt || step.imageAlt || step.title;
  const stepImageLayout = stepMedia.imageLayout || step.imageLayout;
  const useCenterLargeImage = stepImageLayout === "center-large";
  const useRightWithTextImage = stepImageLayout === "right-with-text";
  const useLeftWithTextImage = stepImageLayout === "left-with-text";
  const useBelowCenteredImage = stepImageLayout === "below-centered";
  stepCard.classList.toggle("image-center-large", useCenterLargeImage);
  stepCard.classList.toggle("image-right-with-text", useRightWithTextImage);
  stepCard.classList.toggle("image-left-with-text", useLeftWithTextImage);
  stepCard.classList.toggle("image-below-centered", useBelowCenteredImage);
  if (stepImageSource) {
    stepImage.src = stepImageSource;
    stepImage.alt = stepImageAlt;
    stepImage.classList.toggle("step-image-center-large", useCenterLargeImage);
    stepImage.classList.toggle("step-image-right-with-text", useRightWithTextImage);
    stepImage.classList.toggle("step-image-left-with-text", useLeftWithTextImage);
    stepImage.classList.toggle("step-image-below-centered", useBelowCenteredImage);
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
    stepImage.classList.remove("step-image-right-with-text");
    stepImage.classList.remove("step-image-left-with-text");
    stepImage.classList.remove("step-image-below-centered");
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
  initKioskBoard();
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

const queueTokenizerRun = () => {
  clearTimeout(tokenizerDebounceHandle);
  tokenizerDebounceHandle = setTimeout(() => {
    runTokenizer(tokenizerInput.value);
  }, 250);
};

tokenizerInput.addEventListener("change", queueTokenizerRun);

const startTokenizerWatch = () => {
  if (tokenizerWatchIntervalHandle) {
    return;
  }
  tokenizerLastObservedValue = tokenizerInput.value;
  tokenizerWatchIntervalHandle = setInterval(() => {
    if (document.activeElement !== tokenizerInput) {
      return;
    }
    if (tokenizerInput.value !== tokenizerLastObservedValue) {
      tokenizerLastObservedValue = tokenizerInput.value;
      queueTokenizerRun();
    }
  }, 120);
};

const stopTokenizerWatch = () => {
  if (!tokenizerWatchIntervalHandle) {
    return;
  }
  clearInterval(tokenizerWatchIntervalHandle);
  tokenizerWatchIntervalHandle = null;
};

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

document.addEventListener("focusin", (event) => {
  if (event.target instanceof HTMLElement && event.target.matches(KIOSKBOARD_INPUT_SELECTOR)) {
    setTimeout(() => {
      syncKioskboardBodyState();
      ensureFocusedInputVisibleAboveKeyboard();
    }, 0);
  }
  if (event.target === tokenizerInput) {
    startTokenizerWatch();
  }
});

document.addEventListener("focusout", (event) => {
  if (event.target instanceof HTMLElement && event.target.matches(KIOSKBOARD_INPUT_SELECTOR)) {
    setTimeout(syncKioskboardBodyState, 60);
  }
  if (event.target === tokenizerInput) {
    stopTokenizerWatch();
  }
});

window.addEventListener("resize", () => {
  ensureFocusedInputVisibleAboveKeyboard();
  syncKioskboardBodyState();
});

const kioskboardObserver = new MutationObserver(() => {
  syncKioskboardBodyState();
});
kioskboardObserver.observe(document.body, { childList: true, subtree: true });

document.addEventListener("click", (event) => {
  const keyboardContainer = event.target instanceof HTMLElement
    ? event.target.closest("#KioskBoard-VirtualKeyboard")
    : null;
  if (!keyboardContainer) {
    return;
  }
  if (document.activeElement === tokenizerInput) {
    queueTokenizerRun();
  }
});

initKioskBoard();
if (document.activeElement === tokenizerInput) {
  startTokenizerWatch();
}
startIdleTimer();
