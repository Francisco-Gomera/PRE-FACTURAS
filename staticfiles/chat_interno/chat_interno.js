(function () {
  var config = window.chatInternoConfig || {};
  var chatShell = document.getElementById("chat_shell");
  var roomsWrap = document.getElementById("chat_rooms");
  var roomSearch = document.getElementById("chat_room_search");
  var chatTitle = document.getElementById("chat_title");
  var chatSubtitle = document.getElementById("chat_subtitle");
  var chatHeadAvatar = document.getElementById("chat_head_avatar");
  var btnMobileBack = document.getElementById("btn_chat_mobile_back");
  var chatMessages = document.getElementById("chat_messages");
  var chatInput = document.getElementById("chat_input");
  var recordingStatus = document.getElementById("chat_recording_status");
  var recordingTime = document.getElementById("chat_recording_time");
  var recordingTitle = document.getElementById("chat_recording_title");
  var recordingSubtitle = document.getElementById("chat_recording_subtitle");
  var recordingActions = document.getElementById("chat_recording_actions");
  var btnVoice = document.getElementById("btn_chat_voice");
  var btnAttach = document.getElementById("btn_chat_attach");
  var btnShareRecord = document.getElementById("btn_chat_share_record");
  var attachInput = document.getElementById("chat_attach_input");
  var btnVoiceContinue = document.getElementById("btn_chat_voice_continue");
  var btnVoiceCancel = document.getElementById("btn_chat_voice_cancel");
  var btnVoiceSend = document.getElementById("btn_chat_voice_send");
  var btnEnviar = document.getElementById("btn_chat_enviar");
  var btnNuevoDirecto = document.getElementById("btn_chat_nuevo_directo");
  var btnNuevoGrupo = document.getElementById("btn_chat_nuevo_grupo");
  var modalDirecto = document.getElementById("chat_modal_directo");
  var modalGrupo = document.getElementById("chat_modal_grupo");
  var directSearch = document.getElementById("chat_direct_search");
  var directUsersWrap = document.getElementById("chat_direct_users");
  var directCancel = document.getElementById("chat_direct_cancel");
  var directCreate = document.getElementById("chat_direct_create");
  var groupName = document.getElementById("chat_group_name");
  var groupSearch = document.getElementById("chat_group_search");
  var groupUsersWrap = document.getElementById("chat_group_users");
  var groupCancel = document.getElementById("chat_group_cancel");
  var groupCreate = document.getElementById("chat_group_create");
  var modalShareRecord = document.getElementById("chat_modal_share_record");
  var shareType = document.getElementById("chat_share_type");
  var shareSearch = document.getElementById("chat_share_search");
  var shareResultsWrap = document.getElementById("chat_share_results");
  var shareCancel = document.getElementById("chat_share_cancel");
  var shareSend = document.getElementById("chat_share_send");

  var allRooms = [];
  var activeRoomId = 0;
  var roomSearchTimer = null;
  var directSearchTimer = null;
  var groupSearchTimer = null;
  var chatSocket = null;
  var chatSocketConnected = false;
  var chatSocketReconnectTimer = null;
  var chatSocketPingTimer = null;
  var deferredReadTimer = null;
  var messagesByRoom = {};
  var selectedDirectUserId = 0;
  var selectedGroupMemberIds = {};
  var typingByRoom = {};
  var typingTimersByRoom = {};
  var typingStopTimer = null;
  var typingHeartbeatTimer = null;
  var typingActiveSent = false;
  var typingRoomId = 0;
  var lastReadSentByRoom = {};
  var onlineUsers = {};
  var mediaRecorder = null;
  var mediaRecorderStream = null;
  var mediaRecorderChunks = [];
  var mediaRecorderStartedAt = 0;
  var mediaRecorderBaseDuration = 0;
  var mediaRecorderTimer = null;
  var mediaRecorderMaxTimer = null;
  var discardRecordedSegment = false;
  var voiceDraftParts = [];
  var voiceDraftDuration = 0;
  var voiceDraftMimeType = "";
  var shareSearchTimer = null;
  var selectedSharedRecord = null;
  var MAX_VOICE_SECONDS = 300;
  var MAX_ATTACHMENTS_BYTES = 10 * 1024 * 1024;
  var SHARED_RECORD_PREFIX = "__SHARED_RECORD__:";
  var initialRoomId = 0;
  try {
    initialRoomId = Number(new window.URLSearchParams(window.location.search).get("room") || 0);
  } catch (error) {
    initialRoomId = 0;
  }

  function getCsrfToken() {
    if (config.csrfToken) return config.csrfToken;
    var cookies = document.cookie ? document.cookie.split(";") : [];
    for (var i = 0; i < cookies.length; i += 1) {
      var cookie = cookies[i].trim();
      if (cookie.indexOf("csrftoken=") === 0) {
        return decodeURIComponent(cookie.slice("csrftoken=".length));
      }
    }
    return "";
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function roomDisplayName(room) {
    return String((room && room.nombre) || ("Chat " + (room && room.id_sala ? room.id_sala : "")));
  }

  function initials(name) {
    var text = String(name || "").trim();
    if (!text) return "?";
    var parts = text.split(/\s+/).filter(Boolean);
    if (parts.length === 1) return parts[0].slice(0, 1).toUpperCase();
    return (parts[0].slice(0, 1) + parts[1].slice(0, 1)).toUpperCase();
  }

  function humanTime(raw) {
    var text = String(raw || "").trim();
    if (!text) return "";
    var bits = text.split(" ");
    if (bits.length === 2) return bits[1].slice(0, 5);
    return text;
  }

  function formatDuration(totalSeconds) {
    var safe = Math.max(0, Number(totalSeconds || 0));
    var minutes = Math.floor(safe / 60);
    var seconds = Math.floor(safe % 60);
    return String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");
  }

  function formatBytes(totalBytes) {
    var size = Math.max(0, Number(totalBytes || 0));
    if (size >= 1024 * 1024) return (size / (1024 * 1024)).toFixed(size >= 5 * 1024 * 1024 ? 0 : 1) + " MB";
    if (size >= 1024) return Math.round(size / 1024) + " KB";
    return size + " B";
  }

  function isDirectRoom(room) {
    return String((room && room.tipo) || "").toUpperCase() === "DIRECTO";
  }

  function isUserOnline(userId) {
    return !!onlineUsers[String(Number(userId || 0))];
  }

  function setUserOnline(userId, isOnline) {
    var key = String(Number(userId || 0));
    if (key === "0") return;
    if (isOnline) {
      onlineUsers[key] = true;
      return;
    }
    delete onlineUsers[key];
  }

  function roomPartnerOnline(room) {
    if (!room || !isDirectRoom(room)) return false;
    var partnerId = Number(room.direct_partner_id || 0);
    if (partnerId <= 0) return false;
    return !!room.direct_partner_online || isUserOnline(partnerId);
  }

  function showRoomEmpty(message) {
    roomsWrap.innerHTML = '<div class="chat-empty">' + escapeHtml(message || "No hay chats disponibles.") + "</div>";
  }

  function showMessagesEmpty(message) {
    chatMessages.innerHTML = '<div class="chat-empty">' + escapeHtml(message || "Sin mensajes por ahora.") + "</div>";
  }

  function setComposerEnabled(enabled) {
    var canSend = !!enabled && !!config.permisos && !!config.permisos.enviar_mensajes;
    chatInput.disabled = !canSend;
    btnEnviar.disabled = !canSend;
    if (btnVoice) btnVoice.disabled = !canSend;
    if (btnAttach) btnAttach.disabled = !canSend;
    if (btnShareRecord) btnShareRecord.disabled = !canSend;
    renderVoiceComposerState();
  }

  function isMobileChatLayout() {
    try {
      return !!(window.matchMedia && window.matchMedia("(max-width: 980px)").matches);
    } catch (error) {
      return window.innerWidth <= 980;
    }
  }

  function syncMobileChatView() {
    if (!chatShell) return;
    var roomOpen = isMobileChatLayout() && Number(activeRoomId || 0) > 0;
    chatShell.classList.toggle("mobile-room-open", roomOpen);
  }

  function returnToRoomList() {
    if (!isMobileChatLayout()) return;
    activeRoomId = 0;
    setComposerEnabled(false);
    renderRooms();
    renderHeader();
    showMessagesEmpty("Selecciona un chat para empezar.");
    syncMobileChatView();
  }

  function attachmentKindLabel(kind, qty) {
    var count = Math.max(1, Number(qty || 1));
    if (kind === "image") return count === 1 ? "Imagen" : count + " imagenes";
    if (kind === "audio") return count === 1 ? "Audio" : count + " audios";
    if (kind === "video") return count === 1 ? "Video" : count + " videos";
    return count === 1 ? "Documento" : count + " documentos";
  }

  function detectAttachmentKind(file) {
    var type = String(file && file.type ? file.type : "").toLowerCase();
    var name = String(file && file.name ? file.name : "").toLowerCase();
    var ext = name.lastIndexOf(".") >= 0 ? name.slice(name.lastIndexOf(".")) : "";
    if (type.indexOf("image/") === 0 || [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"].indexOf(ext) >= 0) return "image";
    if (type.indexOf("audio/") === 0 || [".mp3", ".wav", ".ogg", ".m4a", ".aac", ".webm"].indexOf(ext) >= 0) return "audio";
    if (type.indexOf("video/") === 0 || [".mp4", ".webm", ".mov", ".avi", ".mkv", ".mpeg"].indexOf(ext) >= 0) return "video";
    if ([".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".ppt", ".pptx", ".zip", ".rar"].indexOf(ext) >= 0) return "document";
    return "";
  }

  function sortRoomsDesc(rows) {
    return (rows || []).slice().sort(function (a, b) {
      var aKey = String(a && a.actualizada_en ? a.actualizada_en : "");
      var bKey = String(b && b.actualizada_en ? b.actualizada_en : "");
      if (aKey === bKey) return Number(b.id_sala || 0) - Number(a.id_sala || 0);
      return aKey > bKey ? -1 : 1;
    });
  }

  function getRoomById(roomId) {
    return allRooms.find(function (room) {
      return Number(room.id_sala || 0) === Number(roomId || 0);
    }) || null;
  }

  function upsertRoom(room) {
    if (!room || !room.id_sala) return;
    if (room.direct_partner_id) {
      setUserOnline(room.direct_partner_id, !!room.direct_partner_online);
    }
    var exists = false;
    allRooms = allRooms.map(function (row) {
      if (Number(row.id_sala || 0) === Number(room.id_sala || 0)) {
        exists = true;
        return Object.assign({}, row, room);
      }
      return row;
    });
    if (!exists) allRooms.push(room);
    allRooms = sortRoomsDesc(allRooms);
  }

  function syncRoomPresenceFromUsers() {
    allRooms = allRooms.map(function (room) {
      if (!isDirectRoom(room)) return room;
      return Object.assign({}, room, {
        direct_partner_online: isUserOnline(room.direct_partner_id),
      });
    });
  }

  function roomTypingData(roomId) {
    var key = String(roomId || 0);
    var data = typingByRoom[key];
    if (!data) return null;
    if (Date.now() > Number(data.expiresAt || 0)) {
      delete typingByRoom[key];
      return null;
    }
    return data;
  }

  function setRoomTyping(roomId, payload) {
    var key = String(roomId || 0);
    if (!roomId) return;
    if (!payload || !payload.is_typing) {
      delete typingByRoom[key];
      if (typingTimersByRoom[key]) clearTimeout(typingTimersByRoom[key]);
      typingTimersByRoom[key] = null;
      renderTypingIndicator();
      return;
    }
    typingByRoom[key] = {
      id_usuario: Number(payload.id_usuario || 0),
      usuario_nombre: String(payload.usuario_nombre || "").trim(),
      expiresAt: Date.now() + 7000,
    };
    if (typingTimersByRoom[key]) clearTimeout(typingTimersByRoom[key]);
    typingTimersByRoom[key] = setTimeout(function () {
      delete typingByRoom[key];
      typingTimersByRoom[key] = null;
      renderRooms();
      renderHeader();
      renderTypingIndicator();
    }, 7200);
  }

  function renderRooms() {
    var searchValue = String(roomSearch && roomSearch.value ? roomSearch.value : "").trim().toLowerCase();
    var rows = allRooms.filter(function (room) {
      if (!searchValue) return true;
      var hay = [room.nombre || "", room.ultimo_mensaje || "", room.ultimo_usuario || ""].join(" ").toLowerCase();
      return hay.indexOf(searchValue) >= 0;
    });
    if (!rows.length) {
      showRoomEmpty(searchValue ? "No hay coincidencias." : "No hay chats disponibles.");
      return;
    }
    roomsWrap.innerHTML = '<div class="chat-rooms-stack">' + rows.map(function (room) {
      var isActive = Number(room.id_sala || 0) === Number(activeRoomId || 0);
      var typing = roomTypingData(room.id_sala);
      var meta = typing
        ? '<span class="chat-room-meta typing">escribiendo...</span>'
        : '<span class="chat-room-meta">' + escapeHtml(room.ultimo_usuario ? room.ultimo_usuario + ": " : "") + escapeHtml(room.ultimo_mensaje || "") + "</span>";
      return (
        '<div class="chat-room' + (isActive ? " active" : "") + '" data-room-id="' + escapeHtml(room.id_sala) + '">' +
          '<div class="chat-avatar">' + escapeHtml(initials(roomDisplayName(room))) + "</div>" +
          '<div class="chat-room-main">' +
            '<div class="chat-room-name">' + escapeHtml(roomDisplayName(room)) + "</div>" +
            meta +
          "</div>" +
          '<div class="chat-room-time">' + escapeHtml(humanTime(room.ultimo_en || room.actualizada_en || "")) + "</div>" +
          '<button class="chat-item-action chat-room-remove" type="button" data-room-remove="' + escapeHtml(room.id_sala) + '" title="Ocultar chat para mi">' +
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="m19 6-1 14H6L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path></svg>' +
          '</button>' +
        "</div>"
      );
    }).join("") + "</div>";
    Array.prototype.slice.call(roomsWrap.querySelectorAll(".chat-room[data-room-id]")).forEach(function (node) {
      node.addEventListener("click", function () {
        var roomId = Number(node.getAttribute("data-room-id") || 0);
        if (roomId > 0) openRoom(roomId);
      });
    });
    Array.prototype.slice.call(roomsWrap.querySelectorAll(".chat-room-remove[data-room-remove]")).forEach(function (node) {
      node.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopPropagation();
        hideRoomForMe(Number(node.getAttribute("data-room-remove") || 0));
      });
    });
    roomsWrap.scrollTop = 0;
  }

  function setHeaderSubtitle(text, withDots) {
    if (!chatSubtitle) return;
    if (!withDots) {
      chatSubtitle.innerHTML = text || "Sin actividad";
      return;
    }
    chatSubtitle.innerHTML = escapeHtml(text || "Escribiendo...") + '<span class="typing-dots"><span></span><span></span><span></span></span>';
  }

  function removeTypingBubble() {
    var bubble = chatMessages ? chatMessages.querySelector('[data-chat-typing="1"]') : null;
    if (bubble && bubble.parentNode) {
      bubble.parentNode.removeChild(bubble);
    }
  }

  function renderTypingBubble() {
    return '<div class="chat-msg chat-msg-typing" data-chat-typing="1"><span class="typing-dots"><span></span><span></span><span></span></span></div>';
  }

  function renderTypingIndicator() {
    if (!chatMessages || !activeRoomId) return;
    var typing = roomTypingData(activeRoomId);
    var bubble = chatMessages.querySelector('[data-chat-typing="1"]');
    if (!typing) {
      removeTypingBubble();
      return;
    }
    if (!bubble) {
      if (chatMessages.querySelector(".chat-empty")) chatMessages.innerHTML = "";
      chatMessages.insertAdjacentHTML("beforeend", renderTypingBubble());
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function renderHeader() {
    var room = getRoomById(activeRoomId);
    if (!room) {
      chatTitle.textContent = "Selecciona un chat para empezar";
      if (chatHeadAvatar) chatHeadAvatar.textContent = "?";
      setHeaderSubtitle("Sin actividad", false);
      return;
    }
    var name = roomDisplayName(room);
    chatTitle.textContent = name;
    if (chatHeadAvatar) chatHeadAvatar.textContent = initials(name);
    var typing = roomTypingData(room.id_sala);
    if (typing) {
      setHeaderSubtitle((typing.usuario_nombre || "Alguien") + " escribiendo...", true);
      return;
    }
    if (!isDirectRoom(room)) {
      setHeaderSubtitle(String(Number(room.miembros_count || 0)) + " participantes", false);
      return;
    }
    setHeaderSubtitle('<span class="chat-status-dot ' + (roomPartnerOnline(room) ? "online" : "offline") + '"></span>' + (roomPartnerOnline(room) ? "En linea" : "Fuera de linea"), false);
  }

  function getMessageCheckState(message) {
    if (message.read_by_other) return "read";
    if (message.delivered_to_other) return "delivered";
    return "sent";
  }

  function checkMarkup(message) {
    var state = getMessageCheckState(message || {});
    var checkClass = state === "read" ? "chat-check read" : "chat-check";
    var secondClass = checkClass + (state === "sent" ? " hidden" : "");
    return '<span class="chat-checks"><span class="' + checkClass + '">&#10003;</span><span class="' + secondClass + '">&#10003;</span></span>';
  }

  function renderAttachmentsBubble(attachments) {
    var category = String(attachments && attachments.category ? attachments.category : "").toLowerCase();
    var items = Array.isArray(attachments && attachments.items) ? attachments.items : [];
    if (!items.length) return '<div class="chat-msg-text">Adjunto</div>';
    var label = attachmentKindLabel(category, items.length);
    if (category === "image") {
      return '<div class="chat-attachments"><div class="chat-voice-note-label">' + escapeHtml(label) + '</div><div class="chat-attachments-grid">' + items.map(function (item) {
        if (item.file_exists === false) {
          return '<div class="chat-attachment-file"><span class="chat-attachment-file-icon">IMG</span><span class="chat-attachment-file-copy"><span class="chat-attachment-file-name">' + escapeHtml(item.original_name || "Imagen") + '</span><span class="chat-attachment-file-size">Archivo no disponible</span></span></div>';
        }
        return '<a class="chat-attachments-image" href="' + escapeHtml(item.file_url || "") + '" target="_blank" rel="noopener noreferrer"><img src="' + escapeHtml(item.file_url || "") + '" alt="' + escapeHtml(item.original_name || "Imagen") + '"></a>';
      }).join("") + "</div></div>";
    }
    if (category === "audio") {
      return '<div class="chat-attachments"><div class="chat-voice-note-label">' + escapeHtml(label) + '</div><div class="chat-attachments-files">' + items.map(function (item) {
        if (item.file_exists === false) {
          return '<div class="chat-attachment-file"><span class="chat-attachment-file-icon">AUD</span><span class="chat-attachment-file-copy"><span class="chat-attachment-file-name">' + escapeHtml(item.original_name || "Audio") + '</span><span class="chat-attachment-file-size">Archivo no disponible</span></span></div>';
        }
        return '<div class="chat-voice-note-player"><audio class="chat-attachments-media" controls preload="metadata" src="' + escapeHtml(item.file_url || "") + '"></audio></div>';
      }).join("") + "</div></div>";
    }
    if (category === "video") {
      return '<div class="chat-attachments"><div class="chat-voice-note-label">' + escapeHtml(label) + '</div><div class="chat-attachments-files">' + items.map(function (item) {
        if (item.file_exists === false) {
          return '<div class="chat-attachment-file"><span class="chat-attachment-file-icon">VID</span><span class="chat-attachment-file-copy"><span class="chat-attachment-file-name">' + escapeHtml(item.original_name || "Video") + '</span><span class="chat-attachment-file-size">Archivo no disponible</span></span></div>';
        }
        return '<video class="chat-attachments-media" controls preload="metadata" src="' + escapeHtml(item.file_url || "") + '"></video>';
      }).join("") + "</div></div>";
    }
    return '<div class="chat-attachments"><div class="chat-voice-note-label">' + escapeHtml(label) + '</div><div class="chat-attachments-files">' + items.map(function (item) {
      if (item.file_exists === false) {
        return '<div class="chat-attachment-file"><span class="chat-attachment-file-icon">DOC</span><span class="chat-attachment-file-copy"><span class="chat-attachment-file-name">' + escapeHtml(item.original_name || "Documento") + '</span><span class="chat-attachment-file-size">Archivo no disponible</span></span></div>';
      }
      return '<a class="chat-attachment-file" href="' + escapeHtml(item.file_url || "") + '" target="_blank" rel="noopener noreferrer">' +
        '<span class="chat-attachment-file-icon">DOC</span>' +
        '<span class="chat-attachment-file-copy"><span class="chat-attachment-file-name">' + escapeHtml(item.original_name || "Documento") + '</span><span class="chat-attachment-file-size">' + escapeHtml(formatBytes(item.size_bytes || 0)) + '</span></span>' +
      '</a>';
    }).join("") + "</div></div>";
  }

  function renderSharedRecordBubble(sharedRecord) {
    var moduleLabel = String(sharedRecord && sharedRecord.module_label ? sharedRecord.module_label : "Registro").trim();
    var title = String(sharedRecord && sharedRecord.title ? sharedRecord.title : "Registro compartido").trim();
    var subtitle = String(sharedRecord && sharedRecord.subtitle ? sharedRecord.subtitle : "").trim();
    var description = String(sharedRecord && sharedRecord.description ? sharedRecord.description : "").trim();
    var targetUrl = String(sharedRecord && sharedRecord.target_url ? sharedRecord.target_url : "").trim();
    var ctaLabel = String(sharedRecord && sharedRecord.cta_label ? sharedRecord.cta_label : "Abrir registro").trim();
    return '<div class="chat-shared-record">' +
      '<span class="chat-shared-record-badge">' + escapeHtml(moduleLabel) + '</span>' +
      '<div class="chat-shared-record-title">' + escapeHtml(title) + '</div>' +
      (subtitle ? '<div class="chat-shared-record-subtitle">' + escapeHtml(subtitle) + '</div>' : '') +
      (description ? '<div class="chat-shared-record-description">' + escapeHtml(description) + '</div>' : '') +
      (targetUrl ? '<a class="chat-shared-record-link" href="' + escapeHtml(targetUrl) + '">Abrir: ' + escapeHtml(ctaLabel) + '</a>' : '') +
    '</div>';
  }

  function renderMessageBubble(message) {
    var isMine = Number(message.id_usuario || 0) === Number(config.usuarioId || 0);
    var voiceNote = message && message.voice_note ? message.voice_note : null;
    var attachments = message && message.attachments ? message.attachments : null;
    var sharedRecord = message && message.shared_record ? message.shared_record : null;
    var bodyHtml = voiceNote
      ? voiceNote.file_exists === false
        ? '<div class="chat-voice-note"><div class="chat-voice-note-label">Nota de voz</div><div class="chat-attachment-file"><span class="chat-attachment-file-icon">AUD</span><span class="chat-attachment-file-copy"><span class="chat-attachment-file-name">Audio</span><span class="chat-attachment-file-size">Archivo no disponible</span></span></div></div>'
        : '<div class="chat-voice-note">' +
          '<div class="chat-voice-note-label">Nota de voz' + (voiceNote.duration_seconds ? " · " + escapeHtml(formatDuration(voiceNote.duration_seconds)) : "") + '</div>' +
          '<div class="chat-voice-note-player">' +
            '<audio controls preload="auto" data-voice-audio="1" src="' + escapeHtml(voiceNote.file_url || "") + '"></audio>' +
            '<div class="chat-voice-note-loading" data-voice-loading="1">Cargando audio...</div>' +
          '</div>' +
        '</div>'
      : sharedRecord
      ? renderSharedRecordBubble(sharedRecord)
      : attachments
      ? renderAttachmentsBubble(attachments)
      : '<div class="chat-msg-text">' + escapeHtml(message.contenido || "") + "</div>";
    return (
      '<div class="chat-msg' + (isMine ? " me" : "") + '" data-message-id="' + escapeHtml(message.id_mensaje) + '">' +
        '<button class="chat-item-action chat-msg-action" type="button" data-message-remove="' + escapeHtml(message.id_mensaje) + '" title="Ocultar mensaje para mi">' +
          '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6h18"></path><path d="M8 6V4h8v2"></path><path d="m19 6-1 14H6L5 6"></path><path d="M10 11v6"></path><path d="M14 11v6"></path></svg>' +
        '</button>' +
        (isMine ? "" : '<div class="chat-msg-user">' + escapeHtml(message.usuario_nombre || "Usuario") + "</div>") +
        bodyHtml +
        '<div class="chat-msg-meta"><span>' + escapeHtml(humanTime(message.creado_en || "")) + "</span>" + (isMine ? checkMarkup(message) : "") + "</div>" +
      "</div>"
    );
  }

  function hydrateVoiceNotes() {
    if (!chatMessages) return;
    Array.prototype.slice.call(chatMessages.querySelectorAll('audio[data-voice-audio="1"]')).forEach(function (audio) {
      if (audio.dataset.voiceBound === "1") return;
      audio.dataset.voiceBound = "1";
      var loading = audio.parentNode ? audio.parentNode.querySelector('[data-voice-loading="1"]') : null;
      audio.controls = false;
      audio.preload = "auto";
      var unlock = function () {
        audio.controls = true;
        if (loading) loading.hidden = true;
      };
      var lock = function () {
        audio.controls = false;
        if (loading) loading.hidden = false;
      };
      lock();
      audio.addEventListener("canplaythrough", unlock, { once: true });
      audio.addEventListener("loadeddata", function () {
        var readyState = Number(audio.readyState || 0);
        if (readyState >= 4) unlock();
      });
      audio.addEventListener("waiting", lock);
    });
  }

  function integrateRoomMessage(message) {
    if (!message || !message.id_mensaje) return false;
    var roomId = Number(message.id_sala || 0);
    if (!roomId) return false;
    if (!messagesByRoom[roomId]) messagesByRoom[roomId] = [];
    var exists = messagesByRoom[roomId].some(function (row) {
      return Number(row.id_mensaje || 0) === Number(message.id_mensaje || 0);
    });
    if (exists) return false;
    messagesByRoom[roomId].push(message);
    messagesByRoom[roomId].sort(function (a, b) {
      return Number(a.id_mensaje || 0) - Number(b.id_mensaje || 0);
    });
    return true;
  }

  function maybeMarkReadForActiveRoom() {
    if (!activeRoomId) return;
    var rows = messagesByRoom[activeRoomId] || [];
    var lastOtherId = 0;
    rows.forEach(function (msg) {
      if (Number(msg.id_usuario || 0) !== Number(config.usuarioId || 0)) {
        var id = Number(msg.id_mensaje || 0);
        if (id > lastOtherId) lastOtherId = id;
      }
    });
    if (lastOtherId > 0) sendRead(activeRoomId, lastOtherId);
  }

  function scheduleDeferredReadSync() {
    if (deferredReadTimer) {
      clearTimeout(deferredReadTimer);
      deferredReadTimer = null;
    }
    deferredReadTimer = setTimeout(function () {
      deferredReadTimer = null;
      maybeMarkReadForActiveRoom();
    }, 450);
  }

  function updateDeliveredStateForUser(userId, isOnline) {
    var targetUserId = Number(userId || 0);
    if (targetUserId <= 0 || !isOnline) return;
    Object.keys(messagesByRoom).forEach(function (roomKey) {
      var room = getRoomById(roomKey);
      if (!room || !isDirectRoom(room) || Number(room.direct_partner_id || 0) !== targetUserId) return;
      var changed = false;
      (messagesByRoom[roomKey] || []).forEach(function (msg) {
        if (Number(msg.id_usuario || 0) === Number(config.usuarioId || 0) && !msg.read_by_other && !msg.delivered_to_other) {
          msg.delivered_to_other = true;
          changed = true;
        }
      });
      if (changed && Number(roomKey || 0) === Number(activeRoomId || 0)) {
        renderMessages(messagesByRoom[roomKey] || []);
      }
    });
  }

  function appendMessage(message) {
    if (!message || !message.id_mensaje) return;
    var roomId = Number(message.id_sala || 0);
    if (!roomId || roomId !== Number(activeRoomId || 0)) return;
    if (!integrateRoomMessage(message)) return;
    removeTypingBubble();
    if (chatMessages.querySelector(".chat-empty")) chatMessages.innerHTML = "";
    chatMessages.insertAdjacentHTML("beforeend", renderMessageBubble(message));
    chatMessages.scrollTop = chatMessages.scrollHeight;
    hydrateVoiceNotes();
    maybeMarkReadForActiveRoom();
    scheduleDeferredReadSync();
    renderTypingIndicator();
  }

  function renderMessages(rows) {
    var messages = Array.isArray(rows) ? rows : [];
    messagesByRoom[activeRoomId] = messages.slice();
    if (!messages.length) {
      showMessagesEmpty("Sin mensajes por ahora.");
      renderTypingIndicator();
      return;
    }
    chatMessages.innerHTML = messages.map(renderMessageBubble).join("");
    hydrateVoiceNotes();
    renderTypingIndicator();
    chatMessages.scrollTop = chatMessages.scrollHeight;
    maybeMarkReadForActiveRoom();
    scheduleDeferredReadSync();
  }

  function fetchRooms() {
    fetch(config.salasUrl, { headers: { "X-Requested-With": "XMLHttpRequest" } })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data || {} };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          showRoomEmpty(result.data.detail || "No se pudo cargar los chats.");
          return;
        }
        allRooms = sortRoomsDesc(result.data.results || []);
        syncRoomPresenceFromUsers();
        renderRooms();
        renderHeader();
        if (initialRoomId > 0 && !activeRoomId) {
          if (getRoomById(initialRoomId)) {
            openRoom(initialRoomId);
          }
          initialRoomId = 0;
        }
      })
      .catch(function () {
        showRoomEmpty("Error de conexion cargando chats.");
      });
  }

  function fetchMessages(roomId) {
    fetch(config.mensajesUrl + "?sala_id=" + encodeURIComponent(roomId), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data || {} };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          showMessagesEmpty(result.data.detail || "No se pudo cargar los mensajes.");
          return;
        }
        renderMessages(result.data.results || []);
      })
      .catch(function () {
        showMessagesEmpty("Error de conexion cargando mensajes.");
      });
  }

  function openRoom(roomId) {
    if (typingActiveSent && Number(typingRoomId || 0) !== Number(roomId || 0)) {
      sendTyping(false);
    }
    if (Number(activeRoomId || 0) !== Number(roomId || 0)) {
      clearVoiceDraft();
      if (mediaRecorder && mediaRecorder.state === "recording") {
        discardRecordedSegment = true;
        try {
          mediaRecorder.stop();
        } catch (error) {}
      }
      stopRecorderTracks();
      clearVoiceTimers();
      mediaRecorder = null;
      mediaRecorderChunks = [];
      mediaRecorderStartedAt = 0;
      mediaRecorderBaseDuration = 0;
    }
    activeRoomId = Number(roomId || 0);
    setComposerEnabled(activeRoomId > 0);
    renderRooms();
    renderHeader();
    removeTypingBubble();
    fetchMessages(activeRoomId);
    scheduleDeferredReadSync();
    syncMobileChatView();
  }

  function postJson(url, payload) {
    return fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(payload || {}),
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, data: data || {} };
      });
    });
  }

  function buildSharedRecordContent(record) {
    return SHARED_RECORD_PREFIX + JSON.stringify({
      record_type: String(record && record.record_type ? record.record_type : "").trim(),
      record_id: String(record && record.record_id ? record.record_id : "").trim(),
      module_label: String(record && record.module_label ? record.module_label : "").trim(),
      title: String(record && record.title ? record.title : "").trim(),
      subtitle: String(record && record.subtitle ? record.subtitle : "").trim(),
      description: String(record && record.description ? record.description : "").trim(),
      target_url: String(record && record.target_url ? record.target_url : "").trim(),
      cta_label: String(record && record.cta_label ? record.cta_label : "").trim()
    });
  }

  function postVoiceNote(roomId, blob, durationSeconds) {
    var formData = new window.FormData();
    var extension = String(blob.type || "").indexOf("ogg") >= 0 ? "ogg" : "webm";
    var eventId = window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : ("chat-voice-" + Date.now() + "-" + Math.random().toString(16).slice(2));
    formData.append("sala_id", String(roomId || 0));
    formData.append("duration_seconds", String(durationSeconds || 0));
    formData.append("event_id", eventId);
    formData.append("audio", blob, "nota-voz." + extension);
    return fetch(config.enviarNotaVozUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrfToken(),
      },
      body: formData,
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, data: data || {} };
      });
    });
  }

  function postAttachments(roomId, files) {
    var formData = new window.FormData();
    var eventId = window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : ("chat-files-" + Date.now() + "-" + Math.random().toString(16).slice(2));
    formData.append("sala_id", String(roomId || 0));
    formData.append("event_id", eventId);
    Array.prototype.slice.call(files || []).forEach(function (file) {
      formData.append("files", file, file.name || "archivo");
    });
    return fetch(config.enviarAdjuntosUrl, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCsrfToken(),
      },
      body: formData,
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        return { ok: res.ok, data: data || {} };
      });
    });
  }

  function loadUsers(query) {
    return fetch(config.usuariosUrl + "?q=" + encodeURIComponent(query || ""), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    }).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, data: data || {} };
      });
    });
  }

  function setModalOpen(modal, open) {
    if (!modal) return;
    if (open) {
      modal.classList.add("open");
      modal.setAttribute("aria-hidden", "false");
      return;
    }
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
  }

  function renderDirectUsers(rows) {
    var users = Array.isArray(rows) ? rows : [];
    if (!users.length) {
      directUsersWrap.innerHTML = '<div class="chat-empty">No hay usuarios para iniciar chat.</div>';
      return;
    }
    directUsersWrap.innerHTML = users.map(function (user) {
      var id = Number(user.id_usuario || 0);
      var checked = Number(selectedDirectUserId || 0) === id;
      return (
        '<label class="chat-user-row">' +
          '<input type="radio" name="chat_direct_user" value="' + escapeHtml(id) + '"' + (checked ? " checked" : "") + " />" +
          '<div><div><strong>' + escapeHtml(user.usuario_nombre || user.usuario_login || id) + "</strong></div><div style=\"font-size:12px;color:#667781;\">Usuario #" + escapeHtml(id) + "</div></div>" +
        "</label>"
      );
    }).join("");
    Array.prototype.slice.call(directUsersWrap.querySelectorAll('input[name="chat_direct_user"]')).forEach(function (radio) {
      radio.addEventListener("change", function () {
        selectedDirectUserId = Number(radio.value || 0);
      });
    });
  }

  function renderGroupUsers(rows) {
    var users = Array.isArray(rows) ? rows : [];
    if (!users.length) {
      groupUsersWrap.innerHTML = '<div class="chat-empty">No hay usuarios disponibles.</div>';
      return;
    }
    groupUsersWrap.innerHTML = users.map(function (user) {
      var id = Number(user.id_usuario || 0);
      var checked = !!selectedGroupMemberIds[id];
      return (
        '<label class="chat-user-row">' +
          '<input type="checkbox" value="' + escapeHtml(id) + '"' + (checked ? " checked" : "") + " />" +
          '<div><div><strong>' + escapeHtml(user.usuario_nombre || user.usuario_login || id) + "</strong></div><div style=\"font-size:12px;color:#667781;\">Usuario #" + escapeHtml(id) + "</div></div>" +
        "</label>"
      );
    }).join("");
    Array.prototype.slice.call(groupUsersWrap.querySelectorAll('input[type="checkbox"]')).forEach(function (check) {
      check.addEventListener("change", function () {
        var userId = Number(check.value || 0);
        if (!userId) return;
        if (check.checked) selectedGroupMemberIds[userId] = true;
        else delete selectedGroupMemberIds[userId];
      });
    });
  }

  function refreshDirectUsers() {
    var query = String(directSearch && directSearch.value ? directSearch.value : "").trim();
    loadUsers(query).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo cargar usuarios.");
        return;
      }
      renderDirectUsers(result.data.results || []);
    }).catch(function () {
      window.alert("Error de conexion cargando usuarios.");
    });
  }

  function refreshGroupUsers() {
    var query = String(groupSearch && groupSearch.value ? groupSearch.value : "").trim();
    loadUsers(query).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo cargar usuarios.");
        return;
      }
      renderGroupUsers(result.data.results || []);
    }).catch(function () {
      window.alert("Error de conexion cargando usuarios.");
    });
  }

  function openDirectModal() {
    if (!config.permisos || !config.permisos.ver_usuarios) {
      window.alert("No tienes permiso para listar usuarios del chat.");
      return;
    }
    selectedDirectUserId = 0;
    if (directSearch) directSearch.value = "";
    directUsersWrap.innerHTML = '<div class="chat-empty">Cargando usuarios...</div>';
    setModalOpen(modalDirecto, true);
    refreshDirectUsers();
    if (directSearch) {
      setTimeout(function () { directSearch.focus(); }, 40);
    }
  }

  function openGroupModal() {
    if (!config.permisos || !config.permisos.crear_grupos) {
      window.alert("No tienes permiso para crear grupos.");
      return;
    }
    if (!config.permisos || !config.permisos.ver_usuarios) {
      window.alert("No tienes permiso para listar usuarios del chat.");
      return;
    }
    selectedGroupMemberIds = {};
    if (groupName) groupName.value = "";
    if (groupSearch) groupSearch.value = "";
    groupUsersWrap.innerHTML = '<div class="chat-empty">Cargando usuarios...</div>';
    setModalOpen(modalGrupo, true);
    refreshGroupUsers();
    if (groupName) {
      setTimeout(function () { groupName.focus(); }, 40);
    }
  }

  function createDirectRoom() {
    var userId = Number(selectedDirectUserId || 0);
    if (!userId) {
      window.alert("Selecciona un usuario para iniciar chat.");
      return;
    }
    postJson(config.iniciarDirectoUrl, { id_usuario: userId }).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo iniciar el chat.");
        return;
      }
      var room = result.data.sala || null;
      if (!room) return;
      setModalOpen(modalDirecto, false);
      upsertRoom(room);
      renderRooms();
      openRoom(room.id_sala);
    }).catch(function () {
      window.alert("Error de conexion iniciando chat.");
    });
  }

  function createGroupRoom() {
    var name = String(groupName && groupName.value ? groupName.value : "").trim();
    var members = Object.keys(selectedGroupMemberIds || {}).map(function (id) {
      return Number(id || 0);
    }).filter(function (id) {
      return id > 0;
    });
    if (!name) {
      window.alert("Escribe el nombre del grupo.");
      return;
    }
    if (!members.length) {
      window.alert("Selecciona al menos un usuario.");
      return;
    }
    postJson(config.crearGrupoUrl, { nombre: name, miembros: members }).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo crear el grupo.");
        return;
      }
      var room = result.data.sala || null;
      if (!room) return;
      setModalOpen(modalGrupo, false);
      upsertRoom(room);
      renderRooms();
      openRoom(room.id_sala);
    }).catch(function () {
      window.alert("Error de conexion creando grupo.");
    });
  }

  function sendTyping(isTyping) {
    if (!activeRoomId || !chatSocket || !chatSocketConnected || chatSocket.readyState !== window.WebSocket.OPEN) return;
    try {
      chatSocket.send(JSON.stringify({
        action: "typing",
        room_id: Number(activeRoomId || 0),
        is_typing: !!isTyping
      }));
      typingActiveSent = !!isTyping;
      typingRoomId = isTyping ? Number(activeRoomId || 0) : 0;
    } catch (error) {}
  }

  function clearTypingHeartbeat() {
    if (!typingHeartbeatTimer) return;
    clearInterval(typingHeartbeatTimer);
    typingHeartbeatTimer = null;
  }

  function ensureTypingHeartbeat() {
    if (typingHeartbeatTimer) return;
    typingHeartbeatTimer = setInterval(function () {
      if (!typingActiveSent) {
        clearTypingHeartbeat();
        return;
      }
      if (!activeRoomId || Number(typingRoomId || 0) !== Number(activeRoomId || 0)) {
        sendTyping(false);
        clearTypingHeartbeat();
        return;
      }
      if (!chatInput || !String(chatInput.value || "").trim()) {
        sendTyping(false);
        clearTypingHeartbeat();
        return;
      }
      sendTyping(true);
    }, 1800);
  }

  function scheduleTypingStop() {
    if (typingStopTimer) clearTimeout(typingStopTimer);
    typingStopTimer = setTimeout(function () {
      if (typingActiveSent) sendTyping(false);
      clearTypingHeartbeat();
    }, 3200);
  }

  function sendRead(roomId, messageId) {
    if (!roomId || !messageId || !chatSocket || !chatSocketConnected || chatSocket.readyState !== window.WebSocket.OPEN) return;
    var key = String(roomId || 0);
    var lastRead = Number(lastReadSentByRoom[key] || 0);
    if (Number(messageId || 0) <= lastRead) return;
    lastReadSentByRoom[key] = Number(messageId || 0);
    try {
      chatSocket.send(JSON.stringify({
        action: "read",
        room_id: Number(roomId || 0),
        message_id: Number(messageId || 0)
      }));
    } catch (error) {}
  }

  function applyReadReceipt(roomId, messageId) {
    var rows = messagesByRoom[roomId] || [];
    var changed = false;
    rows.forEach(function (msg) {
      if (Number(msg.id_usuario || 0) === Number(config.usuarioId || 0)
        && Number(msg.id_mensaje || 0) <= Number(messageId || 0)
        && !msg.read_by_other) {
        msg.read_by_other = true;
        msg.delivered_to_other = true;
        changed = true;
      }
    });
    if (changed && Number(roomId || 0) === Number(activeRoomId || 0)) {
      renderMessages(rows);
    }
  }

  function sendMessage() {
    if (!activeRoomId || !config.permisos || !config.permisos.enviar_mensajes) return;
    if (hasVoiceDraft()) return;
    var text = String(chatInput.value || "").trim();
    if (!text) return;
    var eventId = window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : ("chat-msg-" + Date.now() + "-" + Math.random().toString(16).slice(2));
    chatInput.value = "";
    if (typingActiveSent) sendTyping(false);
    clearTypingHeartbeat();
    postJson(config.enviarMensajeUrl, {
      sala_id: activeRoomId,
      contenido: text,
      event_id: eventId
    }).then(function (result) {
      if (!result.ok) window.alert(result.data.detail || "No se pudo enviar el mensaje.");
    }).catch(function () {
      window.alert("Error de conexion enviando mensaje.");
    });
  }

  function shareTypeAllowed(typeValue) {
    return !!(config.sharePermissions || {})[String(typeValue || "").trim()];
  }

  function getFirstAllowedShareType() {
    var types = ["cliente", "cuenta_por_cobrar", "factura", "financiamiento"];
    for (var i = 0; i < types.length; i += 1) {
      if (shareTypeAllowed(types[i])) return types[i];
    }
    return "";
  }

  function setShareResultsEmpty(message) {
    if (!shareResultsWrap) return;
    shareResultsWrap.innerHTML = '<div class="chat-empty">' + escapeHtml(message || "No se encontraron registros.") + '</div>';
  }

  function renderShareResults(rows) {
    if (!shareResultsWrap) return;
    var items = Array.isArray(rows) ? rows : [];
    if (!items.length) {
      selectedSharedRecord = null;
      setShareResultsEmpty("No se encontraron registros.");
      return;
    }
    if (!selectedSharedRecord || !items.some(function (item) {
      return String(item.record_type || "") === String(selectedSharedRecord.record_type || "")
        && String(item.record_id || "") === String(selectedSharedRecord.record_id || "");
    })) {
      selectedSharedRecord = items[0];
    }
    shareResultsWrap.innerHTML = items.map(function (item, index) {
      var checked = selectedSharedRecord
        && String(item.record_type || "") === String(selectedSharedRecord.record_type || "")
        && String(item.record_id || "") === String(selectedSharedRecord.record_id || "");
      return '<label class="chat-share-result">' +
        '<input type="radio" name="chat_share_pick" value="' + escapeHtml(String(index)) + '" ' + (checked ? "checked" : "") + '>' +
        '<span class="chat-share-result-copy">' +
          '<span class="chat-share-result-title">' + escapeHtml(item.title || "Registro") + '</span>' +
          '<span class="chat-share-result-meta">' + escapeHtml(item.module_label || "") + (item.subtitle ? " - " + escapeHtml(item.subtitle) : "") + '</span>' +
          (item.description ? '<span class="chat-share-result-desc">' + escapeHtml(item.description) + '</span>' : '') +
        '</span>' +
      '</label>';
    }).join("");
    Array.prototype.slice.call(shareResultsWrap.querySelectorAll('input[name="chat_share_pick"]')).forEach(function (radio) {
      radio.addEventListener("change", function () {
        var idx = Number(radio.value || 0);
        if (items[idx]) selectedSharedRecord = items[idx];
      });
    });
  }

  function fetchShareRecords() {
    if (!shareResultsWrap || !shareType) return;
    var typeValue = String(shareType.value || "").trim();
    if (!typeValue || !shareTypeAllowed(typeValue)) {
      setShareResultsEmpty("No tienes permiso para ese tipo de registro.");
      return;
    }
    var q = String(shareSearch && shareSearch.value ? shareSearch.value : "").trim();
    shareResultsWrap.innerHTML = '<div class="chat-empty">Buscando registros...</div>';
    fetch(config.registrosCompartiblesUrl + "?tipo=" + encodeURIComponent(typeValue) + "&q=" + encodeURIComponent(q), {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    })
      .then(function (res) {
        return res.json().then(function (data) {
          return { ok: res.ok, data: data || {} };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          setShareResultsEmpty(result.data.detail || "No se pudieron cargar los registros.");
          return;
        }
        renderShareResults(result.data.results || []);
      })
      .catch(function () {
        setShareResultsEmpty("Error de conexion buscando registros.");
      });
  }

  function openShareRecordModal() {
    if (!config.permisos || !config.permisos.enviar_mensajes || !modalShareRecord) return;
    if (!activeRoomId) {
      window.alert("Selecciona un chat primero para poder compartir un registro.");
      return;
    }
    var firstType = getFirstAllowedShareType();
    if (!firstType) {
      window.alert("No tienes permiso para compartir registros del sistema.");
      return;
    }
    if (shareType) shareType.value = firstType;
    if (shareSearch) shareSearch.value = "";
    selectedSharedRecord = null;
    setModalOpen(modalShareRecord, true);
    fetchShareRecords();
    if (shareSearch) shareSearch.focus();
  }

  function sendSharedRecord() {
    if (!activeRoomId || !selectedSharedRecord) {
      window.alert("Selecciona un registro para compartir.");
      return;
    }
    var eventId = window.crypto && window.crypto.randomUUID
      ? window.crypto.randomUUID()
      : ("chat-share-" + Date.now() + "-" + Math.random().toString(16).slice(2));
    postJson(config.enviarMensajeUrl, {
      sala_id: activeRoomId,
      contenido: buildSharedRecordContent(selectedSharedRecord),
      event_id: eventId
    }).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo compartir el registro.");
        return;
      }
      selectedSharedRecord = null;
      setModalOpen(modalShareRecord, false);
    }).catch(function () {
      window.alert("Error de conexion compartiendo el registro.");
    });
  }

  function hideMessageForMe(messageId) {
    if (!messageId || !activeRoomId) return;
    if (!window.confirm("Este mensaje se ocultara solo para tu sesion. Deseas continuar?")) return;
    postJson(config.ocultarMensajeUrl, { message_id: Number(messageId || 0) }).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo ocultar el mensaje.");
        return;
      }
      fetchMessages(activeRoomId);
      fetchRooms();
    }).catch(function () {
      window.alert("Error de conexion ocultando mensaje.");
    });
  }

  function hideRoomForMe(roomId) {
    if (!roomId) return;
    if (!window.confirm("Este chat se ocultara solo para tu sesion actual de usuario. Deseas continuar?")) return;
    postJson(config.ocultarSalaUrl, { sala_id: Number(roomId || 0) }).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo ocultar el chat.");
        return;
      }
      allRooms = allRooms.filter(function (room) {
        return Number(room.id_sala || 0) !== Number(roomId || 0);
      });
      if (Number(activeRoomId || 0) === Number(roomId || 0)) {
        activeRoomId = 0;
        setComposerEnabled(false);
        renderHeader();
        showMessagesEmpty("Sin mensajes por ahora.");
        syncMobileChatView();
      }
      renderRooms();
      fetchRooms();
    }).catch(function () {
      window.alert("Error de conexion ocultando chat.");
    });
  }

  function clearVoiceTimers() {
    if (mediaRecorderTimer) {
      clearInterval(mediaRecorderTimer);
      mediaRecorderTimer = null;
    }
    if (mediaRecorderMaxTimer) {
      clearTimeout(mediaRecorderMaxTimer);
      mediaRecorderMaxTimer = null;
    }
  }

  function hasVoiceDraft() {
    return !!voiceDraftParts.length && Number(voiceDraftDuration || 0) > 0;
  }

  function stopRecorderTracks() {
    if (!mediaRecorderStream) return;
    try {
      mediaRecorderStream.getTracks().forEach(function (track) { track.stop(); });
    } catch (error) {}
    mediaRecorderStream = null;
  }

  function clearVoiceDraft() {
    voiceDraftParts = [];
    voiceDraftDuration = 0;
    voiceDraftMimeType = "";
  }

  function renderVoiceComposerState() {
    var canSend = !!activeRoomId && !!config.permisos && !!config.permisos.enviar_mensajes;
    var isRecording = !!(mediaRecorder && mediaRecorder.state === "recording");
    var draftReady = hasVoiceDraft();
    if (btnVoice) {
      btnVoice.classList.toggle("is-recording", isRecording);
      btnVoice.title = isRecording ? "Detener grabacion" : "Grabar nota de voz";
      btnVoice.setAttribute("aria-label", isRecording ? "Detener grabacion" : "Grabar nota de voz");
      btnVoice.disabled = !canSend || draftReady;
    }
    if (btnAttach) {
      btnAttach.disabled = !canSend || isRecording || draftReady;
    }
    if (recordingStatus) recordingStatus.classList.toggle("active", isRecording || draftReady);
    if (recordingActions) recordingActions.style.display = draftReady ? "flex" : "none";
    if (chatInput) chatInput.style.display = (isRecording || draftReady) ? "none" : "";
    if (recordingTime) {
      recordingTime.textContent = formatDuration(
        isRecording
          ? Math.min(MAX_VOICE_SECONDS, mediaRecorderBaseDuration + Math.floor((Date.now() - mediaRecorderStartedAt) / 1000))
          : (draftReady ? voiceDraftDuration : 0)
      );
    }
    if (recordingTitle) {
      recordingTitle.textContent = isRecording ? "Grabando nota de voz" : (draftReady ? "Nota lista para enviar" : "Grabando nota de voz");
    }
    if (recordingSubtitle) {
      if (isRecording) {
        var remaining = Math.max(0, MAX_VOICE_SECONDS - (mediaRecorderBaseDuration + Math.floor((Date.now() - mediaRecorderStartedAt) / 1000)));
        recordingSubtitle.textContent = "Tiempo restante " + formatDuration(remaining) + ".";
      } else if (draftReady) {
        recordingSubtitle.textContent = "Puedes continuar, enviar o cancelar esta nota.";
      } else {
        recordingSubtitle.textContent = "Se enviara cuando la confirmes.";
      }
    }
    if (btnEnviar) {
      btnEnviar.disabled = !canSend || isRecording || draftReady;
    }
  }

  function updateRecordingTimer() {
    if (!recordingTime || !mediaRecorderStartedAt) return;
    var elapsed = Math.min(MAX_VOICE_SECONDS, mediaRecorderBaseDuration + Math.floor((Date.now() - mediaRecorderStartedAt) / 1000));
    recordingTime.textContent = formatDuration(elapsed);
    if (recordingSubtitle) {
      recordingSubtitle.textContent = "Tiempo restante " + formatDuration(Math.max(0, MAX_VOICE_SECONDS - elapsed)) + ".";
    }
  }

  function startVoiceRecording() {
    if (!activeRoomId || !config.permisos || !config.permisos.enviar_mensajes) return;
    if (hasVoiceDraft() && Number(voiceDraftDuration || 0) >= MAX_VOICE_SECONDS) {
      window.alert("La nota de voz alcanzo el limite maximo de 5 minutos.");
      return;
    }
    if (!window.MediaRecorder || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      window.alert("Tu navegador no soporta grabacion de audio.");
      return;
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      mediaRecorderStream = stream;
      mediaRecorderChunks = [];
      mediaRecorderStartedAt = Date.now();
      mediaRecorderBaseDuration = Math.max(0, Number(voiceDraftDuration || 0));
      discardRecordedSegment = false;
      mediaRecorder = new window.MediaRecorder(stream);
      mediaRecorder.addEventListener("dataavailable", function (event) {
        if (event.data && event.data.size > 0) {
          mediaRecorderChunks.push(event.data);
        }
      });
      mediaRecorder.addEventListener("stop", function () {
        var mimeType = (mediaRecorder && mediaRecorder.mimeType) || (stream && stream.mimeType) || "audio/webm";
        var blob = new window.Blob(mediaRecorderChunks, { type: mimeType });
        var durationSeconds = Math.max(1, Math.round((Date.now() - mediaRecorderStartedAt) / 1000));
        stopRecorderTracks();
        clearVoiceTimers();
        mediaRecorder = null;
        mediaRecorderChunks = [];
        mediaRecorderStartedAt = 0;
        mediaRecorderBaseDuration = 0;
        if (!discardRecordedSegment && blob.size > 0) {
          voiceDraftParts.push(blob);
          voiceDraftDuration = Math.min(MAX_VOICE_SECONDS, Number(voiceDraftDuration || 0) + durationSeconds);
          if (!voiceDraftMimeType) voiceDraftMimeType = mimeType;
        }
        discardRecordedSegment = false;
        renderVoiceComposerState();
      });
      mediaRecorder.start();
      renderVoiceComposerState();
      updateRecordingTimer();
      mediaRecorderTimer = setInterval(updateRecordingTimer, 250);
      var remainingSeconds = Math.max(1, MAX_VOICE_SECONDS - Number(voiceDraftDuration || 0));
      mediaRecorderMaxTimer = setTimeout(function () {
        if (mediaRecorder && mediaRecorder.state === "recording") {
          mediaRecorder.stop();
        }
      }, remainingSeconds * 1000);
    }).catch(function () {
      window.alert("No se pudo acceder al microfono.");
      clearVoiceTimers();
      mediaRecorderStartedAt = 0;
      mediaRecorderBaseDuration = 0;
      stopRecorderTracks();
      renderVoiceComposerState();
    });
  }

  function sendVoiceDraft() {
    if (!activeRoomId || !hasVoiceDraft()) return;
    var mimeType = voiceDraftMimeType || (voiceDraftParts[0] && voiceDraftParts[0].type) || "audio/webm";
    var blob = new window.Blob(voiceDraftParts, { type: mimeType });
    var durationSeconds = Math.max(1, Math.round(voiceDraftDuration || 0));
    renderVoiceComposerState();
    postVoiceNote(activeRoomId, blob, durationSeconds).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudo enviar la nota de voz.");
        renderVoiceComposerState();
        return;
      }
      clearVoiceDraft();
      renderVoiceComposerState();
    }).catch(function () {
      window.alert("Error de conexion enviando la nota de voz.");
      renderVoiceComposerState();
    });
  }

  function cancelVoiceDraft() {
    clearVoiceDraft();
    renderVoiceComposerState();
  }

  function openAttachmentPicker() {
    if (!attachInput || !activeRoomId || !config.permisos || !config.permisos.enviar_mensajes) return;
    attachInput.click();
  }

  function handleAttachmentSelection() {
    if (!attachInput) return;
    var files = Array.prototype.slice.call(attachInput.files || []);
    attachInput.value = "";
    if (!files.length) return;
    if (mediaRecorder && mediaRecorder.state === "recording") {
      window.alert("Termina la grabacion actual antes de adjuntar archivos.");
      return;
    }
    if (hasVoiceDraft()) {
      window.alert("Envia o cancela la nota de voz actual antes de adjuntar archivos.");
      return;
    }
    var kind = "";
    var totalBytes = 0;
    for (var i = 0; i < files.length; i += 1) {
      var fileKind = detectAttachmentKind(files[i]);
      if (!fileKind) {
        window.alert("Hay archivos no permitidos en la seleccion.");
        return;
      }
      if (kind && fileKind !== kind) {
        window.alert("Solo puedes enviar varios archivos del mismo tipo en un mismo mensaje.");
        return;
      }
      kind = fileKind;
      totalBytes += Number(files[i].size || 0);
    }
    if (totalBytes > MAX_ATTACHMENTS_BYTES) {
      window.alert("Los adjuntos no pueden superar 10 MB en total.");
      return;
    }
    postAttachments(activeRoomId, files).then(function (result) {
      if (!result.ok) {
        window.alert(result.data.detail || "No se pudieron enviar los adjuntos.");
      }
    }).catch(function () {
      window.alert("Error de conexion enviando adjuntos.");
    });
  }

  function toggleVoiceRecording() {
    if (mediaRecorder && mediaRecorder.state === "recording") {
      mediaRecorder.stop();
      return;
    }
    startVoiceRecording();
  }

  function clearSocketReconnectTimer() {
    if (!chatSocketReconnectTimer) return;
    clearTimeout(chatSocketReconnectTimer);
    chatSocketReconnectTimer = null;
  }

  function clearSocketPingTimer() {
    if (!chatSocketPingTimer) return;
    clearInterval(chatSocketPingTimer);
    chatSocketPingTimer = null;
  }

  function ensureSocketPing() {
    if (chatSocketPingTimer) return;
    chatSocketPingTimer = setInterval(function () {
      if (!chatSocket || !chatSocketConnected || chatSocket.readyState !== window.WebSocket.OPEN) {
        clearSocketPingTimer();
        return;
      }
      try {
        chatSocket.send(JSON.stringify({ action: "ping" }));
      } catch (error) {
        clearSocketPingTimer();
      }
    }, 12000);
  }

  function scheduleSocketReconnect() {
    if (chatSocketReconnectTimer) return;
    chatSocketReconnectTimer = setTimeout(function () {
      chatSocketReconnectTimer = null;
      connectSocket();
    }, 3000);
  }

  function resolveSocketUrl() {
    var raw = String(config.socketUrl || "").trim();
    if (!raw) return "";
    try {
      var target = new URL(raw, window.location.origin);
      target.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      return target.toString();
    } catch (error) {
      return "";
    }
  }

  function connectSocket() {
    var socketTarget = resolveSocketUrl();
    if (!socketTarget || typeof window.WebSocket !== "function") return;
    if (chatSocket && (chatSocket.readyState === window.WebSocket.OPEN || chatSocket.readyState === window.WebSocket.CONNECTING)) return;
    try {
      chatSocket = new window.WebSocket(socketTarget);
    } catch (error) {
      scheduleSocketReconnect();
      return;
    }

    chatSocket.addEventListener("open", function () {
      chatSocketConnected = true;
      clearSocketReconnectTimer();
      ensureSocketPing();
      maybeMarkReadForActiveRoom();
      scheduleDeferredReadSync();
    });

    chatSocket.addEventListener("message", function (event) {
      var data = null;
      try {
        data = JSON.parse(event.data || "{}");
      } catch (error) {
        data = null;
      }
      if (!data || !data.type) return;

      if (data.type === "chat.message") {
        var room = data.room || null;
        var message = data.message || null;
        if (room && room.id_sala) {
          upsertRoom(room);
          renderRooms();
          renderHeader();
        }
        if (message && message.id_mensaje) appendMessage(message);
        return;
      }

      if (data.type === "chat.room") {
        var updatedRoom = data.room || null;
        if (updatedRoom && updatedRoom.id_sala) {
          upsertRoom(updatedRoom);
          renderRooms();
          renderHeader();
        }
        return;
      }

      if (data.type === "chat.typing") {
        var typingRoom = Number(data.room_id || 0);
        if (typingRoom > 0 && Number(data.id_usuario || 0) !== Number(config.usuarioId || 0)) {
          setRoomTyping(typingRoom, data);
          renderRooms();
          renderHeader();
          renderTypingIndicator();
        }
        return;
      }

      if (data.type === "chat.read") {
        var readRoom = Number(data.room_id || 0);
        var readMessage = Number(data.message_id || 0);
        if (readRoom > 0 && readMessage > 0 && Number(data.id_usuario || 0) !== Number(config.usuarioId || 0)) {
          applyReadReceipt(readRoom, readMessage);
        }
        return;
      }

      if (data.type === "chat.presence_snapshot") {
        onlineUsers = {};
        (data.online_user_ids || []).forEach(function (userId) {
          setUserOnline(userId, true);
        });
        syncRoomPresenceFromUsers();
        renderRooms();
        renderHeader();
        return;
      }

      if (data.type === "chat.presence") {
        var presenceUserId = Number(data.id_usuario || 0);
        setUserOnline(presenceUserId, !!data.is_online);
        syncRoomPresenceFromUsers();
        updateDeliveredStateForUser(presenceUserId, !!data.is_online);
        renderRooms();
        renderHeader();
      }
    });

    chatSocket.addEventListener("close", function () {
      chatSocketConnected = false;
      chatSocket = null;
      clearSocketPingTimer();
      scheduleSocketReconnect();
    });

    chatSocket.addEventListener("error", function () {
      try {
        if (chatSocket) chatSocket.close();
      } catch (error) {}
    });
  }

  if (btnNuevoDirecto) {
    btnNuevoDirecto.disabled = !(config.permisos && config.permisos.enviar_mensajes);
    btnNuevoDirecto.addEventListener("click", openDirectModal);
  }
  if (btnNuevoGrupo) {
    btnNuevoGrupo.disabled = !(config.permisos && config.permisos.crear_grupos);
    btnNuevoGrupo.addEventListener("click", openGroupModal);
  }
  if (btnVoice) btnVoice.addEventListener("click", toggleVoiceRecording);
  if (btnAttach) btnAttach.addEventListener("click", openAttachmentPicker);
  if (btnShareRecord) btnShareRecord.addEventListener("click", openShareRecordModal);
  if (attachInput) attachInput.addEventListener("change", handleAttachmentSelection);
  if (btnVoiceContinue) btnVoiceContinue.addEventListener("click", startVoiceRecording);
  if (btnVoiceCancel) btnVoiceCancel.addEventListener("click", cancelVoiceDraft);
  if (btnVoiceSend) btnVoiceSend.addEventListener("click", sendVoiceDraft);
  if (btnEnviar) btnEnviar.addEventListener("click", sendMessage);

  if (chatInput) {
    chatInput.addEventListener("input", function () {
      if (!activeRoomId || !config.permisos || !config.permisos.enviar_mensajes) return;
      var hasText = !!String(chatInput.value || "").trim();
      if (!hasText) {
        if (typingActiveSent) sendTyping(false);
        clearTypingHeartbeat();
        return;
      }
      if (!typingActiveSent || Number(typingRoomId || 0) !== Number(activeRoomId || 0)) {
        sendTyping(true);
      }
      ensureTypingHeartbeat();
      scheduleTypingStop();
    });
    chatInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
      }
    });
  }

  if (roomSearch) {
    roomSearch.addEventListener("input", function () {
      if (roomSearchTimer) clearTimeout(roomSearchTimer);
      roomSearchTimer = setTimeout(renderRooms, 180);
    });
  }
  if (btnMobileBack) {
    btnMobileBack.addEventListener("click", returnToRoomList);
  }
  if (directSearch) {
    directSearch.addEventListener("input", function () {
      if (directSearchTimer) clearTimeout(directSearchTimer);
      directSearchTimer = setTimeout(refreshDirectUsers, 220);
    });
  }
  if (directCancel) directCancel.addEventListener("click", function () { setModalOpen(modalDirecto, false); });
  if (directCreate) directCreate.addEventListener("click", createDirectRoom);
  if (groupSearch) {
    groupSearch.addEventListener("input", function () {
      if (groupSearchTimer) clearTimeout(groupSearchTimer);
      groupSearchTimer = setTimeout(refreshGroupUsers, 220);
    });
  }
  if (groupCancel) groupCancel.addEventListener("click", function () { setModalOpen(modalGrupo, false); });
  if (groupCreate) groupCreate.addEventListener("click", createGroupRoom);
  if (shareType) shareType.addEventListener("change", fetchShareRecords);
  if (shareSearch) {
    shareSearch.addEventListener("input", function () {
      if (shareSearchTimer) clearTimeout(shareSearchTimer);
      shareSearchTimer = setTimeout(fetchShareRecords, 220);
    });
    shareSearch.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        fetchShareRecords();
      }
    });
  }
  if (shareCancel) shareCancel.addEventListener("click", function () { setModalOpen(modalShareRecord, false); });
  if (shareSend) shareSend.addEventListener("click", sendSharedRecord);

  [modalDirecto, modalGrupo, modalShareRecord].forEach(function (modal) {
    if (!modal) return;
    modal.addEventListener("click", function (event) {
      if (event.target === modal) setModalOpen(modal, false);
    });
  });

  setComposerEnabled(false);
  renderVoiceComposerState();
  renderHeader();
  fetchRooms();
  connectSocket();

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && !chatSocketConnected) connectSocket();
    if (!document.hidden) {
      maybeMarkReadForActiveRoom();
      scheduleDeferredReadSync();
    }
  });

  if (chatMessages) {
    chatMessages.addEventListener("scroll", function () {
      scheduleDeferredReadSync();
    });
    chatMessages.addEventListener("click", function (event) {
      var actionButton = event.target && event.target.closest ? event.target.closest("[data-message-remove]") : null;
      if (actionButton) {
        hideMessageForMe(Number(actionButton.getAttribute("data-message-remove") || 0));
        return;
      }
      scheduleDeferredReadSync();
    });
  }

  window.addEventListener("focus", function () {
    scheduleDeferredReadSync();
  });

  window.addEventListener("resize", syncMobileChatView);

  window.addEventListener("beforeunload", function () {
    clearSocketReconnectTimer();
    clearSocketPingTimer();
    clearTypingHeartbeat();
    clearVoiceTimers();
    if (mediaRecorder && mediaRecorder.state === "recording") {
      discardRecordedSegment = true;
      try {
        mediaRecorder.stop();
      } catch (error) {}
    }
    stopRecorderTracks();
    if (deferredReadTimer) {
      clearTimeout(deferredReadTimer);
      deferredReadTimer = null;
    }
    if (typingActiveSent) sendTyping(false);
    try {
      if (chatSocket) chatSocket.close();
    } catch (error) {}
  });

  syncMobileChatView();
})();
