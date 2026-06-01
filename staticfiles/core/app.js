(() => {
  if (window.CALocalPrint) return;
  const AGENT_URLS = ["http://127.0.0.1:8765", "http://localhost:8765"];
  const TERMINAL_STORAGE_KEY = "prefacturas.caja.terminal_nombre";
  const TERMINAL_SEED_KEY = "prefacturas.caja.terminal_seed";
  let prefsCache = null;
  let prefsCacheTerminal = "";
  let activeAgentUrl = "";
  let resolvedTerminalName = "";
  let terminalPromise = null;

  const normalizeTerminalName = (value) =>
    String(value ?? "").replace(/\s+/g, " ").trim().slice(0, 100);

  const getFallbackTerminalName = () => {
    try {
      const stored = normalizeTerminalName(window.localStorage.getItem(TERMINAL_STORAGE_KEY) || "");
      if (stored) return stored;
      const existingSeed = normalizeTerminalName(window.localStorage.getItem(TERMINAL_SEED_KEY) || "");
      if (existingSeed) return `Equipo-${existingSeed}`;
      const generated = `EQ-${Math.random().toString(36).slice(2, 8)}`.toUpperCase();
      window.localStorage.setItem(TERMINAL_SEED_KEY, generated);
      return `Equipo-${generated}`;
    } catch (error) {
      return "default";
    }
  };

  const getTerminalName = () => resolvedTerminalName || getFallbackTerminalName();

  const resolveTerminalName = async (force = false) => {
    if (!force && resolvedTerminalName) return resolvedTerminalName;
    if (!force && terminalPromise) return terminalPromise;
    terminalPromise = (async () => {
      try {
        const agentUrl = await getAgentUrl();
        const response = await fetch(`${agentUrl}/identity`, { method: "GET", cache: "no-store" });
        const data = await response.json().catch(() => ({}));
        const terminal = normalizeTerminalName(data.terminal || data.hostname || data.computer_name || "");
        if (response.ok && terminal) {
          resolvedTerminalName = terminal;
          try {
            window.localStorage.setItem(TERMINAL_STORAGE_KEY, terminal);
          } catch (error) {
            // LocalStorage may be unavailable in restricted browser profiles.
          }
          return terminal;
        }
      } catch (error) {
        console.warn("No se pudo leer la identidad del agente local.", error);
      }
      resolvedTerminalName = getFallbackTerminalName();
      return resolvedTerminalName;
    })();
    try {
      return await terminalPromise;
    } finally {
      terminalPromise = null;
    }
  };

  const getPreferences = async (force = false) => {
    const terminal = await resolveTerminalName();
    if (!force && prefsCache && prefsCacheTerminal === terminal) return prefsCache;
    const url = window.CA_PRINT_PREFS_URL || "/app/ajustes/parametros/impresoras/preferencias/";
    const response = await fetch(`${url}?terminal=${encodeURIComponent(terminal)}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error("No se pudo cargar la preferencia de impresora.");
    const data = await response.json();
    prefsCache = data.preferencias || {};
    prefsCacheTerminal = terminal;
    return prefsCache;
  };

  const getPreferredPrinter = async (tipoDocumento) => {
    const prefs = await getPreferences(true);
    const pref = prefs[String(tipoDocumento || "")] || {};
    return String(pref.nombre_impresora || "").trim();
  };

  const getPrintTarget = async (tipoDocumento) => {
    const printer = await getPreferredPrinter(tipoDocumento);
    return {
      printer,
      hasPrinter: Boolean(printer),
      label: printer ? "Impresora seleccionada: " + printer : "Dialogo del navegador (selecciona la impresora al imprimir)",
    };
  };

  const isAgentAvailable = async () => {
    for (const agentUrl of AGENT_URLS) {
      try {
        const response = await fetch(`${agentUrl}/health`, { method: "GET", cache: "no-store" });
        if (response.ok) {
          activeAgentUrl = agentUrl;
          return true;
        }
      } catch (error) {
        console.warn(`No se pudo contactar el agente local en ${agentUrl}.`, error);
      }
    }
    activeAgentUrl = "";
    return false;
  };

  const getAgentUrl = async () => {
    if (activeAgentUrl && (await isAgentAvailable())) return activeAgentUrl;
    if (await isAgentAvailable()) return activeAgentUrl;
    throw new Error("No se detecta el agente local de impresion en esta maquina.");
  };

  const getLocalPrinters = async () => {
    const agentUrl = await getAgentUrl();
    const response = await fetch(`${agentUrl}/printers`, { method: "GET", cache: "no-store" });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      throw new Error(data.detail || "No se pudo cargar la lista local de impresoras.");
    }
    return Array.isArray(data.printers) ? data.printers : [];
  };

  const printHtml = async (tipoDocumento, html, options) => {
    const printer = await getPreferredPrinter(tipoDocumento);
    if (!printer) return false;
    const agentUrl = await getAgentUrl();
    const response = await fetch(`${agentUrl}/print`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
      body: JSON.stringify({
        printer,
        html,
        title: options?.title || document.title || "",
        wait_seconds: options?.waitSeconds || 5,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.ok === false) {
      throw new Error(data.detail || "No se pudo imprimir con el agente local.");
    }
    return true;
  };

  window.CALocalPrint = {
    getTerminalName,
    getPreferences,
    getPreferredPrinter,
    getPrintTarget,
    resolveTerminalName,
    isAgentAvailable,
    getLocalPrinters,
    printHtml,
    getAgentUrl,
  };
})();

(() => {
  const toggle = document.getElementById("menuToggle");
  const desktopToggle = document.getElementById("sidebarCollapseToggle");
  const overlay = document.getElementById("navOverlay");
  const desktopMedia = window.matchMedia("(min-width: 901px)");
  const desktopStorageKey = "yeo_sidebar_collapsed";

  const notificationShell = document.getElementById("topbarNotifications");
  const activeNav = String(document.body?.dataset?.activeNav || "").trim();
  const currentUserId = Number(document.body?.dataset?.userId || 0);
  const chatEnabled = String(document.body?.dataset?.chatEnabled || "").trim().toLowerCase() === "true";
  const chatSocketUrl = String(document.body?.dataset?.chatSocketUrl || "").trim();
  const chatIndexUrl = String(document.body?.dataset?.chatIndexUrl || "").trim();
  const notificationToggle = document.getElementById("topbarNotificationToggle");
  const notificationBadge = document.getElementById("topbarNotificationBadge");
  const notificationMenu = document.getElementById("topbarNotificationMenu");
  const notificationList = document.getElementById("topbarNotificationList");
  const notificationMenuCount = document.getElementById("topbarNotificationMenuCount");
  const notificationsUrl = String(notificationShell?.dataset.summaryUrl || "").trim();
  const notificationSocketUrl = String(notificationShell?.dataset.socketUrl || "").trim();
  const stockRequestSocketUrl = String(notificationShell?.dataset.stockRequestSocketUrl || "").trim();
  const notificationMarkReadTemplate = String(notificationShell?.dataset.markReadTemplate || "").trim();
  const notificationMarkReadBulkUrl = String(notificationShell?.dataset.markReadBulkUrl || "").trim();
  const notificationDeleteTemplate = String(notificationShell?.dataset.deleteTemplate || "").trim();
  const notificationDeliveredUrl = String(notificationShell?.dataset.deliveredUrl || "").trim();
  const notificationCsrfToken = String(notificationShell?.dataset.csrfToken || "").trim();
  const notificationUserKey = String(notificationShell?.dataset.userKey || "default").trim() || "default";
  const stockRequestNotifyEnabled = String(notificationShell?.dataset.stockRequestNotifyEnabled || "").trim().toLowerCase() === "true";
  const themeStorageKey = "ca_erp.theme_mode";
  const themeRoot = document.documentElement;
  const themeSelect = document.querySelector("[data-theme-select]");
  const themeStatus = document.querySelector("[data-theme-status]");
  const notificationContext = document.getElementById("topbarNotificationContext");
  const notificationMarkRead = document.getElementById("topbarNotificationMarkRead");
  const notificationDelete = document.getElementById("topbarNotificationDelete");
  const accountProfileTrigger = document.getElementById("accountProfileTrigger");
  const accountPasswordModal = document.getElementById("accountPasswordModal");
  const accountPasswordClose = document.getElementById("accountPasswordModalClose");
  const accountPasswordCancel = document.getElementById("accountPasswordCancel");
  const accountPasswordForm = document.getElementById("accountPasswordForm");
  const accountPasswordStatus = document.getElementById("accountPasswordStatus");
  const accountPasswordName = document.getElementById("accountPasswordName");
  const accountPasswordLogin = document.getElementById("accountPasswordLogin");
  const accountPasswordNew = document.getElementById("accountPasswordNew");
  const accountPasswordConfirm = document.getElementById("accountPasswordConfirm");
  const accountPasswordSubmit = document.getElementById("accountPasswordSubmit");
  const notificationReadStorageKey = `ca_erp.notification_reads.${notificationUserKey}`;
  const notificationHiddenStorageKey = `ca_erp.notification_hidden.${notificationUserKey}`;
  const notificationDeliveredStorageKey = `ca_erp.notification_delivered.${notificationUserKey}`;
  const chatNotificationItemsStorageKey = `ca_erp.chat_notifications.${notificationUserKey}`;
  const sharedTerminalStorageKey = "prefacturas.caja.terminal_nombre";
  const sharedTerminalSeedKey = "prefacturas.caja.terminal_seed";
  let notificationsOpen = false;
  let notificationContextItem = null;
  let latestNotificationsPayload = { allowed: false, count: 0, results: [] };
  let notificationPollHandle = null;
  let notificationSocket = null;
  let notificationSocketConnected = false;
  let notificationReconnectHandle = null;
  let notificationPermissionAsked = false;
  let notificationToastHost = null;
  let chatNotificationSocket = null;
  let chatNotificationSocketConnected = false;
  let chatNotificationReconnectHandle = null;
  let stockRequestSocket = null;
  let stockRequestSocketConnected = false;
  let stockRequestReconnectHandle = null;

  const closeNav = () => document.body.classList.remove("nav-open");
  const openNav = () => document.body.classList.add("nav-open");
  const isDesktop = () => desktopMedia.matches;
  const isCollapsed = () => document.body.classList.contains("sidebar-collapsed");
  const normalizeTheme = (value) => String(value || "").trim().toLowerCase() === "dark" ? "dark" : "light";

  const readSavedTheme = () => {
    try {
      return normalizeTheme(window.localStorage.getItem(themeStorageKey));
    } catch (error) {
      return normalizeTheme(themeRoot?.dataset?.theme || "light");
    }
  };

  const syncThemeControls = (theme) => {
    if (themeSelect && themeSelect.value !== theme) {
      themeSelect.value = theme;
    }
    if (themeStatus) {
      themeStatus.textContent = theme === "dark"
        ? "Modo oscuro activo en esta terminal."
        : "Modo claro activo en esta terminal.";
    }
  };

  const applyTheme = (theme, persist = true) => {
    const normalized = normalizeTheme(theme);
    if (themeRoot) {
      themeRoot.setAttribute("data-theme", normalized);
      themeRoot.style.colorScheme = normalized === "dark" ? "dark" : "light";
    }
    if (persist) {
      try {
        window.localStorage.setItem(themeStorageKey, normalized);
      } catch (error) {
        // Ignore storage failures and keep the in-memory state.
      }
    }
    syncThemeControls(normalized);
    window.dispatchEvent(new CustomEvent("ca-erp-theme-change", { detail: { theme: normalized } }));
    return normalized;
  };

  const setAccountPasswordStatus = (message, kind) => {
    if (!accountPasswordStatus) return;
    const text = String(message || "").trim();
    if (!text) {
      accountPasswordStatus.hidden = true;
      accountPasswordStatus.textContent = "";
      accountPasswordStatus.className = "account-modal-status";
      return;
    }
    accountPasswordStatus.hidden = false;
    accountPasswordStatus.textContent = text;
    accountPasswordStatus.className = `account-modal-status ${kind === "success" ? "is-success" : "is-error"}`;
  };

  const closeAccountPasswordModal = () => {
    if (!accountPasswordModal) return;
    accountPasswordModal.hidden = true;
    document.body.style.overflow = "";
    setAccountPasswordStatus("");
    if (accountPasswordForm) {
      accountPasswordForm.reset();
    }
  };

  const openAccountPasswordModal = () => {
    if (!accountPasswordModal || !accountProfileTrigger) return;
    if (accountPasswordName) {
      accountPasswordName.value = String(accountProfileTrigger.dataset.userName || "").trim();
    }
    if (accountPasswordLogin) {
      accountPasswordLogin.value = String(accountProfileTrigger.dataset.userLogin || "").trim();
    }
    if (accountPasswordNew) {
      accountPasswordNew.value = "";
    }
    if (accountPasswordConfirm) {
      accountPasswordConfirm.value = "";
    }
    setAccountPasswordStatus("");
    accountPasswordModal.hidden = false;
    document.body.style.overflow = "hidden";
    window.setTimeout(() => accountPasswordNew?.focus(), 30);
  };

  window.CAERPTheme = {
    apply: (theme) => applyTheme(theme, true),
    current: () => normalizeTheme(themeRoot?.dataset?.theme || readSavedTheme()),
  };

  const persistDesktopState = (collapsed) => {
    try {
      window.localStorage.setItem(desktopStorageKey, collapsed ? "1" : "0");
    } catch (error) {
      // Ignore storage failures and keep the in-memory state.
    }
  };

  const setDesktopCollapsed = (collapsed) => {
    if (!isDesktop()) return;
    document.body.classList.toggle("sidebar-collapsed", collapsed);
    persistDesktopState(collapsed);
    if (desktopToggle) {
      desktopToggle.textContent = collapsed ? "Expandir menu" : "Contraer menu";
      desktopToggle.setAttribute("aria-pressed", collapsed ? "true" : "false");
    }
  };

  const syncNavMode = () => {
    if (!toggle && !desktopToggle) return;
    if (isDesktop()) {
      closeNav();
      let storedCollapsed = false;
      try {
        storedCollapsed = window.localStorage.getItem(desktopStorageKey) === "1";
      } catch (error) {
        storedCollapsed = isCollapsed();
      }
      document.body.classList.remove("nav-open");
      setDesktopCollapsed(storedCollapsed);
      return;
    }

    document.body.classList.remove("sidebar-collapsed");
    if (desktopToggle) {
      desktopToggle.textContent = "Contraer menu";
      desktopToggle.setAttribute("aria-pressed", "false");
    }
  };

  const setNotificationBadge = (count) => {
    if (!notificationBadge) return;
    const safeCount = Number.isFinite(Number(count)) ? Math.max(0, Number(count)) : 0;
    if (safeCount > 0) {
      notificationBadge.hidden = false;
      notificationBadge.textContent = safeCount > 99 ? "99+" : String(safeCount);
      return;
    }
    notificationBadge.hidden = true;
    notificationBadge.textContent = "0";
  };

  const escapeHtml = (value) =>
    String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const loadReadNotificationIds = () => {
    try {
      const raw = window.localStorage.getItem(notificationReadStorageKey);
      const parsed = JSON.parse(raw || "[]");
      if (!Array.isArray(parsed)) return new Set();
      return new Set(parsed.map((item) => String(item || "").trim()).filter(Boolean));
    } catch (error) {
      return new Set();
    }
  };

  const saveReadNotificationIds = (values) => {
    try {
      window.localStorage.setItem(notificationReadStorageKey, JSON.stringify(Array.from(values || [])));
    } catch (error) {
      // Ignore storage issues and keep in-memory behavior only.
    }
  };

  const loadHiddenNotificationIds = () => {
    try {
      const raw = window.localStorage.getItem(notificationHiddenStorageKey);
      const parsed = JSON.parse(raw || "[]");
      if (!Array.isArray(parsed)) return new Set();
      return new Set(parsed.map((item) => String(item || "").trim()).filter(Boolean));
    } catch (error) {
      return new Set();
    }
  };

  const saveHiddenNotificationIds = (values) => {
    try {
      window.localStorage.setItem(notificationHiddenStorageKey, JSON.stringify(Array.from(values || [])));
    } catch (error) {
      // Ignore storage issues and keep in-memory behavior only.
    }
  };

  const loadDeliveredNotificationIds = () => {
    try {
      const raw = window.localStorage.getItem(notificationDeliveredStorageKey);
      const parsed = JSON.parse(raw || "[]");
      if (!Array.isArray(parsed)) return new Set();
      return new Set(parsed.map((item) => String(item || "").trim()).filter(Boolean));
    } catch (error) {
      return new Set();
    }
  };

  const saveDeliveredNotificationIds = (values) => {
    try {
      window.localStorage.setItem(notificationDeliveredStorageKey, JSON.stringify(Array.from(values || [])));
    } catch (error) {
      // Ignore storage issues and keep in-memory behavior only.
    }
  };

  const loadChatNotificationItems = () => {
    try {
      const raw = window.localStorage.getItem(chatNotificationItemsStorageKey);
      const parsed = JSON.parse(raw || "[]");
      if (!Array.isArray(parsed)) return [];
      return parsed.filter((item) => item && typeof item === "object");
    } catch (error) {
      return [];
    }
  };

  const saveChatNotificationItems = (items) => {
    try {
      window.localStorage.setItem(chatNotificationItemsStorageKey, JSON.stringify((items || []).slice(0, 50)));
    } catch (error) {
      // Ignore storage issues and keep in-memory behavior only.
    }
  };

  const parseNotificationSortTime = (item) => {
    const raw = String(item?.sort_timestamp || item?.created_at_iso || item?.creado_en || item?.created_at || "").trim();
    if (!raw) return 0;
    const direct = Date.parse(raw);
    if (Number.isFinite(direct)) return direct;
    const match = raw.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})(?:\s+(\d{1,2}):(\d{2})(?:\s*([AP]\.?M\.?))?)?/i);
    if (!match) return 0;
    let hour = Number(match[4] || 0);
    const minute = Number(match[5] || 0);
    const meridian = String(match[6] || "").replace(/\./g, "").toUpperCase();
    if (meridian === "PM" && hour < 12) hour += 12;
    if (meridian === "AM" && hour === 12) hour = 0;
    const parsed = new Date(Number(match[3]), Number(match[2]) - 1, Number(match[1]), hour, minute).getTime();
    return Number.isFinite(parsed) ? parsed : 0;
  };

  const mergeNotificationResults = (serverPayload) => {
    const payload = serverPayload && typeof serverPayload === "object" ? { ...serverPayload } : { allowed: false, count: 0, results: [] };
    const serverItems = Array.isArray(payload.results) ? payload.results : [];
    const localChatItems = loadChatNotificationItems();
    const combinedMap = new Map();
    [...localChatItems, ...serverItems].forEach((item) => {
      const key = getNotificationKey(item);
      if (!key) return;
      combinedMap.set(key, item);
    });
    const combined = Array.from(combinedMap.values()).sort((a, b) => {
      const timeDiff = parseNotificationSortTime(b) - parseNotificationSortTime(a);
      if (timeDiff) return timeDiff;
      const aId = Number(a?.id || 0);
      const bId = Number(b?.id || 0);
      if (Number.isFinite(aId) && Number.isFinite(bId) && aId !== bId) return bId - aId;
      return String(b?.id || "").localeCompare(String(a?.id || ""));
    });
    payload.allowed = Boolean(payload.allowed || localChatItems.length);
    payload.results = combined;
    payload.count = combined.length;
    return payload;
  };

  const getNotificationType = (item) => String(item?.notification_type || item?.type || "generic").trim() || "generic";
  const getNotificationKey = (item) => `${getNotificationType(item)}:${String(item?.id || "").trim()}`;
  const isServerManagedNotification = (item) => getNotificationType(item) !== "chat_message";
  const isNotificationHidden = (item) => {
    if (isServerManagedNotification(item)) return !!item?.is_hidden;
    return loadHiddenNotificationIds().has(getNotificationKey(item));
  };
  const hasNotificationBeenRead = (item) => {
    if (isServerManagedNotification(item)) return !!item?.is_read;
    return loadReadNotificationIds().has(getNotificationKey(item));
  };
  const hasNotificationBeenDelivered = (item) => {
    if (isServerManagedNotification(item)) return !!item?.is_delivered;
    return loadDeliveredNotificationIds().has(getNotificationKey(item));
  };

  const normalizeTerminalName = (value) =>
    String(value ?? "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 50);

  const getCurrentSharedTerminalName = () => {
    try {
      const stored = normalizeTerminalName(window.localStorage.getItem(sharedTerminalStorageKey) || "");
      if (stored) {
        return stored;
      }
      const existingSeed = normalizeTerminalName(window.localStorage.getItem(sharedTerminalSeedKey) || "");
      if (existingSeed) {
        return `Equipo-${existingSeed}`;
      }
      const generated = `EQ-${Math.random().toString(36).slice(2, 8)}`.toUpperCase();
      window.localStorage.setItem(sharedTerminalSeedKey, generated);
      return `Equipo-${generated}`;
    } catch (error) {
      return "";
    }
  };

  const buildNotificationTitle = (item) => {
    const itemType = getNotificationType(item);
    if (itemType === "chat_message") {
      const sender = String(item?.sender_name || item?.titulo || "Nuevo mensaje").trim();
      return sender ? `Mensaje de ${sender}` : "Nuevo mensaje";
    }
    if (itemType === "payment_agreement" || itemType === "agreement_payment_received") {
      return String(item?.titulo || "Acuerdo de pago").trim() || "Acuerdo de pago";
    }
    return String(item?.titulo || "Pedido de existencia").trim() || "Pedido de existencia";
  };

  const buildNotificationBody = (item) => {
    if (getNotificationType(item) === "chat_message") {
      const referencia = String(item?.referencia || "").trim();
      const resumen = String(item?.resumen || "").trim();
      return [referencia, resumen].filter(Boolean).join(" - ").slice(0, 240);
    }
    const cliente = String(item?.cliente || "").trim();
    const referencia = String(item?.referencia || "").trim();
    const resumen = String(item?.resumen || "").trim();
    return [cliente, referencia, resumen].filter(Boolean).join(" - ").slice(0, 240);
  };

  const playIncomingNotificationTone = () => {
    try {
      const AudioContextCtor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextCtor) return;
      const audioCtx = new AudioContextCtor();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();
      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(880, audioCtx.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(660, audioCtx.currentTime + 0.18);
      gainNode.gain.setValueAtTime(0.0001, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.065, audioCtx.currentTime + 0.02);
      gainNode.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.34);
      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);
      oscillator.start();
      oscillator.stop(audioCtx.currentTime + 0.36);
      oscillator.onended = () => {
        try {
          audioCtx.close();
        } catch (error) {
          // Ignore close failures.
        }
      };
    } catch (error) {
      // Browser blocked autoplay or WebAudio isn't available.
    }
  };

  const ensureNotificationToastHost = () => {
    if (notificationToastHost) {
      return notificationToastHost;
    }
    notificationToastHost = document.createElement("div");
    notificationToastHost.className = "ca-erp-toast-host";
    document.body.appendChild(notificationToastHost);
    return notificationToastHost;
  };

  const showNotificationToast = (item) => {
    const host = ensureNotificationToastHost();
    const toast = document.createElement("button");
    toast.type = "button";
    toast.className = "ca-erp-toast";
    const itemType = getNotificationType(item);
    const eyebrow = (itemType === "payment_agreement" || itemType === "agreement_payment_received")
      ? "Acuerdo"
      : (itemType === "chat_message" ? "Chat" : "Existencia");
    toast.innerHTML =
      `<span class="ca-erp-toast-eyebrow">${escapeHtml(eyebrow)}</span>` +
      `<strong>${escapeHtml(buildNotificationTitle(item))}</strong>` +
      `<span>${escapeHtml(buildNotificationBody(item) || "Nueva notificacion disponible.")}</span>`;
    toast.addEventListener("click", () => {
      const targetUrl = String(item?.url || "/").trim() || "/";
      window.location.href = targetUrl;
    });
    host.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("is-visible"));
    window.setTimeout(() => {
      toast.classList.remove("is-visible");
      window.setTimeout(() => {
        toast.remove();
        if (host && !host.childElementCount) {
          host.remove();
          notificationToastHost = null;
        }
      }, 260);
    }, 5200);
  };

  const notificationPermissionValue = () => {
    if (!("Notification" in window)) return "unsupported";
    return Notification.permission || "default";
  };

  const ensureNotificationPermission = async (options = {}) => {
    if (!("Notification" in window)) return "unsupported";
    if (Notification.permission === "granted" || Notification.permission === "denied") {
      return Notification.permission;
    }
    if (notificationPermissionAsked && !options.force) {
      return Notification.permission;
    }
    notificationPermissionAsked = true;
    try {
      return await Notification.requestPermission();
    } catch (error) {
      return Notification.permission || "default";
    }
  };

  const showSystemNotification = async (item) => {
    if (!item) return "";
    const title = buildNotificationTitle(item);
    const body = buildNotificationBody(item);
    const targetUrl = String(item?.url || "/").trim() || "/";
    const permission = await ensureNotificationPermission();
    playIncomingNotificationTone();
    try {
      if ("vibrate" in navigator) {
        navigator.vibrate([120, 60, 140]);
      }
    } catch (error) {
      // Ignore vibration failures.
    }
    if (permission !== "granted") {
      showNotificationToast(item);
      return "fallback";
    }
    try {
      const registration = await navigator.serviceWorker?.getRegistration?.();
      if (registration && typeof registration.showNotification === "function") {
        await registration.showNotification(title, {
          body,
          tag: getNotificationKey(item),
          renotify: true,
          requireInteraction: false,
          silent: false,
          vibrate: [120, 60, 140],
          data: { url: targetUrl },
        });
        return "native";
      }
    } catch (error) {
      // Fall back to Notification below.
    }
    try {
      const notice = new Notification(title, {
        body,
        tag: getNotificationKey(item),
        renotify: true,
        requireInteraction: false,
        silent: false,
        data: { url: targetUrl },
      });
      notice.onclick = () => {
        try {
          window.focus();
        } catch (error) {
          // Ignore focus failures.
        }
        window.location.href = targetUrl;
        notice.close();
      };
      return "native";
    } catch (error) {
      showNotificationToast(item);
      return "fallback";
    }
    return "";
  };

  const postNotificationState = async (url, payload) => {
    if (!url) return false;
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": notificationCsrfToken,
        },
        body: JSON.stringify(payload || {}),
        keepalive: true,
      });
      return res.ok;
    } catch (error) {
      return false;
    }
  };

  const markVisibleServerNotificationsRead = async (payload) => {
    const items = Array.isArray(payload?.results) ? payload.results : [];
    const unreadServerItems = items
      .filter((item) => isServerManagedNotification(item) && !isNotificationHidden(item) && !hasNotificationBeenRead(item))
      .map((item) => ({
        notification_type: getNotificationType(item),
        notification_id: String(item?.id || "").trim(),
      }))
      .filter((item) => item.notification_type && item.notification_id);
    if (!unreadServerItems.length || !notificationMarkReadBulkUrl) return;
    const ok = await postNotificationState(notificationMarkReadBulkUrl, { items: unreadServerItems });
    if (ok) {
      await fetchNotifications();
    }
  };

  const notifyForNewItems = async (payload) => {
    const allowed = Boolean(payload?.allowed);
    if (!allowed) return;
    const deliveredIds = loadDeliveredNotificationIds();
    const items = Array.isArray(payload?.results) ? payload.results : [];
    const unreadVisibleItems = items.filter((item) => !isNotificationHidden(item) && !hasNotificationBeenRead(item));
    const newItems = unreadVisibleItems.filter((item) => !hasNotificationBeenDelivered(item));
    if (!newItems.length) return;
    const deliveredServerItems = [];
    for (const item of newItems.slice(0, 3)) {
      const deliveryMode = await showSystemNotification(item);
      if (deliveryMode) {
        if (isServerManagedNotification(item)) {
          if (deliveryMode === "native") {
            deliveredServerItems.push({
              notification_type: getNotificationType(item),
              notification_id: String(item?.id || "").trim(),
            });
          }
        } else {
          deliveredIds.add(getNotificationKey(item));
        }
      }
    }
    if (deliveredIds.size) {
      saveDeliveredNotificationIds(deliveredIds);
    }
    if (deliveredServerItems.length && notificationDeliveredUrl) {
      void postNotificationState(notificationDeliveredUrl, { items: deliveredServerItems });
    }
  };

  const positionNotificationSurfaces = () => {
    if (!notificationShell || !notificationToggle) return;
    const rect = notificationToggle.getBoundingClientRect();
    const top = Math.max(8, Math.round(rect.bottom + 8));
    notificationShell.style.setProperty("--topbar-notification-menu-top", `${top}px`);
  };

  const renderNotificationItems = (items, allowed) => {
    if (!notificationList) return;
    if (!allowed) {
      notificationList.innerHTML = '<div class="topbar-notification-empty">Sin acceso a notificaciones.</div>';
      return;
    }
    if (!Array.isArray(items) || !items.length) {
      notificationList.innerHTML = '<div class="topbar-notification-empty">No hay notificaciones activas.</div>';
      return;
    }
    const visibleItems = items.filter((item) => !isNotificationHidden(item));
    if (!visibleItems.length) {
      notificationList.innerHTML = '<div class="topbar-notification-empty">No hay notificaciones activas.</div>';
      return;
    }
    notificationList.innerHTML = visibleItems.map((item) => {
      const cliente = String(item?.cliente || "").trim();
      const referencia = String(item?.referencia || "").trim();
      const resumen = String(item?.resumen || "").trim();
      const created = String(item?.creado_en || "").trim();
      const openUrl = String(item?.url || "").trim();
      const itemId = String(item?.id || "").trim();
      const itemType = getNotificationType(item);
      const itemKey = getNotificationKey(item);
      const deleteMode = String(item?.delete_mode || "server").trim().toLowerCase() || "server";
      const isRead = hasNotificationBeenRead(item);
      const typeLabel = (itemType === "payment_agreement" || itemType === "agreement_payment_received")
        ? "Acuerdos"
        : (itemType === "chat_message" ? "Chat" : "Existencia");
      return (
        `<div class="topbar-notification-item-wrap">` +
          `<button type="button" class="topbar-notification-item${isRead ? " is-read" : ""}" data-id="${escapeHtml(itemId)}" data-url="${escapeHtml(openUrl)}" data-key="${escapeHtml(itemKey)}" data-type="${escapeHtml(itemType)}" data-delete-mode="${escapeHtml(deleteMode)}" data-read="${isRead ? "1" : "0"}">` +
            `<div class="topbar-notification-kind">${escapeHtml(typeLabel)}</div>` +
            `<strong>${escapeHtml(item?.titulo || (itemType === "chat_message" ? "Nuevo mensaje" : "Pedido de existencia"))}</strong>` +
            `<div class="topbar-notification-meta">${escapeHtml(cliente || (itemType === "chat_message" ? String(item?.sender_name || "Sin remitente").trim() : "Sin cliente"))}</div>` +
            `<div class="topbar-notification-meta">${escapeHtml(referencia || (itemType === "chat_message" ? "Chat Interno" : "Desde facturacion"))}</div>` +
            `<div class="topbar-notification-summary">${escapeHtml(resumen || "Notificacion pendiente.")}</div>` +
            `<div class="topbar-notification-time">${escapeHtml(created || "")}${isRead ? " - Leida" : ""}</div>` +
          `</button>` +
          `<button type="button" class="topbar-notification-more" data-id="${escapeHtml(itemId)}" data-key="${escapeHtml(itemKey)}" data-type="${escapeHtml(itemType)}" data-delete-mode="${escapeHtml(deleteMode)}" aria-label="Acciones de notificacion">...</button>` +
        `</div>`
      );
    }).join("");
    Array.from(notificationList.querySelectorAll(".topbar-notification-item[data-url]")).forEach((button) => {
      button.addEventListener("click", () => {
        const url = String(button.getAttribute("data-url") || "").trim();
        const itemType = String(button.getAttribute("data-type") || "").trim();
        const itemId = String(button.getAttribute("data-id") || "").trim();
        const itemKey = String(button.getAttribute("data-key") || "").trim();
        const deleteMode = String(button.getAttribute("data-delete-mode") || "").trim().toLowerCase() || "server";
        if (deleteMode !== "server" && itemKey) {
          const readIds = loadReadNotificationIds();
          readIds.add(itemKey);
          saveReadNotificationIds(readIds);
        } else if (itemId) {
          const readUrl = buildNotificationActionUrl(notificationMarkReadTemplate, itemId);
          void postNotificationState(readUrl, { notification_type: itemType, notification_id: itemId });
        }
        if (!url) return;
        window.location.href = url;
      });
      button.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        const itemId = String(button.getAttribute("data-id") || "").trim();
        const itemKey = String(button.getAttribute("data-key") || "").trim();
        const itemType = String(button.getAttribute("data-type") || "").trim();
        const deleteMode = String(button.getAttribute("data-delete-mode") || "").trim();
        if (!itemId) return;
        openNotificationContext({ id: itemId, key: itemKey, type: itemType, deleteMode: deleteMode }, event.clientX, event.clientY);
      });
    });
    Array.from(notificationList.querySelectorAll(".topbar-notification-more[data-id]")).forEach((button) => {
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const itemId = String(button.getAttribute("data-id") || "").trim();
        const itemKey = String(button.getAttribute("data-key") || "").trim();
        const itemType = String(button.getAttribute("data-type") || "").trim();
        const deleteMode = String(button.getAttribute("data-delete-mode") || "").trim();
        if (!itemId) return;
        const rect = button.getBoundingClientRect();
        openNotificationContext({ id: itemId, key: itemKey, type: itemType, deleteMode: deleteMode }, rect.right - 8, rect.bottom + 8);
      });
    });
  };

  const closeNotificationContext = () => {
    if (!notificationContext) return;
    notificationContext.classList.remove("open");
    notificationContext.setAttribute("aria-hidden", "true");
    notificationContextItem = null;
  };

  const openNotificationContext = (itemMeta, x, y) => {
    if (!notificationContext) return;
    const safeId = String(itemMeta?.id || "").trim();
    if (!safeId) return;
    notificationContextItem = {
      id: safeId,
      key: String(itemMeta?.key || `${String(itemMeta?.type || "generic").trim()}:${safeId}`).trim(),
      type: String(itemMeta?.type || "generic").trim() || "generic",
      deleteMode: String(itemMeta?.deleteMode || "server").trim().toLowerCase() || "server",
    };
    if (notificationDelete) {
      notificationDelete.textContent = notificationContextItem.deleteMode === "server" ? "Eliminar" : "Ocultar";
    }
    notificationContext.classList.add("open");
    notificationContext.setAttribute("aria-hidden", "false");
    const menuWidth = notificationContext.offsetWidth || 184;
    const menuHeight = notificationContext.offsetHeight || 92;
    const maxLeft = Math.max(8, window.innerWidth - menuWidth - 8);
    const maxTop = Math.max(8, window.innerHeight - menuHeight - 8);
    notificationContext.style.left = `${Math.min(x, maxLeft)}px`;
    notificationContext.style.top = `${Math.min(y, maxTop)}px`;
  };

  const buildNotificationActionUrl = (template, itemId) => {
    const safeId = encodeURIComponent(String(itemId || "").trim());
    return String(template || "").replace(/\/0(?=\/|$)/, `/${safeId}`);
  };

  const performNotificationAction = async (action) => {
    const itemId = String(notificationContextItem?.id || "").trim();
    const itemKey = String(notificationContextItem?.key || "").trim();
    const itemType = String(notificationContextItem?.type || "").trim();
    const deleteMode = String(notificationContextItem?.deleteMode || "server").trim().toLowerCase() || "server";
    if (!itemId || !itemKey) return;
    if (action === "read") {
      if (deleteMode !== "server") {
        const readIds = loadReadNotificationIds();
        readIds.add(itemKey);
        saveReadNotificationIds(readIds);
      } else {
        const url = buildNotificationActionUrl(notificationMarkReadTemplate, itemId);
        await postNotificationState(url, { notification_type: itemType, notification_id: itemId });
        await fetchNotifications();
      }
      closeNotificationContext();
      updateNotificationSummary(latestNotificationsPayload);
      return;
    }
    if (deleteMode !== "server") {
      const hiddenIds = loadHiddenNotificationIds();
      hiddenIds.add(itemKey);
      saveHiddenNotificationIds(hiddenIds);
      const localChatItems = loadChatNotificationItems().filter((item) => getNotificationKey(item) !== itemKey);
      saveChatNotificationItems(localChatItems);
      closeNotificationContext();
      updateNotificationSummary(latestNotificationsPayload);
      return;
    }
    const template = action === "delete" ? notificationDeleteTemplate : notificationMarkReadTemplate;
    const url = buildNotificationActionUrl(template, itemId);
    if (!url) return;
    closeNotificationContext();
    try {
      const ok = await postNotificationState(url, { notification_type: itemType, notification_id: itemId });
      if (!ok) {
        return;
      }
      const readIds = loadReadNotificationIds();
      if (readIds.has(itemKey)) {
        readIds.delete(itemKey);
        saveReadNotificationIds(readIds);
      }
      const hiddenIds = loadHiddenNotificationIds();
      if (hiddenIds.has(itemKey)) {
        hiddenIds.delete(itemKey);
        saveHiddenNotificationIds(hiddenIds);
      }
      await fetchNotifications();
    } catch (error) {
      // Ignore fetch failures here and keep the current menu state.
    }
  };

  const updateNotificationSummary = (payload) => {
    latestNotificationsPayload = mergeNotificationResults(payload || { allowed: false, count: 0, results: [] });
    payload = latestNotificationsPayload;
    const allowed = Boolean(payload?.allowed);
    const visibleItems = (Array.isArray(payload?.results) ? payload.results : []).filter((item) => !isNotificationHidden(item));
    const unreadCount = allowed
      ? visibleItems.filter((item) => !hasNotificationBeenRead(item)).length
      : 0;
    if (notificationMenuCount) {
      notificationMenuCount.textContent = allowed ? `${unreadCount} sin leer` : "Sin acceso";
    }
    setNotificationBadge(allowed ? unreadCount : 0);
    renderNotificationItems(visibleItems, allowed);
  };

  const showCreatedStockRequestNotification = async (item) => {
    if (!stockRequestNotifyEnabled) {
      return;
    }
    if (!item || !item.id) {
      await fetchNotifications();
      return;
    }
    const deliveryMode = await showSystemNotification(item);
    if (deliveryMode === "native" && notificationDeliveredUrl && isServerManagedNotification(item)) {
      await postNotificationState(notificationDeliveredUrl, {
        items: [{
          notification_type: getNotificationType(item),
          notification_id: String(item?.id || "").trim(),
        }],
      });
    }
    await fetchNotifications();
  };

  const fetchNotifications = async () => {
    if (!notificationsUrl) return;
    try {
      const res = await fetch(notificationsUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        updateNotificationSummary({ allowed: false, count: 0, results: [] });
        return;
      }
      updateNotificationSummary(data || {});
      void notifyForNewItems(data || {});
    } catch (error) {
      updateNotificationSummary({ allowed: false, count: 0, results: [] });
    }
  };

  const startNotificationPolling = () => {
    if (!notificationsUrl || notificationPollHandle) return;
    notificationPollHandle = window.setInterval(() => {
      void fetchNotifications();
    }, 8000);
  };

  const stopNotificationPolling = () => {
    if (!notificationPollHandle) return;
    window.clearInterval(notificationPollHandle);
    notificationPollHandle = null;
  };

  const clearNotificationReconnect = () => {
    if (!notificationReconnectHandle) return;
    window.clearTimeout(notificationReconnectHandle);
    notificationReconnectHandle = null;
  };

  const resolveNotificationSocketUrl = () => {
    if (!notificationSocketUrl) return "";
    try {
      const target = new URL(notificationSocketUrl, window.location.origin);
      target.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return target.toString();
    } catch (error) {
      return "";
    }
  };

  const scheduleNotificationReconnect = () => {
    if (!notificationSocketUrl || notificationReconnectHandle) return;
    notificationReconnectHandle = window.setTimeout(() => {
      notificationReconnectHandle = null;
      connectNotificationSocket();
    }, 3000);
  };

  const connectNotificationSocket = () => {
    const socketTarget = resolveNotificationSocketUrl();
    if (!socketTarget || typeof window.WebSocket !== "function") {
      startNotificationPolling();
      return;
    }
    if (notificationSocket && (
      notificationSocket.readyState === window.WebSocket.OPEN
      || notificationSocket.readyState === window.WebSocket.CONNECTING
    )) {
      return;
    }
    try {
      notificationSocket = new window.WebSocket(socketTarget);
    } catch (error) {
      startNotificationPolling();
      scheduleNotificationReconnect();
      return;
    }
    notificationSocket.addEventListener("open", () => {
      notificationSocketConnected = true;
      clearNotificationReconnect();
      stopNotificationPolling();
      void fetchNotifications();
    });
    notificationSocket.addEventListener("message", (event) => {
      let data = null;
      try {
        data = JSON.parse(event.data || "{}");
      } catch (error) {
        data = null;
      }
      if (!data || !data.type) return;
      if (data.type === "notification.ready" || data.type === "notification.refresh") {
        void fetchNotifications();
      }
    });
    notificationSocket.addEventListener("close", () => {
      notificationSocketConnected = false;
      notificationSocket = null;
      startNotificationPolling();
      scheduleNotificationReconnect();
    });
    notificationSocket.addEventListener("error", () => {
      try {
        notificationSocket?.close();
      } catch (error) {
        // Ignore close failures after socket errors.
      }
    });
  };

  const buildChatMessagePreview = (payload) => {
    const message = payload?.message || {};
    const messageType = String(message?.message_type || "text").trim().toLowerCase();
    if (messageType === "voice_note") return "Nota de voz";
    if (messageType === "image_attachments") return "Imagen";
    if (messageType === "audio_attachments") return "Audio";
    if (messageType === "video_attachments") return "Video";
    if (messageType === "document_attachments") return "Documento";
    return String(message?.contenido || "").trim() || "Nuevo mensaje";
  };

  const showIncomingChatNotification = async (payload) => {
    const message = payload?.message || {};
    const room = payload?.room || {};
    const senderId = Number(message?.id_usuario || 0);
    const roomId = Number(room?.id_sala || message?.id_sala || 0);
    if (!roomId || (currentUserId > 0 && senderId === currentUserId)) {
      return;
    }
    const item = {
      notification_type: "chat_message",
      id: String(message?.id_mensaje || `${roomId}-${Date.now()}`),
      titulo: String(message?.usuario_nombre || "Nuevo mensaje").trim() || "Nuevo mensaje",
      cliente: String(message?.usuario_nombre || "").trim(),
      sender_name: String(message?.usuario_nombre || "Nuevo mensaje").trim(),
      referencia: String(room?.nombre || "Chat Interno").trim(),
      resumen: buildChatMessagePreview(payload),
      creado_en: new Date().toISOString().slice(0, 19).replace("T", " "),
      delete_mode: "local",
      url: `${chatIndexUrl || "/app/chat-interno/"}?room=${encodeURIComponent(String(roomId))}`,
    };
    const existing = loadChatNotificationItems().filter((entry) => getNotificationKey(entry) !== getNotificationKey(item));
    existing.unshift(item);
    saveChatNotificationItems(existing);
    updateNotificationSummary(latestNotificationsPayload);
    await showSystemNotification(item);
  };

  const resolveChatSocketUrl = () => {
    if (!chatSocketUrl) return "";
    try {
      const target = new URL(chatSocketUrl, window.location.origin);
      target.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return target.toString();
    } catch (error) {
      return "";
    }
  };

  const scheduleChatNotificationReconnect = () => {
    if (!chatSocketUrl || chatNotificationReconnectHandle) return;
    chatNotificationReconnectHandle = window.setTimeout(() => {
      chatNotificationReconnectHandle = null;
      connectChatNotificationSocket();
    }, 3000);
  };

  const clearChatNotificationReconnect = () => {
    if (!chatNotificationReconnectHandle) return;
    window.clearTimeout(chatNotificationReconnectHandle);
    chatNotificationReconnectHandle = null;
  };

  const resolveStockRequestSocketUrl = () => {
    if (!stockRequestSocketUrl) return "";
    try {
      const target = new URL(stockRequestSocketUrl, window.location.origin);
      target.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return target.toString();
    } catch (error) {
      return "";
    }
  };

  const scheduleStockRequestReconnect = () => {
    if (!stockRequestSocketUrl || stockRequestReconnectHandle) return;
    if (stockRequestReconnectHandle) return;
    stockRequestReconnectHandle = window.setTimeout(() => {
      stockRequestReconnectHandle = null;
      connectStockRequestSocket();
    }, 3000);
  };

  const clearStockRequestReconnect = () => {
    if (!stockRequestReconnectHandle) return;
    window.clearTimeout(stockRequestReconnectHandle);
    stockRequestReconnectHandle = null;
  };

  const connectStockRequestSocket = () => {
    if (!stockRequestNotifyEnabled) return;
    const socketTarget = resolveStockRequestSocketUrl();
    if (!socketTarget || typeof window.WebSocket !== "function") return;
    if (stockRequestSocket && (
      stockRequestSocket.readyState === window.WebSocket.OPEN
      || stockRequestSocket.readyState === window.WebSocket.CONNECTING
    )) {
      return;
    }
    try {
      stockRequestSocket = new window.WebSocket(socketTarget);
    } catch (error) {
      scheduleStockRequestReconnect();
      return;
    }
    stockRequestSocket.addEventListener("open", () => {
      stockRequestSocketConnected = true;
      clearStockRequestReconnect();
      void fetchNotifications();
    });
    stockRequestSocket.addEventListener("message", (event) => {
      let data = null;
      try {
        data = JSON.parse(event.data || "{}");
      } catch (error) {
        data = null;
      }
      if (!data || !data.type) return;
      if (data.type === "inventario.solicitudes.ready" || data.type === "inventario.solicitudes.refresh") {
        window.dispatchEvent(new CustomEvent("stock-requests-updated"));
      }
    });
    stockRequestSocket.addEventListener("close", () => {
      stockRequestSocketConnected = false;
      stockRequestSocket = null;
      scheduleStockRequestReconnect();
    });
    stockRequestSocket.addEventListener("error", () => {
      try {
        stockRequestSocket?.close();
      } catch (error) {
        // Ignore close failures after socket errors.
      }
    });
  };

  const connectChatNotificationSocket = () => {
    if (!chatEnabled || activeNav === "chat_interno") return;
    const socketTarget = resolveChatSocketUrl();
    if (!socketTarget || typeof window.WebSocket !== "function") return;
    if (chatNotificationSocket && (
      chatNotificationSocket.readyState === window.WebSocket.OPEN
      || chatNotificationSocket.readyState === window.WebSocket.CONNECTING
    )) {
      return;
    }
    try {
      chatNotificationSocket = new window.WebSocket(socketTarget);
    } catch (error) {
      scheduleChatNotificationReconnect();
      return;
    }
    chatNotificationSocket.addEventListener("open", () => {
      chatNotificationSocketConnected = true;
      clearChatNotificationReconnect();
    });
    chatNotificationSocket.addEventListener("message", (event) => {
      let data = null;
      try {
        data = JSON.parse(event.data || "{}");
      } catch (error) {
        data = null;
      }
      if (!data || data.type !== "chat.message") return;
      void showIncomingChatNotification(data);
    });
    chatNotificationSocket.addEventListener("close", () => {
      chatNotificationSocketConnected = false;
      chatNotificationSocket = null;
      scheduleChatNotificationReconnect();
    });
    chatNotificationSocket.addEventListener("error", () => {
      try {
        chatNotificationSocket?.close();
      } catch (error) {
        // Ignore close failures after socket errors.
      }
    });
  };

  const registerNotificationPermissionTriggers = () => {
    const trigger = () => {
      void ensureNotificationPermission();
      window.removeEventListener("pointerdown", trigger, true);
      window.removeEventListener("keydown", trigger, true);
      window.removeEventListener("touchstart", trigger, true);
    };
    window.addEventListener("pointerdown", trigger, true);
    window.addEventListener("keydown", trigger, true);
    window.addEventListener("touchstart", trigger, true);
  };

  const openNotifications = async () => {
    if (!notificationMenu || !notificationToggle) return;
    positionNotificationSurfaces();
    notificationsOpen = true;
    notificationMenu.classList.add("open");
    notificationMenu.setAttribute("aria-hidden", "false");
    notificationToggle.setAttribute("aria-expanded", "true");
    await fetchNotifications();
    await markVisibleServerNotificationsRead(latestNotificationsPayload);
  };

  const closeNotifications = () => {
    if (!notificationMenu || !notificationToggle) return;
    notificationsOpen = false;
    notificationMenu.classList.remove("open");
    notificationMenu.setAttribute("aria-hidden", "true");
    notificationToggle.setAttribute("aria-expanded", "false");
    closeNotificationContext();
  };

  toggle?.addEventListener("click", () => {
    if (document.body.classList.contains("nav-open")) {
      closeNav();
    } else {
      openNav();
    }
  });

  desktopToggle?.addEventListener("click", () => {
    setDesktopCollapsed(!isCollapsed());
  });

  overlay?.addEventListener("click", closeNav);
  window.addEventListener("resize", () => {
    syncNavMode();
    positionNotificationSurfaces();
  });
  window.addEventListener("scroll", () => {
    if (!notificationsOpen) return;
    positionNotificationSurfaces();
  }, true);
  applyTheme(readSavedTheme(), false);
  themeSelect?.addEventListener("change", () => {
    applyTheme(themeSelect.value, true);
  });
  accountProfileTrigger?.addEventListener("click", () => {
    openAccountPasswordModal();
  });
  accountPasswordClose?.addEventListener("click", () => {
    closeAccountPasswordModal();
  });
  accountPasswordCancel?.addEventListener("click", () => {
    closeAccountPasswordModal();
  });
  accountPasswordModal?.addEventListener("click", (event) => {
    if (event.target === accountPasswordModal) {
      closeAccountPasswordModal();
    }
  });
  accountPasswordForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const changeUrl = String(accountProfileTrigger?.dataset.changePasswordUrl || "").trim();
    const csrfToken = String(accountProfileTrigger?.dataset.csrfToken || "").trim();
    const passwordNueva = String(accountPasswordNew?.value || "");
    const passwordConfirm = String(accountPasswordConfirm?.value || "");
    if (!passwordNueva || !passwordConfirm) {
      setAccountPasswordStatus("Debes completar la nueva clave y la confirmacion.", "error");
      return;
    }
    accountPasswordSubmit?.setAttribute("disabled", "disabled");
    setAccountPasswordStatus("");
    try {
      const response = await fetch(changeUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({
          password_nueva: passwordNueva,
          password_confirm: passwordConfirm,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setAccountPasswordStatus(String(payload?.detail || "No se pudo cambiar la clave."), "error");
        return;
      }
      setAccountPasswordStatus("Clave actualizada correctamente.", "success");
      window.setTimeout(() => {
        closeAccountPasswordModal();
      }, 900);
    } catch (error) {
      setAccountPasswordStatus("No se pudo cambiar la clave.", "error");
    } finally {
      accountPasswordSubmit?.removeAttribute("disabled");
    }
  });
  syncNavMode();
  positionNotificationSurfaces();

  if (notificationToggle && notificationMenu) {
    registerNotificationPermissionTriggers();
    startNotificationPolling();
    connectNotificationSocket();
    connectChatNotificationSocket();
    connectStockRequestSocket();
    notificationToggle.addEventListener("click", async (event) => {
      event.stopPropagation();
      void ensureNotificationPermission();
      if (notificationsOpen) {
        closeNotifications();
        return;
      }
      await openNotifications();
    });
    document.addEventListener("click", (event) => {
      if (notificationContext?.contains(event.target)) return;
      if (!notificationsOpen || !notificationShell) return;
      if (notificationShell.contains(event.target)) return;
      closeNotifications();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && accountPasswordModal && !accountPasswordModal.hidden) {
        closeAccountPasswordModal();
        return;
      }
      if (event.key === "Escape" && notificationsOpen) {
        closeNotifications();
      }
    });
    document.addEventListener("scroll", closeNotificationContext, true);
    notificationMarkRead?.addEventListener("click", () => {
      void performNotificationAction("read");
    });
    notificationDelete?.addEventListener("click", () => {
      void performNotificationAction("delete");
    });
    window.addEventListener("stock-requests-updated", () => {
      void fetchNotifications();
    });
    window.addEventListener("stock-request-created", (event) => {
      void showCreatedStockRequestNotification(event?.detail?.notification || null);
    });
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) {
        if (!notificationSocketConnected) {
          connectNotificationSocket();
        }
        if (!chatNotificationSocketConnected) {
          connectChatNotificationSocket();
        }
        if (!stockRequestSocketConnected) {
          connectStockRequestSocket();
        }
        void fetchNotifications();
      }
    });
    navigator.serviceWorker?.addEventListener?.("message", (event) => {
      const data = event?.data || {};
      if (data?.type === "ca-erp-focus-url" && data?.url) {
        window.location.href = String(data.url);
      }
    });
    window.addEventListener("beforeunload", () => {
      clearNotificationReconnect();
      clearChatNotificationReconnect();
      clearStockRequestReconnect();
      try {
        notificationSocket?.close();
      } catch (error) {
        // Ignore shutdown close failures.
      }
      try {
        chatNotificationSocket?.close();
      } catch (error) {
        // Ignore shutdown close failures.
      }
      try {
        stockRequestSocket?.close();
      } catch (error) {
        // Ignore shutdown close failures.
      }
    });
    void fetchNotifications();
  }
})();


