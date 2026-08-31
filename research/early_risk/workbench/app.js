"use strict";

const SVG_NS = "http://www.w3.org/2000/svg";
const state = {
  dashboard: null,
  simulation: null,
  loadController: null,
  simulationController: null,
  playTimer: null,
  cursorIndex: -1,
};

const ids = [
  "page-loading",
  "page-error",
  "page-error-message",
  "app-content",
  "service-status",
  "reload-form",
  "reload-button",
  "retry-form",
  "retry-button",
  "product-definition",
  "truth-notice",
  "engineering-status",
  "asset-count",
  "leakage-count",
  "notification-count",
  "pipeline-list",
  "external-actions",
  "policy-form",
  "threshold-on",
  "threshold-on-value",
  "threshold-off",
  "threshold-off-value",
  "consecutive-required",
  "cooldown-ms",
  "policy-error",
  "simulate-button",
  "reset-policy-button",
  "timeline-form",
  "play-button",
  "pause-button",
  "reset-timeline-button",
  "score-chart",
  "chart-status",
  "timeline-summary",
  "decision-count",
  "candidate-count",
  "unassessable-count",
  "external-count",
  "decision-table-body",
  "metric-grid",
  "lead-time-table-body",
  "contract-meta",
  "event-count",
  "anchor-count",
  "horizons",
  "sync-limit",
  "approval-list",
  "event-list",
  "contract-hash",
  "usage-matrix",
  "model-registry",
  "download-list",
  "limitations-list",
  "fixture-id",
];

const elements = Object.fromEntries(ids.map((id) => [id, document.getElementById(id)]));

const stateLabels = {
  SILENT: "静默",
  ACCUMULATING: "累积证据",
  DRY_RUN_CANDIDATE: "dry-run 候选",
  COOLDOWN: "冷却",
  UNASSESSABLE: "无法评估",
  SUPPRESSED: "已抑制",
};

const actionLabels = {
  NONE: "无动作",
  RECORD_DRY_RUN_CANDIDATE: "只记录候选",
  SUPPRESSED: "抑制",
};

const modelLabels = {
  FALL_DETECTION: "腕部跌倒检测",
  ROUTINE_ANOMALY: "个人规律异常",
  ACTIVITY_RECOGNITION: "腕部活动识别",
};

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

function createSvgElement(tagName, attributes = {}) {
  const element = document.createElementNS(SVG_NS, tagName);
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, String(value)));
  return element;
}

function formatPercent(value, digits = 1) {
  if (value === null || value === undefined) return "无法计算";
  return `${(Number(value) * 100).toFixed(digits)}%`;
}

function formatDecimal(value, digits = 3) {
  if (value === null || value === undefined) return "无法计算";
  return Number(value).toFixed(digits);
}

function compactHash(value) {
  const text = String(value);
  return text.length > 24 ? `${text.slice(0, 12)}…${text.slice(-10)}` : text;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
  });
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const message = payload?.error?.message || `本地服务返回 ${response.status}。`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return payload;
}

function setLoading(isLoading) {
  elements["reload-button"].disabled = isLoading;
  elements["reload-button"].textContent = isLoading ? "读取中" : "重新读取";
  if (isLoading) elements["service-status"].textContent = "正在读取证据";
}

function showPageError(error) {
  elements["page-loading"].hidden = true;
  elements["app-content"].hidden = true;
  elements["page-error"].hidden = false;
  const rawMessage = error?.message || "";
  elements["page-error-message"].textContent = /failed to fetch|networkerror/i.test(rawMessage)
    ? "无法连接本机证据服务。请重新启动 E0 研究工作台，然后在这里重试。"
    : rawMessage || "本地证据暂时无法读取，请检查证据文件后重试。";
  elements["service-status"].textContent = "证据读取失败";
}

function showContent() {
  elements["page-loading"].hidden = true;
  elements["page-error"].hidden = true;
  elements["app-content"].hidden = false;
}

async function loadDashboard() {
  if (state.loadController) state.loadController.abort();
  state.loadController = new AbortController();
  pauseTimeline();
  setLoading(true);
  elements["page-loading"].hidden = false;
  elements["page-error"].hidden = true;
  try {
    const dashboard = await fetchJson("/api/workbench", {
      signal: state.loadController.signal,
    });
    state.dashboard = dashboard;
    renderDashboard(dashboard);
    showContent();
    elements["service-status"].textContent = "本地证据已读取";
    await runSimulation(true);
  } catch (error) {
    if (error.name !== "AbortError") showPageError(error);
  } finally {
    setLoading(false);
  }
}

function renderDashboard(dashboard) {
  elements["product-definition"].textContent = dashboard.truth.product_definition;
  elements["truth-notice"].textContent = dashboard.truth.notice;
  elements["engineering-status"].textContent = dashboard.meta.engineering_status;
  elements["asset-count"].textContent = `${dashboard.audit.audited_asset_count} / ${dashboard.audit.expected_asset_count}`;
  elements["leakage-count"].textContent = String(dashboard.fixture.temporal_leakage.finding_count);
  elements["notification-count"].textContent = String(dashboard.gate.p2.external_notification_count);
  elements["fixture-id"].textContent = dashboard.fixture.id;

  renderPipeline(dashboard.pipeline, dashboard.gate.required_external_actions);
  applyDefaultPolicy(dashboard.fixture.default_policy);
  renderChart(dashboard.fixture.policy_inputs, Number(elements["threshold-on"].value), -1);
  renderMetrics(dashboard.fixture.metrics);
  renderContract(dashboard.contract);
  renderAudit(dashboard.audit);
  renderDownloads(dashboard.downloads, dashboard.truth.limitations);
}

function renderPipeline(stages, externalActions) {
  const stageNodes = stages.map((item) => {
    const node = createElement("li", {
      className: `evidence-step ${item.state === "engineering_pass" ? "is-complete" : "is-locked"}`,
    });
    const marker = createElement("span", {
      className: "evidence-step__marker",
      text: item.state === "engineering_pass" ? "✓" : item.stage,
      attrs: { "aria-hidden": "true" },
    });
    const content = createElement("div", { className: "evidence-step__content" });
    content.append(
      createElement("strong", { text: `${item.stage} · ${item.title}` }),
      createElement("span", { text: item.detail }),
    );
    const accessible = createElement("span", {
      text: item.state === "engineering_pass" ? "工程检查通过" : "当前锁定",
      attrs: { class: "visually-hidden" },
    });
    node.append(marker, content, accessible);
    return node;
  });
  elements["pipeline-list"].replaceChildren(...stageNodes);

  const actionNodes = externalActions.map((item) => createElement("li", { text: item }));
  elements["external-actions"].replaceChildren(...actionNodes);
}

function applyDefaultPolicy(config) {
  elements["threshold-on"].value = String(config.threshold_on);
  elements["threshold-off"].value = String(config.threshold_off);
  elements["consecutive-required"].value = String(config.consecutive_required);
  elements["cooldown-ms"].value = String(config.cooldown_ms);
  updateRangeOutputs();
}

function readPolicyForm() {
  return {
    threshold_on: Number(elements["threshold-on"].value),
    threshold_off: Number(elements["threshold-off"].value),
    consecutive_required: Number(elements["consecutive-required"].value),
    cooldown_ms: Number(elements["cooldown-ms"].value),
  };
}

function validatePolicy(config) {
  if (config.threshold_off >= config.threshold_on) {
    throw new Error("复位阈值必须低于触发阈值。请先调低复位阈值再重新计算。");
  }
}

function updateRangeOutputs() {
  elements["threshold-on-value"].value = Number(elements["threshold-on"].value).toFixed(2);
  elements["threshold-on-value"].textContent = Number(elements["threshold-on"].value).toFixed(2);
  elements["threshold-off-value"].value = Number(elements["threshold-off"].value).toFixed(2);
  elements["threshold-off-value"].textContent = Number(elements["threshold-off"].value).toFixed(2);
  if (state.dashboard) {
    renderChart(
      state.dashboard.fixture.policy_inputs,
      Number(elements["threshold-on"].value),
      state.cursorIndex,
    );
  }
}

async function runSimulation(isInitial = false) {
  if (!state.dashboard) return;
  const config = readPolicyForm();
  try {
    validatePolicy(config);
  } catch (error) {
    elements["policy-error"].textContent = error.message;
    elements["policy-error"].hidden = false;
    elements["threshold-off"].setAttribute("aria-invalid", "true");
    if (!isInitial) elements["threshold-off"].focus();
    return;
  }

  elements["policy-error"].hidden = true;
  elements["threshold-off"].removeAttribute("aria-invalid");
  if (state.simulationController) state.simulationController.abort();
  state.simulationController = new AbortController();
  elements["simulate-button"].disabled = true;
  elements["simulate-button"].classList.add("is-busy");
  elements["simulate-button"].setAttribute("aria-busy", "true");
  try {
    const simulation = await fetchJson("/api/simulate", {
      method: "POST",
      signal: state.simulationController.signal,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    state.simulation = simulation;
    state.cursorIndex = -1;
    renderSimulation(simulation);
    renderChart(state.dashboard.fixture.policy_inputs, simulation.config.threshold_on, -1);
    elements["chart-status"].textContent = "dry-run 已重新计算，时间轴停在起点。";
  } catch (error) {
    if (error.name !== "AbortError") {
      elements["policy-error"].textContent = error.message;
      elements["policy-error"].hidden = false;
    }
  } finally {
    elements["simulate-button"].disabled = false;
    elements["simulate-button"].classList.remove("is-busy");
    elements["simulate-button"].removeAttribute("aria-busy");
  }
}

function renderSimulation(simulation) {
  const summary = simulation.summary;
  elements["decision-count"].textContent = String(summary.decision_count);
  elements["candidate-count"].textContent = String(summary.dry_run_candidate_count);
  elements["unassessable-count"].textContent = String(summary.unassessable_count);
  elements["external-count"].textContent = String(summary.external_notification_count);
  elements["timeline-summary"].textContent = `${summary.decision_count} 个固定输入点 · 阈值 ${simulation.config.threshold_on.toFixed(2)} · 连续 ${simulation.config.consecutive_required} 个`;

  const inputsByTimestamp = new Map(
    state.dashboard.fixture.policy_inputs.map((item) => [item.timestamp_ms, item]),
  );
  const rows = simulation.decisions.map((decision) => {
    const input = inputsByTimestamp.get(decision.timestamp_ms);
    const row = document.createElement("tr");
    const stateClass =
      decision.state === "DRY_RUN_CANDIDATE"
        ? "state-label--candidate"
        : decision.state === "UNASSESSABLE" || decision.state === "SUPPRESSED"
          ? "state-label--unassessable"
          : "";
    const stateBadge = createElement("span", {
      className: `state-label ${stateClass}`.trim(),
      text: stateLabels[decision.state] || decision.state,
    });
    const cells = [
      createElement("td", { text: `${(decision.timestamp_ms / 1000).toFixed(1)} 秒` }),
      createElement("td", { text: input ? input.score.toFixed(2) : "—" }),
      createElement("td"),
      createElement("td", { text: decision.evidence_count }),
      createElement("td", { text: actionLabels[decision.action] || decision.action }),
      createElement("td", { text: decision.reason }),
      createElement("td", { text: decision.external_notification_sent ? "是" : "否" }),
    ];
    cells[2].append(stateBadge);
    row.append(...cells);
    return row;
  });
  elements["decision-table-body"].replaceChildren(...rows);
}

function renderChart(inputs, threshold, cursorIndex) {
  if (!inputs?.length) {
    elements["score-chart"].replaceChildren(
      createElement("p", { text: "没有可显示的确定性夹具输入。" }),
    );
    return;
  }
  const width = 760;
  const height = 260;
  const padding = { top: 24, right: 28, bottom: 38, left: 46 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const minTime = Math.min(...inputs.map((item) => item.timestamp_ms));
  const maxTime = Math.max(...inputs.map((item) => item.timestamp_ms));
  const timeSpan = Math.max(1, maxTime - minTime);
  const x = (timestamp) => padding.left + ((timestamp - minTime) / timeSpan) * plotWidth;
  const y = (score) => padding.top + (1 - score) * plotHeight;

  const svg = createSvgElement("svg", {
    viewBox: `0 0 ${width} ${height}`,
    role: "img",
    "aria-label": `人工确定性分数折线图，共 ${inputs.length} 个输入点；当前触发阈值 ${threshold.toFixed(2)}。`,
  });

  [0, 0.25, 0.5, 0.75, 1].forEach((tick) => {
    svg.append(
      createSvgElement("line", {
        x1: padding.left,
        y1: y(tick),
        x2: width - padding.right,
        y2: y(tick),
        class: "chart-grid-line",
      }),
    );
    const label = createSvgElement("text", {
      x: padding.left - 10,
      y: y(tick) + 4,
      "text-anchor": "end",
      class: "chart-axis-label",
    });
    label.textContent = tick.toFixed(2);
    svg.append(label);
  });

  inputs.forEach((item) => {
    const label = createSvgElement("text", {
      x: x(item.timestamp_ms),
      y: height - 14,
      "text-anchor": "middle",
      class: "chart-axis-label",
    });
    label.textContent = `${item.timestamp_ms / 1000}s`;
    svg.append(label);
  });

  svg.append(
    createSvgElement("line", {
      x1: padding.left,
      y1: y(threshold),
      x2: width - padding.right,
      y2: y(threshold),
      class: "chart-threshold-line",
    }),
  );

  const pointString = inputs.map((item) => `${x(item.timestamp_ms)},${y(item.score)}`).join(" ");
  svg.append(createSvgElement("polyline", { points: pointString, class: "chart-score-line" }));
  inputs.forEach((item) => {
    svg.append(
      createSvgElement("circle", {
        cx: x(item.timestamp_ms),
        cy: y(item.score),
        r: 4,
        class: "chart-score-point",
      }),
    );
  });

  if (cursorIndex >= 0 && cursorIndex < inputs.length) {
    const current = inputs[cursorIndex];
    svg.append(
      createSvgElement("line", {
        x1: x(current.timestamp_ms),
        y1: padding.top,
        x2: x(current.timestamp_ms),
        y2: height - padding.bottom,
        class: "chart-cursor-line",
      }),
      createSvgElement("circle", {
        cx: x(current.timestamp_ms),
        cy: y(current.score),
        r: 6,
        class: "chart-cursor-dot",
      }),
    );
  }
  elements["score-chart"].replaceChildren(svg);
}

function playTimeline() {
  if (!state.dashboard || !state.simulation || state.playTimer) return;
  const inputs = state.dashboard.fixture.policy_inputs;
  if (state.cursorIndex >= inputs.length - 1) state.cursorIndex = -1;
  elements["play-button"].disabled = true;
  elements["pause-button"].disabled = false;

  const advance = () => {
    state.cursorIndex += 1;
    if (state.cursorIndex >= inputs.length) {
      state.cursorIndex = inputs.length - 1;
      pauseTimeline();
      elements["chart-status"].textContent = "时间轴播放完成；没有产生真实外部通知。";
      return;
    }
    const input = inputs[state.cursorIndex];
    const decision = state.simulation.decisions[state.cursorIndex];
    renderChart(inputs, state.simulation.config.threshold_on, state.cursorIndex);
    elements["chart-status"].textContent = `${(input.timestamp_ms / 1000).toFixed(1)} 秒 · 人工分数 ${input.score.toFixed(2)} · ${stateLabels[decision.state] || decision.state} · ${actionLabels[decision.action] || decision.action}`;
  };

  advance();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  state.playTimer = window.setInterval(advance, reducedMotion ? 1100 : 700);
}

function pauseTimeline() {
  if (state.playTimer) window.clearInterval(state.playTimer);
  state.playTimer = null;
  elements["play-button"].disabled = false;
  elements["pause-button"].disabled = true;
}

function resetTimeline() {
  pauseTimeline();
  state.cursorIndex = -1;
  if (state.dashboard) {
    const threshold = state.simulation?.config.threshold_on ?? Number(elements["threshold-on"].value);
    renderChart(state.dashboard.fixture.policy_inputs, threshold, -1);
  }
  elements["chart-status"].textContent = "时间轴已重置到起点。";
}

function renderMetrics(metrics) {
  const cards = [
    ["事件级精确率", formatPercent(metrics.event_precision)],
    ["AP / AUPRC", formatDecimal(metrics.auprc)],
    ["误报 / 人日", formatDecimal(metrics.false_alerts_per_person_day.overall_per_person_day)],
    ["校准 ECE", formatDecimal(metrics.calibration.ece)],
    ["可评估覆盖率", formatPercent(metrics.coverage_and_abstention.coverage)],
  ].map(([label, value]) => {
    const card = createElement("article", { className: "metric-card" });
    card.append(
      createElement("span", { text: label }),
      createElement("strong", { text: value }),
      createElement("small", { text: "工程夹具 · 不可外推" }),
    );
    return card;
  });
  elements["metric-grid"].replaceChildren(...cards);

  const rows = metrics.event_recall_by_lead_time.map((item) => {
    const row = document.createElement("tr");
    row.append(
      createElement("td", { text: `≥ ${item.horizon_seconds} 秒` }),
      createElement("td", { text: `${item.timely_event_count} / ${item.event_count}` }),
      createElement("td", { text: formatPercent(item.recall) }),
      createElement("td", {
        text: `${formatPercent(item.ci95_wilson[0])} – ${formatPercent(item.ci95_wilson[1])}`,
      }),
      createElement("td", { text: "验证指标公式与报告结构" }),
    );
    return row;
  });
  elements["lead-time-table-body"].replaceChildren(...rows);
}

function renderContract(contract) {
  elements["contract-meta"].textContent = `${contract.id} · v${contract.version} · ${contract.status}`;
  elements["event-count"].textContent = `${contract.events.length} 类`;
  elements["anchor-count"].textContent = `${contract.time_anchors.length} 个`;
  elements["horizons"].textContent = contract.immediate_horizons_seconds.map((value) => `${value}s`).join(" / ");
  elements["sync-limit"].textContent = `≤ ${contract.synchronization_error_limit_ms} ms`;
  elements["contract-hash"].textContent = contract.sha256;

  const approvalLabels = {
    product_owner_signed: "产品负责人",
    research_owner_signed: "研究负责人",
    safety_ethics_owner_signed: "安全与伦理负责人",
  };
  const approvals = Object.entries(approvalLabels).map(([key, label]) => {
    const item = createElement("li");
    item.append(
      createElement("span", { text: label }),
      createElement("strong", {
        text: contract.external_approval_state[key] ? "已签署" : "待正式签署",
      }),
    );
    return item;
  });
  elements["approval-list"].replaceChildren(...approvals);

  const events = contract.events.map((event) => {
    const item = createElement("li");
    item.append(
      document.createTextNode(event.label_zh_cn),
      createElement("small", { text: `${event.code} · ${event.role}` }),
    );
    return item;
  });
  elements["event-list"].replaceChildren(...events);
}

function renderAudit(audit) {
  const usageCards = audit.usage_matrix.map((entry) => {
    const card = createElement("article", { className: "usage-card" });
    const header = createElement("div", { className: "usage-card__header" });
    header.append(
      createElement("h3", { text: entry.asset_id }),
      createElement("span", {
        className: entry.license_status.includes("UNVERIFIED")
          ? "status-pill status-pill--warning"
          : "status-pill status-pill--neutral",
        text: entry.license_status,
      }),
    );
    const lists = createElement("div", { className: "usage-card__lists" });
    const allowed = createElement("div");
    allowed.append(
      createElement("h4", { text: "允许用途" }),
      listFromStrings(entry.allowed_use),
    );
    const prohibited = createElement("div");
    prohibited.append(
      createElement("h4", { text: "禁止用途" }),
      listFromStrings(entry.prohibited_use),
    );
    lists.append(allowed, prohibited);
    card.append(header, createElement("p", { text: entry.truth_scope }), lists);
    return card;
  });
  elements["usage-matrix"].replaceChildren(...usageCards);

  const modelCards = audit.model_registry.map((model) => {
    const card = createElement("article", { className: "model-card" });
    const header = createElement("div", { className: "model-card__header" });
    header.append(
      createElement("h3", { text: modelLabels[model.model_kind] || model.model_kind }),
      createElement("span", {
        className: "status-pill status-pill--warning",
        text: model.deployment_approved ? "已批准" : "未获部署批准",
      }),
    );
    card.append(
      header,
      createElement("p", {
        text: `${model.model_kind} · v${model.version} · 外部验证：${model.external_validation_completed ? "已完成" : "未完成"}`,
      }),
      createElement("p", { text: model.limitations[0] }),
      createElement("code", { text: compactHash(model.artifact_sha256) }),
    );
    return card;
  });
  elements["model-registry"].replaceChildren(...modelCards);
}

function listFromStrings(items) {
  const list = document.createElement("ul");
  list.append(...items.map((item) => createElement("li", { text: item })));
  return list;
}

function renderDownloads(downloads, limitations) {
  const items = downloads.map((download) => {
    const item = createElement("article", { className: "download-item" });
    const metadata = createElement("div");
    metadata.append(
      createElement("strong", { text: download.name }),
      createElement("code", {
        text: `${download.bytes.toLocaleString("zh-CN")} bytes · ${download.sha256}`,
      }),
    );
    const link = createElement("a", {
      text: "下载原件",
      attrs: { href: download.href, download: download.name },
    });
    item.append(metadata, link);
    return item;
  });
  elements["download-list"].replaceChildren(...items);
  elements["limitations-list"].replaceChildren(
    ...limitations.map((item) => createElement("li", { text: item })),
  );
}

function setupNavigationTracking() {
  const links = [...document.querySelectorAll(".nav__link")];
  const targets = links
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean);
  if (!("IntersectionObserver" in window)) return;
  const observer = new IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (!visible) return;
      links.forEach((link) => {
        const current = link.getAttribute("href") === `#${visible.target.id}`;
        link.classList.toggle("is-current", current);
        if (current) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
      });
    },
    { rootMargin: "-20% 0px -65% 0px", threshold: [0, 0.2, 0.5] },
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
elements["policy-form"].addEventListener("submit", (event) => {
  event.preventDefault();
  pauseTimeline();
  if (event.submitter?.id === "reset-policy-button") {
    if (!state.dashboard) return;
    applyDefaultPolicy(state.dashboard.fixture.default_policy);
  }
  runSimulation(false);
});
elements["threshold-on"].addEventListener("input", updateRangeOutputs);
elements["threshold-off"].addEventListener("input", updateRangeOutputs);
elements["timeline-form"].addEventListener("submit", (event) => {
  event.preventDefault();
  if (event.submitter?.id === "play-button") playTimeline();
  if (event.submitter?.id === "pause-button") {
    pauseTimeline();
    elements["chart-status"].textContent = "时间轴已暂停。";
  }
  if (event.submitter?.id === "reset-timeline-button") resetTimeline();
});
window.addEventListener("beforeunload", () => {
  pauseTimeline();
  state.loadController?.abort();
  state.simulationController?.abort();
});

setupNavigationTracking();
loadDashboard();
