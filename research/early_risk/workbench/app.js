"use strict";

const PAGE_TITLE = "模拟手表检测台 — 模拟智能手表";
const LOADING_TITLE = "正在启动检测台 — 模拟智能手表";
const ERROR_TITLE = "检测台无法连接 — 模拟智能手表";
const CASES_PER_PAGE = 6;

const WEDA_CASE_ROWS = [
  ["weda-d01-u01_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D01", 0.057533, 0],
  ["weda-d01-u09_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D01", 0.03146, 0],
  ["weda-d01-u12_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D01", 0.059711, 0],
  ["weda-d01-u21_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D01", 0.078643, 0],
  ["weda-d01-u22_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D01", 0.090039, 0],
  ["weda-d01-u23_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D01", 0.061243, 0],
  ["weda-d01-u27_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D01", 0.038864, 0],
  ["weda-d01-u28_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D01", 0.134768, 0],
  ["weda-d02-u02_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D02", 0.284801, 0],
  ["weda-d02-u10_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D02", 0.049588, 0],
  ["weda-d02-u13_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D02", 0.002639, 0],
  ["weda-d03-u03_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D03", 0.102057, 0],
  ["weda-d03-u11_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D03", 0.040856, 0],
  ["weda-d03-u14_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D03", 0.147951, 0],
  ["weda-d03-u23_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D03", 0.150661, 0],
  ["weda-d03-u24_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D03", 0.222459, 0],
  ["weda-d03-u26_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D03", 0.152424, 0],
  ["weda-d03-u28_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D03", 0.431019, 0],
  ["weda-d03-u29_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D03", 0.103444, 0],
  ["weda-d04-u01_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D04", 0.212843, 0],
  ["weda-d04-u04_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D04", 0.214143, 0],
  ["weda-d04-u12_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D04", 0.236488, 0],
  ["weda-d04-u22_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D04", 0.170471, 0],
  ["weda-d04-u23_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D04", 0.162286, 0],
  ["weda-d04-u24_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D04", 0.079418, 0],
  ["weda-d04-u29_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D04", 0.082168, 0],
  ["weda-d04-u30_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D04", 0.035844, 0],
  ["weda-d05-u02_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D05", 0.080931, 0],
  ["weda-d05-u05_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D05", 0.135286, 0],
  ["weda-d05-u13_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D05", 0.258718, 0],
  ["weda-d06-u03_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D06", 0.049088, 0],
  ["weda-d06-u06_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D06", 0.333015, 0],
  ["weda-d06-u14_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D06", 0.041504, 0],
  ["weda-d07-u01_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D07", 0.880568, 1],
  ["weda-d07-u04_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D07", 0.256565, 0],
  ["weda-d07-u07_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D07", 0.02675, 0],
  ["weda-d08-u02_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D08", 0.059387, 0],
  ["weda-d08-u05_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D08", 0.942673, 1],
  ["weda-d08-u08_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D08", 0.385805, 0],
  ["weda-d09-u06_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D09", 0.616314, 0],
  ["weda-d09-u09_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D09", 0.188189, 0],
  ["weda-d09-u24_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D09", 0.091142, 0],
  ["weda-d09-u25_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D09", 0.167109, 0],
  ["weda-d09-u27_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D09", 0.214232, 0],
  ["weda-d09-u30_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D09", 0.574783, 0],
  ["weda-d09-u31_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D09", 0.414466, 0],
  ["weda-d10-u07_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D10", 0.102555, 0],
  ["weda-d10-u10_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D10", 0.211888, 0],
  ["weda-d10-u21_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D10", 0.221258, 0],
  ["weda-d10-u25_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D10", 0.097841, 0],
  ["weda-d10-u26_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D10", 0.012934, 0],
  ["weda-d10-u28_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D10", 0.052496, 0],
  ["weda-d10-u31_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D10", 0.031775, 0],
  ["weda-d11-u08_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D11", 0.1019, 0],
  ["weda-d11-u11_r01", "REAL_LAB_ACTIVITY", "YOUNG_ADULT", "D11", 0.039683, 0],
  ["weda-d11-u21_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D11", 0.292784, 0],
  ["weda-d11-u22_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D11", 0.357805, 0],
  ["weda-d11-u25_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D11", 0.158925, 0],
  ["weda-d11-u26_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D11", 0.086082, 0],
  ["weda-d11-u27_r01", "REAL_LAB_ACTIVITY", "OLDER_ADULT", "D11", 0.494255, 0],
  ["weda-f01-u01_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F01", 0.998873, 1],
  ["weda-f01-u03_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F01", 0.941192, 1],
  ["weda-f01-u05_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F01", 0.985161, 1],
  ["weda-f01-u09_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F01", 0.985562, 1],
  ["weda-f01-u11_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F01", 0.995324, 1],
  ["weda-f02-u02_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F02", 0.991323, 1],
  ["weda-f02-u04_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F02", 0.998528, 1],
  ["weda-f02-u06_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F02", 0.918948, 1],
  ["weda-f02-u10_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F02", 0.897357, 1],
  ["weda-f02-u12_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F02", 0.99996, 1],
  ["weda-f03-u03_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F03", 0.999274, 1],
  ["weda-f03-u05_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F03", 0.999702, 1],
  ["weda-f03-u07_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F03", 0.986261, 1],
  ["weda-f03-u11_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F03", 0.999723, 1],
  ["weda-f03-u13_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F03", 0.998971, 1],
  ["weda-f04-u04_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F04", 0.985247, 1],
  ["weda-f04-u06_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F04", 0.997017, 1],
  ["weda-f04-u08_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F04", 0.995068, 1],
  ["weda-f04-u12_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F04", 0.988392, 1],
  ["weda-f04-u14_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F04", 0.994962, 1],
  ["weda-f05-u01_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F05", 0.996759, 1],
  ["weda-f05-u05_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F05", 0.960282, 1],
  ["weda-f05-u07_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F05", 0.97658, 1],
  ["weda-f05-u09_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F05", 0.986034, 1],
  ["weda-f05-u13_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F05", 0.998834, 1],
  ["weda-f06-u02_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F06", 0.901064, 1],
  ["weda-f06-u06_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F06", 0.996081, 1],
  ["weda-f06-u08_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F06", 0.817624, 1],
  ["weda-f06-u10_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F06", 0.990961, 1],
  ["weda-f06-u14_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F06", 0.923456, 1],
  ["weda-f07-u01_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F07", 0.999573, 1],
  ["weda-f07-u03_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F07", 0.992559, 1],
  ["weda-f07-u07_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F07", 0.997655, 1],
  ["weda-f07-u09_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F07", 0.999582, 1],
  ["weda-f07-u11_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F07", 0.995049, 1],
  ["weda-f08-u02_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F08", 0.99808, 1],
  ["weda-f08-u04_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F08", 0.99885, 1],
  ["weda-f08-u08_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F08", 0.987896, 1],
  ["weda-f08-u10_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F08", 0.912556, 1],
  ["weda-f08-u12_r01", "SIMULATED_FALL", "YOUNG_ADULT", "F08", 0.970951, 1],
];

const wedaCases = WEDA_CASE_ROWS.map(([id, truth, age, label, score, alarms]) => {
  const participant = id.match(/u\d+/i)?.[0]?.toUpperCase() || "未知";
  const activity = label.startsWith("F") ? "受控模拟跌倒" : "受控日常活动";
  const ageText = age === "OLDER_ADULT" ? "老年参与者" : "年轻参与者";
  return {
    id,
    kind: truth === "SIMULATED_FALL" ? "fall" : "adl",
    source: "WEDA-FALL",
    sourceLabel: "WEDA-FALL 100 组",
    truth,
    truthLabel: truth === "SIMULATED_FALL" ? "受控模拟跌倒" : "受控日常活动",
    title: `${ageText}${activity}`,
    shortTitle: `${activity} · ${label}/${participant}`,
    note:
      truth === "SIMULATED_FALL"
        ? "年轻参与者在受控床垫条件下模拟跌倒；不代表真实老人意外跌倒。"
        : `${ageText}在受控环境中完成日常活动，用于核对误报。`,
    label,
    participant,
    rate: "50 Hz",
    axes: "6 轴 IMU",
    window: "4 秒窗口",
    model: "腕部跌倒检测",
    metricLabel: "已保存最高候选概率",
    score,
    alarms,
  };
});

const activityCases = [
  ["capture24-walking-p123", "走路候选", "walking"],
  ["capture24-eating-candidate-p123", "进食候选", "eating_candidate"],
  ["capture24-sleep-or-lying-candidate-p123", "睡眠或躺卧候选", "sleep_or_lying_candidate"],
  ["capture24-other-unknown-p123", "其他或未知活动", "other_unknown"],
].map(([id, title, label]) => ({
  id,
  kind: "activity",
  source: "CAPTURE-24",
  sourceLabel: "CAPTURE-24 恢复前缀子集",
  truth: "REAL_FREE_LIVING",
  truthLabel: "真实自由生活",
  title: `腕部活动识别：${title}`,
  shortTitle: `${title} · P123`,
  note: "来自 CAPTURE-24 恢复前缀子集；以年轻参与者为主，不是老人专项数据。",
  label,
  participant: "P123",
  rate: "20 Hz",
  axes: "3 轴加速度",
  window: "20 秒窗口",
  model: "腕部活动识别",
  metricLabel: "案例输入规格",
  score: null,
  alarms: null,
}));

const routineCase = {
  id: "synthetic-routine-100-v1",
  kind: "routine",
  source: "合成生活规律",
  sourceLabel: "100 天合成生活规律",
  truth: "SYNTHETIC_ROUTINE",
  truthLabel: "合成生活规律",
  title: "个人规律异常规则演示",
  shortTitle: "用餐、午睡与散步规律",
  note: "固定种子生成的 100 天、551 条生活事件，只验证规则分支，不是真实老人记录。",
  label: "meal_nap_walk_routine",
  participant: "合成档案 01",
  rate: "100 天",
  axes: "551 条事件",
  window: "生活规律",
  model: "个人规律异常",
  metricLabel: "保存的合成历史",
  score: null,
  alarms: null,
};

const caseCatalog = [...wedaCases, ...activityCases, routineCase];

const state = {
  dashboard: null,
  loadController: null,
  filter: "fall",
  query: "",
  page: 1,
  selectedCase: wedaCases.find((item) => item.kind === "fall"),
  playbackStep: -1,
  playbackTimer: null,
  clockTimer: null,
};

const ids = [
  "page-loading", "page-error", "page-error-message", "app-content", "service-status",
  "reload-form", "reload-button", "retry-form", "retry-button", "case-search-form",
  "case-search", "clear-search", "case-filters", "case-count", "case-list", "case-empty",
  "case-pagination-form", "case-prev", "case-next", "case-page-status", "watch-device", "watch-time",
  "watch-case-index", "watch-case-label", "watch-stage-label", "watch-result",
  "watch-score-fill", "watch-score-text", "device-connection", "playback-form", "run-button",
  "pause-button", "reset-button", "playback-status", "result-state", "selected-truth",
  "selected-case-id", "selected-case-title", "selected-case-note", "result-metric-label",
  "result-metric-value", "result-meter-fill", "result-metric-caption", "detection-pipeline",
  "pipeline-input", "pipeline-window", "pipeline-model", "pipeline-review", "external-count",
  "truth-notice", "limitations-list", "fixture-id",
];
const elements = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));

function createElement(tagName, options = {}) {
  const element = document.createElement(tagName);
  if (options.className) element.className = options.className;
  if (options.text !== undefined) element.textContent = String(options.text);
  if (options.attrs) {
    Object.entries(options.attrs).forEach(([name, value]) => {
      if (value !== undefined && value !== null) element.setAttribute(name, String(value));
    });
  }
  return element;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: { Accept: "application/json", ...(options.headers || {}) },
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    throw new Error(payload?.error?.message || `本机服务返回 ${response.status}。`);
  }
  return payload;
}

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function setLoading(isLoading) {
  elements["reload-button"].disabled = isLoading;
  elements["reload-button"].setAttribute("aria-busy", String(isLoading));
  if (isLoading) {
    document.title = LOADING_TITLE;
    elements["service-status"].textContent = "正在读取本机内容";
  }
}

function showPageError(error) {
  document.title = ERROR_TITLE;
  elements["page-loading"].hidden = true;
  elements["app-content"].hidden = true;
  elements["page-error"].hidden = false;
  const rawMessage = error?.message || "";
  elements["page-error-message"].textContent = /failed to fetch|networkerror/i.test(rawMessage)
    ? "无法连接本机 8010 服务。请双击启动脚本后，在这里重新连接。"
    : rawMessage || "本机内容暂时无法读取，请检查文件后重试。";
  elements["service-status"].textContent = "本机服务未连接";
  elements["service-status"].classList.add("is-error");
}

function showContent() {
  document.title = PAGE_TITLE;
  elements["page-loading"].hidden = true;
  elements["page-error"].hidden = true;
  elements["app-content"].hidden = false;
}

async function loadDashboard() {
  state.loadController?.abort();
  state.loadController = new AbortController();
  stopPlayback();
  setLoading(true);
  elements["page-loading"].hidden = false;
  elements["page-error"].hidden = true;
  try {
    const dashboard = await fetchJson("/api/workbench", { signal: state.loadController.signal });
    state.dashboard = dashboard;
    renderDashboardMeta(dashboard);
    renderCases();
    selectCase(state.selectedCase.id, false);
    showContent();
    elements["service-status"].textContent = "本机案例已就绪";
    elements["service-status"].classList.remove("is-error");
  } catch (error) {
    if (error.name !== "AbortError") showPageError(error);
  } finally {
    setLoading(false);
  }
}

function renderDashboardMeta(dashboard) {
  elements["truth-notice"].textContent = dashboard.truth.notice;
  elements["external-count"].textContent = `外部通知 ${dashboard.gate.p2.external_notification_count} 次`;
  elements["fixture-id"].textContent = `${dashboard.meta.evidence_level} · ${dashboard.fixture.id}`;
  elements["limitations-list"].replaceChildren(
    ...dashboard.truth.limitations.slice(0, 6).map((item) => createElement("li", { text: item })),
  );
}

function filteredCases() {
  const query = state.query.trim().toLowerCase();
  return caseCatalog.filter((item) => {
    const matchesFilter = state.filter === "all" || item.kind === state.filter;
    const matchesQuery = !query || `${item.id} ${item.shortTitle} ${item.participant}`.toLowerCase().includes(query);
    return matchesFilter && matchesQuery;
  });
}

function renderCases() {
  const matches = filteredCases();
  const pageCount = Math.max(1, Math.ceil(matches.length / CASES_PER_PAGE));
  state.page = Math.min(Math.max(1, state.page), pageCount);
  const start = (state.page - 1) * CASES_PER_PAGE;
  const pageItems = matches.slice(start, start + CASES_PER_PAGE);

  elements["case-count"].textContent = `${matches.length} 组`;
  elements["case-page-status"].textContent = `第 ${state.page} / ${pageCount} 页`;
  elements["case-prev"].disabled = state.page <= 1;
  elements["case-next"].disabled = state.page >= pageCount;
  elements["case-empty"].hidden = matches.length !== 0;

  const nodes = pageItems.map((item) => {
    const catalogIndex = caseCatalog.indexOf(item) + 1;
    const row = createElement("article", { className: "case-row", attrs: { role: "listitem" } });
    const button = createElement("button", {
      className: `case-item${item.id === state.selectedCase?.id ? " is-selected" : ""}`,
      attrs: {
        type: "button",
        "data-case-id": item.id,
        "aria-pressed": String(item.id === state.selectedCase?.id),
      },
    });
    const index = createElement("span", { className: "case-item__index", text: String(catalogIndex).padStart(3, "0") });
    const copy = createElement("span", { className: "case-item__copy" });
    copy.append(
      createElement("strong", { text: item.shortTitle }),
      createElement("code", { text: item.id }),
    );
    const status = createElement("span", {
      className: `case-item__status case-item__status--${item.kind}`,
      text: item.kind === "fall" ? "跌倒" : item.kind === "adl" ? "日常" : item.kind === "activity" ? "活动" : "规律",
    });
    button.append(index, copy, status);
    row.append(button);
    return row;
  });
  elements["case-list"].replaceChildren(...nodes);
}

function syncSelectionToVisibleCases() {
  const matches = filteredCases();
  const start = (state.page - 1) * CASES_PER_PAGE;
  const visibleCases = matches.slice(start, start + CASES_PER_PAGE);
  if (visibleCases.length && !visibleCases.some((item) => item.id === state.selectedCase?.id)) {
    selectCase(visibleCases[0].id, false);
  }
}

function truthClass(item) {
  if (item.kind === "fall") return "truth-tag truth-tag--fall";
  if (item.kind === "activity") return "truth-tag truth-tag--activity";
  if (item.kind === "routine") return "truth-tag truth-tag--routine";
  return "truth-tag";
}

function selectCase(caseId, announce = true) {
  const selected = caseCatalog.find((item) => item.id === caseId);
  if (!selected) return;
  resetPlayback(false);
  state.selectedCase = selected;
  renderCases();

  const catalogIndex = caseCatalog.indexOf(selected) + 1;
  elements["selected-truth"].className = truthClass(selected);
  elements["selected-truth"].textContent = selected.truthLabel;
  elements["selected-case-id"].textContent = selected.id;
  elements["selected-case-title"].textContent = selected.title;
  elements["selected-case-note"].textContent = selected.note;
  elements["result-metric-label"].textContent = selected.metricLabel;
  elements["result-metric-value"].textContent = "—";
  elements["result-metric-caption"].textContent = "开始检测后显示该案例已经保存的模型回放摘要。";
  elements["result-meter-fill"].style.width = "0%";

  elements["watch-case-index"].textContent = `案例 ${String(catalogIndex).padStart(3, "0")} / 105`;
  elements["watch-case-label"].textContent = selected.source;
  elements["pipeline-input"].textContent = `${selected.sourceLabel} · ${selected.truthLabel}`;
  elements["pipeline-window"].textContent = `${selected.rate} · ${selected.axes} · ${selected.window}`;
  elements["pipeline-model"].textContent = `${selected.model}等待运行`;
  elements["pipeline-review"].textContent = "外部通知保持关闭";

  const footer = document.querySelector(".watch-screen__footer");
  if (footer) {
    footer.children[0].lastChild.textContent = selected.kind === "routine" ? "EVENT" : "IMU";
    footer.children[1].textContent = selected.rate;
    footer.children[2].textContent = selected.axes;
  }
  if (announce) {
    elements["playback-status"].textContent = `已选择 ${selected.id}，可以开始检测。`;
  }
}

function stepCopy(step, item) {
  const copies = [
    ["读取腕部数据", `正在读取 ${item.sourceLabel}`],
    ["整理连续窗口", `${item.rate} · ${item.window}`],
    ["模型独立判断", `正在运行 ${item.model}`],
    ["结果复核", "核对来源、真实性和通知边界"],
  ];
  return copies[step] || copies[0];
}

function updatePipeline(step) {
  const items = elements["detection-pipeline"].querySelectorAll("li");
  items.forEach((item, index) => {
    item.classList.toggle("is-active", index === step);
    item.classList.toggle("is-complete", index < step || (step === 3 && index === 3));
  });
}

function startPlayback() {
  if (!state.selectedCase || state.playbackTimer) return;
  if (state.playbackStep >= 3) resetPlayback(false);
  elements["run-button"].disabled = true;
  elements["pause-button"].disabled = false;
  elements["run-button"].querySelector("span").textContent = "检测进行中";
  elements["watch-device"].dataset.state = "running";
  elements["result-state"].className = "result-state result-state--running";
  elements["result-state"].textContent = "检测中";

  const advance = () => {
    state.playbackStep += 1;
    if (state.playbackStep > 3) {
      finishPlayback();
      return;
    }
    const [label, detail] = stepCopy(state.playbackStep, state.selectedCase);
    updatePipeline(state.playbackStep);
    elements["watch-stage-label"].textContent = label;
    elements["watch-result"].textContent = detail;
    elements["watch-score-text"].textContent = `${Math.min(100, (state.playbackStep + 1) * 25)}%`;
    elements["watch-score-fill"].style.width = `${Math.min(100, (state.playbackStep + 1) * 25)}%`;
    elements["playback-status"].textContent = `步骤 ${state.playbackStep + 1} / 4：${detail}`;
  };

  advance();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  state.playbackTimer = window.setInterval(advance, reducedMotion ? 900 : 650);
}

function finishPlayback() {
  stopPlayback();
  const item = state.selectedCase;
  let result = "案例输入已就绪";
  let resultTone = "info";
  let metricValue = `${item.rate} · ${item.window}`;
  let caption = "该类别已登记；完整逐样本回放将在后端接入阶段完成。";
  let watchState = "complete";

  if (item.kind === "fall" || item.kind === "adl") {
    metricValue = formatPercent(item.score);
    if (item.alarms > 0 && item.kind === "fall") {
      result = "检测到跌倒候选";
      resultTone = "candidate";
      watchState = "candidate";
      caption = `已保存同源回放出现 ${item.alarms} 段候选；这是受控模拟跌倒接线核验，不是提前预测成绩。`;
    } else if (item.alarms > 0) {
      result = "出现误报候选";
      resultTone = "warning";
      watchState = "warning";
      caption = `日常活动中保存了 ${item.alarms} 段误报候选，需要人工复核。`;
    } else {
      result = "未触发跌倒候选";
      resultTone = "clear";
      caption = "保存的同源回放未出现候选告警；不等同于现实安全结论。";
    }
  } else if (item.kind === "activity") {
    result = "活动案例已就绪";
    metricValue = "20 Hz × 20 秒";
    caption = "当前页只完成前端交互预览；活动窗口的逐样本回放仍由产品接口提供。";
  } else if (item.kind === "routine") {
    result = "规律规则已登记";
    metricValue = "100 天 / 551 条";
    caption = "固定种子合成生活规律，只用于演示个人规律模块的输入与分支。";
  }

  elements["watch-device"].dataset.state = watchState;
  elements["watch-stage-label"].textContent = "检测完成";
  elements["watch-result"].textContent = result;
  elements["watch-score-fill"].style.width = item.score === null ? "100%" : `${Math.max(3, item.score * 100)}%`;
  elements["watch-score-text"].textContent = item.score === null ? "案例就绪" : formatPercent(item.score);
  elements["result-state"].className = `result-state result-state--${resultTone}`;
  elements["result-state"].textContent = result;
  elements["result-metric-value"].textContent = metricValue;
  elements["result-meter-fill"].style.width = item.score === null ? "100%" : `${Math.max(3, item.score * 100)}%`;
  elements["result-metric-caption"].textContent = caption;
  elements["pipeline-model"].textContent = `${item.model}已完成独立判断`;
  elements["pipeline-review"].textContent = "结果已显示 · 外部通知 0 次";
  elements["playback-status"].textContent = `${result}。结果来自已保存案例摘要，外部通知保持 0 次。`;
  elements["run-button"].querySelector("span").textContent = "重新检测";
  elements["run-button"].disabled = false;
  elements["pause-button"].disabled = true;
  state.playbackStep = 3;
  updatePipeline(3);
}

function pausePlayback() {
  if (!state.playbackTimer) return;
  stopPlayback();
  elements["watch-device"].dataset.state = "paused";
  elements["watch-stage-label"].textContent = "检测已暂停";
  elements["run-button"].querySelector("span").textContent = "继续检测";
  elements["run-button"].disabled = false;
  elements["pause-button"].disabled = true;
  elements["playback-status"].textContent = `检测停在步骤 ${state.playbackStep + 1} / 4，可以继续或重置。`;
}

function stopPlayback() {
  if (state.playbackTimer) window.clearInterval(state.playbackTimer);
  state.playbackTimer = null;
}

function resetPlayback(announce = true) {
  stopPlayback();
  state.playbackStep = -1;
  updatePipeline(-1);
  elements["watch-device"].dataset.state = "idle";
  elements["watch-stage-label"].textContent = "等待检测";
  elements["watch-result"].textContent = "准备就绪";
  elements["watch-score-fill"].style.width = "0%";
  elements["watch-score-text"].textContent = "尚未运行";
  elements["result-state"].className = "result-state result-state--neutral";
  elements["result-state"].textContent = "等待运行";
  elements["run-button"].disabled = false;
  elements["run-button"].querySelector("span").textContent = "开始检测";
  elements["pause-button"].disabled = true;
  if (announce) elements["playback-status"].textContent = "本次检测已重置，可以重新开始。";
}

function updateClock() {
  elements["watch-time"].textContent = new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());
}

function setupCaseControls() {
  elements["case-filters"].addEventListener("submit", (event) => {
    event.preventDefault();
    const button = event.submitter?.closest("button[data-filter]");
    if (!button) return;
    state.filter = button.dataset.filter;
    state.page = 1;
    elements["case-filters"].querySelectorAll("button[data-filter]").forEach((item) => {
      const active = item === button;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-pressed", String(active));
    });
    renderCases();
    syncSelectionToVisibleCases();
  });
  elements["case-list"].addEventListener("click", (event) => {
    const button = event.target.closest("button[data-case-id]");
    if (button) selectCase(button.dataset.caseId);
  });
  elements["case-search-form"].addEventListener("submit", (event) => {
    event.preventDefault();
    if (event.submitter?.id !== "clear-search") return;
    state.query = "";
    state.page = 1;
    elements["case-search"].value = "";
    elements["clear-search"].hidden = true;
    renderCases();
    syncSelectionToVisibleCases();
    elements["case-search"].focus();
  });
  elements["case-search"].addEventListener("input", (event) => {
    state.query = event.target.value;
    state.page = 1;
    elements["clear-search"].hidden = !state.query;
    renderCases();
    syncSelectionToVisibleCases();
  });
  elements["case-pagination-form"].addEventListener("submit", (event) => {
    event.preventDefault();
    if (event.submitter?.id === "case-prev") state.page -= 1;
    if (event.submitter?.id === "case-next") state.page += 1;
    renderCases();
    syncSelectionToVisibleCases();
  });
}

function setupNavigationTracking() {
  const links = [...document.querySelectorAll(".sidebar-nav__link")];
  const targets = links.map((link) => document.querySelector(link.getAttribute("href"))).filter(Boolean);
  if (!("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      links.forEach((link) => {
        const active = link.getAttribute("href") === `#${visible.target.id}`;
        link.classList.toggle("is-current", active);
        if (active) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
      });
    },
    { rootMargin: "-15% 0px -70% 0px", threshold: [0, 0.2, 0.5] },
  );
  targets.forEach((target) => observer.observe(target));
}

elements["reload-form"].addEventListener("submit", (event) => {
  event.preventDefault();
  loadDashboard();
});
elements["retry-form"].addEventListener("submit", (event) => {
  event.preventDefault();
  loadDashboard();
});
elements["playback-form"].addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.submitter?.id === "run-button") startPlayback();
  if (event.submitter?.id === "pause-button") pausePlayback();
  if (event.submitter?.id === "reset-button") resetPlayback();
});
window.addEventListener("beforeunload", () => {
  stopPlayback();
  state.loadController?.abort();
  if (state.clockTimer) window.clearInterval(state.clockTimer);
});

setupCaseControls();
setupNavigationTracking();
updateClock();
state.clockTimer = window.setInterval(updateClock, 30_000);
loadDashboard();
