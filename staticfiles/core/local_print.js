(function () {
  const TERMINAL_STORAGE_KEY = "prefacturas.caja.terminal_nombre";
  const TERMINAL_SEED_KEY = "prefacturas.caja.terminal_seed";
  const PREFS_CACHE_TTL_MS = 30000;
  let prefsCache = null;
  let prefsCacheTerminal = "";
  let prefsCacheLoadedAt = 0;
  let resolvedTerminalName = "";
  let terminalPromise = null;
  let qzConnectPromise = null;
  let qzSecurityConfigured = false;
  let warmupStarted = false;

  function normalizeTerminalName(value) {
    return String(value ?? "").replace(/\s+/g, " ").trim().slice(0, 100);
  }

  function getFallbackTerminalName() {
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
  }

  function getTerminalName() {
    return resolvedTerminalName || getFallbackTerminalName();
  }

  function ensureQzLoaded() {
    if (!window.qz) {
      throw new Error("No se cargo QZ Tray. Verifica que QZ Tray este instalado y que qz-tray.js este disponible.");
    }
    return window.qz;
  }

  function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (const cookie of cookies) {
      const trimmed = cookie.trim();
      if (trimmed.startsWith(`${name}=`)) {
        return decodeURIComponent(trimmed.slice(name.length + 1));
      }
    }
    return "";
  }

  function configureQzSecurity() {
    const qz = ensureQzLoaded();
    if (qzSecurityConfigured || !qz.security) return;
    if (typeof qz.security.setCertificatePromise === "function") {
      qz.security.setCertificatePromise((resolve, reject) => {
        fetch(window.CA_QZ_CERT_URL || "/app/qz/certificate/", {
          cache: "no-store",
          headers: { "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        })
          .then((response) => {
            if (!response.ok) throw new Error("No se pudo cargar el certificado de QZ Tray.");
            return response.text();
          })
          .then(resolve)
          .catch(reject);
      });
    }
    if (typeof qz.security.setSignaturePromise === "function") {
      if (typeof qz.security.setSignatureAlgorithm === "function") {
        qz.security.setSignatureAlgorithm("SHA512");
      }
      qz.security.setSignaturePromise((toSign) => (resolve, reject) => {
        fetch(window.CA_QZ_SIGN_URL || "/app/qz/sign/", {
          method: "POST",
          cache: "no-store",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCookie("csrftoken") || window.CA_CSRF_TOKEN || "",
          },
          body: JSON.stringify({ request: toSign }),
        })
          .then((response) => {
            if (!response.ok) throw new Error("No se pudo firmar la solicitud de QZ Tray.");
            return response.text();
          })
          .then(resolve)
          .catch(reject);
      });
    }
    qzSecurityConfigured = true;
  }

  async function connectQz() {
    const qz = ensureQzLoaded();
    configureQzSecurity();
    if (qz.websocket?.isActive?.()) return qz;
    if (!qzConnectPromise) {
      qzConnectPromise = qz.websocket.connect({ retries: 2, delay: 1 })
        .then(() => qz)
        .finally(() => {
          qzConnectPromise = null;
        });
    }
    return qzConnectPromise;
  }

  async function resolveTerminalName(force = false) {
    if (!force && resolvedTerminalName) return resolvedTerminalName;
    if (!force && terminalPromise) return terminalPromise;
    terminalPromise = Promise.resolve(getFallbackTerminalName()).then((terminal) => {
      resolvedTerminalName = terminal;
      try {
        window.localStorage.setItem(TERMINAL_STORAGE_KEY, terminal);
      } catch (error) {
        // LocalStorage may be unavailable in restricted browser profiles.
      }
      return resolvedTerminalName;
    });
    try {
      return await terminalPromise;
    } finally {
      terminalPromise = null;
    }
  }

  async function getPreferences(force = false) {
    const terminal = await resolveTerminalName();
    const cacheIsFresh = Date.now() - prefsCacheLoadedAt < PREFS_CACHE_TTL_MS;
    if (!force && prefsCache && prefsCacheTerminal === terminal && cacheIsFresh) {
      return prefsCache;
    }
    const url = window.CA_PRINT_PREFS_URL || "/app/ajustes/parametros/impresoras/preferencias/";
    const response = await fetch(`${url}?terminal=${encodeURIComponent(terminal)}`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });
    if (!response.ok) throw new Error("No se pudo cargar la preferencia de impresora.");
    const data = await response.json();
    prefsCache = data.preferencias || {};
    prefsCacheTerminal = terminal;
    prefsCacheLoadedAt = Date.now();
    return prefsCache;
  }

  async function getPreferredPrinter(tipoDocumento) {
    const prefs = await getPreferences(false);
    const pref = prefs[String(tipoDocumento || "")] || {};
    return String(pref.nombre_impresora || "").trim();
  }

  async function getPrintTarget(tipoDocumento) {
    const printer = await getPreferredPrinter(tipoDocumento);
    return {
      printer,
      hasPrinter: Boolean(printer),
      label: printer
        ? "Impresora QZ Tray seleccionada: " + printer
        : "Dialogo del navegador (selecciona la impresora al imprimir)",
    };
  }

  async function isAgentAvailable() {
    try {
      await connectQz();
      return true;
    } catch (error) {
      console.warn("No se pudo conectar con QZ Tray.", error);
      return false;
    }
  }

  async function getAgentUrl() {
    await connectQz();
    return "qz-tray";
  }

  async function getLocalPrinters() {
    const qz = await connectQz();
    const printers = await qz.printers.find();
    let defaultPrinter = "";
    try {
      defaultPrinter = String(await qz.printers.getDefault() || "").trim();
    } catch (error) {
      defaultPrinter = "";
    }
    return (Array.isArray(printers) ? printers : [])
      .map((name) => String(name || "").trim())
      .filter(Boolean)
      .map((name) => ({
        nombre: name,
        es_predeterminada: defaultPrinter ? name === defaultPrinter : false,
      }));
  }

  function prepareHtmlForQz(tipoDocumento, html) {
    const htmlText = String(html || "");
    if (String(tipoDocumento || "").trim() !== "factura" || !htmlText) return htmlText;
    try {
      const doc = new DOMParser().parseFromString(htmlText, "text/html");
      doc.querySelectorAll(".toolbar").forEach((node) => node.remove());
      const style = doc.createElement("style");
      style.textContent = `
        @media screen, print {
          * {
            box-shadow: none !important;
            text-shadow: none !important;
          }
          body {
            background: #fff !important;
            color: #000 !important;
          }
          .page {
            margin: 0 !important;
            border: 0 !important;
          }
          .doc-box,
          .section,
          .notes,
          .totals-box,
          .legal-note {
            border-radius: 0 !important;
            background: #fff !important;
          }
          .section-head,
          th,
          .totals-box .grand td {
            background: #fff !important;
            color: #000 !important;
          }
        }
      `;
      (doc.head || doc.documentElement).appendChild(style);
      return "<!doctype html>\n" + doc.documentElement.outerHTML;
    } catch (error) {
      return htmlText;
    }
  }

  async function printHtml(tipoDocumento, html, options) {
    const printer = await getPreferredPrinter(tipoDocumento);
    if (!printer) return false;
    const qz = await connectQz();
    const htmlText = prepareHtmlForQz(tipoDocumento, html);
    const lowerHtml = htmlText.toLowerCase();
    const is58mm = lowerHtml.includes("print-format-58mm") || lowerHtml.includes("size: 58mm");
    const is80mm = lowerHtml.includes("print-format-80mm") || lowerHtml.includes("size: 80mm");
    const printOptions = {
      jobName: options?.title || document.title || "CA ERP",
      units: "mm",
      margins: 0,
      scaleContent: false,
      colorType: "blackwhite",
      interpolation: "nearest-neighbor",
    };
    if (is58mm) {
      printOptions.size = { width: 58, height: 297, custom: true };
    } else if (is80mm) {
      printOptions.size = { width: 80, height: 297, custom: true };
    } else {
      printOptions.size = { width: 210, height: 297 };
      printOptions.orientation = "portrait";
    }
    const config = qz.configs.create(printer, printOptions);
    const data = [{
      type: "pixel",
      format: "html",
      flavor: "plain",
      data: htmlText,
    }];
    await qz.print(config, data);
    return true;
  }

  function warmup() {
    if (warmupStarted) return;
    warmupStarted = true;
    Promise.resolve()
      .then(() => resolveTerminalName())
      .then(() => getPreferences(false))
      .then(() => connectQz())
      .catch((error) => {
        console.warn("No se pudo preparar QZ Tray antes de imprimir.", error);
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(warmup, 300), { once: true });
  } else {
    setTimeout(warmup, 300);
  }

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
    warmup,
  };
})();
