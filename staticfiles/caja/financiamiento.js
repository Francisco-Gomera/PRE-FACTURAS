(function () {
  var config = window.financiamientoConfig || {};
  var finPanel = document.getElementById("fin_panel");
  var tabButtons = Array.prototype.slice.call(document.querySelectorAll(".financ-tab"));
  var tabPanels = Array.prototype.slice.call(document.querySelectorAll(".financ-tab-panel"));

  var fieldNoFactura = document.getElementById("fin_no_factura");
  var fieldNo = document.getElementById("fin_no");
  var fieldEstado = document.getElementById("fin_estado");
  var fieldFecha = document.getElementById("fin_fecha");
  var fieldTipo = document.getElementById("fin_tipo");
  var fieldCodigo = document.getElementById("fin_codigo");
  var fieldNombre = document.getElementById("fin_nombre");
  var fieldCedula = document.getElementById("fin_cedula");
  var fieldMoneda = document.getElementById("fin_moneda");
  var fieldTasa = document.getElementById("fin_tasa");
  var fieldMonto = document.getElementById("fin_monto");
  var fieldPorcInteres = document.getElementById("fin_porc_interes");
  var fieldPlazo = document.getElementById("fin_plazo");
  var fieldMetodo = document.getElementById("fin_metodo");
  var fieldTipoCuota = document.getElementById("fin_tipo_cuota");
  var fieldFechaBase = document.getElementById("fin_fecha_base");
  var fieldTotalPagado = document.getElementById("fin_total_pagado");
  var fieldValorCuota = document.getElementById("fin_valor_cuota");
  var fieldComentario = document.getElementById("fin_comentario");

  var detalleBody = document.getElementById("fin_detalle_body");
  var historialBody = document.getElementById("fin_historial_body");

  var capitalTotal = document.getElementById("fin_capital_total");
  var interesTotal = document.getElementById("fin_interes_total");
  var cuotaTotal = document.getElementById("fin_cuota_total");
  var pagadoTotal = document.getElementById("fin_pagado_total");
  var pendienteTotal = document.getElementById("fin_pendiente_total");

  var btnNuevo = document.getElementById("btn_fin_nuevo");
  var btnBuscar = document.getElementById("btn_fin_buscar");
  var btnOpenSearchTop = document.getElementById("btn_fin_open_search_top");
  var btnCancel = document.getElementById("btn_fin_cancel");
  var btnGrabar = document.getElementById("btn_fin_grabar");
  var btnPrint = document.getElementById("btn_fin_print");
  var btnCerrar = document.getElementById("btn_fin_cerrar");
  var btnShortcutCxc = document.getElementById("btn_fin_shortcut_cxc");
  var btnShortcutFactura = document.getElementById("btn_fin_shortcut_factura");
  var btnShortcutPrefactura = document.getElementById("btn_fin_shortcut_prefactura");

  var searchBackdrop = document.getElementById("fin_search_backdrop");
  var btnCloseSearch = document.getElementById("btn_close_fin_search");
  var fieldSearchQ = document.getElementById("fin_search_q");
  var fieldSearchFiltro = document.getElementById("fin_search_filtro");
  var btnSearchExec = document.getElementById("btn_fin_search_exec");
  var searchBody = document.getElementById("fin_search_body");

  var facturaBackdrop = document.getElementById("fin_factura_backdrop");
  var btnCloseFactura = document.getElementById("btn_close_fin_factura");
  var fieldFacturaQ = document.getElementById("fin_factura_q");
  var fieldFacturaFiltro = document.getElementById("fin_factura_filtro");
  var btnFacturaExec = document.getElementById("btn_fin_factura_exec");
  var facturaBody = document.getElementById("fin_factura_body");

  var printBackdrop = document.getElementById("fin_print_backdrop");
  var btnClosePrint = document.getElementById("btn_close_fin_print");
  var fieldPrintCopies = document.getElementById("fin_print_copies");
  var printDocumento = document.getElementById("fin_print_documento");
  var printTotalHojas = document.getElementById("fin_print_total_hojas");
  var printTotalCopias = document.getElementById("fin_print_total_copias");
  var printPrinter = document.getElementById("fin_print_printer");
  var btnPrintCancel = document.getElementById("btn_fin_print_cancel");
  var btnPrintConfirm = document.getElementById("btn_fin_print_confirm");

  var alertBackdrop = document.getElementById("fin_alert_backdrop");
  var alertMessage = document.getElementById("fin_alert_message");
  var btnAlertClose = document.getElementById("btn_fin_alert_close");
  var btnAlertOk = document.getElementById("btn_fin_alert_ok");

  var searchTimer = null;
  var facturaSearchTimer = null;
  var currentNoDoc = "";
  var currentFacturaBase = null;
  var isCreatingNew = false;
  var agreementDatesByCuota = {};
  var finPrintPendingDoc = "";
  var financSocket = null;
  var financSocketConnected = false;
  var financSocketReconnectTimer = null;
  var pendingLocalFinEventId = "";
  var lastFinEventKey = "";
  var recentLocalFinDocs = new Map();
  var recentLocalFinFacturas = new Map();
  var LOCAL_FIN_EVENT_TTL_MS = 12000;

  function fallback(value, defaultValue) {
    return value == null ? defaultValue : value;
  }

  function pruneRecentLocalFinEvents() {
    var now = Date.now();
    [recentLocalFinDocs, recentLocalFinFacturas].forEach(function (targetMap) {
      Array.from(targetMap.entries()).forEach(function (entry) {
        if (!entry[1] || entry[1] <= now) {
          targetMap.delete(entry[0]);
        }
      });
    });
  }

  function rememberRecentLocalFinDoc(docId) {
    var normalizedDoc = String(docId || "").trim();
    if (!normalizedDoc) {
      return;
    }
    pruneRecentLocalFinEvents();
    recentLocalFinDocs.set(normalizedDoc, Date.now() + LOCAL_FIN_EVENT_TTL_MS);
  }

  function rememberRecentLocalFinFactura(facturaNo) {
    var normalizedFactura = String(facturaNo || "").trim();
    if (!normalizedFactura) {
      return;
    }
    pruneRecentLocalFinEvents();
    recentLocalFinFacturas.set(normalizedFactura, Date.now() + LOCAL_FIN_EVENT_TTL_MS);
  }

  function shouldIgnoreRecentLocalFinDoc(docId) {
    var normalizedDoc = String(docId || "").trim();
    if (!normalizedDoc) {
      return false;
    }
    pruneRecentLocalFinEvents();
    return recentLocalFinDocs.has(normalizedDoc);
  }

  function shouldIgnoreRecentLocalFinFactura(facturaNo) {
    var normalizedFactura = String(facturaNo || "").trim();
    if (!normalizedFactura) {
      return false;
    }
    pruneRecentLocalFinEvents();
    return recentLocalFinFacturas.has(normalizedFactura);
  }

  function escapeHtml(value) {
    return String(fallback(value, ""))
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function toNumber(value) {
    var amount = Number(String(fallback(value, "0")).replace(/,/g, "").trim());
    return Number.isFinite(amount) ? amount : 0;
  }

  function fmtMoney(value, digits) {
    var amount = toNumber(value);
    var decimals = typeof digits === "number" ? digits : 2;
    return amount.toLocaleString("en-US", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function fmtRate(value) {
    return fmtMoney(value, 4);
  }

  function normalizePrintCopies(value) {
    var numericValue = Math.round(toNumber(value || 2));
    if (!Number.isFinite(numericValue) || numericValue <= 0) {
      return 2;
    }
    return Math.max(1, Math.min(20, numericValue));
  }

  function buildImageSrc(base64Value, imageType) {
    var normalizedValue = String(base64Value || "").trim();
    if (!normalizedValue) {
      return "";
    }
    var normalizedType = String(imageType || "").trim().toLowerCase();
    if (normalizedType.indexOf("image/") === 0) {
      return "data:" + normalizedType + ";base64," + normalizedValue;
    }
    if (normalizedType) {
      return "data:image/" + normalizedType + ";base64," + normalizedValue;
    }
    return "data:image/png;base64," + normalizedValue;
  }

  function setFieldValue(field, value, formatter) {
    if (!field) {
      return;
    }
    if (field.type === "number") {
      if (value == null || value === "") {
        field.value = "";
        return;
      }
      field.value = String(value);
      return;
    }
    if (typeof formatter === "function") {
      field.value = formatter(value);
      return;
    }
    field.value = String(fallback(value, ""));
  }

  function normalizeChoice(value, allowed, fallbackValue) {
    var text = String(fallback(value, "")).trim().toLowerCase();
    for (var idx = 0; idx < allowed.length; idx += 1) {
      if (String(allowed[idx]).toLowerCase() === text) {
        return allowed[idx];
      }
    }
    return fallbackValue;
  }

  function setActionVisualState(mode) {
    if (!finPanel) {
      return;
    }
    finPanel.classList.remove("fin-state-idle", "fin-state-editing", "fin-state-viewing");
    var normalizedMode = ["editing", "viewing"].indexOf(mode) >= 0 ? mode : "idle";
    finPanel.classList.add("fin-state-" + normalizedMode);
  }

  function syncActionButtons(modeOverride) {
    var hasSavedRecord = !!String(currentNoDoc || "").trim();
    var mode = modeOverride || (isCreatingNew ? "editing" : (hasSavedRecord ? "viewing" : "idle"));
    setActionVisualState(mode);
    if (btnNuevo) {
      btnNuevo.disabled = mode === "editing";
    }
    if (btnBuscar) {
      btnBuscar.disabled = mode === "editing";
    }
    if (btnCancel) {
      btnCancel.disabled = mode === "idle";
    }
    if (btnGrabar) {
      btnGrabar.disabled = mode !== "editing";
    }
    if (btnPrint) {
      btnPrint.disabled = !hasSavedRecord;
    }
    if (btnCerrar) {
      btnCerrar.disabled = false;
    }
  }

  function setCreateMode(enabled) {
    isCreatingNew = !!enabled;
    [fieldPorcInteres, fieldPlazo, fieldMetodo, fieldTipoCuota, fieldFechaBase].forEach(function (field) {
      if (field) {
        field.disabled = !enabled;
      }
    });
  }

  function clampNumberField(field, minValue, maxValue, fallbackValue, decimals) {
    if (!field) {
      return;
    }
    var rawValue = String(field.value || "").trim();
    if (!rawValue) {
      field.value = fallbackValue == null ? "" : String(fallbackValue);
      return;
    }
    var numericValue = Number(rawValue);
    if (!Number.isFinite(numericValue)) {
      field.value = fallbackValue == null ? "" : String(fallbackValue);
      return;
    }
    numericValue = Math.max(minValue, Math.min(maxValue, numericValue));
    if (typeof decimals === "number") {
      field.value = numericValue.toFixed(decimals);
      return;
    }
    field.value = String(Math.round(numericValue));
  }

  function roundMoney(value) {
    return Math.round((toNumber(value) + Number.EPSILON) * 100) / 100;
  }

  function parseInputDate(value) {
    var text = String(fallback(value, "")).trim();
    if (!text) {
      return null;
    }
    var parts = text.split("-");
    if (parts.length !== 3) {
      return null;
    }
    var year = Number(parts[0]);
    var month = Number(parts[1]);
    var day = Number(parts[2]);
    if (!Number.isFinite(year) || !Number.isFinite(month) || !Number.isFinite(day)) {
      return null;
    }
    return new Date(year, month - 1, day);
  }

  function formatDateDisplay(dateValue) {
    if (!(dateValue instanceof Date) || Number.isNaN(dateValue.getTime())) {
      return "";
    }
    var day = String(dateValue.getDate()).padStart(2, "0");
    var month = String(dateValue.getMonth() + 1).padStart(2, "0");
    var year = String(dateValue.getFullYear());
    return day + "/" + month + "/" + year;
  }

  function toDateInputValue(value) {
    if (!value) {
      return "";
    }
    if (value instanceof Date && !Number.isNaN(value.getTime())) {
      return [
        String(value.getFullYear()),
        String(value.getMonth() + 1).padStart(2, "0"),
        String(value.getDate()).padStart(2, "0"),
      ].join("-");
    }
    var text = String(value).trim();
    if (!text) {
      return "";
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(text)) {
      return text;
    }
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(text)) {
      return text.slice(6, 10) + "-" + text.slice(3, 5) + "-" + text.slice(0, 2);
    }
    return "";
  }

  function formatLongSpanishDate(value) {
    var parsed = parseInputDate(value);
    if (!parsed || Number.isNaN(parsed.getTime())) {
      return formatDateDisplay(parsed);
    }
    try {
      return new Intl.DateTimeFormat("es-DO", {
        year: "numeric",
        month: "long",
        day: "numeric",
      }).format(parsed);
    } catch (error) {
      return formatDateDisplay(parsed);
    }
  }

  function addDays(dateValue, daysToAdd) {
    var nextDate = new Date(dateValue.getFullYear(), dateValue.getMonth(), dateValue.getDate());
    nextDate.setDate(nextDate.getDate() + daysToAdd);
    return nextDate;
  }

  function addMonths(dateValue, monthsToAdd) {
    var year = dateValue.getFullYear();
    var month = dateValue.getMonth() + monthsToAdd;
    var day = dateValue.getDate();
    var lastDay = new Date(year, month + 1, 0).getDate();
    return new Date(year, month, Math.min(day, lastDay));
  }

  function resolveDueDate(baseDate, tipoCuota, cuotaIndex) {
    if (!(baseDate instanceof Date) || Number.isNaN(baseDate.getTime())) {
      return "";
    }
    var index = Math.max(Number(cuotaIndex) || 1, 1);
    var tipo = String(fallback(tipoCuota, "Mensual")).trim().toLowerCase();
    if (tipo === "quincenal") {
      return formatDateDisplay(addDays(baseDate, 15 * index));
    }
    if (tipo === "semanal") {
      return formatDateDisplay(addDays(baseDate, 7 * index));
    }
    if (tipo === "diario") {
      return formatDateDisplay(addDays(baseDate, index));
    }
    if (tipo === "acuerdo") {
      return formatDateDisplay(baseDate);
    }
    return formatDateDisplay(addMonths(baseDate, index));
  }

  function buildLinealSchedule(amount, ratePct, plazo, baseDate, tipoCuota) {
    var rows = [];
    var principalRemaining = roundMoney(amount);
    var capitalBase = plazo > 0 ? amount / plazo : 0;
    var interesBase = roundMoney(amount * (ratePct / 100));
    for (var idx = 1; idx <= plazo; idx += 1) {
      var capital = idx === plazo ? roundMoney(principalRemaining) : roundMoney(capitalBase);
      if (capital > principalRemaining) {
        capital = roundMoney(principalRemaining);
      }
      var interes = interesBase;
      var cuota = roundMoney(capital + interes);
      principalRemaining = roundMoney(Math.max(principalRemaining - capital, 0));
      rows.push(
        {
          no_cuota: String(idx),
          fecha_venc: resolveDueDate(baseDate, tipoCuota, idx),
          monto_interes: interes,
          capital: capital,
          balance: principalRemaining,
          cuota: cuota,
          pagado: 0,
          pendiente: cuota,
        }
      );
    }
    return rows;
  }

  function buildInsolutoSchedule(amount, ratePct, plazo, baseDate, tipoCuota) {
    if (ratePct <= 0) {
      return buildLinealSchedule(amount, 0, plazo, baseDate, tipoCuota);
    }
    var rows = [];
    var principalRemaining = roundMoney(amount);
    var periodicRate = ratePct / 100;
    var cuotaBase = amount * periodicRate / (1 - Math.pow(1 + periodicRate, -plazo));
    var cuotaConstante = roundMoney(cuotaBase);
    for (var idx = 1; idx <= plazo; idx += 1) {
      var interes = roundMoney(principalRemaining * periodicRate);
      var capital = roundMoney(cuotaConstante - interes);
      var cuota = cuotaConstante;
      if (idx === plazo) {
        capital = roundMoney(principalRemaining);
        cuota = roundMoney(capital + interes);
      } else if (capital > principalRemaining) {
        capital = roundMoney(principalRemaining);
        cuota = roundMoney(capital + interes);
      }
      principalRemaining = roundMoney(Math.max(principalRemaining - capital, 0));
      rows.push(
        {
          no_cuota: String(idx),
          fecha_venc: resolveDueDate(baseDate, tipoCuota, idx),
          monto_interes: interes,
          capital: capital,
          balance: principalRemaining,
          cuota: cuota,
          pagado: 0,
          pendiente: cuota,
        }
      );
    }
    return rows;
  }

  function refreshPreviewSchedule() {
    if (!isCreatingNew || (!currentFacturaBase && !currentNoDoc)) {
      return;
    }

    clampNumberField(fieldPorcInteres, 0, 100, 0, 2);
    clampNumberField(fieldPlazo, 1, 36, 1);

    var amount = roundMoney(toNumber(fieldMonto ? fieldMonto.value : 0));
    var ratePct = Math.max(0, Math.min(100, toNumber(fieldPorcInteres ? fieldPorcInteres.value : 0)));
    var plazo = Math.max(1, Math.min(36, Math.round(toNumber(fieldPlazo ? fieldPlazo.value : 1))));
    var metodo = normalizeChoice(fieldMetodo ? fieldMetodo.value : "Lineal", ["Lineal", "Insoluto"], "Lineal");
    var tipoCuota = normalizeChoice(
      fieldTipoCuota ? fieldTipoCuota.value : "Mensual",
      ["Mensual", "Quincenal", "Semanal", "Diario", "Acuerdo"],
      "Mensual"
    );
    var baseDate = parseInputDate(fieldFechaBase ? fieldFechaBase.value : "");

    setFieldValue(fieldPlazo, plazo);
    setFieldValue(fieldMetodo, metodo);
    setFieldValue(fieldTipoCuota, tipoCuota);

    if (amount <= 0.01) {
      setFieldValue(fieldValorCuota, 0, fmtMoney);
      setFieldValue(fieldTotalPagado, 0, fmtMoney);
      setEmptyRow(detalleBody, 8, "La factura seleccionada no tiene saldo disponible para financiar.");
      renderFinanzas({});
      return;
    }

    var rows = metodo === "Insoluto"
      ? buildInsolutoSchedule(amount, ratePct, plazo, baseDate, tipoCuota)
      : buildLinealSchedule(amount, ratePct, plazo, baseDate, tipoCuota);

    if (tipoCuota === "Acuerdo") {
      rows.forEach(function (row) {
        var savedDate = agreementDatesByCuota[row.no_cuota];
        if (savedDate) {
          row.fecha_venc = formatDateDisplay(parseInputDate(savedDate));
        }
      });
    }

    var capitalSum = 0;
    var interesSum = 0;
    var cuotaSum = 0;
    rows.forEach(function (row) {
      capitalSum += toNumber(row.capital);
      interesSum += toNumber(row.monto_interes);
      cuotaSum += toNumber(row.cuota);
    });

    renderDetalleRows(rows);
    renderFinanzas(
      {
        capital_total: roundMoney(capitalSum),
        interes_total: roundMoney(interesSum),
        cuota_total: roundMoney(cuotaSum),
        pagado_total: 0,
        pendiente_total: roundMoney(cuotaSum),
      }
    );
    setFieldValorCuotaFromRows(rows);
    setFieldValue(fieldTotalPagado, 0, fmtMoney);
    setEmptyRow(historialBody, 5, "Sin movimientos aplicados.");
  }

  function setFieldValorCuotaFromRows(rows) {
    var firstRow = rows && rows.length ? rows[0] : null;
    setFieldValue(fieldValorCuota, firstRow ? firstRow.cuota : 0, fmtMoney);
  }

  function activateTab(targetId) {
    tabButtons.forEach(function (button) {
      button.classList.toggle("active", button.getAttribute("data-target") === targetId);
    });
    tabPanels.forEach(function (panel) {
      panel.classList.toggle("active", panel.id === targetId);
    });
  }

  function lockScroll() {
    document.body.style.overflow = "hidden";
  }

  function unlockScroll() {
    var keepLocked = false;
    [searchBackdrop, facturaBackdrop, printBackdrop, alertBackdrop].forEach(function (node) {
      if (node && node.classList.contains("open")) {
        keepLocked = true;
      }
    });
    document.body.style.overflow = keepLocked ? "hidden" : "";
  }

  function syncPrintModalSummary() {
    var copies = normalizePrintCopies(fieldPrintCopies ? fieldPrintCopies.value : 2);
    if (fieldPrintCopies) {
      fieldPrintCopies.value = String(copies);
    }
    if (printDocumento) {
      printDocumento.textContent = finPrintPendingDoc || currentNoDoc || "-";
    }
    if (printTotalHojas) {
      printTotalHojas.textContent = String(copies);
    }
    if (printTotalCopias) {
      printTotalCopias.textContent = String(copies);
    }
  }

  async function syncPrintModalPrinter() {
    if (!printPrinter) return;
    printPrinter.textContent = "Verificando...";
    try {
      if (window.CALocalPrint && typeof window.CALocalPrint.getPrintTarget === "function") {
        var target = await window.CALocalPrint.getPrintTarget("financiamiento");
        printPrinter.textContent = target.label || "Dialogo del navegador (selecciona la impresora al imprimir)";
        return;
      }
    } catch (error) {
      /* keep browser dialog fallback visible */
    }
    printPrinter.textContent = "Dialogo del navegador (selecciona la impresora al imprimir)";
  }

  function openPrintModal() {
    if (!currentNoDoc) {
      showAlert("Carga un financiamiento antes de imprimir.");
      return;
    }
    if (!printBackdrop) {
      void openFinanciamientoPrint(2);
      return;
    }
    finPrintPendingDoc = String(fieldNo && fieldNo.value ? fieldNo.value : currentNoDoc).trim();
    if (fieldPrintCopies) {
      fieldPrintCopies.value = "2";
    }
    syncPrintModalSummary();
    void syncPrintModalPrinter();
    printBackdrop.classList.add("open");
    printBackdrop.setAttribute("aria-hidden", "false");
    lockScroll();
    if (fieldPrintCopies) {
      fieldPrintCopies.focus();
      fieldPrintCopies.select();
    }
  }

  function closePrintModal() {
    if (!printBackdrop) {
      return;
    }
    if (document.activeElement && printBackdrop.contains(document.activeElement) && btnPrint) {
      btnPrint.focus();
    }
    printBackdrop.classList.remove("open");
    printBackdrop.setAttribute("aria-hidden", "true");
    finPrintPendingDoc = "";
    unlockScroll();
  }

  function showAlert(message) {
    if (!alertBackdrop || !alertMessage) {
      window.alert(String(fallback(message, "")));
      return;
    }
    alertMessage.textContent = String(fallback(message, ""));
    alertBackdrop.classList.add("open");
    alertBackdrop.setAttribute("aria-hidden", "false");
    lockScroll();
  }

  function closeAlert() {
    if (!alertBackdrop) {
      return;
    }
    alertBackdrop.classList.remove("open");
    alertBackdrop.setAttribute("aria-hidden", "true");
    unlockScroll();
  }

  function syncShortcutButtonsEnabled() {
    [btnShortcutCxc, btnShortcutFactura, btnShortcutPrefactura].forEach(function (button) {
      if (button) {
        button.disabled = false;
      }
    });
  }

  function openShortcut(shortcutKey, deniedMessage) {
    var permissions = config.shortcutPermissions || {};
    var urls = config.shortcutUrls || {};
    var allowed = !!permissions[shortcutKey];
    var targetUrl = String(urls[shortcutKey] || "").trim();
    if (!allowed) {
      showAlert(deniedMessage || "No tienes permiso para acceder a esta opcion.");
      return;
    }
    if (!targetUrl) {
      showAlert("No se pudo abrir el acceso directo solicitado.");
      return;
    }
    if (shortcutKey === "cuentas_por_cobrar") {
      var idSn = String(fieldCodigo && fieldCodigo.value ? fieldCodigo.value : "").trim();
      if (idSn) {
        var target = new URL(targetUrl, window.location.origin);
        var nombre = String(fieldNombre && fieldNombre.value ? fieldNombre.value : "").trim();
        target.searchParams.set("id_sn", idSn);
        if (nombre) {
          target.searchParams.set("nombre", nombre);
        }
        window.location.href = target.toString();
        return;
      }
    }
    window.location.href = targetUrl;
  }

  function getCsrfToken() {
    var configuredToken = String(config.csrfToken || "").trim();
    if (configuredToken && configuredToken !== "NOTPROVIDED") {
      return configuredToken;
    }
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function readDetalleDateCell(cell) {
    if (!cell) {
      return "";
    }
    var input = cell.querySelector("input[type='date']");
    if (input) {
      return String(input.value || "").trim();
    }
    return toDateInputValue(cell.textContent || "");
  }

  function readDetalleMoneyCell(cell) {
    return roundMoney(toNumber(cell ? cell.textContent : 0));
  }

  function collectDetalleRows() {
    if (!detalleBody) {
      return [];
    }
    return Array.prototype.slice.call(detalleBody.querySelectorAll("tr")).map(function (row) {
      var cells = row.children || [];
      if (!cells.length || row.classList.contains("financ-empty-row")) {
        return null;
      }
      var noCuota = String(cells[0] && cells[0].textContent ? cells[0].textContent : "").trim();
      if (!noCuota) {
        return null;
      }
      return {
        no_cuota: noCuota,
        fecha_venc: readDetalleDateCell(cells[1]),
        monto_interes: readDetalleMoneyCell(cells[2]),
        capital: readDetalleMoneyCell(cells[3]),
        balance: readDetalleMoneyCell(cells[4]),
        cuota: readDetalleMoneyCell(cells[5]),
        pagado: readDetalleMoneyCell(cells[6]),
        pendiente: readDetalleMoneyCell(cells[7]),
      };
    }).filter(function (row) {
      return !!row;
    });
  }

  function buildSavePayload(detailRows) {
    var facturaNo = String(fieldNoFactura && fieldNoFactura.value ? fieldNoFactura.value : "").trim();
    var recordLookup = String(
      currentNoDoc ||
      (fieldNo && fieldNo.value ? fieldNo.value : "")
    ).trim();
    if (!facturaNo && currentFacturaBase && currentFacturaBase.no_doc) {
      facturaNo = String(currentFacturaBase.no_doc || "").trim();
    }
    return {
      record_lookup: recordLookup,
      factura_no: facturaNo,
      no: String(fieldNo && fieldNo.value ? fieldNo.value : "").trim(),
      fecha: String(fieldFecha && fieldFecha.value ? fieldFecha.value : "").trim(),
      tipo: String(fieldTipo && fieldTipo.value ? fieldTipo.value : "").trim(),
      codigo: String(fieldCodigo && fieldCodigo.value ? fieldCodigo.value : "").trim(),
      nombre: String(fieldNombre && fieldNombre.value ? fieldNombre.value : "").trim(),
      cedula: String(fieldCedula && fieldCedula.value ? fieldCedula.value : "").trim(),
      monto: roundMoney(toNumber(fieldMonto && fieldMonto.value ? fieldMonto.value : 0)),
      porc_interes: roundMoney(toNumber(fieldPorcInteres && fieldPorcInteres.value ? fieldPorcInteres.value : 0)),
      plazo: Math.max(1, Math.round(toNumber(fieldPlazo && fieldPlazo.value ? fieldPlazo.value : detailRows.length || 1))),
      metodo: String(fieldMetodo && fieldMetodo.value ? fieldMetodo.value : "Lineal").trim(),
      tipo_cuota: String(fieldTipoCuota && fieldTipoCuota.value ? fieldTipoCuota.value : "Mensual").trim(),
      fecha_base: String(fieldFechaBase && fieldFechaBase.value ? fieldFechaBase.value : "").trim(),
      comentario: String(fieldComentario && fieldComentario.value ? fieldComentario.value : "").trim(),
      detail: detailRows,
    };
  }

  function buildFinanciamientoPrintHtml(copyCount) {
    var copies = normalizePrintCopies(copyCount);
    var empresa = config.empresa || {};
    var detailRows = collectDetalleRows();
    var logoSrc = buildImageSrc(empresa.logo_b64, empresa.logo_tipo);
    var firmaSrc = String(config.usuarioFirmaB64 || "").trim() ? ("data:image/png;base64," + String(config.usuarioFirmaB64 || "").trim()) : "";
    var fechaDocumento = String(fieldFecha && fieldFecha.value ? fieldFecha.value : "").trim();
    var telefono = [empresa.tel1, empresa.tel2].filter(function (value) {
      return String(value || "").trim();
    }).join("   ");
    var legalClauseHtml = escapeHtml(
      "El cliente autoriza a " + String(empresa.nombre || "la empresa") + " a consultar, compartir y reportar su informacion crediticia a las sociedades de informacion crediticia, conforme a la normativa vigente, en caso de incumplimiento de sus obligaciones."
    );
    var comentarioHtml = escapeHtml(fieldComentario && fieldComentario.value ? fieldComentario.value : "").replace(/\n/g, "<br>");
    var condicionesHtml = escapeHtml(
      "La falta de pago en tres (3) meses le da derecho a la empresa a recuperar los articulos financiados."
    );
    var rowsHtml = detailRows.map(function (row) {
      return (
        "<tr>" +
        "<td>" + escapeHtml(row.no_cuota || "") + "</td>" +
        "<td>" + escapeHtml(formatDateDisplay(parseInputDate(row.fecha_venc))) + "</td>" +
        "<td class=\"align-r\">" + escapeHtml(fmtMoney(row.monto_interes || 0)) + "</td>" +
        "<td class=\"align-r\">" + escapeHtml(fmtMoney(row.capital || 0)) + "</td>" +
        "<td class=\"align-r\">" + escapeHtml(fmtMoney(row.balance || 0)) + "</td>" +
        "</tr>"
      );
    }).join("");

    var pageHtml =
      "<main class=\"page\">" +
      "<header class=\"company-head\">" +
      "<div class=\"logo-wrap\">" + (logoSrc ? ("<img src=\"" + logoSrc + "\" alt=\"Logo empresa\" />") : "") + "</div>" +
      "<div class=\"company-info\"><h1>" + escapeHtml(empresa.nombre || "EMPRESA") + "</h1>" +
      "<div class=\"meta\">" +
      "<div>" + escapeHtml(empresa.direccion || "") + "</div>" +
      "<div>Telefonos: " + escapeHtml(telefono || "") + (empresa.email ? ("   E-Mail: " + escapeHtml(empresa.email)) : "") + "</div>" +
      "<div><strong>RNC:</strong> " + escapeHtml(empresa.rnc || "") + "</div>" +
      "</div></div></header>" +
      "<div class=\"title\">PAGARE Y/O CONTRATO</div>" +
      "<div class=\"doc-top\"><div>No.: " + escapeHtml(fieldNo && fieldNo.value ? fieldNo.value : "") + "</div><div>Fecha: " + escapeHtml(formatLongSpanishDate(fechaDocumento)) + "</div></div>" +
      "<section class=\"info-grid\">" +
      "<div class=\"info-block\">" +
      "<div class=\"info-row\"><strong>Codigo</strong><span>:</span><span>" + escapeHtml(fieldCodigo && fieldCodigo.value ? fieldCodigo.value : "") + "</span></div>" +
      "<div class=\"info-row\"><strong>Nombre</strong><span>:</span><span>" + escapeHtml(fieldNombre && fieldNombre.value ? fieldNombre.value : "") + "</span></div>" +
      "<div class=\"info-row\"><strong>Cedula</strong><span>:</span><span>" + escapeHtml(fieldCedula && fieldCedula.value ? fieldCedula.value : "") + "</span></div>" +
      "</div>" +
      "<div class=\"info-block\">" +
      "<div class=\"info-row\"><strong>Moneda</strong><span>:</span><span>RD$</span></div>" +
      "<div class=\"info-row\"><strong>Tasa</strong><span>:</span><span>1.0000</span></div>" +
      "</div></section>" +
      "<div class=\"fin-data\">" +
      "<div><div class=\"section-title\">Datos del Financiamiento:</div>" +
      "<div class=\"fin-inline\">" +
      "<span><strong>Monto:</strong> " + escapeHtml(fmtMoney(fieldMonto && fieldMonto.value ? fieldMonto.value : 0)) + "</span>" +
      "<span><strong>% Int. mensual:</strong> " + escapeHtml(fmtRate(fieldPorcInteres && fieldPorcInteres.value ? fieldPorcInteres.value : 0)) + " %</span>" +
      "<span><strong>Plazo:</strong> " + escapeHtml(String(fieldPlazo && fieldPlazo.value ? fieldPlazo.value : detailRows.length || "")) + " mes(es)</span>" +
      "<span><strong>Forma de Pago:</strong> " + escapeHtml(fieldTipoCuota && fieldTipoCuota.value ? fieldTipoCuota.value : "") + "</span>" +
      "<span><strong>Metodo:</strong> " + escapeHtml(fieldMetodo && fieldMetodo.value ? fieldMetodo.value : "") + "</span>" +
      "</div></div>" +
      "<div class=\"info-block\">" +
      "<div class=\"info-row\"><strong>Tipo</strong><span>:</span><span>" + escapeHtml(fieldTipo && fieldTipo.value ? fieldTipo.value : "") + "</span></div>" +
      "<div class=\"info-row\"><strong>Estado</strong><span>:</span><span>" + escapeHtml(fieldEstado && fieldEstado.value ? fieldEstado.value : "") + "</span></div>" +
      "<div class=\"info-row\"><strong>Valor Cuota</strong><span>:</span><span>" + escapeHtml(fmtMoney(fieldValorCuota && fieldValorCuota.value ? fieldValorCuota.value : 0)) + "</span></div>" +
      "</div></div>" +
      "<div class=\"section-title\">Amortizacion de Cuota:</div>" +
      "<table><thead><tr><th>No. Cuota</th><th>Fecha Venc.</th><th class=\"align-r\">Monto Interes</th><th class=\"align-r\">Monto Capital</th><th class=\"align-r\">Saldo/Balance</th></tr></thead><tbody>" + rowsHtml + "</tbody></table>" +
      "<div class=\"bottom-grid\">" +
      "<div><div class=\"section-title\">Comentario:</div><div class=\"comment-box\">" + comentarioHtml + "</div></div>" +
      "<div class=\"conditions\"><strong>Condicion de Pagare:</strong>* " + condicionesHtml + "</div>" +
      "</div>" +
      "<div class=\"legal-note\">" + legalClauseHtml + "</div>" +
      "<div class=\"signatures\">" +
      "<div class=\"sign-box\"><div class=\"sign-space\"></div><div class=\"sign-line\">Recibido por</div></div>" +
      "<div class=\"sign-box\"><div class=\"sign-space\">" +
      (firmaSrc ? ("<img class=\"sign-img\" src=\"" + firmaSrc + "\" alt=\"Firma registrada\" />") : "") +
      "</div><div class=\"sign-line\">" + escapeHtml(config.usuarioNombre || "") + "<br>Registrado por</div></div>" +
      "</div>" +
      "</main>";

    var pagesHtml = Array.from({ length: copies }, function () {
      return pageHtml;
    }).join("");

    return (
      "<!DOCTYPE html>" +
      "<html lang=\"es\"><head><meta charset=\"UTF-8\" />" +
      "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />" +
      "<title>Financiamiento " + escapeHtml(fieldNo && fieldNo.value ? fieldNo.value : fieldNoFactura && fieldNoFactura.value ? fieldNoFactura.value : "") + "</title>" +
      "<style>" +
      "@page { size: A4 portrait; margin: 12mm; }" +
      "html,body{margin:0;padding:0;background:#ffffff;color:#111;font-family:Arial,Helvetica,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact;}" +
      "*{box-sizing:border-box;}" +
      "body{background:#eef2f8;}" +
      ".toolbar{max-width:210mm;margin:10px auto 0;display:flex;justify-content:flex-end;gap:8px;padding:0 8px;}" +
      ".toolbar button{border:1px solid #6b6b6b;background:linear-gradient(#ffffff,#d9d9d9);border-radius:6px;height:32px;min-width:110px;font-size:13px;font-weight:700;cursor:pointer;}" +
      ".page{width:210mm;min-height:297mm;margin:8px auto 24px;background:#fff;border:1px solid #c6ccd7;padding:10mm 10mm 12mm;page-break-after:always;break-after:page;display:flex;flex-direction:column;}" +
      ".page:last-child{page-break-after:auto;break-after:auto;}" +
      ".company-head{display:grid;grid-template-columns:58mm 1fr;gap:14px;align-items:start;}" +
      ".logo-wrap{display:flex;align-items:flex-start;justify-content:center;min-height:42mm;}" +
      ".logo-wrap img{max-width:54mm;max-height:40mm;object-fit:contain;}" +
      ".company-info h1{margin:0;font-size:22px;line-height:1;color:#1b1b1b;font-weight:900;text-transform:uppercase;}" +
      ".company-info .meta{margin-top:6px;font-size:11px;line-height:1.28;}" +
      ".title{margin:10px 0 8px;text-align:center;font-size:21px;font-weight:900;color:#183a83;letter-spacing:.8px;}" +
      ".doc-top{display:grid;grid-template-columns:1fr auto;gap:18px;align-items:end;border-bottom:2px solid #222;padding-bottom:5px;margin-bottom:10px;font-size:13px;font-weight:800;}" +
      ".info-grid{display:grid;grid-template-columns:1.25fr .95fr;gap:24px;margin-bottom:10px;}" +
      ".info-block{font-size:12px;line-height:1.34;}" +
      ".info-row{display:grid;grid-template-columns:95px 10px 1fr;gap:4px;}" +
      ".section-title{margin:6px 0 3px;font-size:12px;font-weight:800;text-decoration:underline;}" +
      ".fin-data{display:grid;grid-template-columns:1.3fr .9fr;gap:24px;margin-bottom:10px;}" +
      ".fin-inline{display:flex;flex-wrap:wrap;gap:16px;font-size:12px;}" +
      ".fin-inline span strong{display:inline-block;min-width:0;}" +
      "table{width:100%;border-collapse:collapse;font-size:10.5px;margin-top:3px;}" +
      "th,td{border:1px solid #333;padding:2px 4px;text-align:left;line-height:1.02;}" +
      "th{background:#f4f6fb;font-weight:800;font-size:9.5px;}" +
      ".align-r{text-align:right;font-variant-numeric:tabular-nums;}" +
      ".bottom-grid{display:grid;grid-template-columns:1.15fr .85fr;gap:26px;margin-top:16px;align-items:start;}" +
      ".comment-box{border:1px solid #333;border-radius:10px;min-height:76px;padding:8px;font-size:11px;white-space:normal;}" +
      ".conditions{font-size:12px;line-height:1.45;}" +
      ".conditions strong{display:block;margin-bottom:6px;font-size:13px;text-decoration:underline;}" +
      ".legal-note{margin-top:10px;border:1px solid #93a3bf;border-radius:10px;padding:8px 10px;font-size:10.5px;line-height:1.35;background:#f8fbff;}" +
      ".signatures{margin-top:auto;display:grid;grid-template-columns:1fr 1fr;gap:80px;font-size:12px;padding-top:10px;align-items:end;}" +
      ".sign-box{display:flex;flex-direction:column;justify-content:flex-end;align-items:center;min-height:38mm;}" +
      ".sign-space{height:18mm;display:flex;align-items:flex-end;justify-content:center;width:100%;overflow:hidden;}" +
      ".sign-img{max-width:42mm;max-height:24mm;object-fit:contain;display:block;}" +
      ".sign-line{width:100%;padding-top:5px;border-top:1px solid #333;text-align:center;}" +
      "@media print{body{background:#fff;} .toolbar{display:none;} .page{width:auto;min-height:273mm;margin:0;border:none;padding:10mm 10mm 12mm;display:flex;flex-direction:column;}}" +
      "<\/style></head><body>" +
      "<div class=\"toolbar\"><button type=\"button\" onclick=\"window.print()\">Imprimir</button><button type=\"button\" onclick=\"window.close()\">Cerrar</button></div>" +
      pagesHtml +
      "</body></html>"
    );
  }

  async function openFinanciamientoPrint(copyCount) {
    var html = buildFinanciamientoPrintHtml(copyCount);
    if (window.CALocalPrint) {
      try {
        var printedByAgent = await window.CALocalPrint.printHtml("financiamiento", html, {
          title: "Financiamiento " + (fieldNo && fieldNo.value ? fieldNo.value : currentNoDoc || ""),
          waitSeconds: 5,
        });
        if (printedByAgent) {
          return;
        }
      } catch (error) {
        showAlert(error.message || "No se pudo imprimir con el agente local.");
        return;
      }
    }
    var printFrame = document.createElement("iframe");
    printFrame.setAttribute("aria-hidden", "true");
    printFrame.style.position = "fixed";
    printFrame.style.right = "0";
    printFrame.style.bottom = "0";
    printFrame.style.width = "0";
    printFrame.style.height = "0";
    printFrame.style.border = "0";
    printFrame.style.opacity = "0";
    printFrame.style.pointerEvents = "none";
    document.body.appendChild(printFrame);

    var frameWindow = printFrame.contentWindow;
    if (!frameWindow || !frameWindow.document) {
      if (printFrame.parentNode) {
        printFrame.parentNode.removeChild(printFrame);
      }
      showAlert("No se pudo preparar la impresion del financiamiento.");
      return;
    }
    frameWindow.document.open();
    frameWindow.document.write(html);
    frameWindow.document.close();

    window.setTimeout(function () {
      try {
        frameWindow.focus();
        frameWindow.print();
      } catch (error) {
        showAlert("No se pudo enviar el financiamiento a impresion.");
      } finally {
        window.setTimeout(function () {
          if (printFrame.parentNode) {
            printFrame.parentNode.removeChild(printFrame);
          }
        }, 1500);
      }
    }, 180);
  }

  function saveRecord() {
    if (!isCreatingNew) {
      showAlert("Solo puedes grabar un financiamiento nuevo o uno virgen en edicion.");
      return;
    }
    if (!config.guardarUrl) {
      showAlert("No se configuro la ruta para grabar financiamientos.");
      return;
    }

    clampNumberField(fieldPorcInteres, 0, 100, 0, 2);
    clampNumberField(fieldPlazo, 1, 36, 1);

    var detailRows = collectDetalleRows();
    var payload = buildSavePayload(detailRows);
    var clientEventId = window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : ("fin-save-" + Date.now() + "-" + Math.random().toString(16).slice(2));
    payload.event_id = clientEventId;
    pendingLocalFinEventId = clientEventId;
    if (!payload.factura_no) {
      showAlert("Debes seleccionar la factura a financiar.");
      return;
    }
    if (!payload.codigo) {
      showAlert("No se pudo determinar el cliente del financiamiento.");
      return;
    }
    if (!detailRows.length) {
      showAlert("Debes generar las cuotas antes de grabar.");
      return;
    }
    rememberRecentLocalFinDoc(payload.record_lookup || payload.no);
    rememberRecentLocalFinFactura(payload.factura_no);

    if (btnGrabar) {
      btnGrabar.disabled = true;
    }
    fetch(config.guardarUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(payload),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data || {} };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          pendingLocalFinEventId = "";
          showAlert(result.data.detail || "No se pudo grabar el financiamiento.");
          return;
        }
        var savedRecord = result.data.record || {};
        var prestamo = savedRecord && savedRecord.prestamo ? savedRecord.prestamo : {};
        rememberRecentLocalFinDoc(prestamo.no_doc || prestamo.no || payload.record_lookup || payload.no);
        rememberRecentLocalFinFactura(prestamo.no_factura || payload.factura_no);
        applyRecord(savedRecord);
        openPrintModal();
      })
      .catch(function () {
        pendingLocalFinEventId = "";
        showAlert("Error de conexion grabando el financiamiento.");
      })
      .finally(function () {
        syncActionButtons();
      });
  }

  function clearFinancSocketReconnectTimer() {
    if (!financSocketReconnectTimer) {
      return;
    }
    clearTimeout(financSocketReconnectTimer);
    financSocketReconnectTimer = null;
  }

  function scheduleFinancSocketReconnect() {
    if (financSocketReconnectTimer) {
      return;
    }
    financSocketReconnectTimer = setTimeout(function () {
      financSocketReconnectTimer = null;
      connectFinanciamientoSocket();
    }, 3000);
  }

  function resolveFinanciamientoSocketUrl() {
    var raw = String(config.socketUrl || "").trim();
    if (!raw) {
      return "";
    }
    try {
      var target = new URL(raw, window.location.origin);
      target.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return target.toString();
    } catch (error) {
      return "";
    }
  }

  function handleExternalFinanciamientoEvent(data) {
    var incomingEventId = String(data && data.event_id ? data.event_id : "").trim();
    if (incomingEventId && incomingEventId === pendingLocalFinEventId) {
      pendingLocalFinEventId = "";
      return;
    }

    var targetId = String(data && data.document_id ? data.document_id : "").trim();
    var targetFactura = String(data && data.factura_no ? data.factura_no : "").trim();
    var currentDoc = String(currentNoDoc || (fieldNo && fieldNo.value ? fieldNo.value : "") || "").trim();
    var currentFactura = String(fieldNoFactura && fieldNoFactura.value ? fieldNoFactura.value : "").trim();
    var eventKey = incomingEventId || (targetId + "|" + targetFactura + "|" + String(data && data.reason ? data.reason : "").trim());
    if (eventKey && eventKey === lastFinEventKey) {
      return;
    }
    lastFinEventKey = eventKey;

    if (searchBackdrop && searchBackdrop.classList.contains("open")) {
      fetchSearchResults();
    }
    if (facturaBackdrop && facturaBackdrop.classList.contains("open")) {
      fetchFacturaResults();
    }

    if (targetId && shouldIgnoreRecentLocalFinDoc(targetId)) {
      return;
    }
    if (targetFactura && shouldIgnoreRecentLocalFinFactura(targetFactura)) {
      return;
    }

    if (currentDoc && targetId && currentDoc === targetId) {
      showAlert("El financiamiento " + currentDoc + " cambio en otra terminal. Se recargara para mostrar el estado actual.");
      loadRecord(currentDoc);
      return;
    }

    if (isCreatingNew && currentFactura && targetFactura && currentFactura === targetFactura) {
      showAlert("La factura " + currentFactura + " ya fue financiada en otra terminal. Debes seleccionar otra factura.");
      setBlankState();
    }
  }

  function connectFinanciamientoSocket() {
    var socketTarget = resolveFinanciamientoSocketUrl();
    if (!socketTarget || typeof window.WebSocket !== "function") {
      return;
    }
    if (
      financSocket
      && (
        financSocket.readyState === window.WebSocket.OPEN
        || financSocket.readyState === window.WebSocket.CONNECTING
      )
    ) {
      return;
    }
    try {
      financSocket = new window.WebSocket(socketTarget);
    } catch (error) {
      scheduleFinancSocketReconnect();
      return;
    }
    financSocket.addEventListener("open", function () {
      financSocketConnected = true;
      clearFinancSocketReconnectTimer();
    });
    financSocket.addEventListener("message", function (event) {
      var data = null;
      try {
        data = JSON.parse(event.data || "{}");
      } catch (error) {
        data = null;
      }
      if (!data || !data.type) {
        return;
      }
      if (data.type === "financiamiento.document_status") {
        handleExternalFinanciamientoEvent(data);
      }
    });
    financSocket.addEventListener("close", function () {
      financSocketConnected = false;
      financSocket = null;
      scheduleFinancSocketReconnect();
    });
    financSocket.addEventListener("error", function () {
      try {
        if (financSocket) {
          financSocket.close();
        }
      } catch (error) {
        // Ignore close failures after socket errors.
      }
    });
  }

  function openSearchModal() {
    if (!searchBackdrop) {
      return;
    }
    searchBackdrop.classList.add("open");
    searchBackdrop.setAttribute("aria-hidden", "false");
    lockScroll();
    if (fieldSearchQ) {
      fieldSearchQ.focus();
      fieldSearchQ.select();
    }
    fetchSearchResults();
  }

  function closeSearchModal() {
    if (!searchBackdrop) {
      return;
    }
    if (document.activeElement && searchBackdrop.contains(document.activeElement) && btnBuscar) {
      btnBuscar.focus();
    }
    searchBackdrop.classList.remove("open");
    searchBackdrop.setAttribute("aria-hidden", "true");
    unlockScroll();
  }

  function openFacturaModal() {
    if (!facturaBackdrop) {
      return;
    }
    facturaBackdrop.classList.add("open");
    facturaBackdrop.setAttribute("aria-hidden", "false");
    lockScroll();
    if (fieldFacturaQ) {
      fieldFacturaQ.focus();
      fieldFacturaQ.select();
    }
    fetchFacturaResults();
  }

  function closeFacturaModal() {
    if (!facturaBackdrop) {
      return;
    }
    if (document.activeElement && facturaBackdrop.contains(document.activeElement) && btnNuevo) {
      btnNuevo.focus();
    }
    facturaBackdrop.classList.remove("open");
    facturaBackdrop.setAttribute("aria-hidden", "true");
    unlockScroll();
  }

  function setEmptyRow(targetBody, colspan, message) {
    if (!targetBody) {
      return;
    }
    targetBody.innerHTML =
      "<tr class=\"financ-empty-row\"><td colspan=\"" + colspan + "\">" + escapeHtml(message) + "</td></tr>";
  }

  function renderDetalleRows(rows) {
    if (!detalleBody) {
      return;
    }
    if (!rows || !rows.length) {
      setEmptyRow(detalleBody, 8, "Sin cuotas registradas para este financiamiento.");
      return;
    }
    var isAgreementEditable = isCreatingNew &&
      normalizeChoice(
        fieldTipoCuota ? fieldTipoCuota.value : "",
        ["Mensual", "Quincenal", "Semanal", "Diario", "Acuerdo"],
        "Mensual"
      ) === "Acuerdo";
    detalleBody.innerHTML = rows.map(function (row) {
      var fechaCell = escapeHtml(row.fecha_venc || row.fecha || "");
      if (isAgreementEditable) {
        fechaCell =
          "<input type=\"date\" class=\"financ-grid-date\" data-no-cuota=\"" +
          escapeHtml(row.no_cuota || "") +
          "\" value=\"" +
          escapeHtml(toDateInputValue(row.fecha_venc || row.fecha || "")) +
          "\" />";
      }
      return (
        "<tr>" +
        "<td>" + escapeHtml(row.no_cuota || "") + "</td>" +
        "<td>" + fechaCell + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.monto_interes || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.capital || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.balance || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.cuota || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.pagado || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.pendiente || 0)) + "</td>" +
        "</tr>"
      );
    }).join("");
    if (isAgreementEditable) {
      Array.prototype.slice.call(detalleBody.querySelectorAll(".financ-grid-date[data-no-cuota]")).forEach(function (input) {
        input.addEventListener("change", function () {
          var noCuota = String(input.getAttribute("data-no-cuota") || "").trim();
          if (!noCuota) {
            return;
          }
          agreementDatesByCuota[noCuota] = String(input.value || "").trim();
        });
      });
    }
  }

  function cacheAgreementDates(rows) {
    agreementDatesByCuota = {};
    (rows || []).forEach(function (row) {
      var noCuota = String(row && row.no_cuota ? row.no_cuota : "").trim();
      var fechaVenc = toDateInputValue(row ? (row.fecha_venc || row.fecha || "") : "");
      if (noCuota && fechaVenc) {
        agreementDatesByCuota[noCuota] = fechaVenc;
      }
    });
  }

  function renderHistorialRows(rows) {
    if (!historialBody) {
      return;
    }
    if (!rows || !rows.length) {
      setEmptyRow(historialBody, 5, "Sin movimientos aplicados.");
      return;
    }
    historialBody.innerHTML = rows.map(function (row) {
      return (
        "<tr>" +
        "<td>" + escapeHtml(row.no_cuota || "") + "</td>" +
        "<td>" + escapeHtml(row.fecha_venc || row.fecha || "") + "</td>" +
        "<td>" + escapeHtml(row.no_recibo || "") + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.pagado || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.pendiente || 0)) + "</td>" +
        "</tr>"
      );
    }).join("");
  }

  function renderFinanzas(finanzas) {
    finanzas = finanzas || {};
    if (capitalTotal) capitalTotal.textContent = fmtMoney(finanzas.capital_total || 0);
    if (interesTotal) interesTotal.textContent = fmtMoney(finanzas.interes_total || 0);
    if (cuotaTotal) cuotaTotal.textContent = fmtMoney(finanzas.cuota_total || 0);
    if (pagadoTotal) pagadoTotal.textContent = fmtMoney(finanzas.pagado_total || 0);
    if (pendienteTotal) pendienteTotal.textContent = fmtMoney(finanzas.pendiente_total || 0);
  }

  function setBlankState(options) {
    options = options || {};
    currentNoDoc = "";
    currentFacturaBase = null;
    agreementDatesByCuota = {};
    syncShortcutButtonsEnabled();
    setCreateMode(!!options.newMode);
    [
      fieldNoFactura,
      fieldNo,
      fieldEstado,
      fieldTipo,
      fieldCodigo,
      fieldNombre,
      fieldCedula,
      fieldMoneda,
      fieldComentario,
    ].forEach(function (field) {
      setFieldValue(field, "");
    });
    setFieldValue(fieldFecha, "");
    setFieldValue(fieldFechaBase, config.serverToday || "");
    setFieldValue(fieldTasa, 1, fmtRate);
    setFieldValue(fieldMonto, 0, fmtMoney);
    setFieldValue(fieldPorcInteres, 0);
    setFieldValue(fieldPlazo, 1);
    setFieldValue(fieldMetodo, "Lineal");
    setFieldValue(fieldTipoCuota, "Mensual");
    setFieldValue(fieldTotalPagado, 0, fmtMoney);
    setFieldValue(fieldValorCuota, 0, fmtMoney);
    setEmptyRow(detalleBody, 8, "Selecciona una factura para iniciar el financiamiento.");
    setEmptyRow(historialBody, 5, "Sin movimientos aplicados.");
    renderFinanzas({});
    activateTab("fin_tab_detalle");
    syncActionButtons(options.newMode ? "editing" : "idle");
  }

  function applyRecord(data) {
    var prestamo = (data && data.prestamo) || {};
    var facturaBase = (data && data.factura_base) || null;
    var montoBaseEditable = data && data.editable && facturaBase && facturaBase.disponible
      ? toNumber(facturaBase.saldo || facturaBase.total_doc || 0)
      : toNumber(prestamo.monto || 0);
    currentNoDoc = String(prestamo.no_doc || prestamo.no || prestamo.no_factura || "").trim();
    currentFacturaBase = data && data.editable
      ? {
          no_doc: (facturaBase && facturaBase.no_doc) || prestamo.no_factura || prestamo.no_doc || "",
          saldo: montoBaseEditable,
          total_doc: facturaBase && facturaBase.total_doc ? facturaBase.total_doc : montoBaseEditable,
        }
      : null;
    agreementDatesByCuota = {};
    syncShortcutButtonsEnabled();
    setCreateMode(!!(data && data.editable));
    setFieldValue(fieldNoFactura, prestamo.no_factura || prestamo.no_doc || "");
    setFieldValue(fieldNo, prestamo.no || prestamo.no_doc || "");
    setFieldValue(fieldEstado, prestamo.estado || "");
    setFieldValue(fieldFecha, prestamo.fecha || "");
    setFieldValue(fieldTipo, prestamo.tipo || "");
    setFieldValue(fieldCodigo, prestamo.codigo || "");
    setFieldValue(fieldNombre, prestamo.nombre || "");
    setFieldValue(fieldCedula, prestamo.cedula || "");
    setFieldValue(fieldMoneda, prestamo.moneda || "RD$");
    setFieldValue(fieldTasa, prestamo.tasa || 1, fmtRate);
    setFieldValue(fieldMonto, montoBaseEditable, fmtMoney);
    setFieldValue(fieldPorcInteres, prestamo.porc_interes || 0);
    setFieldValue(fieldPlazo, prestamo.plazo || "");
    setFieldValue(fieldMetodo, normalizeChoice(prestamo.metodo, ["Lineal", "Insoluto"], "Lineal"));
    setFieldValue(
      fieldTipoCuota,
      normalizeChoice(prestamo.tipo_cuota, ["Mensual", "Quincenal", "Semanal", "Diario", "Acuerdo"], "Mensual")
    );
    setFieldValue(fieldFechaBase, prestamo.fecha_base || "");
    setFieldValue(fieldTotalPagado, prestamo.total_pagado || 0, fmtMoney);
    setFieldValue(fieldValorCuota, prestamo.valor_cuota || 0, fmtMoney);
    setFieldValue(fieldComentario, prestamo.comentario || "");
    if (data && data.editable) {
      cacheAgreementDates(data.detalle || []);
    }
    renderDetalleRows(data.detalle || []);
    renderHistorialRows(data.historial || []);
    renderFinanzas(data.finanzas || {});
    activateTab("fin_tab_detalle");
    syncActionButtons(data && data.editable ? "editing" : "viewing");
  }

  function applyFacturaSelection(row) {
    currentNoDoc = "";
    currentFacturaBase = row || null;
    agreementDatesByCuota = {};
    setCreateMode(true);
    setFieldValue(fieldNoFactura, row && row.no_doc ? row.no_doc : "");
    setFieldValue(fieldNo, "");
    setFieldValue(fieldEstado, "Nuevo");
    setFieldValue(fieldFecha, config.serverToday || (row && row.fecha_iso) || "");
    setFieldValue(fieldTipo, "Financiamiento");
    setFieldValue(fieldCodigo, row && row.codigo ? row.codigo : "");
    setFieldValue(fieldNombre, row && row.nombre ? row.nombre : "");
    setFieldValue(fieldCedula, row && row.cedula ? row.cedula : "");
    setFieldValue(fieldMoneda, "");
    setFieldValue(fieldTasa, 1, fmtRate);
    setFieldValue(fieldMonto, row && row.saldo ? row.saldo : 0, fmtMoney);
    setFieldValue(fieldPorcInteres, 0);
    setFieldValue(fieldPlazo, 1);
    setFieldValue(fieldMetodo, "Lineal");
    setFieldValue(fieldTipoCuota, "Mensual");
    setFieldValue(fieldFechaBase, config.serverToday || "");
    setFieldValue(fieldTotalPagado, 0, fmtMoney);
    setFieldValue(fieldValorCuota, 0, fmtMoney);
    setFieldValue(fieldComentario, row && row.comentario ? row.comentario : "");
    activateTab("fin_tab_detalle");
    refreshPreviewSchedule();
    syncActionButtons("editing");
  }

  function renderSearchResults(rows) {
    if (!searchBody) {
      return;
    }
    if (!rows || !rows.length) {
      setEmptyRow(searchBody, 8, "No se encontraron financiamientos.");
      return;
    }
    searchBody.innerHTML = rows.map(function (row) {
      return (
        "<tr data-no-doc=\"" + escapeHtml(row.no_doc || "") + "\">" +
        "<td>" + escapeHtml(row.no_factura || row.no_doc || "") + "</td>" +
        "<td>" + escapeHtml(row.no || row.no_doc || "") + "</td>" +
        "<td>" + escapeHtml(row.codigo || "") + "</td>" +
        "<td>" + escapeHtml(row.nombre || "") + "</td>" +
        "<td>" + escapeHtml(row.fecha || "") + "</td>" +
        "<td>" + escapeHtml(row.estado || "") + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.monto || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.saldo || 0)) + "</td>" +
        "</tr>"
      );
    }).join("");
    Array.prototype.slice.call(searchBody.querySelectorAll("tr[data-no-doc]")).forEach(function (row) {
      row.addEventListener("click", function () {
        var noDoc = row.getAttribute("data-no-doc") || "";
        if (!noDoc) {
          return;
        }
        closeSearchModal();
        loadRecord(noDoc);
      });
    });
  }

  function fetchSearchResults() {
    if (!searchBody) {
      return;
    }
    var q = fieldSearchQ ? String(fieldSearchQ.value || "").trim() : "";
    var filtro = fieldSearchFiltro ? String(fieldSearchFiltro.value || "nombre").trim() : "nombre";
    setEmptyRow(searchBody, 8, "Buscando financiamientos...");
    fetch(config.buscarUrl + "?q=" + encodeURIComponent(q) + "&filtro=" + encodeURIComponent(filtro), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("search_failed");
        }
        return res.json();
      })
      .then(function (data) {
        renderSearchResults(data.results || []);
      })
      .catch(function () {
        setEmptyRow(searchBody, 8, "No se pudo cargar la lista.");
      });
  }

  function renderFacturaResults(rows) {
    if (!facturaBody) {
      return;
    }
    if (!rows || !rows.length) {
      setEmptyRow(facturaBody, 8, "No se encontraron facturas disponibles.");
      return;
    }
    facturaBody.innerHTML = rows.map(function (row) {
      return (
        "<tr data-no-doc=\"" + escapeHtml(row.no_doc || "") + "\">" +
        "<td>" + escapeHtml(row.no_doc || "") + "</td>" +
        "<td>" + escapeHtml(row.codigo || "") + "</td>" +
        "<td>" + escapeHtml(row.nombre || "") + "</td>" +
        "<td>" + escapeHtml(row.cedula || "") + "</td>" +
        "<td>" + escapeHtml(row.fecha || "") + "</td>" +
        "<td>" + escapeHtml(row.estado || "") + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.total_doc || 0)) + "</td>" +
        "<td class=\"is-num\">" + escapeHtml(fmtMoney(row.saldo || 0)) + "</td>" +
        "</tr>"
      );
    }).join("");
    Array.prototype.slice.call(facturaBody.querySelectorAll("tr[data-no-doc]")).forEach(function (rowNode, index) {
      rowNode.addEventListener("click", function () {
        var row = rows[index] || null;
        if (!row) {
          return;
        }
        closeFacturaModal();
        applyFacturaSelection(row);
      });
    });
  }

  function fetchFacturaResults() {
    if (!facturaBody) {
      return;
    }
    if (!config.facturasDisponiblesUrl) {
      setEmptyRow(facturaBody, 8, "No se configuro la ruta de facturas disponibles.");
      return;
    }
    var q = fieldFacturaQ ? String(fieldFacturaQ.value || "").trim() : "";
    var filtro = fieldFacturaFiltro ? String(fieldFacturaFiltro.value || "nombre").trim() : "nombre";
    setEmptyRow(facturaBody, 8, "Buscando facturas disponibles...");
    fetch(config.facturasDisponiblesUrl + "?q=" + encodeURIComponent(q) + "&filtro=" + encodeURIComponent(filtro), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (res) {
        if (!res.ok) {
          throw new Error("facturas_failed");
        }
        return res.json();
      })
      .then(function (data) {
        renderFacturaResults(data.results || []);
      })
      .catch(function () {
        setEmptyRow(facturaBody, 8, "No se pudo cargar la lista.");
      });
  }

  function loadRecord(noDoc) {
    var doc = String(noDoc || "").trim();
    if (!doc) {
      return;
    }
    fetch(config.detalleUrl + "?no_doc=" + encodeURIComponent(doc), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          showAlert(result.data.detail || "No se pudo cargar el financiamiento.");
          return;
        }
        applyRecord(result.data || {});
      })
      .catch(function () {
        showAlert("Error de conexion cargando el financiamiento.");
      });
  }

  tabButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      activateTab(button.getAttribute("data-target") || "fin_tab_detalle");
    });
  });

  if (btnNuevo) {
    btnNuevo.addEventListener("click", function () {
      setBlankState({ newMode: true });
      openFacturaModal();
    });
  }
  if (btnBuscar) {
    btnBuscar.addEventListener("click", openSearchModal);
  }
  if (btnOpenSearchTop) {
    btnOpenSearchTop.addEventListener("click", openFacturaModal);
  }
  if (btnCancel) {
    btnCancel.addEventListener("click", function () {
      setBlankState();
    });
  }
  if (btnGrabar) {
    btnGrabar.addEventListener("click", function () {
      saveRecord();
    });
  }
  if (btnPrint) {
    btnPrint.addEventListener("click", function () {
      openPrintModal();
    });
  }
  if (btnCerrar) {
    btnCerrar.addEventListener("click", function () {
      window.location.href = config.indexUrl || "/app/caja/";
    });
  }
  if (btnShortcutCxc) {
    btnShortcutCxc.addEventListener("click", function () {
      openShortcut("cuentas_por_cobrar", "No tienes permiso para acceder a Cuentas por cobrar.");
    });
  }
  if (btnShortcutFactura) {
    btnShortcutFactura.addEventListener("click", function () {
      openShortcut("factura", "No tienes permiso para acceder a Factura.");
    });
  }
  if (btnShortcutPrefactura) {
    btnShortcutPrefactura.addEventListener("click", function () {
      openShortcut("prefactura", "No tienes permiso para acceder a Prefactura.");
    });
  }

  if (btnCloseSearch) {
    btnCloseSearch.addEventListener("click", closeSearchModal);
  }
  if (searchBackdrop) {
    searchBackdrop.addEventListener("click", function (event) {
      if (event.target === searchBackdrop) {
        closeSearchModal();
      }
    });
  }
  if (btnSearchExec) {
    btnSearchExec.addEventListener("click", fetchSearchResults);
  }
  if (fieldSearchQ) {
    fieldSearchQ.addEventListener("input", function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(fetchSearchResults, 260);
    });
    fieldSearchQ.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        fetchSearchResults();
      }
    });
  }
  if (fieldSearchFiltro) {
    fieldSearchFiltro.addEventListener("change", fetchSearchResults);
  }

  if (btnCloseFactura) {
    btnCloseFactura.addEventListener("click", closeFacturaModal);
  }
  if (facturaBackdrop) {
    facturaBackdrop.addEventListener("click", function (event) {
      if (event.target === facturaBackdrop) {
        closeFacturaModal();
      }
    });
  }
  if (btnFacturaExec) {
    btnFacturaExec.addEventListener("click", fetchFacturaResults);
  }
  if (fieldFacturaQ) {
    fieldFacturaQ.addEventListener("input", function () {
      clearTimeout(facturaSearchTimer);
      facturaSearchTimer = setTimeout(fetchFacturaResults, 260);
    });
    fieldFacturaQ.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        fetchFacturaResults();
      }
    });
  }
  if (fieldFacturaFiltro) {
    fieldFacturaFiltro.addEventListener("change", fetchFacturaResults);
  }

  if (btnClosePrint) {
    btnClosePrint.addEventListener("click", closePrintModal);
  }
  if (btnPrintCancel) {
    btnPrintCancel.addEventListener("click", closePrintModal);
  }
  if (btnPrintConfirm) {
    btnPrintConfirm.addEventListener("click", function () {
      var copies = normalizePrintCopies(fieldPrintCopies ? fieldPrintCopies.value : 2);
      closePrintModal();
      void openFinanciamientoPrint(copies);
    });
  }
  if (fieldPrintCopies) {
    fieldPrintCopies.addEventListener("input", syncPrintModalSummary);
    fieldPrintCopies.addEventListener("blur", syncPrintModalSummary);
    fieldPrintCopies.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        if (btnPrintConfirm) {
          btnPrintConfirm.click();
        }
      }
    });
  }
  if (printBackdrop) {
    printBackdrop.addEventListener("click", function (event) {
      if (event.target === printBackdrop) {
        closePrintModal();
      }
    });
  }

  if (fieldPorcInteres) {
    fieldPorcInteres.addEventListener("input", function () {
      if (!isCreatingNew) {
        return;
      }
      refreshPreviewSchedule();
    });
    fieldPorcInteres.addEventListener("blur", function () {
      if (!isCreatingNew) {
        return;
      }
      clampNumberField(fieldPorcInteres, 0, 100, 0, 2);
      refreshPreviewSchedule();
    });
  }
  if (fieldPlazo) {
    fieldPlazo.addEventListener("input", function () {
      if (!isCreatingNew) {
        return;
      }
      refreshPreviewSchedule();
    });
    fieldPlazo.addEventListener("blur", function () {
      if (!isCreatingNew) {
        return;
      }
      clampNumberField(fieldPlazo, 1, 36, 1);
      refreshPreviewSchedule();
    });
  }
  if (fieldMetodo) {
    fieldMetodo.addEventListener("change", function () {
      if (!isCreatingNew) {
        return;
      }
      refreshPreviewSchedule();
    });
  }
  if (fieldTipoCuota) {
    fieldTipoCuota.addEventListener("change", function () {
      if (!isCreatingNew) {
        return;
      }
      refreshPreviewSchedule();
    });
  }
  if (fieldFechaBase) {
    fieldFechaBase.addEventListener("change", function () {
      if (!isCreatingNew) {
        return;
      }
      refreshPreviewSchedule();
    });
  }

  if (btnAlertClose) {
    btnAlertClose.addEventListener("click", closeAlert);
  }
  if (btnAlertOk) {
    btnAlertOk.addEventListener("click", closeAlert);
  }
  if (alertBackdrop) {
    alertBackdrop.addEventListener("click", function (event) {
      if (event.target === alertBackdrop) {
        closeAlert();
      }
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") {
      return;
    }
    if (alertBackdrop && alertBackdrop.classList.contains("open")) {
      closeAlert();
      return;
    }
    if (searchBackdrop && searchBackdrop.classList.contains("open")) {
      closeSearchModal();
      return;
    }
    if (facturaBackdrop && facturaBackdrop.classList.contains("open")) {
      closeFacturaModal();
    }
  });

  var params = null;
  var autoOpenNuevo = false;
  var sharedNoDoc = "";
  var sharedRecordType = "";
  try {
    params = new URLSearchParams(window.location.search || "");
    autoOpenNuevo = ["1", "true", "yes", "si"].indexOf(String(params.get("nuevo") || "").trim().toLowerCase()) >= 0;
    sharedNoDoc = String(params.get("no_doc") || "").trim();
    sharedRecordType = String(params.get("shared_record") || "").trim().toLowerCase();
  } catch (error) {
    autoOpenNuevo = false;
    sharedNoDoc = "";
    sharedRecordType = "";
  }

  if (autoOpenNuevo) {
    setBlankState({ newMode: true });
    openFacturaModal();
    if (window.history && typeof window.history.replaceState === "function") {
      try {
        var cleanedUrl = window.location.pathname + (window.location.hash || "");
        window.history.replaceState({}, document.title, cleanedUrl);
      } catch (error) {
        /* noop */
      }
    }
  } else {
    setBlankState();
    if (sharedRecordType === "financiamiento" && sharedNoDoc) {
      loadRecord(sharedNoDoc);
      if (window.history && typeof window.history.replaceState === "function") {
        try {
          var cleanedParams = new URLSearchParams(params.toString());
          cleanedParams.delete("shared_record");
          cleanedParams.delete("no_doc");
          var cleanedQuery = cleanedParams.toString();
          var cleanedUrl = window.location.pathname + (cleanedQuery ? "?" + cleanedQuery : "") + (window.location.hash || "");
          window.history.replaceState({}, document.title, cleanedUrl);
        } catch (error) {
          /* noop */
        }
      }
    }
  }
  connectFinanciamientoSocket();
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && !financSocketConnected) {
      connectFinanciamientoSocket();
    }
  });
  window.addEventListener("beforeunload", function () {
    clearFinancSocketReconnectTimer();
    try {
      if (financSocket) {
        financSocket.close();
      }
    } catch (error) {
      // Ignore shutdown close failures.
    }
  });
})();
