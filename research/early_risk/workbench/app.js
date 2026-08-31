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
  metricLabel: "案例输入规格",
  metricHelp: "显示这组案例的采样频率和连续动作窗口长度；当前没有逐样本识别结果。",
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
  evidenceController: null,
  evidenceCache: new Map(),
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
  "result-analysis-copy", "detection-pipeline",
  "pipeline-input", "pipeline-window", "pipeline-model", "pipeline-review", "external-count",
  "evidence", "evidence-intro", "evidence-badge", "evidence-loading", "evidence-error",
  "evidence-error-copy", "evidence-content", "motion-figure", "motion-title", "motion-caption",
  "chart-kicker", "chart-title", "chart-meta", "evidence-chart", "evidence-legend",
  "chart-summary", "evidence-source", "evidence-input", "evidence-method", "evidence-result",
  "evidence-limit", "truth-notice", "limitations-list", "fixture-id",
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
    return "并列复核 20 秒三轴腕部波形与已登记活动标签；当前页不把标签冒充新模型成绩。";
  }
  return "比较同一合成档案每天用餐、午睡和散步的时间、次数与持续时长。";
}

function pendingEvidenceConclusion(item) {
  if (item.kind === "fall" || item.kind === "adl") return "开始检测后，结合保存匹配度与跌倒动作记录生成。";
  if (item.kind === "activity") return "开始检测后，说明已登记活动类别与输入是否对应。";
  return "开始检测后，说明这组固定种子规律输入能支持什么。";
}

function completedEvidenceConclusion(item, result) {
  if (item.kind === "fall" || item.kind === "adl") {
    return `${result}；匹配度 ${formatPercent(item.score)}，保存记录 ${item.alarms} 段。`;
  }
  if (item.kind === "activity") return `${result}；登记类别为“${item.shortTitle.split(" · ")[0]}”。`;
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
  const height = 270;
  const paddingLeft = 54;
  const paddingRight = 18;
  const paddingTop = 34;
  const paddingBottom = 32;
  const panelGap = evidence.series.length > 1 ? 28 : 0;
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

  evidence.events.forEach((event, index) => {
    const startX = xFor(event.start_offset_ms);
    const endX = xFor(event.end_offset_ms);
    const truthTone = evidence.truth_category === "SIMULATED_FALL" ? "fall" : "activity";
    svg.append(createSvgElement("rect", {
      x: startX,
      y: paddingTop - 12,
      width: Math.max(1, endX - startX),
      height: height - paddingTop - paddingBottom + 18,
      class: `evidence-chart__truth evidence-chart__truth--${truthTone}`,
    }));
    if (index === 0 && endX - startX > 48) {
      appendSvgText(svg, `已登记标签 ${event.label}`, startX + 5, 16, `evidence-chart__annotation evidence-chart__annotation--${truthTone}`);
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
    appendSvgText(svg, `${series.label} · ${series.unit}`, paddingLeft, panelTop - 8, "evidence-chart__label");
    appendSvgText(svg, yMaximum.toFixed(yMaximum >= 10 ? 1 : 2), paddingLeft - 7, panelTop + 4, "evidence-chart__tick", "end");
    appendSvgText(svg, "0", paddingLeft - 7, panelBottom + 3, "evidence-chart__tick", "end");

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

function showEvidenceLoading(item) {
  elements["evidence"].dataset.state = "loading";
  elements["evidence-loading"].hidden = false;
  elements["evidence-error"].hidden = true;
  elements["evidence-content"].hidden = true;
  elements["evidence-badge"].className = "evidence-badge";
  elements["evidence-badge"].textContent = "正在核对";
  elements["evidence-intro"].textContent = `正在读取 ${item.id} 对应的本机依据，不生成随机曲线。`;
}

function showEvidenceError(item, error) {
  elements["evidence"].dataset.state = "error";
  elements["evidence-loading"].hidden = true;
  elements["evidence-content"].hidden = true;
  elements["evidence-error"].hidden = false;
  elements["evidence-error-copy"].textContent = `${error?.message || "本机文件暂时无法读取。"} 页面不会用示意波形替代。`;
  elements["evidence-badge"].className = "evidence-badge is-error";
  elements["evidence-badge"].textContent = "依据不可用";
  elements["evidence-intro"].textContent = `${item.id} 的检测流程仍可演示，但缺失依据时不能把图表当作证据。`;
}

function renderEvidence(item, evidence) {
  const motion = motionPresentation(item);
  elements["evidence"].dataset.state = "ready";
  elements["evidence-loading"].hidden = true;
  elements["evidence-error"].hidden = true;
  elements["evidence-content"].hidden = false;
  elements["motion-figure"].dataset.motion = motion.motion;
  elements["motion-title"].textContent = motion.title;
  elements["motion-caption"].textContent = motion.caption;
  elements["evidence-method"].textContent = evidenceMethod(item);
  elements["evidence-result"].textContent = state.playbackStep >= 3
    ? completedEvidenceConclusion(item, elements["result-state"].textContent)
    : pendingEvidenceConclusion(item);

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

function pendingResultAnalysis() {
  return {
    title: "等待本次检测",
    copy: "开始检测后，这里会用一段话说明系统看到了什么、为什么给出这个结果，以及这个结果不能说明什么。",
  };
}

function completedResultAnalysis(item) {
  if (item.kind === "fall" && item.alarms > 0) {
    return {
      title: "为什么显示“检测到跌倒动作”",
      copy: `参与者完成的是受控模拟跌倒。系统把 ${item.window}内的 ${item.axes} 数据作为整体进行比较，跌倒特征匹配度为 ${formatPercent(item.score)}，保存回放记录了 ${item.alarms} 段跌倒动作，因此给出这一结果。当前资料没有逐轴原因说明，不能进一步断定具体哪个方向或身体部位“哪里不对”；这也不是现实跌倒概率或提前预测。`,
    };
  }
  if (item.kind === "fall") {
    return {
      title: "为什么这次需要人工复核",
      copy: `参与者完成的是受控模拟跌倒，但保存回放没有记录到足够明确的跌倒动作，因此这次可能被模型漏掉。跌倒特征匹配度 ${formatPercent(item.score)} 只表示整体动作相似程度，不能单独代替检测结果。`,
    };
  }
  if (item.kind === "adl" && item.alarms > 0) {
    return {
      title: "为什么属于疑似误判",
      copy: `参与者完成的是受控日常活动，并不是跌倒。系统认为这段整体腕部动作与受控跌倒动作较相似，匹配度为 ${formatPercent(item.score)}，并保存了 ${item.alarms} 段跌倒动作记录，因此这次应当标为疑似误判并交给人工复核，不能据此报警。`,
    };
  }
  if (item.kind === "adl") {
    return {
      title: "为什么未给出跌倒提示",
      copy: `参与者完成的是受控日常活动。保存回放没有把这段动作记录为跌倒动作，匹配度为 ${formatPercent(item.score)}，因此本次未给出跌倒提示；这只说明该案例的保存结果，不等于现实环境中的安全结论。`,
    };
  }
  if (item.kind === "activity") {
    return {
      title: "这次活动案例能说明什么",
      copy: `这是一段参与者自由生活中的腕部活动案例，输入规格为 ${item.rate}、${item.axes}、${item.window}。当前前端只确认案例已经登记，尚未接入逐样本识别结果，因此不能断定这段动作最终被识别成哪一种活动。`,
    };
  }
  return {
    title: "这次规律案例能说明什么",
    copy: "这是程序生成的 100 天生活规律案例，用来演示用餐、午睡和散步是否偏离既定规律。它不是参与者的生活记录，也不是医学风险判断。",
  };
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
  elements["result-metric-caption"].textContent = selected.metricHelp;
  elements["result-meter-fill"].style.width = "0%";
  const pendingAnalysis = pendingResultAnalysis();
  elements["result-analysis-title"].textContent = pendingAnalysis.title;
  elements["result-analysis-copy"].textContent = pendingAnalysis.copy;

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
  loadCaseEvidence(selected);
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
  elements["result-analysis-title"].textContent = "正在整理判断依据";
  elements["result-analysis-copy"].textContent = "检测完成后，这里会把案例类型、动作匹配程度和需要保留的限制合成一段通俗说明。";
  elements["evidence-result"].textContent = "正在把案例结果与已核验输入依据并列复核。";

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
      result = "检测到跌倒动作";
      resultTone = "candidate";
      watchState = "candidate";
      caption = `匹配度表示与受控跌倒动作的相似程度；保存回放记录了 ${item.alarms} 段跌倒动作。它不是现实跌倒概率。`;
    } else if (item.alarms > 0) {
      result = "疑似误判为跌倒";
      resultTone = "warning";
      watchState = "warning";
      caption = `参与者做的是日常活动，但保存回放记录了 ${item.alarms} 段跌倒动作，需要人工复核。`;
    } else {
      result = "未检测到跌倒动作";
      resultTone = "clear";
      caption = "保存回放未记录跌倒动作；这只说明本案例结果，不等同于现实安全结论。";
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
  elements["watch-score-text"].textContent = item.score === null ? "案例就绪" : `匹配 ${formatPercent(item.score)}`;
  elements["result-state"].className = `result-state result-state--${resultTone}`;
  elements["result-state"].textContent = result;
  elements["result-metric-value"].textContent = metricValue;
  elements["result-meter-fill"].style.width = item.score === null ? "100%" : `${Math.max(3, item.score * 100)}%`;
  elements["result-metric-caption"].textContent = caption;
  const analysis = completedResultAnalysis(item);
  elements["result-analysis-title"].textContent = analysis.title;
  elements["result-analysis-copy"].textContent = analysis.copy;
  elements["evidence-result"].textContent = completedEvidenceConclusion(item, result);
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
  const pendingAnalysis = pendingResultAnalysis();
  elements["result-analysis-title"].textContent = pendingAnalysis.title;
  elements["result-analysis-copy"].textContent = pendingAnalysis.copy;
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
  if (state.clockTimer) window.clearInterval(state.clockTimer);
});

setupCaseControls();
setupNavigationTracking();
updateClock();
state.clockTimer = window.setInterval(updateClock, 30_000);
loadDashboard();
