(function () {
  const config = window.facturacionManualConfig || {};
  const prefSearchInput = document.getElementById("fac_pref_q");
  const prefSearchFilter = document.getElementById("fac_pref_filtro");
  const btnPrefBuscar = document.getElementById("btn_fac_pref_buscar");
  const prefResultsBody = document.getElementById("fac_pref_results_body");
  const prefSelectedLabel = document.getElementById("fac_pref_selected_label");
  const detalleBody = document.getElementById("facturacion_detalle_body");
  const lineCommentField = document.getElementById("fac_comentario_linea");
  const btnNuevo = document.getElementById("btn_facturacion_nuevo");
  const btnBuscar = document.getElementById("btn_facturacion_buscar");
  const btnCancel = document.getElementById("btn_facturacion_cancel");
  const btnGrabar = document.getElementById("btn_facturacion_grabar");
  const btnImprimir = document.getElementById("btn_facturacion_imprimir");
  const btnCargarCliente = document.getElementById("btn_facturacion_cargar_cliente");
  const btnBorrarLinea = document.getElementById("btn_facturacion_borrar_linea");
  const btnShortcutCxc = document.getElementById("btn_facturacion_shortcut_cxc");
  const btnShortcutFinanc = document.getElementById("btn_facturacion_shortcut_financ");
  const btnShortcutPref = document.getElementById("btn_facturacion_shortcut_pref");
  const historyBackdrop = document.getElementById("facturacion_history_backdrop");
  const btnCloseHistory = document.getElementById("btn_close_facturacion_history");
  const historySearchInput = document.getElementById("facturacion_hist_q");
  const historySearchFilter = document.getElementById("facturacion_hist_filtro");
  const btnHistoryBuscar = document.getElementById("btn_facturacion_hist_buscar");
  const historyResultsBody = document.getElementById("facturacion_hist_results_body");
  const clienteBackdrop = document.getElementById("facturacion_cliente_backdrop");
  const btnCloseCliente = document.getElementById("btn_close_facturacion_cliente");
  const clienteSearchInput = document.getElementById("facturacion_cliente_q");
  const clienteSearchFilter = document.getElementById("facturacion_cliente_filtro");
  const clienteResultsBody = document.getElementById("facturacion_cliente_results_body");
  const detalleCodigoBackdrop = document.getElementById("facturacion_detalle_codigo_backdrop");
  const detalleCodigoTitle = document.getElementById("facturacion_detalle_codigo_title");
  const btnCloseDetalleCodigo = document.getElementById("btn_close_facturacion_detalle_codigo");
  const detalleCodigoSearchInput = document.getElementById("facturacion_detalle_codigo_q");
  const detalleCodigoResultsBody = document.getElementById("facturacion_detalle_codigo_results_body");
  const articuloBackdrop = document.getElementById("facturacion_articulo_backdrop");
  const btnCloseArticulo = document.getElementById("btn_close_facturacion_articulo");
  const articuloSearchInput = document.getElementById("facturacion_articulo_q");
  const articuloSearchFilter = document.getElementById("facturacion_articulo_filtro");
  const articuloResultsBody = document.getElementById("facturacion_articulo_results_body");
  const alertBackdrop = document.getElementById("facturacion_alert_backdrop");
  const alertMessage = document.getElementById("facturacion_alert_message");
  const btnAlertClose = document.getElementById("btn_facturacion_alert_close");
  const btnAlertOk = document.getElementById("btn_facturacion_alert_ok");
  const estadoContextMenu = document.getElementById("facturacion_estado_context_menu");
  const btnEstadoContextCancel = document.getElementById("btn_facturacion_estado_context_cancel");
  const confirmBackdrop = document.getElementById("facturacion_confirm_backdrop");
  const confirmMessage = document.getElementById("facturacion_confirm_message");
  const btnConfirmClose = document.getElementById("btn_facturacion_confirm_close");
  const btnConfirmCancel = document.getElementById("btn_facturacion_confirm_cancel");
  const btnConfirmOk = document.getElementById("btn_facturacion_confirm_ok");
  const printBackdrop = document.getElementById("facturacion_print_backdrop");
  const btnClosePrint = document.getElementById("btn_close_facturacion_print");
  const fieldPrintCopies = document.getElementById("facturacion_print_copies");
  const printDocumento = document.getElementById("facturacion_print_documento");
  const printTotalHojas = document.getElementById("facturacion_print_total_hojas");
  const printTotalCopias = document.getElementById("facturacion_print_total_copias");
  const btnPrintCancel = document.getElementById("btn_facturacion_print_cancel");
  const btnPrintConfirm = document.getElementById("btn_facturacion_print_confirm");
  const tabs = Array.from(document.querySelectorAll(".prefactura-tab"));
  const tabPanels = Array.from(document.querySelectorAll(".prefactura-tab-panel"));

  const fieldIdSn = document.getElementById("fac_id_sn");
  const fieldNoDoc = document.getElementById("fac_no_doc");
  const fieldNomSocio = document.getElementById("fac_nom_socio");
  const fieldEstDoc = document.getElementById("fac_est_doc");
  const fieldContacto = document.getElementById("fac_contacto");
  const fieldFechaCont = document.getElementById("fac_fecha_cont");
  const fieldDireccion = document.getElementById("fac_direccion");
  const fieldFechaVenc = document.getElementById("fac_fecha_venc");
  const fieldRncCed = document.getElementById("fac_rnc_ced");
  const fieldFechaDoc = document.getElementById("fac_fecha_doc");
  const fieldTelefono = document.getElementById("fac_telefono");
  const fieldVendedor = document.getElementById("fac_vendedor");
  const fieldComentario = document.getElementById("fac_comentario");
  const fieldSubtotal = document.getElementById("fac_subtotal");
  const fieldTotalDesc = document.getElementById("fac_total_desc");
  const fieldImpuesto = document.getElementById("fac_impuesto");
  const fieldTotalDoc = document.getElementById("fac_total_doc");
  const fieldPagado = document.getElementById("fac_pagado");
  const fieldBalance = document.getElementById("fac_balance");
  const fieldSectorCliente = document.getElementById("fac_sector_cliente");
  const fieldDirFactura = document.getElementById("fac_dir_factura");
  const fieldDirMercancia = document.getElementById("fac_dir_mercancia");
  const fieldIdCondicion = document.getElementById("fac_id_condicion");
  const fieldCondicionDesc = document.getElementById("fac_condicion_desc");
  const fieldDias = document.getElementById("fac_dias");
  const fieldMoraDia = document.getElementById("fac_mora_dia");
  const fieldLimCredito = document.getElementById("fac_lim_credito");
  const fieldIdPrecio = document.getElementById("fac_id_precio");

  let prefSearchTimer = null;
  let historySearchTimer = null;
  let clienteSearchTimer = null;
  let articuloSearchTimer = null;
  let detalleCodigoTimer = null;
  let activePrefId = "";
  let activeFacturaId = "";
  let activeFacturaPrintUrl = "";
  let activeFacturaEditable = false;
  let unidadesMedida = [];
  let selectedDetalleRow = null;
  let detalleCodigoMode = "";
  let detalleCodigoTargetInput = null;
  let articuloTargetRow = null;
  let facturacionMode = "initial";
  let alertOpen = false;
  let alertQueue = [];
  let alertResolver = null;
  let confirmOpen = false;
  let confirmResolver = null;
  let printPendingUrl = "";
  let printPendingLabel = "";

  function fallback(value, defaultValue) {
    return value == null ? defaultValue : value;
  }

  function getQueryNode(root, selector) {
    if (!root || typeof root.querySelector !== "function") {
      return null;
    }
    return root.querySelector(selector);
  }

  function getNodeValue(node) {
    return node && typeof node.value !== "undefined" ? node.value : "";
  }

  function getQueryValue(root, selector) {
    return getNodeValue(getQueryNode(root, selector));
  }

  function getNodeText(node) {
    return node && typeof node.textContent === "string" ? node.textContent : "";
  }

  function getQueryText(root, selector) {
    return getNodeText(getQueryNode(root, selector));
  }

  function getChildText(root, index) {
    if (!root || !root.children || !root.children[index]) {
      return "";
    }
    return getNodeText(root.children[index]);
  }

  function focusIfPossible(node) {
    if (node && typeof node.focus === "function") {
      node.focus();
    }
  }

  function selectIfPossible(node) {
    if (node && typeof node.select === "function") {
      node.select();
    }
  }

  function escapeHtml(value) {
    return String(fallback(value, ""))
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
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

  function formatDecimal(value, digits = 2) {
    const amount = Number(fallback(value, 0));
    if (!Number.isFinite(amount)) {
      return digits === 0 ? "0" : "0.00";
    }
    return amount.toLocaleString("en-US", {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    });
  }

  function fmtNum(value, digits = 2) {
    const amount = Number(fallback(value, 0));
    if (!Number.isFinite(amount)) {
      return digits === 0 ? "0" : "0.00";
    }
    return amount.toFixed(digits);
  }

  function parseNum(value) {
    const amount = Number(String(fallback(value, "")).replace(/,/g, "").trim());
    return Number.isFinite(amount) ? amount : 0;
  }

  function normalizePrintCopies(value) {
    const numericValue = Math.round(parseNum(value || 2));
    if (!Number.isFinite(numericValue) || numericValue <= 0) {
      return 2;
    }
    return Math.max(1, Math.min(20, numericValue));
  }

  function sanitizeDecimalInput(value) {
    let clean = String(fallback(value, "")).replace(/[^0-9.]/g, "");
    const firstDot = clean.indexOf(".");
    if (firstDot >= 0) {
      clean = clean.slice(0, firstDot + 1) + clean.slice(firstDot + 1).replace(/\./g, "");
    }
    return clean;
  }

  function formatDecimal2(value) {
    return fmtNum(parseNum(value), 2);
  }

  function clampPercent(value) {
    const numeric = parseNum(value);
    if (numeric < 0) return 0;
    if (numeric > 100) return 100;
    return numeric;
  }

  function closeAlert() {
    if (!alertOpen || !alertBackdrop) {
      return;
    }
    alertBackdrop.classList.remove("open");
    alertBackdrop.setAttribute("aria-hidden", "true");
    alertOpen = false;
    unlockPageScroll();
    if (alertResolver) {
      const resolve = alertResolver;
      alertResolver = null;
      resolve();
    }
    if (alertQueue.length) {
      const next = alertQueue.shift();
      openAlert(next);
    }
  }

  function closeConfirm(accepted) {
    if (!confirmOpen || !confirmBackdrop) {
      return;
    }
    confirmBackdrop.classList.remove("open");
    confirmBackdrop.setAttribute("aria-hidden", "true");
    confirmOpen = false;
    unlockPageScroll();
    if (confirmResolver) {
      const resolve = confirmResolver;
      confirmResolver = null;
      resolve(!!accepted);
    }
  }

  function openConfirm(message) {
    if (!confirmBackdrop || !confirmMessage) {
      return;
    }
    confirmMessage.textContent = String(message == null ? "" : message);
    confirmBackdrop.classList.add("open");
    confirmBackdrop.setAttribute("aria-hidden", "false");
    confirmOpen = true;
    lockPageScroll();
    focusIfPossible(btnConfirmOk);
  }

  function openAlert(message) {
    if (!alertBackdrop || !alertMessage) {
      return;
    }
    alertMessage.textContent = String(message == null ? "" : message);
    alertBackdrop.classList.add("open");
    alertBackdrop.setAttribute("aria-hidden", "false");
    alertOpen = true;
    lockPageScroll();
    focusIfPossible(btnAlertOk);
  }

  function showAlert(message) {
    return new Promise((resolve) => {
      const text = String(message == null ? "" : message);
      if (!alertBackdrop || !alertMessage) {
        const nativeAlert = window.alert && window.alert !== showAlert ? window.alert : null;
        if (nativeAlert) {
          nativeAlert(text);
        }
        resolve();
        return;
      }
      if (alertOpen) {
        alertQueue.push(text);
        resolve();
        return;
      }
      alertResolver = resolve;
      openAlert(text);
    });
  }

  function showConfirm(message) {
    return new Promise((resolve) => {
      const text = String(message == null ? "" : message);
      if (!confirmBackdrop || !confirmMessage) {
        const nativeConfirm = typeof window.confirm === "function" ? window.confirm : null;
        resolve(nativeConfirm ? nativeConfirm(text) : false);
        return;
      }
      if (confirmOpen) {
        resolve(false);
        return;
      }
      confirmResolver = resolve;
      openConfirm(text);
    });
  }

  function setStatus(message, kind = "") {
    if (!message || !kind) {
      return;
    }
    showAlert(message);
  }

  function openShortcut(shortcutKey, deniedMessage) {
    const permissions = config.shortcutPermissions || {};
    const urls = config.shortcutUrls || {};
    const allowed = Boolean(permissions[shortcutKey]);
    const targetUrl = String(urls[shortcutKey] || "").trim();
    if (!allowed) {
      showAlert(deniedMessage || "No tienes permiso para acceder a esta pantalla.");
      return;
    }
    if (!targetUrl) {
      showAlert("No se pudo resolver la ruta del acceso directo.");
      return;
    }
    if (shortcutKey === "cuentas_por_cobrar") {
      const idSn = String(fieldIdSn?.value || "").trim();
      if (idSn) {
        const target = new URL(targetUrl, window.location.origin);
        const nombre = String(fieldNomSocio?.value || "").trim();
        const apodo = String(fieldContacto?.value || "").trim();
        target.searchParams.set("id_sn", idSn);
        if (nombre) {
          target.searchParams.set("nombre", nombre);
        }
        if (apodo) {
          target.searchParams.set("apodo", apodo);
        }
        window.location.href = target.toString();
        return;
      }
    }
    window.location.href = targetUrl;
  }

  function updatePrintButton() {
    if (!btnImprimir) {
      return;
    }
    btnImprimir.disabled = !activeFacturaPrintUrl;
  }

  function buildPrintUrlWithCopies(printUrl, copies) {
    const baseUrl = String(printUrl || "").trim();
    if (!baseUrl) {
      return "";
    }
    try {
      const target = new URL(baseUrl, window.location.origin);
      target.searchParams.set("copies", String(normalizePrintCopies(copies)));
      return target.toString();
    } catch (error) {
      return baseUrl;
    }
  }

  async function printFacturaDirectly(printUrl, copies) {
    const targetUrl = buildPrintUrlWithCopies(printUrl, copies);
    if (!targetUrl) {
      await showAlert("No se pudo identificar la factura para imprimir.");
      return;
    }
    try {
      const target = new URL(targetUrl, window.location.origin);
      target.searchParams.delete("autoprint");
      const response = await fetch(target.toString(), {
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      });
      if (!response.ok) {
        throw new Error("print-fetch-failed");
      }
      const html = await response.text();
      const printFrame = document.createElement("iframe");
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
      const frameWindow = printFrame.contentWindow;
      if (!frameWindow || !frameWindow.document) {
        if (printFrame.parentNode) {
          printFrame.parentNode.removeChild(printFrame);
        }
        throw new Error("print-frame-unavailable");
      }
      frameWindow.document.open();
      frameWindow.document.write(html);
      frameWindow.document.close();
      window.setTimeout(function () {
        try {
          frameWindow.focus();
          frameWindow.print();
        } catch (error) {
          showAlert("No se pudo enviar la factura a impresion.");
        } finally {
          window.setTimeout(function () {
            if (printFrame.parentNode) {
              printFrame.parentNode.removeChild(printFrame);
            }
          }, 1500);
        }
      }, 180);
    } catch (error) {
      await showAlert("No se pudo enviar la factura a impresion.");
    }
  }

  function syncPrintModalSummary() {
    const copies = normalizePrintCopies(fieldPrintCopies?.value);
    if (fieldPrintCopies) {
      fieldPrintCopies.value = String(copies);
    }
    if (printDocumento) {
      printDocumento.textContent = printPendingLabel || activeFacturaId || fieldNoDoc.value || "-";
    }
    if (printTotalHojas) {
      printTotalHojas.textContent = String(copies);
    }
    if (printTotalCopias) {
      printTotalCopias.textContent = String(copies);
    }
  }

  function closePrintModal() {
    if (!printBackdrop || !printBackdrop.classList.contains("open")) {
      return;
    }
    printBackdrop.classList.remove("open");
    printBackdrop.setAttribute("aria-hidden", "true");
    printPendingUrl = "";
    printPendingLabel = "";
    unlockPageScroll();
  }

  function openPrintModal(printUrl, facturaLabel = "") {
    const targetUrl = String(printUrl || "").trim();
    if (!targetUrl) {
      showAlert("No se pudo identificar la factura para imprimir.");
      return;
    }
    if (!printBackdrop) {
      printFacturaDirectly(targetUrl, 2);
      return;
    }
    printPendingUrl = targetUrl;
    printPendingLabel = String(facturaLabel || fieldNoDoc.value || activeFacturaId || "").trim();
    if (fieldPrintCopies) {
      fieldPrintCopies.value = "2";
    }
    syncPrintModalSummary();
    printBackdrop.classList.add("open");
    printBackdrop.setAttribute("aria-hidden", "false");
    lockPageScroll();
    focusIfPossible(fieldPrintCopies);
    selectIfPossible(fieldPrintCopies);
  }

  function activateTab(targetId) {
    tabs.forEach((tab) => tab.classList.toggle("active", (tab.dataset.target || "") === targetId));
    tabPanels.forEach((panel) => panel.classList.toggle("active", panel.id === targetId));
  }

  function isAnyModalOpen() {
    return [historyBackdrop, clienteBackdrop, articuloBackdrop, detalleCodigoBackdrop, alertBackdrop, confirmBackdrop, printBackdrop]
      .some((backdrop) => backdrop && backdrop.classList.contains("open"));
  }

  function hideEstadoContextMenu() {
    if (!estadoContextMenu) {
      return;
    }
    estadoContextMenu.classList.remove("open");
    estadoContextMenu.setAttribute("aria-hidden", "true");
    estadoContextMenu.style.left = "-9999px";
    estadoContextMenu.style.top = "-9999px";
  }

  function showEstadoContextMenu(event) {
    if (!estadoContextMenu) {
      return;
    }
    const menuWidth = 132;
    const menuHeight = 44;
    const left = Math.min(event.clientX, window.innerWidth - menuWidth - 8);
    const top = Math.min(event.clientY, window.innerHeight - menuHeight - 8);
    estadoContextMenu.style.left = `${Math.max(8, left)}px`;
    estadoContextMenu.style.top = `${Math.max(8, top)}px`;
    estadoContextMenu.classList.add("open");
    estadoContextMenu.setAttribute("aria-hidden", "false");
  }

  function lockPageScroll() {
    document.body.style.overflow = "hidden";
  }

  function unlockPageScroll() {
    document.body.style.overflow = isAnyModalOpen() ? "hidden" : "";
  }

  function setEditingFieldsDisabled(disabled) {
    [fieldFechaCont, fieldFechaVenc, fieldFechaDoc, fieldDirFactura, fieldDirMercancia].forEach((field) => {
      field.disabled = !!disabled;
      field.readOnly = !!disabled;
    });
    fieldComentario.disabled = false;
    fieldComentario.readOnly = true;
    lineCommentField.disabled = !!disabled || !selectedDetalleRow;
  }

  function clearFormValues() {
    [
      fieldIdSn, fieldNoDoc, fieldNomSocio, fieldEstDoc, fieldContacto, fieldFechaCont,
      fieldDireccion, fieldFechaVenc, fieldRncCed, fieldFechaDoc, fieldTelefono,
      fieldComentario, lineCommentField, fieldSectorCliente, fieldDirFactura,
      fieldDirMercancia, fieldIdCondicion, fieldCondicionDesc, fieldDias,
      fieldMoraDia, fieldLimCredito, fieldIdPrecio,
    ].forEach((field) => {
      field.value = "";
    });
    fieldVendedor.value = config.usuarioNombre || "";
    fieldSubtotal.value = "0.00";
    fieldTotalDesc.value = "0.00";
    fieldImpuesto.value = "0.00";
    fieldTotalDoc.value = "0.00";
    fieldPagado.value = "0.00";
    fieldBalance.value = "0.00";
    prefSelectedLabel.textContent = "-";
  }

  function clearPrefSelection() {
    prefResultsBody.querySelectorAll(".facturacion-pref-row.active").forEach((row) => row.classList.remove("active"));
  }

  function setDetallePlaceholder(message) {
    detalleBody.innerHTML = `<tr><td colspan="14" class="result-empty" style="height: 90px;">${escapeHtml(message)}</td></tr>`;
    selectedDetalleRow = null;
    lineCommentField.value = "";
    lineCommentField.disabled = true;
    updateDeleteLineButton();
  }

  function hasSelectedCliente() {
    return !!String(fieldIdSn.value || "").trim();
  }

  function setInitialState(clearStatus = true) {
    facturacionMode = "initial";
    activePrefId = "";
    activeFacturaId = "";
    activeFacturaPrintUrl = "";
    activeFacturaEditable = false;
    hideEstadoContextMenu();
    clearFormValues();
    clearPrefSelection();
    setDetallePlaceholder("Pulsa Nuevo para crear una factura o selecciona una prefactura activa.");
    btnNuevo.disabled = false;
    btnBuscar.disabled = false;
    btnCancel.disabled = true;
    btnGrabar.disabled = true;
    btnCargarCliente.disabled = true;
    setEditingFieldsDisabled(true);
    activateTab("facturacion_tab_detalle");
    updatePrintButton();
    if (clearStatus) {
      setStatus("");
    }
  }

  function setNewState() {
    facturacionMode = "new";
    activePrefId = "";
    activeFacturaId = "";
    activeFacturaPrintUrl = "";
    activeFacturaEditable = false;
    hideEstadoContextMenu();
    clearFormValues();
    clearPrefSelection();
    fieldEstDoc.value = "Abierto";
    fieldFechaCont.value = config.serverToday || "";
    fieldFechaVenc.value = config.serverToday || "";
    fieldFechaDoc.value = config.serverToday || "";
    btnNuevo.disabled = true;
    btnBuscar.disabled = true;
    btnCancel.disabled = false;
    btnGrabar.disabled = false;
    btnCargarCliente.disabled = false;
    updatePrintButton();
    setEditingFieldsDisabled(false);
    activateTab("facturacion_tab_detalle");
    setDetallePlaceholder("Carga un cliente para comenzar el detalle.");
    setStatus("");
  }

  function setLoadedPrefState() {
    facturacionMode = "loaded";
    activeFacturaId = "";
    activeFacturaEditable = false;
    btnNuevo.disabled = true;
    btnBuscar.disabled = true;
    btnCancel.disabled = false;
    btnGrabar.disabled = false;
    btnCargarCliente.disabled = true;
    setEditingFieldsDisabled(false);
    applyDetalleEditableAvailability();
    updateDeleteLineButton();
  }

  function setSavedState() {
    facturacionMode = "saved";
    activeFacturaEditable = false;
    btnNuevo.disabled = false;
    btnBuscar.disabled = false;
    btnCancel.disabled = false;
    btnGrabar.disabled = true;
    btnCargarCliente.disabled = true;
    setEditingFieldsDisabled(true);
    applyDetalleEditableAvailability();
    updateDeleteLineButton();
    updatePrintButton();
  }

  function setEditableSavedState() {
    facturacionMode = "editing_saved";
    activeFacturaEditable = true;
    btnNuevo.disabled = true;
    btnBuscar.disabled = true;
    btnCancel.disabled = false;
    btnGrabar.disabled = false;
    btnCargarCliente.disabled = !!activePrefId;
    setEditingFieldsDisabled(false);
    applyDetalleEditableAvailability();
    updateDeleteLineButton();
    updatePrintButton();
  }

  function renderPrefacturaResults(rows) {
    if (!Array.isArray(rows) || !rows.length) {
      prefResultsBody.innerHTML = '<tr class="facturacion-pref-empty"><td colspan="4">No hay prefacturas activas con ese filtro.</td></tr>';
      return;
    }
    prefResultsBody.innerHTML = rows.map((row) => `
      <tr class="facturacion-pref-row ${activePrefId === String(row.id_doc || "") ? "active" : ""}" data-id-doc="${escapeHtml(row.id_doc || "")}">
        <td>${escapeHtml(row.id_doc || "")}</td>
        <td title="${escapeHtml(row.nom_socio || "")}">${escapeHtml(row.nom_socio || "")}</td>
        <td>${escapeHtml(row.fecha_doc || "")}</td>
        <td>${escapeHtml(formatDecimal(row.total_doc || 0))}</td>
      </tr>
    `).join("");

    prefResultsBody.querySelectorAll(".facturacion-pref-row").forEach((row) => {
      row.addEventListener("click", () => {
        const idDoc = row.dataset.idDoc || "";
        if (idDoc) {
          loadPrefactura(idDoc);
        }
      });
    });
  }

  async function fetchPrefacturas() {
    const q = (prefSearchInput.value || "").trim();
    const filtro = (prefSearchFilter.value || "documento").trim();
    prefResultsBody.innerHTML = '<tr class="facturacion-pref-empty"><td colspan="4">Buscando prefacturas...</td></tr>';
    try {
      const res = await fetch(`${config.prefListUrl}?q=${encodeURIComponent(q)}&filtro=${encodeURIComponent(filtro)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        prefResultsBody.innerHTML = '<tr class="facturacion-pref-empty"><td colspan="4">No se pudo cargar la lista.</td></tr>';
        return;
      }
      const data = await res.json().catch(() => ({}));
      renderPrefacturaResults(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      prefResultsBody.innerHTML = '<tr class="facturacion-pref-empty"><td colspan="4">Error de conexion.</td></tr>';
    }
  }

  async function fetchClienteDetalle(idSn) {
    const clienteId = String(idSn || "").trim();
    if (!clienteId) {
      return null;
    }
    try {
      const res = await fetch(`${config.clienteDetalleUrl}?id_sn=${encodeURIComponent(clienteId)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        return null;
      }
      const data = await res.json().catch(() => ({}));
      return data.cliente || null;
    } catch (error) {
      return null;
    }
  }

  function fillClienteFields(cliente) {
    if (!cliente) {
      return;
    }
    fieldIdSn.value = cliente.id_sn || "";
    fieldNomSocio.value = cliente.nom_socio || "";
    fieldContacto.value = cliente.contacto || "";
    fieldRncCed.value = cliente.rnc_ced || "";
    fieldDireccion.value = cliente.dir_factura || "";
    fieldTelefono.value = cliente.tel1 || cliente.tel2 || "";
    fieldSectorCliente.value = cliente.comentario || cliente.descripcion || "";
    fieldDirFactura.value = cliente.dir_factura || "";
    fieldDirMercancia.value = cliente.dir_mercancia || "";
    fieldIdCondicion.value = cliente.id_condicion || "";
    fieldCondicionDesc.value = cliente.condicion || "";
    fieldDias.value = cliente.dia || "";
    fieldMoraDia.value = cliente.tarifa_int || "";
    fieldLimCredito.value = cliente.lim_credito != null && cliente.lim_credito !== "" ? formatDecimal(cliente.lim_credito, 2) : "";
    fieldIdPrecio.value = cliente.id_precio || "";
  }

  function fillFromPrefactura(pref, cliente) {
    fillClienteFields(cliente || {});
    fieldIdSn.value = pref.id_sn || fieldIdSn.value;
    fieldNomSocio.value = pref.nom_socio || fieldNomSocio.value;
    fieldContacto.value = (cliente && cliente.contacto) || pref.contacto || fieldContacto.value;
    fieldRncCed.value = pref.rnc_ced || fieldRncCed.value;
    fieldDireccion.value = (cliente && cliente.dir_factura) || pref.ent_factura || fieldDireccion.value;
    fieldTelefono.value = (cliente && (cliente.tel1 || cliente.tel2)) || fieldTelefono.value;
    fieldEstDoc.value = "Abierto";
    fieldNoDoc.value = "";
    fieldFechaCont.value = pref.fecha_cont || config.serverToday || "";
    fieldFechaVenc.value = pref.fecha_venc || pref.fecha_doc || config.serverToday || "";
    fieldFechaDoc.value = pref.fecha_doc || config.serverToday || "";
    fieldComentario.value = pref.comentario || "";
    fieldSubtotal.value = fmtNum(pref.subtotal || 0, 2);
    fieldTotalDesc.value = fmtNum(pref.total_desc || 0, 2);
    fieldImpuesto.value = fmtNum(pref.impuesto || 0, 2);
    fieldTotalDoc.value = fmtNum(pref.total_doc || 0, 2);
    fieldPagado.value = "0.00";
    fieldBalance.value = fmtNum(pref.total_doc || 0, 2);
    fieldDirFactura.value = (cliente && cliente.dir_factura) || pref.ent_factura || fieldDirFactura.value;
    fieldDirMercancia.value = (cliente && cliente.dir_mercancia) || pref.ent_mercancia || fieldDirMercancia.value;
    fieldIdCondicion.value = pref.id_condicion || fieldIdCondicion.value;
    fieldCondicionDesc.value = pref.condicion || fieldCondicionDesc.value;
    fieldDias.value = pref.dia || fieldDias.value;
    fieldIdPrecio.value = (cliente && cliente.id_precio) || pref.id_precio || fieldIdPrecio.value;
    prefSelectedLabel.textContent = `${pref.id_doc || "-"} - ${pref.nom_socio || ""}`.trim();
  }

  function fillFromFactura(factura, cliente) {
    activeFacturaId = factura.id_doc || "";
    activeFacturaEditable = !!factura.editable;
    fillClienteFields(cliente || {});
    activePrefId = factura.id_doc_pv || "";
    fieldIdSn.value = factura.id_sn || fieldIdSn.value;
    fieldNoDoc.value = factura.id_doc || "";
    fieldNomSocio.value = factura.nom_socio || fieldNomSocio.value;
    fieldEstDoc.value = factura.est_doc || "Facturada";
    fieldContacto.value = factura.contacto || fieldContacto.value;
    fieldFechaCont.value = factura.fecha_cont || "";
    fieldDireccion.value = (cliente && cliente.dir_factura) || factura.ent_factura || fieldDireccion.value;
    fieldFechaVenc.value = factura.fecha_venc || factura.fecha_doc || "";
    fieldRncCed.value = factura.rnc_ced || fieldRncCed.value;
    fieldFechaDoc.value = factura.fecha_doc || "";
    fieldTelefono.value = (cliente && (cliente.tel1 || cliente.tel2)) || fieldTelefono.value;
    fieldComentario.value = factura.comentario || "";
    fieldSubtotal.value = fmtNum(factura.subtotal || 0, 2);
    fieldTotalDesc.value = fmtNum(factura.total_desc || 0, 2);
    fieldImpuesto.value = fmtNum(factura.impuesto || 0, 2);
    fieldTotalDoc.value = fmtNum(factura.total_doc || 0, 2);
    fieldPagado.value = fmtNum(factura.pagado || 0, 2);
    fieldBalance.value = fmtNum(factura.balance || 0, 2);
    fieldDirFactura.value = (cliente && cliente.dir_factura) || factura.ent_factura || fieldDirFactura.value;
    fieldDirMercancia.value = (cliente && cliente.dir_mercancia) || factura.ent_mercancia || fieldDirMercancia.value;
    fieldIdCondicion.value = factura.id_condicion || fieldIdCondicion.value;
    fieldCondicionDesc.value = factura.condicion || fieldCondicionDesc.value;
    fieldDias.value = factura.dia || fieldDias.value;
    fieldIdPrecio.value = (cliente && cliente.id_precio) || factura.id_precio || fieldIdPrecio.value;
    prefSelectedLabel.textContent = factura.id_doc_pv || "-";
  }

  async function cargarUnidadesMedida() {
    if (unidadesMedida.length) {
      return;
    }
    try {
      const res = await fetch(config.unidadMedidaBuscarUrl, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        unidadesMedida = [];
        return;
      }
      const data = await res.json().catch(() => ({}));
      unidadesMedida = Array.isArray(data.results) ? data.results : [];
    } catch (error) {
      unidadesMedida = [];
    }
  }

  function getUnidadMedidaDefault() {
    return unidadesMedida[0] || "UND";
  }

  function renderUnidadMedidaOptions(selectedValue = "") {
    const selected = String(selectedValue || "").trim();
    const values = unidadesMedida.length ? unidadesMedida.slice() : [getUnidadMedidaDefault()];
    if (selected && !values.includes(selected)) {
      values.unshift(selected);
    }
    return values
      .map((value) => `<option value="${escapeHtml(value)}" ${value === selected ? "selected" : ""}>${escapeHtml(value)}</option>`)
      .join("");
  }

  function canEditDetalle() {
    return facturacionMode === "new" || facturacionMode === "loaded" || facturacionMode === "editing_saved";
  }

  function isDetalleDataRow(row) {
    return !!getQueryNode(row, ".detalle-desc");
  }

  function getDetalleRows() {
    return Array.from(detalleBody.querySelectorAll("tr")).filter((row) => isDetalleDataRow(row));
  }

  function updateDeleteLineButton() {
    btnBorrarLinea.disabled = !(canEditDetalle() && selectedDetalleRow && isDetalleDataRow(selectedDetalleRow));
  }

  function clearDetalleRowSelection() {
    if (selectedDetalleRow) {
      selectedDetalleRow.classList.remove("detalle-row-selected");
    }
    selectedDetalleRow = null;
    lineCommentField.value = "";
    lineCommentField.disabled = true;
    updateDeleteLineButton();
  }

  function selectDetalleRow(row) {
    if (!isDetalleDataRow(row)) {
      clearDetalleRowSelection();
      return;
    }
    if (selectedDetalleRow && selectedDetalleRow !== row) {
      selectedDetalleRow.classList.remove("detalle-row-selected");
    }
    selectedDetalleRow = row;
    selectedDetalleRow.classList.add("detalle-row-selected");
    lineCommentField.value = row.dataset.observacion || "";
    lineCommentField.disabled = !canEditDetalle();
    updateDeleteLineButton();
  }

  function updateTotalsFromDetalle() {
    let subtotal = 0;
    let totalDesc = 0;
    getDetalleRows().forEach((row) => {
      const grossValue = parseNum(getQueryText(row, "[data-col='valor']"));
      const porcDesc = clampPercent(getQueryValue(row, ".detalle-porc-desc"));
      subtotal += grossValue;
      totalDesc += grossValue * (porcDesc / 100);
    });
    const impuesto = parseNum(fieldImpuesto.value);
    const totalDoc = subtotal - totalDesc + impuesto;
    fieldSubtotal.value = fmtNum(subtotal, 2);
    fieldTotalDesc.value = fmtNum(totalDesc, 2);
    fieldTotalDoc.value = fmtNum(totalDoc, 2);
    fieldPagado.value = "0.00";
    fieldBalance.value = fmtNum(totalDoc, 2);
  }

  function syncComentarioFromDetalle() {
    const names = [];
    getDetalleRows().forEach((row) => {
      const idArticulo = String(getQueryValue(row, ".detalle-art") || "").trim();
      if (!idArticulo) {
        return;
      }
      const nombre = String(getQueryValue(row, ".detalle-desc") || "").trim();
      names.push(nombre || idArticulo);
    });
    fieldComentario.value = names.join(", ");
  }

  function updateRowCalculations(row) {
    const cantInput = row.querySelector(".detalle-cant");
    const precioInput = row.querySelector(".detalle-precio-unit");
    if (!cantInput || !precioInput) {
      return;
    }
    const cantidad = parseNum(cantInput.value) || 0;
    const precio = parseNum(precioInput.value) || 0;
    const tdCantEmp = row.querySelector("[data-col='cant_emp']");
    const tdPrecioBruto = row.querySelector("[data-col='precio_bruto']");
    const tdValor = row.querySelector("[data-col='valor']");
    if (tdCantEmp) tdCantEmp.textContent = fmtNum(cantidad, 2);
    if (tdPrecioBruto) tdPrecioBruto.textContent = fmtNum(precio, 2);
    if (tdValor) tdValor.textContent = fmtNum(cantidad * precio, 2);
    updateTotalsFromDetalle();
    syncComentarioFromDetalle();
  }

  function buildEditableDetalleRowHtml(data = {}) {
    const cantidad = parseNum(data.cantidad || 1) || 1;
    const precio = parseNum(data.precio_unit || 0);
    const valor = cantidad * precio;
    return `
      <tr data-id-detalle="${escapeHtml(data.id_detalle == null ? "" : String(data.id_detalle))}" data-observacion="${escapeHtml(data.observacion || "")}">
        <td class="facturacion-edit-cell"><input class="detalle-desc" type="text" value="${escapeHtml(data.descrip_art || "")}" /></td>
        <td class="facturacion-edit-cell"><input class="detalle-art" type="text" value="${escapeHtml(data.id_articulo || "")}" readonly /></td>
        <td data-col="cant_emp">${escapeHtml(fmtNum(data.cant_emp == null ? cantidad : data.cant_emp, 2))}</td>
        <td class="facturacion-edit-cell"><input class="detalle-cant" type="text" inputmode="decimal" value="${escapeHtml(fmtNum(cantidad, 2))}" /></td>
        <td>${escapeHtml(fmtNum(data.entregado == null ? cantidad : data.entregado, 2))}</td>
        <td class="facturacion-edit-cell"><select class="detalle-uom">${renderUnidadMedidaOptions(data.uom || getUnidadMedidaDefault())}</select></td>
        <td>${escapeHtml(String(data.alm == null || data.alm === "" ? "1" : data.alm))}</td>
        <td class="facturacion-edit-cell">
          <div class="cell-picker">
            <input class="detalle-proyecto" type="text" value="${escapeHtml(data.proyecto || "P01")}" readonly />
            <button type="button" class="cell-pick-btn detalle-pick-proyecto">...</button>
          </div>
        </td>
        <td class="facturacion-edit-cell">
          <div class="cell-picker">
            <input class="detalle-cebe" type="text" value="${escapeHtml(data.cebe || "C01")}" readonly />
            <button type="button" class="cell-pick-btn detalle-pick-cebe">...</button>
          </div>
        </td>
        <td class="facturacion-edit-cell"><input class="detalle-precio-unit" type="text" inputmode="decimal" value="${escapeHtml(fmtNum(precio, 2))}" /></td>
        <td data-col="precio_bruto">${escapeHtml(fmtNum(data.precio_bruto == null ? precio : data.precio_bruto, 2))}</td>
        <td data-col="valor">${escapeHtml(fmtNum(data.valor == null ? valor : data.valor, 2))}</td>
        <td class="facturacion-edit-cell"><input class="detalle-porc-desc" type="text" inputmode="decimal" value="${escapeHtml(fmtNum(data.porc_desc || 0, 2))}" /></td>
        <td data-col="id_itbis">${escapeHtml(String(data.id_itbis == null ? "" : data.id_itbis))}</td>
      </tr>
    `;
  }

  function applyDetalleEditableAvailability() {
    const canEdit = canEditDetalle() && hasSelectedCliente();
    getDetalleRows().forEach((row) => {
      const hasArticulo = !!String(getQueryValue(row, ".detalle-art") || "").trim();
      row.querySelector(".detalle-desc").disabled = !canEdit;
      row.querySelector(".detalle-cant").disabled = !canEdit || !hasArticulo;
      row.querySelector(".detalle-uom").disabled = !canEdit || !hasArticulo;
      row.querySelector(".detalle-precio-unit").disabled = !canEdit || !hasArticulo;
      row.querySelector(".detalle-porc-desc").disabled = !canEdit || !hasArticulo;
      row.querySelector(".detalle-proyecto").disabled = true;
      row.querySelector(".detalle-cebe").disabled = true;
      row.querySelector(".detalle-pick-proyecto").disabled = !canEdit || !hasArticulo;
      row.querySelector(".detalle-pick-cebe").disabled = !canEdit || !hasArticulo;
    });
    if (!canEdit) {
      lineCommentField.disabled = true;
    } else if (selectedDetalleRow) {
      lineCommentField.disabled = false;
    }
    updateDeleteLineButton();
  }

  function attachDetalleEditableRowBehavior(row) {
    const descInput = row.querySelector(".detalle-desc");
    const artInput = row.querySelector(".detalle-art");
    const cantInput = row.querySelector(".detalle-cant");
    const uomInput = row.querySelector(".detalle-uom");
    const precioInput = row.querySelector(".detalle-precio-unit");
    const porcDescInput = row.querySelector(".detalle-porc-desc");
    const proyectoInput = row.querySelector(".detalle-proyecto");
    const cebeInput = row.querySelector(".detalle-cebe");
    const btnPickProyecto = row.querySelector(".detalle-pick-proyecto");
    const btnPickCebe = row.querySelector(".detalle-pick-cebe");

    row.addEventListener("click", () => selectDetalleRow(row));
    descInput.addEventListener("dblclick", () => {
      if (!descInput.disabled) {
        openArticuloModal(row, descInput.value || "");
      }
    });
    descInput.addEventListener("input", () => {
      syncComentarioFromDetalle();
    });
    descInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        if (!descInput.disabled) {
          openArticuloModal(row, descInput.value || "");
        }
      }
    });
    cantInput.addEventListener("input", () => {
      cantInput.value = sanitizeDecimalInput(cantInput.value);
      updateRowCalculations(row);
    });
    precioInput.addEventListener("input", () => {
      precioInput.value = sanitizeDecimalInput(precioInput.value);
      updateRowCalculations(row);
    });
    porcDescInput.addEventListener("input", () => {
      porcDescInput.value = sanitizeDecimalInput(porcDescInput.value);
      const clamped = clampPercent(porcDescInput.value);
      porcDescInput.value = clamped === 0 && porcDescInput.value === "" ? "" : String(clamped);
      updateTotalsFromDetalle();
    });
    cantInput.addEventListener("blur", () => {
      cantInput.value = formatDecimal2(cantInput.value || "1");
      updateRowCalculations(row);
    });
    precioInput.addEventListener("blur", () => {
      precioInput.value = formatDecimal2(precioInput.value);
      updateRowCalculations(row);
    });
    porcDescInput.addEventListener("blur", () => {
      porcDescInput.value = fmtNum(clampPercent(porcDescInput.value), 2);
      updateTotalsFromDetalle();
    });
    btnPickProyecto.addEventListener("click", () => {
      if (!btnPickProyecto.disabled) {
        openDetalleCodigoModal("proyecto", proyectoInput);
      }
    });
    btnPickCebe.addEventListener("click", () => {
      if (!btnPickCebe.disabled) {
        openDetalleCodigoModal("cebe", cebeInput);
      }
    });

    [cantInput, uomInput, precioInput, porcDescInput].forEach((input, index, allInputs) => {
      input.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") {
          return;
        }
        event.preventDefault();
        if (!artInput.value.trim()) {
          descInput.focus();
          return;
        }
        const next = allInputs[index + 1];
        if (next) {
          next.focus();
          selectIfPossible(next);
          return;
        }
        ensureTrailingEmptyRow();
      });
    });
  }

  function addEmptyDetalleRow() {
    if (!hasSelectedCliente()) {
      setDetallePlaceholder("Carga un cliente para comenzar el detalle.");
      return;
    }
    const hasOnlyPlaceholder = !getDetalleRows().length;
    if (hasOnlyPlaceholder) {
      detalleBody.innerHTML = "";
    }
    detalleBody.insertAdjacentHTML("beforeend", buildEditableDetalleRowHtml({}));
    const row = detalleBody.lastElementChild;
    if (row) {
      attachDetalleEditableRowBehavior(row);
      applyDetalleEditableAvailability();
      selectDetalleRow(row);
      focusIfPossible(row.querySelector(".detalle-desc"));
    }
    updateTotalsFromDetalle();
    syncComentarioFromDetalle();
  }

  function ensureTrailingEmptyRow() {
    const emptyRow = getDetalleRows().find((row) => {
      const desc = String(getQueryValue(row, ".detalle-desc") || "").trim();
      const art = String(getQueryValue(row, ".detalle-art") || "").trim();
      return !desc && !art;
    });
    if (emptyRow) {
      selectDetalleRow(emptyRow);
      focusIfPossible(emptyRow.querySelector(".detalle-desc"));
      return;
    }
    addEmptyDetalleRow();
  }

  async function renderEditableDetalleRows(rows) {
    await cargarUnidadesMedida();
    const normalizedRows = Array.isArray(rows) ? rows : [];
    if (!normalizedRows.length) {
      if (!hasSelectedCliente()) {
        setDetallePlaceholder("Carga un cliente para comenzar el detalle.");
        syncComentarioFromDetalle();
        return;
      }
      detalleBody.innerHTML = "";
      addEmptyDetalleRow();
      syncComentarioFromDetalle();
      return;
    }
    detalleBody.innerHTML = normalizedRows.map((row) => buildEditableDetalleRowHtml(row)).join("");
    getDetalleRows().forEach((row) => attachDetalleEditableRowBehavior(row));
    applyDetalleEditableAvailability();
    updateTotalsFromDetalle();
    syncComentarioFromDetalle();
    selectDetalleRow(getDetalleRows()[0] || null);
  }

  async function applyArticuloToFacturaRow(row, data) {
    if (!row || !data) {
      return;
    }
    await cargarUnidadesMedida();
    row.querySelector(".detalle-desc").value = data.descrip_art || "";
    row.querySelector(".detalle-art").value = data.id_articulo || "";
    row.querySelector(".detalle-uom").innerHTML = renderUnidadMedidaOptions(data.um_inv || getUnidadMedidaDefault());
    row.querySelector(".detalle-precio-unit").value = fmtNum(data.precio_det || 0, 2);
    row.querySelector("[data-col='id_itbis']").textContent = String(data.id_impto_vt || "");
    updateRowCalculations(row);
    applyDetalleEditableAvailability();
    selectDetalleRow(row);
    syncComentarioFromDetalle();
    const cantInput = row.querySelector(".detalle-cant");
    cantInput.focus();
    selectIfPossible(cantInput);
  }

  function collectDetallePayload() {
    return getDetalleRows()
      .map((row) => {
        const idArticulo = String(getQueryValue(row, ".detalle-art") || "").trim();
        const descripArt = String(getQueryValue(row, ".detalle-desc") || "").trim();
        if (!idArticulo && !descripArt) {
          return null;
        }
        return {
          id_detalle: (row.dataset.idDetalle || "").trim() || null,
          descrip_art: descripArt,
          id_articulo: idArticulo,
          cant_emp: parseNum(getQueryText(row, "[data-col='cant_emp']")),
          cantidad: parseNum(getQueryValue(row, ".detalle-cant")),
          entregado: parseNum(getChildText(row, 4)),
          uom: String(getQueryValue(row, ".detalle-uom") || "").trim(),
          alm: String(getChildText(row, 6) || "").trim(),
          proyecto: String(getQueryValue(row, ".detalle-proyecto") || "").trim(),
          cebe: String(getQueryValue(row, ".detalle-cebe") || "").trim(),
          precio_unit: parseNum(getQueryValue(row, ".detalle-precio-unit")),
          precio_bruto: parseNum(getQueryText(row, "[data-col='precio_bruto']")),
          valor: parseNum(getQueryText(row, "[data-col='valor']")),
          porc_desc: parseNum(getQueryValue(row, ".detalle-porc-desc")),
          id_itbis: String(getQueryText(row, "[data-col='id_itbis']") || "").trim(),
          observacion: row.dataset.observacion || "",
        };
      })
      .filter(Boolean);
  }

  function collectFacturaPayload() {
    return {
      factura_id: facturacionMode === "editing_saved" ? (activeFacturaId || fieldNoDoc.value || "") : "",
      prefactura_id: activePrefId || "",
      fecha_cont: fieldFechaCont.value || "",
      fecha_venc: fieldFechaVenc.value || "",
      fecha_doc: fieldFechaDoc.value || "",
      id_sn: fieldIdSn.value || "",
      nom_socio: fieldNomSocio.value || "",
      rnc_ced: fieldRncCed.value || "",
      contacto: fieldContacto.value || "",
      ent_factura: fieldDirFactura.value || fieldDireccion.value || "",
      ent_mercancia: fieldDirMercancia.value || "",
      comentario: fieldComentario.value || "",
      comentario_linea: lineCommentField.value || "",
      subtotal: parseNum(fieldSubtotal.value),
      total_desc: parseNum(fieldTotalDesc.value),
      impuesto: parseNum(fieldImpuesto.value),
      total_doc: parseNum(fieldTotalDoc.value),
      id_condicion: fieldIdCondicion.value || "",
      dia: fieldDias.value || "",
      condicion: fieldCondicionDesc.value || "",
      id_precio: fieldIdPrecio.value || "",
      detalles: collectDetallePayload(),
    };
  }

  async function loadPrefactura(idDoc) {
    const prefacturaId = String(idDoc || "").trim();
    if (!prefacturaId) {
      return;
    }
    activePrefId = prefacturaId;
    activeFacturaId = "";
    activeFacturaEditable = false;
    activeFacturaPrintUrl = "";
    updatePrintButton();
    setStatus("Cargando prefactura seleccionada...");
    setDetallePlaceholder("Cargando detalle...");
    try {
      const res = await fetch(`${config.prefDetailUrl}?id_doc=${encodeURIComponent(prefacturaId)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        setInitialState(false);
        setStatus("No se pudo cargar la prefactura seleccionada.", "err");
        return;
      }
      const data = await res.json().catch(() => ({}));
      const pref = data.prefactura || {};
      const cliente = await fetchClienteDetalle(pref.id_sn || "");
      fillFromPrefactura(pref, cliente);
      await renderEditableDetalleRows(data.detalles || []);
      setLoadedPrefState();
      prefResultsBody.querySelectorAll(".facturacion-pref-row").forEach((row) => {
        row.classList.toggle("active", (row.dataset.idDoc || "") === prefacturaId);
      });
    } catch (error) {
      setInitialState(false);
      setStatus("Error de conexion al cargar la prefactura.", "err");
    }
  }

  async function guardarFactura() {
    if (!fieldIdSn.value.trim()) {
      setStatus("Debes seleccionar un cliente antes de grabar.", "err");
      return;
    }
    const payload = collectFacturaPayload();
    if (!payload.detalles.length) {
      setStatus("Debes agregar al menos un articulo.", "err");
      return;
    }
    const editingExisting = facturacionMode === "editing_saved" && !!(payload.factura_id || activeFacturaId);
    btnGrabar.disabled = true;
    if (editingExisting) {
      setStatus(`Actualizando factura ${payload.factura_id || activeFacturaId}...`);
    } else {
      setStatus(activePrefId ? "Procesando factura desde prefactura..." : "Grabando factura manual...");
    }
    try {
      const res = await fetch(config.emitirFacturaManualUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken") || config.csrfToken || "",
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (data.factura_id) {
          fieldNoDoc.value = data.factura_id || "";
          fieldEstDoc.value = "Facturada";
          activeFacturaPrintUrl = data.print_url || activeFacturaPrintUrl;
          updatePrintButton();
        }
        btnGrabar.disabled = false;
        setStatus(data.detail || "No se pudo grabar la factura.", "err");
        return;
      }
      activeFacturaId = data.factura_id || activeFacturaId || "";
      fieldNoDoc.value = data.factura_id || "";
      fieldEstDoc.value = "Abierto";
      activeFacturaPrintUrl = data.print_url || "";
      updatePrintButton();
      setSavedState();
      await fetchPrefacturas();
      setStatus("");
      if (activeFacturaPrintUrl) {
        openPrintModal(activeFacturaPrintUrl, data.factura_id || activeFacturaId || fieldNoDoc.value || "");
      }
    } catch (error) {
      btnGrabar.disabled = false;
      setStatus("Error de conexion al grabar la factura.", "err");
    }
  }

  function openHistoryModal() {
    historyBackdrop.classList.add("open");
    historyBackdrop.setAttribute("aria-hidden", "false");
    lockPageScroll();
    fetchFacturasEmitidas();
  }

  function closeHistoryModal() {
    historyBackdrop.classList.remove("open");
    historyBackdrop.setAttribute("aria-hidden", "true");
    unlockPageScroll();
  }

  async function loadFacturaEmitida(idDoc) {
    const facturaId = String(idDoc || "").trim();
    if (!facturaId) {
      return;
    }
    activeFacturaId = facturaId;
    activeFacturaEditable = false;
    activeFacturaPrintUrl = "";
    updatePrintButton();
    setStatus("Cargando factura seleccionada...");
    setDetallePlaceholder("Cargando detalle...");
    try {
      const res = await fetch(`${config.facturaDetalleUrl}?id_doc=${encodeURIComponent(facturaId)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        setStatus("No se pudo cargar la factura seleccionada.", "err");
        return;
      }
      const data = await res.json().catch(() => ({}));
      const factura = data.factura || {};
      const cliente = factura.id_sn ? await fetchClienteDetalle(factura.id_sn) : null;
      clearPrefSelection();
      fillFromFactura(factura, cliente);
      await renderEditableDetalleRows(data.detalles || []);
      activeFacturaPrintUrl = factura.print_url || "";
      if (factura.editable) {
        setEditableSavedState();
      } else {
        setSavedState();
      }
      closeHistoryModal();
      activateTab("facturacion_tab_detalle");
    } catch (error) {
      setStatus("Error de conexion al cargar la factura.", "err");
    }
  }

  function canOpenFacturaCancelMenu() {
    const facturaId = String(activeFacturaId || fieldNoDoc.value || "").trim();
    const estado = String(fieldEstDoc.value || "").trim().toUpperCase();
    return !!facturaId && estado === "ABIERTO";
  }

  function openFacturaCancelMenu(event) {
    if (!canOpenFacturaCancelMenu()) {
      hideEstadoContextMenu();
      return;
    }
    if (event && typeof event.preventDefault === "function") {
      event.preventDefault();
    }
    if (event && typeof event.stopPropagation === "function") {
      event.stopPropagation();
    }
    showEstadoContextMenu(event);
  }

  async function requestCancelCurrentFactura() {
    const facturaId = String(activeFacturaId || fieldNoDoc.value || "").trim();
    const facturaLabel = String(fieldNoDoc.value || activeFacturaId || "").trim();
    if (!facturaId) {
      await showAlert("No se pudo identificar la factura a cancelar.");
      return false;
    }
    const estadoActual = String(fieldEstDoc.value || "").trim().toUpperCase();
    if (estadoActual !== "ABIERTO") {
      await showAlert("Solo las facturas abiertas se pueden cancelar.");
      return false;
    }
    const confirmed = await showConfirm(
      `Se cancelara la factura ${facturaLabel || facturaId}. Esta accion revertira los movimientos contables y devolvera el stock. Deseas continuar?`
    );
    if (!confirmed) {
      return false;
    }

    try {
      const res = await fetch(config.cancelarFacturaManualUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCookie("csrftoken") || config.csrfToken || "",
        },
        body: JSON.stringify({
          factura_id: facturaId,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        await showAlert(data.detail || "No se pudo cancelar la factura.");
        return false;
      }
      await loadFacturaEmitida(facturaId);
      await fetchPrefacturas();
      await showAlert(data.detail || `La factura ${facturaLabel || facturaId} fue cancelada correctamente.`);
      return true;
    } catch (error) {
      await showAlert("Error de conexion cancelando la factura.");
      return false;
    }
  }

  function renderFacturasEmitidas(rows) {
    if (!Array.isArray(rows) || !rows.length) {
      historyResultsBody.innerHTML = '<tr><td colspan="6" class="result-empty">No se encontraron facturas emitidas.</td></tr>';
      return;
    }
    historyResultsBody.innerHTML = rows.map((row) => `
      <tr class="click-row" data-id-doc="${escapeHtml(row.id_doc || "")}">
        <td>${escapeHtml(row.id_doc || "")}</td>
        <td>${escapeHtml(row.id_sn || "")}</td>
        <td title="${escapeHtml(row.nom_socio || "")}">${escapeHtml(row.nom_socio || "")}</td>
        <td>${escapeHtml(row.fecha_doc || "")}</td>
        <td>${escapeHtml(formatDecimal(row.total_doc || 0))}</td>
        <td>${escapeHtml(row.id_doc_pv || "-")}</td>
      </tr>
    `).join("");
    historyResultsBody.querySelectorAll("tr[data-id-doc]").forEach((row) => {
      row.addEventListener("click", () => {
        const facturaId = row.dataset.idDoc || "";
        if (facturaId) {
          loadFacturaEmitida(facturaId);
        }
      });
    });
  }

  async function fetchFacturasEmitidas() {
    const q = (historySearchInput.value || "").trim();
    const filtro = (historySearchFilter.value || "documento").trim();
    historyResultsBody.innerHTML = '<tr><td colspan="6" class="result-empty">Buscando facturas...</td></tr>';
    try {
      const res = await fetch(`${config.facturasBuscarUrl}?modo=manual&q=${encodeURIComponent(q)}&filtro=${encodeURIComponent(filtro)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        historyResultsBody.innerHTML = '<tr><td colspan="6" class="result-empty">No se pudo cargar la lista.</td></tr>';
        return;
      }
      const data = await res.json().catch(() => ({}));
      renderFacturasEmitidas(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      historyResultsBody.innerHTML = '<tr><td colspan="6" class="result-empty">Error de conexion.</td></tr>';
    }
  }

  function openClienteModal() {
    clienteBackdrop.classList.add("open");
    clienteBackdrop.setAttribute("aria-hidden", "false");
    lockPageScroll();
    clienteSearchInput.focus();
    fetchClientes();
  }

  function closeClienteModal() {
    clienteBackdrop.classList.remove("open");
    clienteBackdrop.setAttribute("aria-hidden", "true");
    unlockPageScroll();
  }

  function renderClienteResults(rows) {
    if (!rows.length) {
      clienteResultsBody.innerHTML = "<tr><td colspan='6' class='result-empty'>No se encontraron clientes.</td></tr>";
      return;
    }
    clienteResultsBody.innerHTML = rows.map((row) => `
      <tr class="click-row" data-id-sn="${escapeHtml(row.id_sn || "")}">
        <td>${escapeHtml(row.id_sn || "")}</td>
        <td>${escapeHtml(row.nom_socio || "")}</td>
        <td>${escapeHtml(row.rnc_ced || "")}</td>
        <td>${escapeHtml(row.contacto || "")}</td>
        <td>${escapeHtml(row.dir_factura || "")}</td>
        <td>${escapeHtml(row.tel1 || "")}</td>
      </tr>
    `).join("");
    clienteResultsBody.querySelectorAll("tr[data-id-sn]").forEach((row) => {
      row.addEventListener("click", async () => {
        const idSn = row.dataset.idSn || "";
        const cliente = await fetchClienteDetalle(idSn);
        if (!cliente) {
          setStatus("No se pudo cargar el cliente seleccionado.", "err");
          return;
        }
        fillClienteFields(cliente);
        closeClienteModal();
        activateTab("facturacion_tab_detalle");
        if (!getDetalleRows().length) {
          await renderEditableDetalleRows([]);
        }
      });
    });
  }

  async function fetchClientes() {
    const q = (clienteSearchInput.value || "").trim();
    const filtro = (clienteSearchFilter.value || "nombre").trim();
    clienteResultsBody.innerHTML = "<tr><td colspan='6' class='result-empty'>Buscando...</td></tr>";
    try {
      const res = await fetch(`${config.clienteBuscarUrl}?q=${encodeURIComponent(q)}&filtro=${encodeURIComponent(filtro)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        clienteResultsBody.innerHTML = "<tr><td colspan='6' class='result-empty'>No se pudo consultar clientes.</td></tr>";
        return;
      }
      const data = await res.json().catch(() => ({}));
      renderClienteResults(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      clienteResultsBody.innerHTML = "<tr><td colspan='6' class='result-empty'>Error de conexion.</td></tr>";
    }
  }

  function renderDetalleCodigoResults(rows) {
    if (!rows.length) {
      detalleCodigoResultsBody.innerHTML = "<tr><td colspan='2' class='result-empty'>No se encontraron registros.</td></tr>";
      return;
    }
    detalleCodigoResultsBody.innerHTML = rows.map((row) => `
      <tr class="click-row" data-value="${escapeHtml(String(row.codigo || ""))}">
        <td>${escapeHtml(String(row.codigo || ""))}</td>
        <td>${escapeHtml(String(row.descripcion || ""))}</td>
      </tr>
    `).join("");
    detalleCodigoResultsBody.querySelectorAll("tr[data-value]").forEach((row) => {
      row.addEventListener("click", () => {
        if (detalleCodigoTargetInput) {
          detalleCodigoTargetInput.value = row.dataset.value || "";
        }
        closeDetalleCodigoModal();
      });
    });
  }

  async function fetchDetalleCodigoOptions(query = "") {
    const baseUrl = detalleCodigoMode === "cebe" ? config.cebesBuscarUrl : config.proyectosBuscarUrl;
    detalleCodigoResultsBody.innerHTML = "<tr><td colspan='2' class='result-empty'>Cargando...</td></tr>";
    try {
      const res = await fetch(`${baseUrl}?q=${encodeURIComponent(query)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        detalleCodigoResultsBody.innerHTML = "<tr><td colspan='2' class='result-empty'>No se pudo consultar.</td></tr>";
        return;
      }
      const data = await res.json().catch(() => ({}));
      renderDetalleCodigoResults(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      detalleCodigoResultsBody.innerHTML = "<tr><td colspan='2' class='result-empty'>Error de conexion.</td></tr>";
    }
  }

  function openDetalleCodigoModal(mode, targetInput) {
    detalleCodigoMode = mode === "cebe" ? "cebe" : "proyecto";
    detalleCodigoTargetInput = targetInput || null;
    detalleCodigoTitle.textContent = detalleCodigoMode === "cebe" ? "Seleccionar CeBe" : "Seleccionar Proyecto";
    detalleCodigoSearchInput.value = "";
    detalleCodigoBackdrop.classList.add("open");
    detalleCodigoBackdrop.setAttribute("aria-hidden", "false");
    lockPageScroll();
    fetchDetalleCodigoOptions("");
    detalleCodigoSearchInput.focus();
  }

  function closeDetalleCodigoModal() {
    detalleCodigoBackdrop.classList.remove("open");
    detalleCodigoBackdrop.setAttribute("aria-hidden", "true");
    detalleCodigoMode = "";
    detalleCodigoTargetInput = null;
    unlockPageScroll();
  }

  function openArticuloModal(targetRow, initialQuery = "") {
    articuloTargetRow = targetRow || null;
    articuloBackdrop.classList.add("open");
    articuloBackdrop.setAttribute("aria-hidden", "false");
    lockPageScroll();
    articuloSearchInput.value = initialQuery || "";
    articuloSearchFilter.value = "descripcion";
    fetchArticulos();
    articuloSearchInput.focus();
  }

  function closeArticuloModal() {
    articuloBackdrop.classList.remove("open");
    articuloBackdrop.setAttribute("aria-hidden", "true");
    articuloTargetRow = null;
    unlockPageScroll();
  }

  function renderArticulosResults(rows) {
    if (!rows.length) {
      articuloResultsBody.innerHTML = "<tr><td colspan='4' class='result-empty'>No se encontraron articulos.</td></tr>";
      return;
    }
    articuloResultsBody.innerHTML = rows.map((row) => `
      <tr class="click-row" data-row="${encodeURIComponent(JSON.stringify(row))}">
        <td>${escapeHtml(row.referencia || row.id_articulo || "")}</td>
        <td>${escapeHtml(row.descrip_art || "")}</td>
        <td>${escapeHtml(fmtNum(row.precio_det || 0, 2))}</td>
        <td>${escapeHtml(fmtNum(row.stock || 0, 2))}</td>
      </tr>
    `).join("");
    articuloResultsBody.querySelectorAll("tr[data-row]").forEach((row) => {
      row.addEventListener("click", async () => {
        if (!articuloTargetRow) {
          return;
        }
        const data = JSON.parse(decodeURIComponent(row.dataset.row || "{}"));
        await applyArticuloToFacturaRow(articuloTargetRow, data);
        closeArticuloModal();
      });
    });
  }

  async function fetchArticulos() {
    const q = (articuloSearchInput.value || "").trim();
    const filtro = (articuloSearchFilter.value || "descripcion").trim();
    articuloResultsBody.innerHTML = "<tr><td colspan='4' class='result-empty'>Buscando...</td></tr>";
    try {
      const res = await fetch(`${config.articuloBuscarUrl}?q=${encodeURIComponent(q)}&filtro=${encodeURIComponent(filtro)}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!res.ok) {
        articuloResultsBody.innerHTML = "<tr><td colspan='4' class='result-empty'>No se pudo consultar articulos.</td></tr>";
        return;
      }
      const data = await res.json().catch(() => ({}));
      renderArticulosResults(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      articuloResultsBody.innerHTML = "<tr><td colspan='4' class='result-empty'>Error de conexion.</td></tr>";
    }
  }

  btnPrefBuscar.addEventListener("click", fetchPrefacturas);
  prefSearchInput.addEventListener("input", () => {
    clearTimeout(prefSearchTimer);
    prefSearchTimer = setTimeout(fetchPrefacturas, 260);
  });
  prefSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      fetchPrefacturas();
    }
  });
  prefSearchFilter.addEventListener("change", fetchPrefacturas);

  btnNuevo.addEventListener("click", async () => {
    setNewState();
    btnCargarCliente.focus();
  });
  btnBuscar.addEventListener("click", openHistoryModal);
  btnCancel.addEventListener("click", () => setInitialState());
  btnGrabar.addEventListener("click", guardarFactura);
  if (btnImprimir) {
    btnImprimir.addEventListener("click", () => {
      if (activeFacturaPrintUrl) {
        openPrintModal(activeFacturaPrintUrl, activeFacturaId || fieldNoDoc.value || "");
      }
    });
  }
  btnCargarCliente.addEventListener("click", () => {
    if (!btnCargarCliente.disabled) {
      openClienteModal();
    }
  });
  btnShortcutCxc?.addEventListener("click", () => {
    openShortcut("cuentas_por_cobrar", "No tienes permiso para acceder a Cuentas por cobrar.");
  });
  btnShortcutFinanc?.addEventListener("click", () => {
    openShortcut("financiamiento", "No tienes permiso para acceder a Financiamiento.");
  });
  btnShortcutPref?.addEventListener("click", () => {
    openShortcut("prefactura", "No tienes permiso para acceder a Prefactura.");
  });
  btnBorrarLinea.addEventListener("click", () => {
    if (!selectedDetalleRow || !isDetalleDataRow(selectedDetalleRow)) {
      return;
    }
    const rowToRemove = selectedDetalleRow;
    clearDetalleRowSelection();
    rowToRemove.remove();
    if (!getDetalleRows().length && canEditDetalle()) {
      addEmptyDetalleRow();
    } else {
      selectDetalleRow(getDetalleRows()[0] || null);
      updateTotalsFromDetalle();
      applyDetalleEditableAvailability();
    }
    syncComentarioFromDetalle();
  });

  btnCloseHistory.addEventListener("click", closeHistoryModal);
  historyBackdrop.addEventListener("click", (event) => {
    if (event.target === historyBackdrop) {
      closeHistoryModal();
    }
  });
  if (btnAlertClose) {
    btnAlertClose.addEventListener("click", closeAlert);
  }
  if (btnAlertOk) {
    btnAlertOk.addEventListener("click", closeAlert);
  }
  if (alertBackdrop) {
    alertBackdrop.addEventListener("click", (event) => {
      if (event.target === alertBackdrop) {
        closeAlert();
      }
    });
  }
  if (btnConfirmClose) {
    btnConfirmClose.addEventListener("click", () => closeConfirm(false));
  }
  if (btnConfirmCancel) {
    btnConfirmCancel.addEventListener("click", () => closeConfirm(false));
  }
  if (btnConfirmOk) {
    btnConfirmOk.addEventListener("click", () => closeConfirm(true));
  }
  if (confirmBackdrop) {
    confirmBackdrop.addEventListener("click", (event) => {
      if (event.target === confirmBackdrop) {
        closeConfirm(false);
      }
    });
  }
  if (btnClosePrint) {
    btnClosePrint.addEventListener("click", closePrintModal);
  }
  if (btnPrintCancel) {
    btnPrintCancel.addEventListener("click", closePrintModal);
  }
  if (btnPrintConfirm) {
    btnPrintConfirm.addEventListener("click", () => {
      const targetUrl = printPendingUrl;
      const copies = fieldPrintCopies?.value;
      closePrintModal();
      if (targetUrl) {
        void printFacturaDirectly(targetUrl, copies);
      }
    });
  }
  if (fieldPrintCopies) {
    fieldPrintCopies.addEventListener("input", syncPrintModalSummary);
    fieldPrintCopies.addEventListener("blur", syncPrintModalSummary);
    fieldPrintCopies.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        btnPrintConfirm?.click();
      }
    });
  }
  if (printBackdrop) {
    printBackdrop.addEventListener("click", (event) => {
      if (event.target === printBackdrop) {
        closePrintModal();
      }
    });
  }
  btnHistoryBuscar.addEventListener("click", fetchFacturasEmitidas);
  historySearchInput.addEventListener("input", () => {
    clearTimeout(historySearchTimer);
    historySearchTimer = setTimeout(fetchFacturasEmitidas, 260);
  });
  historySearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      fetchFacturasEmitidas();
    }
  });
  historySearchFilter.addEventListener("change", fetchFacturasEmitidas);

  btnCloseCliente.addEventListener("click", closeClienteModal);
  clienteBackdrop.addEventListener("click", (event) => {
    if (event.target === clienteBackdrop) {
      closeClienteModal();
    }
  });
  clienteSearchInput.addEventListener("input", () => {
    clearTimeout(clienteSearchTimer);
    clienteSearchTimer = setTimeout(fetchClientes, 260);
  });
  clienteSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      fetchClientes();
    }
  });
  clienteSearchFilter.addEventListener("change", fetchClientes);

  btnCloseDetalleCodigo.addEventListener("click", closeDetalleCodigoModal);
  detalleCodigoBackdrop.addEventListener("click", (event) => {
    if (event.target === detalleCodigoBackdrop) {
      closeDetalleCodigoModal();
    }
  });
  detalleCodigoSearchInput.addEventListener("input", () => {
    clearTimeout(detalleCodigoTimer);
    detalleCodigoTimer = setTimeout(() => fetchDetalleCodigoOptions(detalleCodigoSearchInput.value || ""), 220);
  });
  detalleCodigoSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      fetchDetalleCodigoOptions(detalleCodigoSearchInput.value || "");
    }
  });

  btnCloseArticulo.addEventListener("click", closeArticuloModal);
  articuloBackdrop.addEventListener("click", (event) => {
    if (event.target === articuloBackdrop) {
      closeArticuloModal();
    }
  });
  articuloSearchInput.addEventListener("input", () => {
    clearTimeout(articuloSearchTimer);
    articuloSearchTimer = setTimeout(fetchArticulos, 260);
  });
  articuloSearchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      fetchArticulos();
    }
  });
  articuloSearchFilter.addEventListener("change", fetchArticulos);

  fieldEstDoc?.addEventListener("contextmenu", openFacturaCancelMenu);
  fieldEstDoc?.addEventListener("click", openFacturaCancelMenu);
  btnEstadoContextCancel?.addEventListener("click", async () => {
    hideEstadoContextMenu();
    await requestCancelCurrentFactura();
  });

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => activateTab(tab.dataset.target || "facturacion_tab_detalle"));
  });

  lineCommentField.addEventListener("input", () => {
    if (selectedDetalleRow) {
      selectedDetalleRow.dataset.observacion = lineCommentField.value || "";
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }
    hideEstadoContextMenu();
    if (confirmBackdrop && confirmBackdrop.classList.contains("open")) {
      closeConfirm(false);
      return;
    }
    if (alertBackdrop && alertBackdrop.classList.contains("open")) {
      closeAlert();
      return;
    }
    if (articuloBackdrop.classList.contains("open")) {
      closeArticuloModal();
      return;
    }
    if (detalleCodigoBackdrop.classList.contains("open")) {
      closeDetalleCodigoModal();
      return;
    }
    if (clienteBackdrop.classList.contains("open")) {
      closeClienteModal();
      return;
    }
    if (historyBackdrop.classList.contains("open")) {
      closeHistoryModal();
    }
  });

  document.addEventListener("click", (event) => {
    if (event.target === fieldEstDoc) {
      return;
    }
    if (estadoContextMenu && event.target && !estadoContextMenu.contains(event.target)) {
      hideEstadoContextMenu();
    }
  });
  document.addEventListener("scroll", () => {
    hideEstadoContextMenu();
  }, true);

  setInitialState();
  fetchPrefacturas();
})();
