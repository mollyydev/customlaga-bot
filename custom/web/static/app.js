// customlaga Bot Customization Frontend

let config = null;
let activePageId = "main";
let activePageLang = "ru";
let activeNotifKey = "subscription_expiring";

document.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  loadConfig();
  setupEventListeners();
});

function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => n.classList.remove("active"));
      item.classList.add("active");
      const tabId = item.getAttribute("data-tab");
      document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
      const targetPane = document.getElementById("tab-" + tabId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  const langPills = document.querySelectorAll("#pageLangTabs .lang-pill");
  langPills.forEach(pill => {
    pill.addEventListener("click", () => {
      langPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activePageLang = pill.getAttribute("data-lang");
      loadPageTextForLang();
    });
  });
}

function setupEventListeners() {
  document.getElementById("masterToggle").addEventListener("change", async (e) => {
    if (!config) return;
    config.enabled = e.target.checked;
    await saveConfigToServer({ enabled: config.enabled });
  });

  document.getElementById("syncBtn").addEventListener("click", async () => {
    try {
      const resp = await fetch("/api/customization/sync", { method: "POST" });
      if (resp.ok) {
        showRestartWarning(false);
        updateStatusBadge(true);
        alert("Конфигурация успешно сохранена в файл JSON!");
      }
    } catch (err) {
      console.error(err);
      alert("Ошибка при сохранении в файл");
    }
  });
}

async function loadConfig() {
  try {
    const resp = await fetch("/api/customization/config");
    if (!resp.ok) throw new Error("Failed to load config");
    config = await resp.json();
    renderUI();
  } catch (err) {
    console.error("Config fetch error:", err);
  }
}

function renderUI() {
  if (!config) return;

  // Master toggle
  document.getElementById("masterToggle").checked = Boolean(config.enabled);

  // Status & banner
  showRestartWarning(config.needs_restart);
  updateStatusBadge(!config.needs_restart);

  // Render pages list
  renderPagesList();
  renderActivePage();

  // Render all buttons table
  renderButtonsTable();

  // Render start flow
  renderStartFlow();

  // Render notifications
  renderNotificationsList();

  // Render languages
  document.getElementById("autoDetectLangToggle").checked = Boolean(config.auto_detect_language);
  document.getElementById("defaultLangSelect").value = config.default_language || "ru";

  // Render emoji packs
  renderEmojiPacks();
}

function showRestartWarning(show) {
  const banner = document.getElementById("restartBanner");
  banner.style.display = show ? "flex" : "none";
}

function dismissBanner() {
  document.getElementById("restartBanner").style.display = "none";
}

function updateStatusBadge(isSynced) {
  const badge = document.getElementById("statusBadge");
  const text = document.getElementById("statusText");
  if (isSynced) {
    badge.className = "status-indicator";
    text.textContent = "Синхронизировано";
  } else {
    badge.className = "status-indicator realtime";
    text.textContent = "Режим Real-time";
  }
}

// ---------------- PAGES ----------------

function renderPagesList() {
  const list = document.getElementById("pagesList");
  list.innerHTML = "";
  for (const pageId in config.pages) {
    const page = config.pages[pageId];
    const li = document.createElement("li");
    li.className = "list-item" + (pageId === activePageId ? " active" : "");
    li.innerHTML = `<span><strong>${page.title || pageId}</strong> <small style="color:var(--text-muted)">(${pageId})</small></span>`;
    li.onclick = () => {
      activePageId = pageId;
      renderPagesList();
      renderActivePage();
    };
    list.appendChild(li);
  }
}

function renderActivePage() {
  const page = config.pages[activePageId];
  if (!page) return;

  document.getElementById("editingPageTitle").textContent = page.title || activePageId;
  document.getElementById("editingPageId").textContent = "id: " + activePageId;

  // Media
  const mediaTypeRadios = document.getElementsByName("mediaType");
  mediaTypeRadios.forEach(radio => {
    radio.checked = radio.value === (page.media_type || "none");
  });
  document.getElementById("pageMediaUrl").value = page.media_url || "";

  // Text
  loadPageTextForLang();

  // Page Buttons
  renderPageButtons();
}

function loadPageTextForLang() {
  const page = config.pages[activePageId];
  if (!page || !page.text) return;
  document.getElementById("pageText").value = page.text[activePageLang] || page.text["ru"] || "";
}

function renderPageButtons() {
  const page = config.pages[activePageId];
  const container = document.getElementById("pageButtonsList");
  container.innerHTML = "";

  (page.buttons || []).forEach((btn, idx) => {
    const div = document.createElement("div");
    div.className = "btn-card";
    const btnText = (btn.text && (btn.text["ru"] || btn.text[activePageLang])) || btn.id;
    const targetLabel = btn.target_type === "webapp" ? `🌐 WebApp (${btn.target_value})` :
                        btn.target_type === "page" ? `📄 Страница: ${btn.target_value}` :
                        btn.target_type === "url" ? `🔗 Ссылка: ${btn.target_value}` : `⚡ Встроенная: ${btn.target_value}`;

    div.innerHTML = `
      <div>
        <strong>${btn.emoji ? btn.emoji + " " : ""}${btnText}</strong>
        <div style="font-size:12px; color:var(--text-muted);">${targetLabel}</div>
      </div>
      <div style="display:flex; gap:8px;">
        <button class="btn btn-sm btn-secondary" onclick="editButton('${activePageId}', ${idx})">✏️ Изменить</button>
        ${!btn.is_builtin ? `<button class="btn btn-sm btn-secondary" style="color:var(--danger)" onclick="deletePageButton('${activePageId}', ${idx})">🗑</button>` : ''}
      </div>
    `;
    container.appendChild(div);
  });
}

async function saveCurrentPage() {
  const page = config.pages[activePageId];
  if (!page) return;

  // Media
  let selectedMediaType = "none";
  document.getElementsByName("mediaType").forEach(r => {
    if (r.checked) selectedMediaType = r.value;
  });
  page.media_type = selectedMediaType;
  page.media_url = document.getElementById("pageMediaUrl").value.trim();

  // Text
  if (!page.text) page.text = {};
  page.text[activePageLang] = document.getElementById("pageText").value;

  await saveConfigToServer({ pages: config.pages });
  alert("Страница сохранена в реальном времени!");
}

async function translateActivePageText() {
  const currentText = document.getElementById("pageText").value;
  if (!currentText.trim()) return;

  try {
    const resp = await fetch("/api/customization/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: currentText,
        source_lang: activePageLang
      })
    });
    if (resp.ok) {
      const data = await resp.json();
      const page = config.pages[activePageId];
      if (!page.text) page.text = {};
      Object.assign(page.text, data.translations);
      alert("Текст автоматически переведен на все поддерживаемые языки!");
    }
  } catch (err) {
    console.error(err);
    alert("Ошибка автоперевода");
  }
}

// ---------------- BUTTONS MODAL ----------------

let editingButtonRef = null;

function openAddButtonToPageModal() {
  editingButtonRef = { pageId: activePageId, index: -1 };
  document.getElementById("buttonModalTitle").textContent = "Добавить кнопку на страницу";
  document.getElementById("modalBtnId").value = "btn_" + Date.now();
  document.getElementById("modalBtnId").disabled = false;
  document.getElementById("modalBtnTextRu").value = "";
  document.getElementById("modalBtnTargetType").value = "page";
  document.getElementById("modalBtnTargetValue").value = "";
  document.getElementById("modalBtnEnabled").checked = true;
  document.getElementById("buttonModal").style.display = "flex";
}

function editButton(pageId, index) {
  const page = config.pages[pageId];
  const btn = page.buttons[index];
  editingButtonRef = { pageId, index };
  document.getElementById("buttonModalTitle").textContent = "Редактировать кнопку";
  document.getElementById("modalBtnId").value = btn.id;
  document.getElementById("modalBtnId").disabled = btn.is_builtin;
  document.getElementById("modalBtnTextRu").value = (btn.text && btn.text["ru"]) || "";
  document.getElementById("modalBtnTargetType").value = btn.target_type || "builtin";
  document.getElementById("modalBtnTargetValue").value = btn.target_value || "";
  document.getElementById("modalBtnEnabled").checked = Boolean(btn.enabled);
  document.getElementById("buttonModal").style.display = "flex";
}

function closeButtonModal() {
  document.getElementById("buttonModal").style.display = "none";
}

async function saveButtonFromModal() {
  if (!editingButtonRef) return;
  const page = config.pages[editingButtonRef.pageId];
  if (!page) return;

  const btnId = document.getElementById("modalBtnId").value.trim();
  const textRu = document.getElementById("modalBtnTextRu").value.trim();
  const targetType = document.getElementById("modalBtnTargetType").value;
  const targetValue = document.getElementById("modalBtnTargetValue").value.trim();
  const enabled = document.getElementById("modalBtnEnabled").checked;

  if (editingButtonRef.index === -1) {
    // New button
    page.buttons.push({
      id: btnId,
      is_builtin: false,
      target_type: targetType,
      target_value: targetValue,
      text: { ru: textRu },
      enabled: enabled,
      row: page.buttons.length
    });
  } else {
    // Existing button
    const btn = page.buttons[editingButtonRef.index];
    if (!btn.text) btn.text = {};
    btn.text["ru"] = textRu;
    btn.target_type = targetType;
    btn.target_value = targetValue;
    btn.enabled = enabled;
  }

  closeButtonModal();
  renderPageButtons();
  renderButtonsTable();
  await saveConfigToServer({ pages: config.pages });
}

function deletePageButton(pageId, index) {
  const page = config.pages[pageId];
  if (confirm("Удалить кнопку?")) {
    page.buttons.splice(index, 1);
    renderPageButtons();
    renderButtonsTable();
    saveConfigToServer({ pages: config.pages });
  }
}

// ---------------- ALL BUTTONS TABLE ----------------

function renderButtonsTable() {
  const tbody = document.querySelector("#allButtonsTable tbody");
  tbody.innerHTML = "";

  for (const pageId in config.pages) {
    const page = config.pages[pageId];
    (page.buttons || []).forEach((btn, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${btn.id}</code></td>
        <td>${btn.is_builtin ? '<span class="badge">Системная</span>' : '<span class="badge" style="background:#0284c7">Кастомная</span>'}</td>
        <td>${(btn.text && btn.text["ru"]) || btn.id}</td>
        <td>${btn.target_type}: <strong>${btn.target_value || '-'}</strong></td>
        <td>${btn.enabled ? '🟢 Вкл' : '🔴 Выкл'}</td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="editButton('${pageId}', ${idx})">✏️ Изменить</button>
          ${btn.target_type === 'page' && config.pages[btn.target_value] ? `<button class="btn btn-sm btn-outline" onclick="goToPage('${btn.target_value}')">Страница ➔</button>` : ''}
        </td>
      `;
      tbody.appendChild(tr);
    });
  }
}

function goToPage(pageId) {
  activePageId = pageId;
  document.querySelector('.nav-item[data-tab="pages"]').click();
  renderPagesList();
  renderActivePage();
}

// ---------------- START SCENARIOS ----------------

function renderStartFlow() {
  const currentScenario = config.start_flow.scenario || "default";
  document.querySelectorAll(".scenario-card").forEach(card => {
    const sc = card.getAttribute("data-scenario");
    const input = card.querySelector("input");
    if (sc === currentScenario) {
      card.classList.add("active");
      input.checked = true;
    } else {
      card.classList.remove("active");
      input.checked = false;
    }
  });

  const firstMsg = config.start_flow.first_message || {};
  document.getElementById("startFirstMediaUrl").value = firstMsg.media_url || "";
  document.getElementById("startFirstTextRu").value = (firstMsg.text && firstMsg.text["ru"]) || "";
}

function selectStartScenario(sc) {
  config.start_flow.scenario = sc;
  renderStartFlow();
}

async function saveStartFlow() {
  if (!config.start_flow.first_message) config.start_flow.first_message = {};
  if (!config.start_flow.first_message.text) config.start_flow.first_message.text = {};

  config.start_flow.first_message.media_url = document.getElementById("startFirstMediaUrl").value.trim();
  config.start_flow.first_message.text["ru"] = document.getElementById("startFirstTextRu").value.trim();

  await saveConfigToServer({ start_flow: config.start_flow });
  alert("Настройки сценария /start сохранены!");
}

// ---------------- NOTIFICATIONS ----------------

function renderNotificationsList() {
  const list = document.getElementById("notifsList");
  list.innerHTML = "";

  const knownNotifs = [
    { key: "subscription_expiring", title: "⏳ Скорое истечение подписки" },
    { key: "webhook_device_added", title: "📱 Добавлено новое устройство" },
    { key: "subscription_expired", title: "❌ Подписка истекла" },
    { key: "balance_low", title: "💰 Низкий баланс" },
  ];

  knownNotifs.forEach(item => {
    const div = document.createElement("div");
    div.className = "list-item" + (item.key === activeNotifKey ? " active" : "");
    div.textContent = item.title;
    div.onclick = () => {
      activeNotifKey = item.key;
      renderNotificationsList();
      renderActiveNotification();
    };
    list.appendChild(div);
  });

  renderActiveNotification();
}

function renderActiveNotification() {
  const notif = (config.notifications && config.notifications[activeNotifKey]) || {};
  document.getElementById("notifEditorTitle").textContent = "Уведомление: " + activeNotifKey;
  document.getElementById("notifEnabledToggle").checked = notif.enabled !== false;
  document.getElementById("notifMediaUrl").value = notif.media_url || "";
  document.getElementById("notifTextRu").value = (notif.text && notif.text["ru"]) || "";
}

async function saveCurrentNotification() {
  if (!config.notifications) config.notifications = {};
  const notif = config.notifications[activeNotifKey] || { text: {}, buttons: [] };

  notif.enabled = document.getElementById("notifEnabledToggle").checked;
  notif.media_url = document.getElementById("notifMediaUrl").value.trim();
  if (!notif.text) notif.text = {};
  notif.text["ru"] = document.getElementById("notifTextRu").value.trim();

  config.notifications[activeNotifKey] = notif;
  await saveConfigToServer({ notifications: config.notifications });
  alert("Шаблон уведомления сохранен!");
}

// ---------------- LANGUAGES ----------------

async function saveLanguageSettings() {
  const autoDetect = document.getElementById("autoDetectLangToggle").checked;
  const defLang = document.getElementById("defaultLangSelect").value;

  config.auto_detect_language = autoDetect;
  config.default_language = defLang;

  await saveConfigToServer({
    auto_detect_language: autoDetect,
    default_language: defLang
  });
  alert("Настройки языков сохранены!");
}

// ---------------- EMOJI PACKS ----------------

function renderEmojiPacks() {
  const list = document.getElementById("emojiPacksList");
  list.innerHTML = "";
  (config.emoji_packs || []).forEach(pack => {
    const div = document.createElement("div");
    div.className = "btn-card";
    div.style.marginTop = "10px";
    div.innerHTML = `
      <div>
        <strong>📦 ${pack.name}</strong>
        <div style="font-size:12px; color:var(--text-muted);">${pack.url}</div>
      </div>
    `;
    list.appendChild(div);
  });
}

async function addEmojiPack() {
  const url = document.getElementById("emojiPackUrlInput").value.trim();
  if (!url) return;

  try {
    const resp = await fetch("/api/customization/emoji-pack", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });
    if (resp.ok) {
      const pack = await resp.json();
      if (!config.emoji_packs) config.emoji_packs = [];
      config.emoji_packs.push(pack);
      document.getElementById("emojiPackUrlInput").value = "";
      renderEmojiPacks();
      alert("Набор эмодзи успешно добавлен!");
    }
  } catch (err) {
    console.error(err);
    alert("Ошибка добавления набора эмодзи");
  }
}

function insertEmojiModal() {
  const emojiId = prompt("Введите Telegram Premium Emoji ID:");
  if (emojiId) {
    const tag = `<tg-emoji emoji-id="${emojiId.trim()}">✨</tg-emoji>`;
    const textarea = document.getElementById("pageText");
    textarea.value += " " + tag;
  }
}

// ---------------- SERVER SYNC ----------------

async function saveConfigToServer(patchData) {
  try {
    const resp = await fetch("/api/customization/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patchData)
    });
    if (resp.ok) {
      config = await resp.json();
      showRestartWarning(config.needs_restart);
      updateStatusBadge(!config.needs_restart);
    }
  } catch (err) {
    console.error("Save config error:", err);
  }
}
