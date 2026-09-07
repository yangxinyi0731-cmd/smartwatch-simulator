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

const wedaCases = WEDA_CASE_ROWS.map(([id, truth, , label, score, alarms]) => {
  const participant = id.match(/u\d+/i)?.[0]?.toUpperCase() || "未知";
  const activity = label.startsWith("F") ? "受控模拟跌倒" : "受控日常活动";
  return {
    id,
    kind: truth === "SIMULATED_FALL" ? "fall" : "adl",
    source: "WEDA-FALL",
    sourceLabel: "WEDA-FALL 100 组",
    truth,
    truthLabel: truth === "SIMULATED_FALL" ? "受控模拟跌倒" : "受控日常活动",
    title: `参与者${activity}`,
    shortTitle: `${activity} · ${label}/${participant}`,
    note:
      truth === "SIMULATED_FALL"
        ? "参与者在受控床垫环境中完成模拟跌倒，用于核对跌倒动作检测。"
        : "参与者在受控环境中完成日常活动，用于核对系统是否发生误判。",
    label,
    participant,
    rate: "50 Hz",
    axes: "6 轴 IMU",
    window: "4 秒窗口",
    model: "腕部跌倒检测",
    metricLabel: "跌倒特征匹配度",
    metricHelp: "表示这段动作与模型见过的受控跌倒动作有多相似；越高越相似，但不是现实跌倒概率，也不能单独用来报警。",
    score,
    alarms,
  };
});

const activityCases = [
  ["capture24-walking-p123", "走路动作", "walking"],
  ["capture24-eating-candidate-p123", "可能是进食", "eating_candidate"],
  ["capture24-sleep-or-lying-candidate-p123", "可能是睡眠或躺卧", "sleep_or_lying_candidate"],
  ["capture24-other-unknown-p123", "其他或无法判断", "other_unknown"],
].map(([id, title, label]) => ({
  id,
  kind: "activity",
  source: "CAPTURE-24",
  sourceLabel: "CAPTURE-24 恢复前缀子集",
  truth: "REAL_FREE_LIVING",
  truthLabel: "自由生活活动",
  title: `参与者腕部活动：${title}`,
  shortTitle: `${title} · P123`,
  note: "来自 CAPTURE-24 恢复前缀子集，是参与者的一段自由生活腕部活动数据。",
  label,
  participant: "P123",
  rate: "20 Hz",
  axes: "3 轴加速度",
  window: "20 秒窗口",
  model: "腕部活动识别",
  metricLabel: "活动模型最高输出值",
  metricHelp: "表示四类活动结果中排名第一的模型输出值；用于类别排序，不是安全或跌倒概率。",
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
  note: "程序固定生成 100 天、551 条生活事件，只验证规则分支，不是参与者生活记录。",
  label: "meal_nap_walk_routine",
  participant: "合成档案 01",
  rate: "100 天",
  axes: "551 条事件",
  window: "生活规律",
  model: "个人规律异常",
  metricLabel: "保存的合成历史",
  metricHelp: "显示这组合成案例覆盖的天数和生活事件数量；不是参与者的生活风险分数。",
  score: null,
  alarms: null,
};

const baseCaseCatalog = [...wedaCases, ...activityCases, routineCase];
let caseCatalog = [...baseCaseCatalog];

function buildSelfCollectedCases(dashboard) {
  return (dashboard.self_collected?.cases || []).map((item) => {
    const summary = item.analysis_summary || {};
    const durationSeconds = (item.duration_ms / 1000).toFixed(1);
    return {
      id: item.case_id,
      kind: "self",
      source: "自主采集",
      sourceLabel: `自主采集 · ${item.participant_id}`,
      truth: item.truth_category,
      truthLabel: `自主采集 · ${item.action_label}`,
      title: `自主采集动作：${item.action_label}`,
      shortTitle: `${item.action_label} · ${item.participant_id}`,
      note: `${item.participant_id} 使用 phyphox 完成的真实采集记录；登记含义为“${item.expected_meaning}”。`,
      label: item.action_code,
      participant: item.participant_id,
      rate: `${item.sample_rate_hz} Hz`,
      axes: "6 轴 IMU",
      window: `${durationSeconds} 秒连续记录`,
      model: "三个研究模型共同分析",
      metricLabel: "跌倒特征匹配度",
      metricHelp: "表示这段自主采集动作与受控模拟跌倒窗口的相似程度；用于工程复核，不是现实跌倒概率。",
      score: summary.fall_max_score,
      alarms: summary.fall_candidate_window_count,
    };
  });
}

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
  evidenceController: null,
  evidenceCache: new Map(),
  selectedEvidence: null,
  uploadFile: null,
  uploadController: null,
  initialSelectionApplied: false,
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
  "result-metric-value", "result-meter-fill", "result-metric-caption", "result-analysis-title",
  "result-analysis-summary", "result-analysis-activity", "result-analysis-fall", "result-analysis-risk",
  "result-analysis-evidence-list", "result-model-reasoning", "result-analysis-synthesis",
  "result-analysis-conclusion", "result-analysis-rule", "result-analysis-scope", "detection-pipeline",
  "case-pipeline-state", "external-count",
  "evidence", "evidence-intro", "evidence-badge", "evidence-loading", "evidence-error",
  "evidence-error-copy", "evidence-content", "motion-figure", "motion-title", "motion-caption",
  "chart-kicker", "chart-title", "chart-meta", "evidence-chart", "evidence-legend",
  "chart-summary", "evidence-source", "evidence-input", "evidence-method", "evidence-result",
  "evidence-limit", "truth-notice", "limitations-list", "fixture-id",
  "collection-count", "collection-status-copy", "heading-collection-count", "boundary-collection-count",
  "boundary-title", "filter-all-count", "filter-self-count", "upload-form", "upload-dropzone", "sensor-file",
  "upload-file-row", "upload-file-name", "upload-file-meta", "upload-remove", "acceleration-unit",
  "gyroscope-unit", "upload-error", "upload-error-copy", "upload-submit", "upload-process-title",
  "upload-pipeline", "upload-result", "upload-result-title", "upload-result-state", "upload-quality", "upload-activity",
  "upload-fall", "upload-persistence", "upload-evidence-list", "upload-conclusion", "upload-risk-meta",
  "upload-analysis-summary", "upload-model-reasoning", "upload-analysis-rule", "upload-analysis-scope",
  "upload-risk-chart", "upload-risk-summary", "upload-signal-chart", "upload-waveform-meta", "upload-waveform-summary",
  "case-risk-panel", "case-risk-chart", "case-risk-anchor",
  "case-risk-snapshots", "case-risk-summary",
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

const ANALYSIS_PIPELINE_STEPS = [
  { id: "validate", label: "检查输入数据", pending: "等待核对数据来源、通道和完整性。" },
  { id: "normalize", label: "统一数据标准", pending: "等待核对采样率、单位或事件时间。" },
  { id: "activity", label: "识别动作或规律", pending: "等待运行满足输入条件的活动或规律模型。" },
  { id: "fall", label: "筛查跌倒动作", pending: "等待检查连续六轴失稳与撞击特征。" },
  { id: "risk", label: "分析提前风险", pending: "等待逐秒核对 1、2、3 秒代理风险线索。" },
  { id: "explain", label: "生成结果分析", pending: "等待汇总实测依据、模型推导和适用边界。" },
];

const PIPELINE_STATUS_COPY = {
  PENDING: "等待",
  RUNNING: "运行中",
  COMPLETED: "已完成",
  INSUFFICIENT_DURATION: "数据不足",
  NOT_APPLICABLE: "未运行",
  FAILED: "未完成",
};

function normalizedPipeline(pipeline = []) {
  const byId = new Map((Array.isArray(pipeline) ? pipeline : []).map((item) => [item.id, item]));
  return ANALYSIS_PIPELINE_STEPS.map((step) => {
    const received = byId.get(step.id) || {};
    return {
      ...step,
      detail: received.detail || step.pending,
      status: received.status || "PENDING",
    };
  });
}

function renderSharedPipeline(container, pipeline = [], options = {}) {
  const { activeIndex = -1, final = false } = options;
  const items = normalizedPipeline(pipeline);
  const nodes = items.map((item, index) => {
    let status = "PENDING";
    if (final) status = item.status;
    else if (index < activeIndex) status = item.status === "PENDING" ? "COMPLETED" : item.status;
    else if (index === activeIndex) status = "RUNNING";
    const detail = !final && (activeIndex < 0 || index > activeIndex) ? item.pending : item.detail;
    const row = createElement("li", {
      className: `pipeline-status--${status.toLowerCase().replaceAll("_", "-")}`,
      attrs: { "data-pipeline-step": item.id, "data-status": status },
    });
    const number = createElement("span", { text: String(index + 1).padStart(2, "0") });
    const copy = createElement("div");
    copy.append(
      createElement("strong", { text: item.label }),
      createElement("small", { text: detail }),
    );
    const badge = createElement("em", { text: PIPELINE_STATUS_COPY[status] || "等待" });
    row.append(number, copy, badge);
    return row;
  });
  container.replaceChildren(...nodes);
}

renderSharedPipeline(elements["upload-pipeline"]);
renderSharedPipeline(elements["detection-pipeline"]);

const SVG_NAMESPACE = "http://www.w3.org/2000/svg";

function createSvgElement(tagName, attributes = {}, text = null) {
  const element = document.createElementNS(SVG_NAMESPACE, tagName);
  Object.entries(attributes).forEach(([name, value]) => {
    if (value !== undefined && value !== null) element.setAttribute(name, String(value));
  });
  if (text !== null) element.textContent = String(text);
  return element;
}

function appendSvgText(svg, text, x, y, className, anchor = "start") {
  svg.append(createSvgElement("text", { x, y, class: className, "text-anchor": anchor }, text));
}

function motionPresentation(item) {
  if (item.kind === "fall") {
    return { motion: "fall", title: "受控模拟跌倒", caption: "线条人物标出跌倒动作与腕表位置；不是参与者影像。" };
  }
  if (item.kind === "adl") {
    return { motion: "daily", title: "受控日常活动", caption: "用日常伸手动作代表这一类受控活动；不推断具体动作名称。" };
  }
  if (item.kind === "routine") {
    return { motion: "routine", title: "生活规律时间分布", caption: "时钟示意用餐、午睡和散步发生时间；不是参与者影像。" };
  }
  if (item.kind === "self") {
    const selfMotions = {
      walking: ["walking", "正常走路"],
      normal_sit: ["daily", "正常坐下"],
      quick_sit: ["daily", "快速坐下"],
      bend_pickup: ["daily", "弯腰捡东西"],
      large_arm_swing: ["daily", "大幅度摆臂"],
      safe_imbalance: ["fall", "安全失衡"],
    };
    const [motion, title] = selfMotions[item.label] || ["unknown", item.shortTitle.split(" · ")[0]];
    return { motion, title, caption: "线条人物只说明采集时登记的动作；实际判断依据来自六轴波形和模型输出。" };
  }
  if (item.label === "walking") {
    return { motion: "walking", title: "走路动作", caption: "线条人物只说明案例类别；实际依据来自腕部三轴信号。" };
  }
  if (item.label === "eating_candidate") {
    return { motion: "eating", title: "进食候选活动", caption: "线条人物只说明候选类别；不是摄像头识别结果。" };
  }
  if (item.label === "sleep_or_lying_candidate") {
    return { motion: "resting", title: "睡眠或躺卧候选", caption: "线条人物只说明候选类别；不是参与者影像。" };
  }
  return { motion: "unknown", title: "其他或无法判断", caption: "问号表示类别不确定；不把未知动作强行解释成具体活动。" };
}

function evidenceMethod(item) {
  if (item.kind === "fall" || item.kind === "adl") {
    return "把连续 4 秒六轴腕部窗口作为整体，与固定跌倒模型学习到的动作模式比较。";
  }
  if (item.kind === "activity") {
    return "把连续 20 秒三轴腕部加速度送入活动识别模型，再把最高输出类别与登记标签并列核对。";
  }
  if (item.kind === "self") {
    return "同一段六轴记录依次运行活动识别、跌倒候选筛查和提前 1/2/3 秒研究模型，再用原始波形交叉核对。";
  }
  return "运行生活规律模型，逐日比较同一合成档案中用餐、午睡和散步的时间、次数与持续时长。";
}

function pendingEvidenceConclusion(item) {
  if (item.kind === "fall" || item.kind === "adl") return "开始检测后，结合保存匹配度与跌倒动作记录生成。";
  if (item.kind === "activity") return "开始检测后，显示活动模型的实际输出以及它是否与登记类别一致。";
  if (item.kind === "self") return "开始检测后，显示三个模型的实际输出、关键波形和生成结论。";
  return "开始检测后，显示规律模型实际标记了多少项规则偏离。";
}

function completedEvidenceConclusion(item, result) {
  if (item.kind === "fall" || item.kind === "adl") {
    return `${result}；匹配度 ${formatPercent(item.score)}，保存记录 ${item.alarms} 段。`;
  }
  if (item.kind === "activity") return `${result}；登记类别为“${item.shortTitle.split(" · ")[0]}”。`;
  if (item.kind === "self") return `${result}；跌倒特征匹配度 ${formatPercent(item.score)}，达到筛查条件的窗口 ${item.alarms} 个。`;
  return `${result}；输入为 100 天、551 条固定种子合成事件。`;
}

function setEvidenceLegend(items) {
  const nodes = items.map(({ className, label }) => {
    const row = createElement("span");
    row.append(createElement("i", { className, attrs: { "aria-hidden": "true" } }), document.createTextNode(label));
    return row;
  });
  elements["evidence-legend"].replaceChildren(...nodes);
}

function renderSensorChart(evidence) {
  const svg = elements["evidence-chart"];
  const width = 760;
  const height = 356;
  const paddingLeft = 64;
  const paddingRight = 20;
  const paddingTop = 80;
  const paddingBottom = 42;
  const panelGap = evidence.series.length > 1 ? 52 : 0;
  const panelHeight = (height - paddingTop - paddingBottom - panelGap) / evidence.series.length;
  const durationMs = Math.max(1, evidence.stream.duration_ms);
  const xFor = (offsetMs) => paddingLeft + (Math.min(durationMs, Math.max(0, offsetMs)) / durationMs) * (width - paddingLeft - paddingRight);

  const title = createSvgElement("title", { id: "evidence-chart-title" }, "当前案例的真实传感器波形");
  const description = createSvgElement(
    "desc",
    { id: "evidence-chart-description" },
    `显示 ${evidence.stream.displayed_point_count} 个实际抽样点；每条曲线按自己的单位单独缩放。`,
  );
  svg.replaceChildren(title, description);
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

  evidence.events.forEach((event, index) => {
    const startX = xFor(event.start_offset_ms);
    const endX = xFor(event.end_offset_ms);
    const truthTone = evidence.truth_category === "SIMULATED_FALL" ? "fall" : "activity";
    svg.append(createSvgElement("rect", {
      x: startX,
      y: paddingTop - 8,
      width: Math.max(1, endX - startX),
      height: height - paddingTop - paddingBottom + 8,
      class: `evidence-chart__truth evidence-chart__truth--${truthTone}`,
    }));
    if (index === 0 && endX - startX > 48) {
      const annotationText = `登记动作：${event.label}`;
      const annotationWidth = Math.min(260, Math.max(128, annotationText.length * 15 + 24));
      svg.append(createSvgElement("rect", {
        x: paddingLeft,
        y: 12,
        width: annotationWidth,
        height: 28,
        rx: 6,
        class: `evidence-chart__annotation-bg evidence-chart__annotation-bg--${truthTone}`,
      }));
      appendSvgText(svg, annotationText, paddingLeft + 11, 31, `evidence-chart__annotation evidence-chart__annotation--${truthTone}`);
    }
  });

  [0, 0.25, 0.5, 0.75, 1].forEach((ratio) => {
    const x = paddingLeft + ratio * (width - paddingLeft - paddingRight);
    svg.append(createSvgElement("line", { x1: x, x2: x, y1: paddingTop - 4, y2: height - paddingBottom, class: "evidence-chart__grid" }));
    appendSvgText(svg, `${(durationMs * ratio / 1000).toFixed(ratio === 0 ? 0 : 1)}s`, x, height - 11, "evidence-chart__tick", "middle");
  });

  const peakSummaries = [];
  evidence.series.forEach((series, seriesIndex) => {
    const panelTop = paddingTop + seriesIndex * (panelHeight + panelGap);
    const panelBottom = panelTop + panelHeight;
    const values = series.values;
    const maximum = Math.max(...values.map((point) => Number(point[1])), 0.000001);
    const yMaximum = maximum * 1.08;
    const yFor = (value) => panelBottom - (Math.max(0, Number(value)) / yMaximum) * panelHeight;

    [0, 0.5, 1].forEach((ratio) => {
      const y = panelTop + ratio * panelHeight;
      svg.append(createSvgElement("line", { x1: paddingLeft, x2: width - paddingRight, y1: y, y2: y, class: ratio === 1 ? "evidence-chart__axis" : "evidence-chart__grid" }));
    });
    appendSvgText(svg, `${series.label} · ${series.unit}`, paddingLeft, panelTop - 13, "evidence-chart__label");
    appendSvgText(svg, yMaximum.toFixed(yMaximum >= 10 ? 1 : 2), paddingLeft - 10, panelTop + 5, "evidence-chart__tick", "end");
    appendSvgText(svg, "0", paddingLeft - 10, panelBottom + 4, "evidence-chart__tick", "end");

    const pathData = values.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command}${xFor(point[0]).toFixed(2)},${yFor(point[1]).toFixed(2)}`;
    }).join(" ");
    svg.append(createSvgElement("path", { d: pathData, class: `evidence-chart__line evidence-chart__line--${seriesIndex}` }));

    const peak = values.reduce((current, point) => Number(point[1]) > Number(current[1]) ? point : current, values[0]);
    svg.append(createSvgElement("circle", {
      cx: xFor(peak[0]), cy: yFor(peak[1]), r: 4,
      class: `evidence-chart__peak evidence-chart__peak--${seriesIndex}`,
    }));
    peakSummaries.push(`${series.label}峰值 ${Number(peak[1]).toFixed(series.unit === "m/s²" ? 1 : 2)} ${series.unit}（${(Number(peak[0]) / 1000).toFixed(1)} 秒）`);
  });

  elements["chart-summary"].textContent = `${peakSummaries.join("；")}。峰值只描述输入变化，不等同于模型作出判断的单一原因。`;
  const legend = [
    { className: "", label: "实际加速度合量（动作强弱）" },
  ];
  if (evidence.series.length > 1) legend.push({ className: "legend-blue", label: "实际角速度合量（转动快慢）" });
  if (evidence.events.length) {
    legend.push({
      className: evidence.truth_category === "SIMULATED_FALL" ? "legend-red" : "legend-activity",
      label: evidence.truth_category === "SIMULATED_FALL" ? "已登记跌倒标签区间" : "已登记活动标签区间",
    });
  }
  setEvidenceLegend(legend);
}

function renderRoutineChart(evidence) {
  const svg = elements["evidence-chart"];
  const width = 760;
  const height = 270;
  const paddingLeft = 80;
  const paddingRight = 18;
  const paddingTop = 34;
  const paddingBottom = 30;
  const plotWidth = width - paddingLeft - paddingRight;
  const rowHeight = (height - paddingTop - paddingBottom) / evidence.days.length;
  const xFor = (minute) => paddingLeft + (Math.min(1440, Math.max(0, minute)) / 1440) * plotWidth;

  const title = createSvgElement("title", { id: "evidence-chart-title" }, "最近十四天的合成生活规律时间图");
  const description = createSvgElement(
    "desc",
    { id: "evidence-chart-description" },
    "每一行代表一天，圆形是用餐，三角形是散步，方形是午睡；横向位置表示一天中的发生时间。",
  );
  svg.replaceChildren(title, description);

  [0, 360, 720, 1080, 1440].forEach((minute) => {
    const x = xFor(minute);
    svg.append(createSvgElement("line", { x1: x, x2: x, y1: paddingTop - 12, y2: height - paddingBottom, class: "evidence-chart__grid" }));
    appendSvgText(svg, `${String(Math.round(minute / 60)).padStart(2, "0")}:00`, x, height - 10, "evidence-chart__tick", "middle");
  });

  let displayedEventCount = 0;
  evidence.days.forEach((day, dayIndex) => {
    const y = paddingTop + dayIndex * rowHeight + rowHeight / 2;
    svg.append(createSvgElement("line", { x1: paddingLeft, x2: width - paddingRight, y1: y, y2: y, class: "evidence-chart__routine-row" }));
    appendSvgText(svg, day.day.slice(5), paddingLeft - 9, y + 3, "evidence-chart__tick", "end");
    day.events.forEach((event) => {
      displayedEventCount += 1;
      const x = xFor(event.start_minute);
      if (event.event_type === "meal") {
        svg.append(createSvgElement("circle", { cx: x, cy: y, r: 4.2, class: "evidence-chart__event--meal" }));
      } else if (event.event_type === "walk") {
        svg.append(createSvgElement("path", { d: `M${x},${y - 5} L${x + 5},${y + 4} L${x - 5},${y + 4} Z`, class: "evidence-chart__event--walk" }));
      } else if (event.event_type === "nap") {
        svg.append(createSvgElement("rect", { x: x - 4, y: y - 4, width: 8, height: 8, rx: 1, class: "evidence-chart__event--nap" }));
      }
    });
  });

  appendSvgText(svg, "合成日期", paddingLeft - 9, 18, "evidence-chart__label", "end");
  appendSvgText(svg, "一天中的发生时间", paddingLeft, 18, "evidence-chart__label");
  elements["chart-summary"].textContent = `图中显示最近 ${evidence.days.length} 天的 ${displayedEventCount} 条合成事件；完整档案为 ${evidence.profile.history_days} 天、${evidence.profile.event_count} 条。形状与文字共同区分事件类型。`;
  setEvidenceLegend([
    { className: "legend-meal", label: "用餐（圆形）" },
    { className: "legend-walk", label: "散步（三角形）" },
    { className: "legend-nap", label: "午睡（方形）" },
  ]);
}

function renderRiskChart(svg, risk, options = {}) {
  const timeline = risk?.timeline || [];
  const width = 760;
  const height = 280;
  const left = 54;
  const right = 18;
  const top = 24;
  const bottom = 38;
  const titleId = options.titleId || "risk-chart-title";
  const descriptionId = options.descriptionId || "risk-chart-description";
  const title = createSvgElement("title", { id: titleId }, options.title || "逐秒提前风险研究分数");
  if (!timeline.length) {
    const description = createSvgElement("desc", { id: descriptionId }, "当前记录不足一个 1 秒六轴窗口，不能绘制研究分数。");
    svg.replaceChildren(title, description);
    appendSvgText(svg, "需要至少 1 秒连续六轴数据", width / 2, height / 2, "risk-chart__empty", "middle");
    return;
  }
  const durationMs = Math.max(...timeline.map((point) => Number(point.offset_ms)), 1);
  const xFor = (offsetMs) => left + (Number(offsetMs) / durationMs) * (width - left - right);
  const yFor = (value) => top + (1 - Number(value)) * (height - top - bottom);
  const anchorMs = Number(options.anchorMs);
  const anchorCopy = Number.isFinite(anchorMs)
    ? `竖线标出数据集跌倒区间开始代理锚点 ${ (anchorMs / 1000).toFixed(1) } 秒。`
    : "当前记录没有已登记代理锚点。";
  const description = createSvgElement(
    "desc",
    { id: descriptionId },
    `三条曲线分别是未来 1、2、3 秒公开代理标签研究分数。${anchorCopy}`,
  );
  svg.replaceChildren(title, description);

  [0, 0.25, 0.5, 0.75, 1].forEach((value) => {
    const y = yFor(value);
    svg.append(createSvgElement("line", { x1: left, x2: width - right, y1: y, y2: y, class: "risk-chart__grid" }));
    appendSvgText(svg, value.toFixed(2), left - 8, y + 4, "risk-chart__tick", "end");
  });
  [0, 0.25, 0.5, 0.75, 1].forEach((ratio) => {
    const x = left + ratio * (width - left - right);
    svg.append(createSvgElement("line", { x1: x, x2: x, y1: top, y2: height - bottom, class: "risk-chart__grid" }));
    appendSvgText(svg, `${(durationMs * ratio / 1000).toFixed(ratio === 0 ? 0 : 1)}s`, x, height - 13, "risk-chart__tick", "middle");
  });
  appendSvgText(svg, "研究分数", left, 14, "risk-chart__label");

  const definitions = [
    { horizon: "1", key: "risk_1s", className: "risk-chart__line--1" },
    { horizon: "2", key: "risk_2s", className: "risk-chart__line--2" },
    { horizon: "3", key: "risk_3s", className: "risk-chart__line--3" },
  ];
  definitions.forEach((definition) => {
    const threshold = Number(risk.thresholds?.[definition.horizon]);
    if (Number.isFinite(threshold)) {
      const thresholdY = yFor(threshold);
      svg.append(createSvgElement("line", {
        x1: left, x2: width - right, y1: thresholdY, y2: thresholdY,
        class: `risk-chart__threshold risk-chart__threshold--${definition.horizon}`,
      }));
      appendSvgText(svg, `${definition.horizon}s 阈值 ${threshold.toFixed(2)}`, width - right - 3, thresholdY - 4, "risk-chart__threshold-label", "end");
    }
    const path = timeline.map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command}${xFor(point.offset_ms).toFixed(2)},${yFor(point[definition.key]).toFixed(2)}`;
    }).join(" ");
    svg.append(createSvgElement("path", { d: path, class: `risk-chart__line ${definition.className}` }));
  });
  if (Number.isFinite(anchorMs) && anchorMs >= 0 && anchorMs <= durationMs) {
    const anchorX = xFor(anchorMs);
    svg.append(createSvgElement("line", { x1: anchorX, x2: anchorX, y1: top, y2: height - bottom, class: "risk-chart__anchor" }));
    appendSvgText(svg, "代理锚点", anchorX - 4, top + 12, "risk-chart__anchor-label", "end");
  }
}

function renderUploadSignalChart(waveform, quality) {
  const svg = elements["upload-signal-chart"];
  const width = 760;
  const height = 240;
  const left = 54;
  const right = 18;
  const top = 22;
  const bottom = 34;
  const acceleration = waveform.acceleration_magnitude || [];
  const rotation = waveform.angular_velocity_magnitude || [];
  const durationMs = Math.max(
    acceleration.at(-1)?.[0] || 1,
    rotation.at(-1)?.[0] || 1,
  );
  const title = createSvgElement("title", { id: "upload-signal-title" }, "上传记录的真实加速度与角速度合量波形");
  const description = createSvgElement(
    "desc",
    { id: "upload-signal-description" },
    `显示重采样记录中的 ${waveform.displayed_point_count} 个实际抽样点；两条曲线分别按自己的单位缩放。`,
  );
  svg.replaceChildren(title, description);
  const xFor = (offsetMs) => left + (Number(offsetMs) / durationMs) * (width - left - right);
  [0, 0.25, 0.5, 0.75, 1].forEach((ratio) => {
    const x = left + ratio * (width - left - right);
    svg.append(createSvgElement("line", { x1: x, x2: x, y1: top, y2: height - bottom, class: "risk-chart__grid" }));
    appendSvgText(svg, `${(durationMs * ratio / 1000).toFixed(ratio === 0 ? 0 : 1)}s`, x, height - 10, "risk-chart__tick", "middle");
  });
  const panels = [
    { values: acceleration, label: "加速度合量 · m/s²", className: "risk-chart__line--1" },
    { values: rotation, label: "角速度合量 · rad/s", className: "risk-chart__line--2" },
  ];
  const gap = 22;
  const panelHeight = (height - top - bottom - gap) / 2;
  const summaries = [];
  panels.forEach((panel, index) => {
    const panelTop = top + index * (panelHeight + gap);
    const panelBottom = panelTop + panelHeight;
    const maximum = Math.max(...panel.values.map((point) => Number(point[1])), 0.000001);
    const yFor = (value) => panelBottom - Number(value) / (maximum * 1.08) * panelHeight;
    svg.append(createSvgElement("line", { x1: left, x2: width - right, y1: panelBottom, y2: panelBottom, class: "risk-chart__grid" }));
    appendSvgText(svg, panel.label, left, panelTop - 5, "risk-chart__label");
    appendSvgText(svg, maximum.toFixed(index === 0 ? 1 : 2), left - 7, panelTop + 5, "risk-chart__tick", "end");
    const path = panel.values.map((point, pointIndex) => {
      const command = pointIndex === 0 ? "M" : "L";
      return `${command}${xFor(point[0]).toFixed(2)},${yFor(point[1]).toFixed(2)}`;
    }).join(" ");
    svg.append(createSvgElement("path", { d: path, class: `risk-chart__line ${panel.className}` }));
    const peak = panel.values.reduce((best, point) => Number(point[1]) > Number(best[1]) ? point : best, panel.values[0]);
    summaries.push(`${panel.label.split(" · ")[0]}峰值 ${Number(peak[1]).toFixed(index === 0 ? 2 : 3)}（${(Number(peak[0]) / 1000).toFixed(1)} 秒）`);
  });
  elements["upload-waveform-meta"].textContent = `${quality.normalized_rate_hz} Hz · ${quality.normalized_sample_count} 点 · 显示 ${waveform.displayed_point_count} 点`;
  elements["upload-waveform-summary"].textContent = `${summaries.join("；")}。峰值只是依据之一，系统没有凭单次峰值直接下结论。`;
}

function renderCaseRisk(evidence) {
  const risk = evidence.analysis?.early_risk_model;
  if (!risk || risk.status !== "COMPLETED") {
    elements["case-risk-panel"].hidden = true;
    return;
  }
  elements["case-risk-panel"].hidden = false;
  const anchorMs = risk.proxy_anchor_offset_ms;
  elements["case-risk-anchor"].textContent = Number.isFinite(Number(anchorMs))
    ? `数据集代理锚点 ${(Number(anchorMs) / 1000).toFixed(1)} 秒`
    : "日常案例 · 无跌倒代理锚点";
  renderRiskChart(elements["case-risk-chart"], risk, {
    title: "当前公开案例逐秒提前风险研究分数",
    titleId: "case-risk-svg-title",
    descriptionId: "case-risk-description",
    anchorMs,
  });
  const maxima = risk.max_scores;
  const attention = risk.attention_detected;
  elements["case-risk-summary"].textContent = `本文件最高研究分数：1 秒 ${Number(maxima["1"]).toFixed(3)}、2 秒 ${Number(maxima["2"]).toFixed(3)}、3 秒 ${Number(maxima["3"]).toFixed(3)}；${Object.values(attention).some(Boolean) ? "至少一个时间点达到公开模型关注阈值。" : "没有时间点达到三个公开模型的各自关注阈值。"}这不是现实个人跌倒概率。`;
  const snapshots = state.dashboard?.public_risk_model?.evaluation_snapshot_at_exact_lead || {};
  const nodes = ["1", "2", "3"].map((horizon) => {
    const item = snapshots[horizon];
    const row = createElement("div");
    row.append(
      createElement("span", { text: `恰好提前 ${horizon} 秒` }),
      createElement("strong", { text: item ? `${item.detected_at_or_above_threshold} / ${item.eligible_simulated_fall_count}` : "—" }),
      createElement("small", { text: "独立参与者评估快照" }),
    );
    return row;
  });
  elements["case-risk-snapshots"].replaceChildren(...nodes);
}

function showEvidenceLoading(item) {
  elements["evidence"].dataset.state = "loading";
  elements["evidence-loading"].hidden = false;
  elements["evidence-error"].hidden = true;
  elements["evidence-content"].hidden = true;
  elements["case-risk-panel"].hidden = true;
  elements["evidence-badge"].className = "evidence-badge";
  elements["evidence-badge"].textContent = "正在核对";
  elements["evidence-intro"].textContent = `正在读取 ${item.id} 对应的本机依据，不生成随机曲线。`;
  elements["case-pipeline-state"].textContent = "正在读取案例";
  elements["playback-status"].textContent = `正在读取 ${item.id} 的实际数据，完成后可以开始检测。`;
  renderSharedPipeline(elements["detection-pipeline"]);
}

function showEvidenceError(item, error) {
  elements["evidence"].dataset.state = "error";
  elements["evidence-loading"].hidden = true;
  elements["evidence-content"].hidden = true;
  elements["evidence-error"].hidden = false;
  elements["case-risk-panel"].hidden = true;
  elements["evidence-error-copy"].textContent = `${error?.message || "本机文件暂时无法读取。"} 页面不会用示意波形替代。`;
  elements["evidence-badge"].className = "evidence-badge is-error";
  elements["evidence-badge"].textContent = "依据不可用";
  elements["evidence-intro"].textContent = `${item.id} 的检测流程仍可演示，但缺失依据时不能把图表当作证据。`;
  elements["case-pipeline-state"].textContent = "实际依据不可用";
  elements["playback-status"].textContent = `${item.id} 的实际依据读取失败，本次不能开始检测。`;
  const failed = normalizedPipeline().map((step, index) => ({
    ...step,
    status: index === 0 ? "FAILED" : "PENDING",
    detail: index === 0 ? "没有读取到可核验的本机案例文件。" : step.pending,
  }));
  renderSharedPipeline(elements["detection-pipeline"], failed, { final: true });
}

function renderEvidence(item, evidence) {
  state.selectedEvidence = evidence;
  const motion = motionPresentation(item);
  elements["evidence"].dataset.state = "ready";
  elements["evidence-loading"].hidden = true;
  elements["evidence-error"].hidden = true;
  elements["evidence-content"].hidden = false;
  elements["motion-figure"].dataset.motion = motion.motion;
  elements["motion-title"].textContent = motion.title;
  elements["motion-caption"].textContent = motion.caption;
  elements["evidence-method"].textContent = evidenceMethod(item);
  elements["evidence-result"].textContent = state.playbackStep >= 5
    ? completedEvidenceConclusion(item, elements["result-state"].textContent)
    : pendingEvidenceConclusion(item);
  elements["case-pipeline-state"].textContent = "数据已核对 · 等待运行";
  if (state.playbackStep < 0) {
    elements["playback-status"].textContent = `已选择 ${item.id}，实际数据已核对，可以开始检测。`;
  }
  renderSharedPipeline(elements["detection-pipeline"], evidence.pipeline);

  if (evidence.evidence_type === "sensor_waveform") {
    const seconds = (evidence.stream.duration_ms / 1000).toFixed(1);
    const qualityText = evidence.quality.flag_count
      ? `保留 ${evidence.quality.flag_count} 项质量标记`
      : "未登记质量异常";
    elements["evidence-badge"].className = "evidence-badge is-verified";
    elements["evidence-badge"].textContent = "本机文件已核验";
    elements["evidence-intro"].textContent = "波形来自所选案例的本机登记文件；示意图只帮助理解动作类别。";
    elements["chart-kicker"].textContent = "实际信号";
    elements["chart-title"].textContent = `由真实${evidence.stream.axis_count}轴信号计算的合量波形`;
    elements["chart-meta"].textContent = `${evidence.stream.sample_rate_hz} Hz · ${evidence.stream.sample_count} 个原始采样 · 显示 ${evidence.stream.displayed_point_count} 个实际抽样点`;
    elements["evidence-source"].textContent = `${evidence.source_label} · 文件哈希与数组形状已核对 · ${qualityText}`;
    elements["evidence-input"].textContent = `${evidence.stream.sample_rate_hz} Hz · ${evidence.stream.axis_count} 轴 · 记录 ${seconds} 秒；模型窗口为 ${item.window}`;
    elements["evidence-limit"].textContent = evidence.limitations.slice(1).join(" ");
    renderSensorChart(evidence);
    renderCaseRisk(evidence);
  } else {
    elements["evidence-badge"].className = "evidence-badge is-synthetic";
    elements["evidence-badge"].textContent = "固定种子合成";
    elements["evidence-intro"].textContent = "这类案例没有腕部传感器流，因此用事件时间图展示规律依据，不伪造波形。";
    elements["chart-kicker"].textContent = "规律输入";
    elements["chart-title"].textContent = "最近 14 天合成规律时间图";
    elements["chart-meta"].textContent = `固定种子 ${evidence.profile.seed} · 完整档案 ${evidence.profile.history_days} 天 / ${evidence.profile.event_count} 条事件`;
    elements["evidence-source"].textContent = `${evidence.source_label} · 固定种子 ${evidence.profile.seed} · 文件内容已读取`;
    elements["evidence-input"].textContent = `${evidence.profile.history_days} 天 · ${evidence.profile.event_count} 条用餐、午睡和散步事件`;
    elements["evidence-limit"].textContent = evidence.limitations.join(" ");
    renderRoutineChart(evidence);
    elements["case-risk-panel"].hidden = true;
  }
}

async function loadCaseEvidence(item) {
  state.evidenceController?.abort();
  state.evidenceController = new AbortController();
  showEvidenceLoading(item);
  try {
    let evidence = state.evidenceCache.get(item.id);
    if (!evidence) {
      evidence = await fetchJson(`/api/case-evidence/${encodeURIComponent(item.id)}`, {
        signal: state.evidenceController.signal,
      });
      state.evidenceCache.set(item.id, evidence);
    }
    if (state.selectedCase?.id === item.id) renderEvidence(item, evidence);
  } catch (error) {
    if (error.name !== "AbortError" && state.selectedCase?.id === item.id) showEvidenceError(item, error);
  }
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

function modelStatusLabel(status) {
  return PIPELINE_STATUS_COPY[status] || "状态未知";
}

function renderModelReasoning(container, reasoning = []) {
  const items = reasoning.length
    ? reasoning
    : [{
        model: "等待模型",
        plain_name: "检测开始后会显示模型的中文作用",
        status: "PENDING",
        finding: "尚未生成实际模型结果。",
        role: "没有运行的模型不会参与结论。",
      }];
  container.replaceChildren(...items.map((item, index) => {
    const row = createElement("li");
    const heading = createElement("div");
    heading.append(
      createElement("span", { text: String(index + 1).padStart(2, "0") }),
      createElement("strong", { text: item.model }),
      createElement("em", {
        className: `model-status model-status--${String(item.status || "PENDING").toLowerCase().replaceAll("_", "-")}`,
        text: modelStatusLabel(item.status),
      }),
    );
    row.append(
      heading,
      createElement("p", { className: "model-plain-name", text: item.plain_name }),
      createElement("p", { className: "model-finding", text: item.finding }),
      createElement("small", { text: item.role }),
    );
    return row;
  }));
}

function renderReasonedAnalysis(target, interpretation) {
  target.summary.textContent = interpretation.headline || interpretation.conclusion;
  target.evidence.replaceChildren(
    ...interpretation.evidence.map((entry) => createElement("li", { text: entry })),
  );
  renderModelReasoning(target.models, interpretation.model_reasoning);
  target.conclusion.textContent = interpretation.conclusion;
  target.rule.textContent = interpretation.decision_rule;
  target.scope.textContent = interpretation.scope_note;
}

function renderPendingCaseAnalysis(mode = "pending") {
  const running = mode === "running";
  elements["result-analysis-title"].textContent = running ? "正在按六步流程形成结论" : "等待本次检测";
  elements["result-analysis-summary"].textContent = running
    ? "系统正在依次核对输入、模型结果和波形依据；完成前不提前写结论。"
    : "开始检测后，这里会先给结论，再列出实测依据、模型推导过程和适用边界。";
  elements["result-analysis-activity"].textContent = running ? "正在识别" : "等待运行";
  elements["result-analysis-fall"].textContent = running ? "正在筛查" : "等待运行";
  elements["result-analysis-risk"].textContent = running ? "正在分析" : "等待运行";
  elements["result-analysis-evidence-list"].replaceChildren(
    createElement("li", { text: running ? "正在读取实际输入和模型数值。" : "检测完成后显示实际波形数值和模型窗口结果。" }),
  );
  renderModelReasoning(elements["result-model-reasoning"]);
  elements["result-analysis-synthesis"].textContent = running ? "正在交叉核对，尚未形成结论。" : "等待实际模型结果。";
  elements["result-analysis-conclusion"].textContent = running ? "尚未完成。" : "等待本次检测。";
  elements["result-analysis-rule"].textContent = "模型结果分开计算，不会相加成一个“综合风险分”。";
  elements["result-analysis-scope"].textContent = "没有实际输入或未运行的模型，不会被写成已经排除风险。";
}

function renderCompletedCaseAnalysis(interpretation) {
  elements["result-analysis-title"].textContent = "结论先看";
  elements["result-analysis-activity"].textContent = interpretation.current_activity;
  elements["result-analysis-fall"].textContent = interpretation.fall_screening;
  elements["result-analysis-risk"].textContent = interpretation.risk_screening;
  elements["result-analysis-synthesis"].textContent = interpretation.synthesis;
  renderReasonedAnalysis({
    summary: elements["result-analysis-summary"],
    evidence: elements["result-analysis-evidence-list"],
    models: elements["result-model-reasoning"],
    conclusion: elements["result-analysis-conclusion"],
    rule: elements["result-analysis-rule"],
    scope: elements["result-analysis-scope"],
  }, interpretation);
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
    const selfCollectedCases = buildSelfCollectedCases(dashboard);
    caseCatalog = [...selfCollectedCases, ...baseCaseCatalog];
    if (!state.initialSelectionApplied && selfCollectedCases.length) {
      state.filter = "self";
      state.page = 1;
      state.selectedCase = selfCollectedCases[0];
      state.initialSelectionApplied = true;
    }
    renderDashboardMeta(dashboard);
    syncFilterButtons();
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
  elements["collection-count"].textContent = `${dashboard.self_collected.received_case_count} / 约${dashboard.self_collected.expected_case_count}组`;
  elements["collection-status-copy"].textContent = dashboard.self_collected.received_case_count
    ? "30组已完成工程检查"
    : "等待真实文件";
  elements["heading-collection-count"].textContent = `自主采集 ${dashboard.self_collected.received_case_count} / 约${dashboard.self_collected.expected_case_count}组`;
  elements["boundary-collection-count"].textContent = `自主采集 ${dashboard.self_collected.received_case_count} / 约${dashboard.self_collected.expected_case_count}组`;
  elements["boundary-title"].textContent = dashboard.self_collected.claim_enabled
    ? "公开数据模型与30组自主采集工程验证均已接入"
    : "公开数据模型已运行，自主采集验证仍为空";
  elements["filter-all-count"].textContent = String(caseCatalog.length);
  elements["filter-self-count"].textContent = String(dashboard.self_collected.received_case_count);
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
      text: item.kind === "fall" ? "跌倒" : item.kind === "adl" ? "日常" : item.kind === "activity" ? "活动" : item.kind === "self" ? "自采" : "规律",
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
  if (item.kind === "self") return "truth-tag truth-tag--activity";
  if (item.kind === "routine") return "truth-tag truth-tag--routine";
  return "truth-tag";
}

function selectCase(caseId, announce = true) {
  const selected = caseCatalog.find((item) => item.id === caseId);
  if (!selected) return;
  resetPlayback(false);
  state.selectedCase = selected;
  state.selectedEvidence = null;
  renderCases();

  const catalogIndex = caseCatalog.indexOf(selected) + 1;
  elements["selected-truth"].className = truthClass(selected);
  elements["selected-truth"].textContent = selected.truthLabel;
  elements["selected-case-id"].textContent = selected.id;
  elements["selected-case-title"].textContent = selected.title;
  elements["selected-case-note"].textContent = selected.note;
  elements["result-metric-label"].textContent = selected.metricLabel;
  elements["result-metric-value"].textContent = "—";
  elements["result-metric-caption"].textContent = selected.metricHelp;
  elements["result-meter-fill"].style.width = "0%";
  renderPendingCaseAnalysis();

  elements["watch-case-index"].textContent = `案例 ${String(catalogIndex).padStart(3, "0")} / ${caseCatalog.length}`;
  elements["watch-case-label"].textContent = selected.source;
  elements["case-pipeline-state"].textContent = "正在读取案例";
  renderSharedPipeline(elements["detection-pipeline"]);

  const footer = document.querySelector(".watch-screen__footer");
  if (footer) {
    footer.children[0].lastChild.textContent = selected.kind === "routine" ? "EVENT" : "IMU";
    footer.children[1].textContent = selected.rate;
    footer.children[2].textContent = selected.axes;
  }
  if (announce) {
    elements["playback-status"].textContent = `已选择 ${selected.id}，可以开始检测。`;
  }
  loadCaseEvidence(selected);
}

function stepCopy(step) {
  const item = normalizedPipeline(state.selectedEvidence?.pipeline)[step] || ANALYSIS_PIPELINE_STEPS[0];
  return [item.label, item.detail || item.pending];
}

function updatePipeline(step, final = false) {
  renderSharedPipeline(
    elements["detection-pipeline"],
    state.selectedEvidence?.pipeline,
    { activeIndex: step, final },
  );
}

function startPlayback() {
  if (!state.selectedCase || state.playbackTimer) return;
  if (!state.selectedEvidence?.analysis || !state.selectedEvidence?.pipeline) {
    elements["playback-status"].textContent = "正在读取并核对案例实际数据，请稍候再开始。";
    return;
  }
  if (state.playbackStep >= 5) resetPlayback(false);
  elements["run-button"].disabled = true;
  elements["pause-button"].disabled = false;
  elements["run-button"].querySelector("span").textContent = "检测进行中";
  elements["watch-device"].dataset.state = "running";
  elements["result-state"].className = "result-state result-state--running";
  elements["result-state"].textContent = "检测中";
  elements["case-pipeline-state"].textContent = "六步流程运行中";
  renderPendingCaseAnalysis("running");
  elements["evidence-result"].textContent = "正在把案例结果与已核验输入依据并列复核。";

  const advance = () => {
    state.playbackStep += 1;
    if (state.playbackStep > 5) {
      finishPlayback();
      return;
    }
    const [label, detail] = stepCopy(state.playbackStep);
    updatePipeline(state.playbackStep);
    elements["watch-stage-label"].textContent = label;
    elements["watch-result"].textContent = detail;
    const progress = Math.min(100, Math.round(((state.playbackStep + 1) / 6) * 100));
    elements["watch-score-text"].textContent = `${progress}%`;
    elements["watch-score-fill"].style.width = `${progress}%`;
    elements["playback-status"].textContent = `步骤 ${state.playbackStep + 1} / 6：${detail}`;
  };

  advance();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  state.playbackTimer = window.setInterval(advance, reducedMotion ? 800 : 560);
}

function finishPlayback() {
  stopPlayback();
  const item = state.selectedCase;
  const live = state.selectedEvidence.analysis;
  const interpretation = live.interpretation;
  let result = "案例输入已就绪";
  let resultTone = "info";
  let metricValue = `${item.rate} · ${item.window}`;
  let caption = "本次只显示实际运行且满足输入条件的模型结果。";
  let watchState = "complete";
  let meterWidth = 100;

  if (item.kind === "fall" || item.kind === "adl") {
    const fall = live.fall_model;
    result = fall.screening;
    metricValue = fall.max_score === null ? "数据不足" : Number(fall.max_score).toFixed(3);
    caption = fall.detail;
    meterWidth = Number.isFinite(Number(fall.max_score)) ? Number(fall.max_score) * 100 : 0;
    if (fall.candidate_windows?.length) {
      resultTone = "candidate";
      watchState = "candidate";
    } else if (interpretation.review_required) {
      result = "需要复核";
      resultTone = "warning";
      watchState = "warning";
    } else {
      resultTone = "clear";
    }
  } else if (item.kind === "activity") {
    const activity = live.activity_model;
    const topOutput = activity.probabilities?.[activity.label_code];
    result = interpretation.review_required ? "活动结果需要复核" : "活动识别完成";
    metricValue = Number.isFinite(Number(topOutput)) ? Number(topOutput).toFixed(3) : "—";
    caption = `${activity.label}在四类输出中排名第一；与登记类别${activity.matches_registered_label ? "一致" : "不一致"}。`;
    meterWidth = Number.isFinite(Number(topOutput)) ? Number(topOutput) * 100 : 0;
    resultTone = interpretation.review_required ? "warning" : "clear";
    watchState = interpretation.review_required ? "warning" : "complete";
  } else if (item.kind === "routine") {
    const routine = live.routine_model;
    result = "规律对照完成";
    metricValue = `${routine.deviation_count} / ${routine.assessment_count} 项`;
    caption = "表示偏离合成规律范围的规则项数量，不是健康或跌倒风险分。";
    meterWidth = routine.assessment_count ? (routine.deviation_count / routine.assessment_count) * 100 : 0;
    resultTone = "info";
  }

  elements["watch-device"].dataset.state = watchState;
  elements["watch-stage-label"].textContent = "检测完成";
  elements["watch-result"].textContent = interpretation.current_activity;
  const liveRiskReady = Boolean(live.early_risk_model?.timeline?.length);
  elements["watch-score-fill"].style.width = "100%";
  elements["watch-score-text"].textContent = liveRiskReady ? "1 / 2 / 3 秒已计算" : "判断完成";
  elements["result-state"].className = `result-state result-state--${resultTone}`;
  elements["result-state"].textContent = result;
  elements["result-metric-value"].textContent = metricValue;
  elements["result-meter-fill"].style.width = `${Math.max(3, Math.min(100, meterWidth))}%`;
  elements["result-metric-caption"].textContent = caption;
  renderCompletedCaseAnalysis(interpretation);
  elements["evidence-result"].textContent = interpretation.conclusion;
  const skippedCount = normalizedPipeline(state.selectedEvidence.pipeline)
    .filter((step) => ["NOT_APPLICABLE", "INSUFFICIENT_DURATION"].includes(step.status)).length;
  elements["case-pipeline-state"].textContent = skippedCount
    ? `六步已核对 · ${skippedCount} 项未运行`
    : "六步全部完成";
  elements["playback-status"].textContent = `${result}。本次只运行满足实际输入条件的模型，外部通知保持 0 次。`;
  elements["run-button"].querySelector("span").textContent = "重新检测";
  elements["run-button"].disabled = false;
  elements["pause-button"].disabled = true;
  state.playbackStep = 5;
  updatePipeline(5, true);
}

function pausePlayback() {
  if (!state.playbackTimer) return;
  stopPlayback();
  elements["watch-device"].dataset.state = "paused";
  elements["watch-stage-label"].textContent = "检测已暂停";
  elements["run-button"].querySelector("span").textContent = "继续检测";
  elements["run-button"].disabled = false;
  elements["pause-button"].disabled = true;
  elements["playback-status"].textContent = `检测停在步骤 ${state.playbackStep + 1} / 6，可以继续或重置。`;
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
  renderPendingCaseAnalysis();
  elements["case-pipeline-state"].textContent = state.selectedEvidence ? "数据已核对 · 等待运行" : "等待运行";
  if (state.selectedCase) elements["evidence-result"].textContent = pendingEvidenceConclusion(state.selectedCase);
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

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function resetUploadPipeline() {
  renderSharedPipeline(elements["upload-pipeline"]);
  elements["upload-process-title"].textContent = state.uploadFile ? "文件已选择" : "等待文件";
}

function setUploadFile(file) {
  elements["upload-error"].hidden = true;
  elements["upload-result"].hidden = true;
  state.uploadFile = null;
  elements["upload-file-row"].hidden = true;
  elements["upload-dropzone"].dataset.state = "empty";
  elements["upload-submit"].disabled = true;
  if (!file) {
    elements["sensor-file"].value = "";
    resetUploadPipeline();
    return;
  }
  const suffix = file.name.toLowerCase().split(".").pop();
  if (!["csv", "json"].includes(suffix)) {
    showUploadError("请选择扩展名为 .csv 或 .json 的标准六轴文件。");
    return;
  }
  if (file.size <= 0 || file.size > 5 * 1024 * 1024) {
    showUploadError("文件必须大于 0 B 且不超过 5 MB。");
    return;
  }
  state.uploadFile = file;
  elements["upload-file-name"].textContent = file.name;
  elements["upload-file-meta"].textContent = `${formatBytes(file.size)} · 只在本机内存分析`;
  elements["upload-file-row"].hidden = false;
  elements["upload-dropzone"].dataset.state = "selected";
  elements["upload-submit"].disabled = false;
  resetUploadPipeline();
}

function showUploadError(message) {
  elements["upload-error-copy"].textContent = message;
  elements["upload-error"].hidden = false;
  elements["upload-error"].setAttribute("tabindex", "-1");
  elements["upload-error"].focus();
  elements["upload-process-title"].textContent = "需要修正文件";
}

function bytesToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  let binary = "";
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(offset, Math.min(offset + chunkSize, bytes.length)));
  }
  return window.btoa(binary);
}

function setUploadBusy(isBusy) {
  elements["upload-submit"].disabled = isBusy || !state.uploadFile;
  elements["upload-submit"].setAttribute("aria-busy", String(isBusy));
  elements["upload-submit"].querySelector("span").textContent = isBusy ? "正在运行全部模型" : "开始分析新数据";
  elements["sensor-file"].disabled = isBusy;
  elements["acceleration-unit"].disabled = isBusy;
  elements["gyroscope-unit"].disabled = isBusy;
  elements["upload-remove"].disabled = isBusy;
}

function renderUploadPipeline(pipeline) {
  renderSharedPipeline(elements["upload-pipeline"], pipeline, { final: true });
}

function renderUploadResult(payload) {
  const analysis = payload.analysis;
  const interpretation = analysis.interpretation;
  const risk = analysis.early_risk_model;
  elements["upload-result"].hidden = false;
  elements["upload-quality"].textContent = `${payload.quality.level} · ${payload.quality.source_rate_hz} Hz → 50 Hz · ${payload.quality.duration_s} 秒`;
  elements["upload-activity"].textContent = analysis.activity_model.label;
  elements["upload-fall"].textContent = interpretation.fall_screening;
  elements["upload-persistence"].textContent = `未保存 · SHA-256 ${payload.file.sha256.slice(0, 12)}…`;
  renderReasonedAnalysis({
    summary: elements["upload-analysis-summary"],
    evidence: elements["upload-evidence-list"],
    models: elements["upload-model-reasoning"],
    conclusion: elements["upload-conclusion"],
    rule: elements["upload-analysis-rule"],
    scope: elements["upload-analysis-scope"],
  }, interpretation);
  renderUploadSignalChart(analysis.waveform, payload.quality);
  elements["upload-result-state"].className = interpretation.review_required
    ? "result-state result-state--warning"
    : "result-state result-state--clear";
  elements["upload-result-state"].textContent = analysis.fall_model.candidate_windows?.length
    ? "发现跌倒候选"
    : interpretation.review_required
      ? "需要复核"
      : "更接近日常活动";
  if (risk.status === "COMPLETED") {
    elements["upload-risk-meta"].textContent = `${risk.timeline.length} 个逐秒时间点 · 公开数据代理模型`;
    renderRiskChart(elements["upload-risk-chart"], risk, {
      title: "上传记录逐秒提前风险研究分数",
      titleId: "upload-risk-title",
      descriptionId: "upload-risk-description",
    });
    const maxima = risk.max_scores;
    elements["upload-risk-summary"].textContent = `最高研究分数：1 秒 ${Number(maxima["1"]).toFixed(3)}、2 秒 ${Number(maxima["2"]).toFixed(3)}、3 秒 ${Number(maxima["3"]).toFixed(3)}。这是与公开受控数据代理标签的匹配程度，不是现实跌倒概率。`;
  } else {
    elements["upload-risk-meta"].textContent = "数据不足";
    renderRiskChart(elements["upload-risk-chart"], risk, {
      title: "上传记录逐秒提前风险研究分数",
      titleId: "upload-risk-title",
      descriptionId: "upload-risk-description",
    });
    elements["upload-risk-summary"].textContent = "记录不足一个完整研究窗口，未生成风险曲线。";
  }
  elements["upload-process-title"].textContent = "六步分析完成";
  elements["upload-result-title"].setAttribute("tabindex", "-1");
  elements["upload-result-title"].focus();
}

async function runUploadAnalysis() {
  if (!state.uploadFile) {
    showUploadError("请先选择一个标准六轴 CSV 或 JSON 文件。");
    return;
  }
  state.uploadController?.abort();
  state.uploadController = new AbortController();
  elements["upload-error"].hidden = true;
  elements["upload-result"].hidden = true;
  resetUploadPipeline();
  renderSharedPipeline(elements["upload-pipeline"], [], { activeIndex: 0 });
  elements["upload-process-title"].textContent = "服务器正在依次运行模型";
  setUploadBusy(true);
  try {
    const content = await state.uploadFile.arrayBuffer();
    const payload = await fetchJson("/api/analyze-upload", {
      method: "POST",
      signal: state.uploadController.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        file_name: state.uploadFile.name,
        content_base64: bytesToBase64(content),
        acceleration_unit: elements["acceleration-unit"].value,
        gyroscope_unit: elements["gyroscope-unit"].value,
      }),
    });
    renderUploadPipeline(payload.pipeline);
    renderUploadResult(payload);
  } catch (error) {
    if (error.name === "AbortError") return;
    const failed = normalizedPipeline().map((step, index) => ({
      ...step,
      status: index === 0 ? "FAILED" : "PENDING",
      detail: index === 0 ? "文件未通过输入检查，请根据错误说明修正。" : step.pending,
    }));
    renderSharedPipeline(elements["upload-pipeline"], failed, { final: true });
    showUploadError(error.message || "模型分析失败，请检查文件后重试。");
  } finally {
    setUploadBusy(false);
  }
}

function setupUploadControls() {
  elements["sensor-file"].addEventListener("change", (event) => setUploadFile(event.target.files?.[0] || null));
  elements["upload-form"].addEventListener("submit", (event) => {
    event.preventDefault();
    if (event.submitter?.id === "upload-remove") {
      setUploadFile(null);
      elements["sensor-file"].focus();
      return;
    }
    runUploadAnalysis();
  });
  ["dragenter", "dragover"].forEach((name) => {
    elements["upload-dropzone"].addEventListener(name, (event) => {
      event.preventDefault();
      if (!elements["sensor-file"].disabled) elements["upload-dropzone"].classList.add("is-dragging");
    });
  });
  ["dragleave", "drop"].forEach((name) => {
    elements["upload-dropzone"].addEventListener(name, (event) => {
      event.preventDefault();
      elements["upload-dropzone"].classList.remove("is-dragging");
    });
  });
  elements["upload-dropzone"].addEventListener("drop", (event) => {
    if (!elements["sensor-file"].disabled) setUploadFile(event.dataTransfer?.files?.[0] || null);
  });
}

function syncFilterButtons() {
  elements["case-filters"].querySelectorAll("button[data-filter]").forEach((item) => {
    const active = item.dataset.filter === state.filter;
    item.classList.toggle("is-active", active);
    item.setAttribute("aria-pressed", String(active));
  });
}

function setupCaseControls() {
  elements["case-filters"].addEventListener("submit", (event) => {
    event.preventDefault();
    const button = event.submitter?.closest("button[data-filter]");
    if (!button) return;
    state.filter = button.dataset.filter;
    state.page = 1;
    syncFilterButtons();
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
  const setCurrent = (targetId) => {
    links.forEach((link) => {
      const active = link.getAttribute("href") === `#${targetId}`;
      link.classList.toggle("is-current", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  };

  links.forEach((link) => {
    link.addEventListener("click", () => setCurrent(link.getAttribute("href").slice(1)));
  });
  if (!("IntersectionObserver" in window)) return;
  const visibility = new Map(targets.map((target) => [target.id, { target, isIntersecting: false, ratio: 0 }]));
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        visibility.set(entry.target.id, {
          target: entry.target,
          isIntersecting: entry.isIntersecting,
          ratio: entry.intersectionRatio,
        });
      });
      const visibleTargets = [...visibility.values()].filter((entry) => entry.isIntersecting);
      const requestedId = window.location.hash.replace(/^#/, "");
      const requested = visibleTargets.find((entry) => entry.target.id === requestedId);
      const visible = requested || visibleTargets.sort((a, b) => b.ratio - a.ratio)[0];
      if (!visible) return;
      setCurrent(visible.target.id);
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
  state.evidenceController?.abort();
  state.uploadController?.abort();
  if (state.clockTimer) window.clearInterval(state.clockTimer);
});

setupCaseControls();
setupUploadControls();
setupNavigationTracking();
updateClock();
state.clockTimer = window.setInterval(updateClock, 30_000);
loadDashboard();
