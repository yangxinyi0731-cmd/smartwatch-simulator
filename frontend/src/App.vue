<script setup lang="ts">
import { computed, ref, watch, type Component } from 'vue'
import {
  IconActivityHeartbeat,
  IconAlertTriangle,
  IconCalendarStats,
  IconDatabaseOff,
  IconDeviceWatch,
  IconFileSearch,
  IconPlayerPause,
  IconPlayerPlay,
  IconRefresh,
  IconShieldCheck,
  IconTimeline,
  IconWaveSine,
  IconWalk,
} from '@tabler/icons-vue'

import AppCard from './components/AppCard.vue'
import AppButton from './components/AppButton.vue'
import AppShell from './components/AppShell.vue'
import EmptyState from './components/EmptyState.vue'
import SensorWaveform from './components/SensorWaveform.vue'
import StatusBadge from './components/StatusBadge.vue'
import type { CaseListItem, ModelKind, TruthCategory } from './api/generated'
import { useCatalog } from './composables/useCatalog'
import { useReplayPreview } from './composables/useReplayPreview'
import { useSystemConnection } from './composables/useSystemConnection'

type BadgeTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

interface ModelSummary {
  id: string
  name: string
  purpose: string
  description: string
  input: string
  status: string
  tone: BadgeTone
  icon: Component
  kind: ModelKind
  version?: string
}

interface SystemStatusItem {
  label: string
  value: string
  detail: string
  tone: BadgeTone
}

const { phase, status, errorMessage, isRefreshing, refresh } = useSystemConnection()
const {
  cases,
  models,
  isLoading: isCatalogLoading,
  errorMessage: catalogError,
  refresh: refreshCatalog,
} = useCatalog()
const selectedCaseId = ref('')
const truthFilter = ref<'ALL' | TruthCategory>('ALL')
const {
  preview,
  phase: replayPhase,
  cursorMs,
  speed: replaySpeed,
  errorMessage: replayError,
  effectiveDurationMs,
  progress: replayProgress,
  currentFallWindow,
  visibleAlarmEpisodes,
  currentRoutineDay,
  start: startReplay,
  pause: pauseReplay,
  reset: resetReplay,
  reload: reloadReplay,
} = useReplayPreview(selectedCaseId)

const truthLabels: Record<TruthCategory, string> = {
  REAL_FREE_LIVING: '真实自由生活',
  REAL_LAB_ACTIVITY: '真实受控日常活动',
  SIMULATED_FALL: '受控模拟跌倒',
  SYNTHETIC_ROUTINE: '合成生活规律',
  DERIVED_PERTURBATION: '派生扰动',
}

const ageLabels: Record<CaseListItem['age_group'], string> = {
  YOUNG_ADULT: '年轻参与者',
  OLDER_ADULT: '老年参与者',
  MIXED: '混合年龄',
  UNKNOWN: '年龄未知',
  NOT_APPLICABLE: '不适用',
}

const modelLabels: Record<ModelKind, string> = {
  FALL_DETECTION: '腕部跌倒检测',
  ROUTINE_ANOMALY: '个人规律异常',
  ACTIVITY_RECOGNITION: '腕部活动识别',
}

const caseCounts = computed(() => {
  const counts = new Map<TruthCategory, number>()
  for (const item of cases.value) {
    counts.set(item.truth_category, (counts.get(item.truth_category) ?? 0) + 1)
  }
  return counts
})

const filteredCases = computed(() =>
  truthFilter.value === 'ALL'
    ? cases.value
    : cases.value.filter((item) => item.truth_category === truthFilter.value),
)

const selectedCase = computed(() =>
  cases.value.find((item) => item.case_id === selectedCaseId.value) ?? null,
)

watch(
  cases,
  (availableCases) => {
    if (availableCases.length === 0 || selectedCaseId.value) return
    selectedCaseId.value =
      availableCases.find((item) => item.truth_category === 'SIMULATED_FALL')?.case_id ??
      availableCases[0].case_id
  },
  { immediate: true },
)

watch(truthFilter, () => {
  if (!filteredCases.value.some((item) => item.case_id === selectedCaseId.value)) {
    selectedCaseId.value = filteredCases.value[0]?.case_id ?? ''
  }
})

const connectionTone = computed<BadgeTone>(() => {
  if (phase.value === 'connected') return 'success'
  if (phase.value === 'checking' || phase.value === 'connecting') return 'info'
  return 'warning'
})

const connectionLabel = computed(() => {
  if (phase.value === 'connected') return '本地服务已连接'
  if (phase.value === 'checking') return '正在检查本地服务'
  if (phase.value === 'connecting') return '正在连接实时通道'
  if (phase.value === 'degraded') return '本地服务部分可用'
  return '后端未连接'
})

const connectionDetail = computed(() => {
  if (phase.value === 'connected') {
    return `后端、SQLite 与实时通道已连接；已读取 ${cases.value.length} 个案例和 ${models.value.length} 个模型。`
  }
  if (phase.value === 'checking' || phase.value === 'connecting') {
    return '正在核对后端、SQLite 与实时通道的真实状态。'
  }
  return '本地服务当前不可完整使用；页面会保留最后一次成功读取的清单。'
})

const connectionMessage = computed(() => {
  if (phase.value === 'connected') {
    return `本地后端、SQLite 和 WebSocket 已连通；案例库实读 ${cases.value.length} 个，模型清单实读 ${models.value.length} 个。`
  }
  if (phase.value === 'checking') {
    return '正在向本地后端发送健康检查，请稍候。'
  }
  if (phase.value === 'connecting') {
    return '健康检查已通过，正在建立 WebSocket 实时状态通道。'
  }
  return errorMessage.value || '本地服务当前不可用，页面会自动重试。'
})

const systemStatus = computed<SystemStatusItem[]>(() => {
  const backendReady = status.value?.service.state === 'ready'
  const databaseReady = status.value?.database.state === 'ready'
  const caseCount = status.value?.cases.count

  return [
    { label: '前端界面', value: '已就绪', detail: 'Vue 3 · Tabler', tone: 'success' },
    {
      label: 'FastAPI 后端',
      value: backendReady ? '已连接' : phase.value === 'checking' ? '检查中' : '未连接',
      detail: backendReady
        ? `v${status.value?.service.version}${phase.value === 'connected' ? ' · 实时通道' : ''}`
        : '自动重试中',
      tone: backendReady ? (phase.value === 'connected' ? 'success' : 'info') : connectionTone.value,
    },
    {
      label: 'SQLite 数据库',
      value: databaseReady ? '已就绪' : phase.value === 'checking' ? '检查中' : '未连接',
      detail: databaseReady ? `结构版本 ${status.value?.database.schema_version}` : '等待健康检查',
      tone: databaseReady ? 'success' : connectionTone.value,
    },
    {
      label: '测试案例',
      value: typeof caseCount === 'number' ? `${caseCount} 个` : '—',
      detail: caseCount === 0 ? '尚未导入' : typeof caseCount === 'number' ? '数据库实数' : '暂不可读取',
      tone: typeof caseCount === 'number' && caseCount > 0 ? 'info' : 'neutral',
    },
  ]
})

const modelDefinitions: ModelSummary[] = [
  {
    id: 'model-fall',
    name: '腕部跌倒检测',
    purpose: '事件识别',
    description: '读取腕部六轴 IMU 窗口，识别刚刚发生的受控模拟跌倒候选，不预测未来跌倒。',
    input: '50 Hz · 4 秒 · 200 × 6',
    status: '待接入',
    tone: 'warning',
    icon: IconAlertTriangle,
    kind: 'FALL_DETECTION',
  },
  {
    id: 'model-routine',
    name: '个人规律异常',
    purpose: '规律偏离',
    description: '学习多日用餐、午睡和散步事件，判断时间、次数、时长或缺失是否偏离个人规律。',
    input: '多日生活事件',
    status: '待重构',
    tone: 'info',
    icon: IconCalendarStats,
    kind: 'ROUTINE_ANOMALY',
  },
  {
    id: 'model-activity',
    name: '腕部活动识别',
    purpose: '活动分类',
    description: '把腕部三轴加速度转换为走路、进食候选、睡眠或躺卧候选，以及其他或未知。',
    input: '20 Hz · 20 秒 · 400 × 3',
    status: '待训练',
    tone: 'neutral',
    icon: IconWalk,
    kind: 'ACTIVITY_RECOGNITION',
  },
]

const modelSummaries = computed<ModelSummary[]>(() =>
  modelDefinitions.map((definition) => {
    const manifest = models.value.find((item) => item.model_kind === definition.kind)
    if (!manifest) return definition
    return {
      ...definition,
      status: manifest.deployment_approved ? '已批准部署' : '已接入 · 研究版',
      tone: manifest.deployment_approved ? 'success' : 'info',
      version: manifest.version,
    }
  }),
)

const connectedModelCount = computed(() => models.value.length)

function allowedModelText(item: { allowed_models: readonly ModelKind[] } | null): string {
  if (!item || item.allowed_models.length === 0) return '无可运行模型'
  return item.allowed_models.map((kind) => modelLabels[kind]).join('、')
}

const replayPhaseLabel = computed(() => {
  const labels = {
    idle: '未选择',
    loading: '正在读取',
    ready: '等待启动',
    running: '正在回放',
    paused: '已暂停',
    completed: '回放完成',
    error: '读取失败',
  }
  return labels[replayPhase.value]
})

const replayTone = computed<BadgeTone>(() => {
  if (replayPhase.value === 'running') return 'success'
  if (replayPhase.value === 'loading') return 'info'
  if (replayPhase.value === 'error') return 'danger'
  if (replayPhase.value === 'paused' || replayPhase.value === 'completed') return 'warning'
  return preview.value ? 'info' : 'neutral'
})

function formatReplayTime(valueMs: number): string {
  const totalSeconds = Math.max(0, Math.floor(valueMs / 1_000))
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function intervalStyle(startMs: number, endMs: number) {
  const duration = Math.max(1, effectiveDurationMs.value)
  return {
    left: `${Math.min(100, (startMs / duration) * 100)}%`,
    width: `${Math.max(0.7, ((endMs - startMs) / duration) * 100)}%`,
  }
}

function routineStatusText(status: string): string {
  const labels: Record<string, string> = {
    WITHIN_ROUTINE: '规律范围内',
    EARLY: '时间偏早',
    LATE: '时间偏晚',
    DURATION_DEVIATION: '时长偏离',
    COUNT_DEVIATION: '次数偏离',
    MISSING: '记录缺失',
  }
  return labels[status] ?? status
}

function activityLabelText(label: string): string {
  const labels: Record<string, string> = {
    walking: '走路',
    eating_candidate: '进食候选',
    sleep_or_lying_candidate: '睡眠或躺卧候选',
    other_unknown: '其他或未知',
  }
  return labels[label] ?? label
}

const replayOutputs = computed(() => [
  {
    label: '六轴 / 三轴波形',
    status: preview.value?.sensor_samples.length
      ? `${preview.value.sensor_samples.length} 个真实显示点`
      : preview.value?.routine_profile
        ? '此案例无传感器流'
        : '暂无数据',
    icon: IconWaveSine,
  },
  {
    label: '活动时间线',
    status: preview.value?.routine_days.length
      ? `${preview.value.routine_days.length} 天`
      : preview.value?.ground_truth_events.length
        ? `${preview.value.ground_truth_events.length} 个真实标签区间`
        : '暂无数据',
    icon: IconTimeline,
  },
  {
    label: '告警事件',
    status: preview.value?.fall_alarm_episodes.length
      ? `${visibleAlarmEpisodes.value.length} / ${preview.value.fall_alarm_episodes.length} 段已到达`
      : currentRoutineDay.value
        ? `${currentRoutineDay.value.assessments.filter((item) => item.status !== 'WITHIN_ROUTINE').length} 项规律偏离`
        : preview.value?.activity_result
          ? activityLabelText(preview.value.activity_result.predicted_label)
        : '暂无数据',
    icon: IconActivityHeartbeat,
  },
])

</script>

<template>
  <AppShell
    :connection-label="connectionLabel"
    :connection-tone="connectionTone"
    :connection-detail="connectionDetail"
    :is-refreshing="isRefreshing"
    @refresh="refresh"
  >
    <div id="overview" class="page-header app-page-header">
      <div>
        <p class="page-pretitle">老年人 AI 模拟智能手表</p>
        <h1 class="page-title">系统总览</h1>
        <p class="app-page-header__summary">
          查看数据接入、模拟回放和三个模型的当前真实状态。
        </p>
      </div>
      <StatusBadge tone="info">研究与比赛演示</StatusBadge>
    </div>

    <section class="card system-strip" aria-labelledby="system-status-title">
      <h2 id="system-status-title" class="visually-hidden">系统连接状态</h2>
      <div v-for="item in systemStatus" :key="item.label" class="system-strip__item">
        <div class="system-strip__label">{{ item.label }}</div>
        <div class="system-strip__value">
          <strong>{{ item.value }}</strong>
          <StatusBadge :tone="item.tone">{{ item.detail }}</StatusBadge>
        </div>
      </div>
    </section>

    <p class="connection-message" :class="`connection-message--${connectionTone}`" role="status">
      {{ connectionMessage }}
    </p>

    <p v-if="catalogError" class="connection-message connection-message--warning" role="alert">
      {{ catalogError }}
      <button class="text-action" type="button" @click="refreshCatalog">重新读取</button>
    </p>

    <div class="dashboard-grid">
      <AppCard id="replay" class="replay-card" aria-labelledby="replay-title">
        <template #header>
          <div class="app-card__heading">
            <span class="app-card__icon" aria-hidden="true">
              <IconPlayerPlay :size="20" :stroke-width="1.8" />
            </span>
            <div>
              <h2 id="replay-title" class="card-title">模拟手表回放</h2>
              <p>选择案例后，这里按时间显示传感器、活动和告警。</p>
            </div>
          </div>
          <StatusBadge :tone="replayTone">{{ replayPhaseLabel }}</StatusBadge>
        </template>

        <section class="case-picker" aria-labelledby="case-picker-title">
          <div class="case-picker__heading">
            <div>
              <h3 id="case-picker-title">选择可追溯测试案例</h3>
              <p>这里只列出已写入本机 SQLite、并保留来源版本的案例。</p>
            </div>
            <span>{{ filteredCases.length }} / {{ cases.length }} 个</span>
          </div>
          <div class="case-filter" aria-label="按真实性类别筛选">
            <button
              type="button"
              :class="{ 'is-active': truthFilter === 'ALL' }"
              @click="truthFilter = 'ALL'"
            >
              全部 {{ cases.length }}
            </button>
            <button
              v-for="category in (Object.keys(truthLabels) as TruthCategory[])"
              :key="category"
              type="button"
              :class="{ 'is-active': truthFilter === category }"
              :disabled="!caseCounts.get(category)"
              @click="truthFilter = category"
            >
              {{ truthLabels[category] }} {{ caseCounts.get(category) ?? 0 }}
            </button>
          </div>
          <label class="case-select">
            <span>当前案例</span>
            <select v-model="selectedCaseId" :disabled="isCatalogLoading || filteredCases.length === 0">
              <option value="" disabled>{{ isCatalogLoading ? '正在读取案例…' : '请选择案例' }}</option>
              <option v-for="item in filteredCases" :key="item.case_id" :value="item.case_id">
                {{ item.title }}
              </option>
            </select>
          </label>
          <div class="replay-controls" aria-label="回放控制">
            <AppButton
              v-if="replayPhase !== 'running'"
              intent="primary"
              emphasis="solid"
              :busy="replayPhase === 'loading'"
              :disabled="!preview || replayPhase === 'error'"
              @click="startReplay"
            >
              <IconPlayerPlay :size="16" :stroke-width="1.8" aria-hidden="true" />
              {{ replayPhase === 'paused' ? '继续回放' : replayPhase === 'completed' ? '重新回放' : '开始回放' }}
            </AppButton>
            <AppButton v-else intent="primary" emphasis="outline" @click="pauseReplay">
              <IconPlayerPause :size="16" :stroke-width="1.8" aria-hidden="true" />
              暂停
            </AppButton>
            <AppButton :disabled="!preview || replayPhase === 'loading'" @click="resetReplay">
              <IconRefresh :size="16" :stroke-width="1.8" aria-hidden="true" />
              重置
            </AppButton>
            <label class="speed-control">
              <span>速度</span>
              <select v-model.number="replaySpeed" :disabled="replayPhase === 'loading'">
                <option :value="1">1×</option>
                <option :value="2">2×</option>
                <option :value="4">4×</option>
                <option :value="8">8×</option>
                <option :value="16">16×</option>
              </select>
            </label>
            <div class="replay-clock" aria-live="polite">
              <span>{{ formatReplayTime(cursorMs) }} / {{ formatReplayTime(effectiveDurationMs) }}</span>
              <div class="replay-clock__track" aria-hidden="true">
                <i :style="{ width: `${replayProgress * 100}%` }"></i>
              </div>
            </div>
          </div>
          <p v-if="replayError" class="replay-error" role="alert">
            {{ replayError }}
            <button type="button" class="text-action" @click="reloadReplay">重新读取</button>
          </p>
        </section>

        <div class="replay-layout">
          <section class="device-status" aria-labelledby="device-status-title">
            <div class="device-status__screen" aria-hidden="true">
              <IconDeviceWatch :size="34" :stroke-width="1.6" />
              <strong>{{ preview ? formatReplayTime(cursorMs) : '--:--' }}</strong>
              <span>{{ replayPhaseLabel }}</span>
            </div>
            <h3 id="device-status-title">设备与回放状态</h3>
            <dl>
              <div>
                <dt>采样流</dt>
                <dd>{{ selectedCase?.sensor_stream_count ? `${selectedCase.sensor_stream_count} 条已登记` : '无传感器流' }}</dd>
              </div>
              <div>
                <dt>允许模型</dt>
                <dd>{{ selectedCase?.allowed_models.length ?? 0 }} 个</dd>
              </div>
              <div>
                <dt>回放进度</dt>
                <dd>{{ preview ? `${Math.round(replayProgress * 100)}%` : '未开始' }}</dd>
              </div>
            </dl>
          </section>

          <div class="replay-content">
            <EmptyState
              v-if="!selectedCase"
              title="尚未选择测试案例"
              description="案例清单尚未就绪，因此不显示随机波形、假进度或模型分数。"
            >
              <template #icon>
                <IconDatabaseOff :size="30" :stroke-width="1.7" />
              </template>
            </EmptyState>

            <section v-else class="selected-case" aria-live="polite">
              <div class="selected-case__topline">
                <StatusBadge :tone="selectedCase.truth_category === 'SIMULATED_FALL' ? 'warning' : 'info'">
                  {{ truthLabels[selectedCase.truth_category] }}
                </StatusBadge>
                <span>{{ ageLabels[selectedCase.age_group] }}</span>
              </div>
              <h3>{{ selectedCase.title }}</h3>
              <p>{{ allowedModelText(selectedCase) }}</p>
              <dl>
                <div>
                  <dt>案例编号</dt>
                  <dd>{{ selectedCase.case_id }}</dd>
                </div>
                <div>
                  <dt>动作标签</dt>
                  <dd>{{ selectedCase.activity_label ?? '未设置' }}</dd>
                </div>
              </dl>
            </section>

            <div class="output-list" aria-label="回放输出状态">
              <div v-for="output in replayOutputs" :key="output.label" class="output-list__row">
                <component :is="output.icon" :size="18" :stroke-width="1.7" aria-hidden="true" />
                <span>{{ output.label }}</span>
                <strong>{{ output.status }}</strong>
              </div>
            </div>
          </div>
        </div>

        <section v-if="preview?.sensor_stream" class="replay-evidence" aria-labelledby="sensor-waveform-title">
          <div class="replay-evidence__header">
            <div>
              <h3 id="sensor-waveform-title">真实六轴传感器波形</h3>
              <p>
                {{ preview.sensor_stream.sample_rate_hz }} Hz ·
                {{ preview.sensor_stream.sample_count }} 个原始采样 ·
                显示 {{ preview.sensor_samples.length }} 个实际抽样点
              </p>
            </div>
            <StatusBadge :tone="preview.sensor_quality?.flags.length ? 'warning' : 'success'">
              {{ preview.sensor_quality?.flags.length ? `${preview.sensor_quality.flags.length} 个质量标记` : '未登记质量异常' }}
            </StatusBadge>
          </div>
          <SensorWaveform
            :samples="preview.sensor_samples"
            :channels="preview.sensor_stream.channels"
            :units="preview.sensor_stream.units"
            :duration-ms="preview.duration_ms"
            :cursor-ms="cursorMs"
          />

          <div class="evidence-timeline" aria-label="真实标签、模型候选与当前进度时间线">
            <div class="evidence-timeline__row">
              <span>真实标签</span>
              <div class="evidence-timeline__track">
                <i
                  v-for="event in preview.ground_truth_events"
                  :key="event.event_id"
                  class="evidence-timeline__interval evidence-timeline__interval--truth"
                  :style="intervalStyle(event.start_offset_ms, event.end_offset_ms)"
                  :title="`${event.label}：${formatReplayTime(event.start_offset_ms)}–${formatReplayTime(event.end_offset_ms)}`"
                ></i>
              </div>
            </div>
            <div class="evidence-timeline__row">
              <span>候选告警</span>
              <div class="evidence-timeline__track">
                <i
                  v-for="episode in preview.fall_alarm_episodes"
                  :key="`${episode.start_offset_ms}-${episode.end_offset_ms}`"
                  class="evidence-timeline__interval evidence-timeline__interval--alarm"
                  :class="{ 'is-pending': episode.start_offset_ms > cursorMs }"
                  :style="intervalStyle(episode.start_offset_ms, episode.end_offset_ms)"
                  :title="`峰值 ${episode.peak_probability.toFixed(3)}；${episode.window_count} 个窗口`"
                ></i>
              </div>
            </div>
            <i class="evidence-timeline__cursor" :style="{ left: `${replayProgress * 100}%` }" aria-hidden="true"></i>
          </div>

          <div class="model-evidence-grid">
            <div>
              <span>当前跌倒候选概率</span>
              <strong>{{ currentFallWindow ? currentFallWindow.fall_probability.toFixed(3) : '尚未到达模型窗口' }}</strong>
            </div>
            <div>
              <span>manifest 阈值</span>
              <strong>{{ preview.fall_threshold?.toFixed(2) ?? '不适用' }}</strong>
            </div>
            <div>
              <span>已到达候选告警</span>
              <strong>{{ visibleAlarmEpisodes.length }} 段</strong>
            </div>
            <div>
              <span>模型状态</span>
              <strong>研究版 · 未获部署批准</strong>
            </div>
          </div>
        </section>

        <section v-if="preview?.routine_profile && currentRoutineDay" class="replay-evidence" aria-labelledby="routine-timeline-title">
          <div class="replay-evidence__header">
            <div>
              <h3 id="routine-timeline-title">100 天合成生活规律时间线</h3>
              <p>
                第 {{ Math.min(preview.routine_days.length, Math.floor(cursorMs / 1000) + 1) }} / {{ preview.routine_days.length }} 天 ·
                固定种子 {{ preview.routine_profile.seed }} · 共 {{ preview.routine_profile.event_count }} 条事件
              </p>
            </div>
            <StatusBadge tone="warning">合成事件，不是真实老人记录</StatusBadge>
          </div>
          <div class="routine-day-grid">
            <article>
              <span>当前日期</span>
              <strong>{{ currentRoutineDay.day }}</strong>
              <p>{{ currentRoutineDay.events.length }} 条用餐、午睡或散步事件</p>
            </article>
            <article v-for="assessment in currentRoutineDay.assessments" :key="assessment.event_type">
              <span>{{ assessment.event_type }}</span>
              <strong>{{ routineStatusText(assessment.status) }}</strong>
              <p>{{ assessment.evidence[0] }}</p>
            </article>
          </div>
        </section>

        <section v-if="preview?.activity_result" class="replay-evidence" aria-labelledby="activity-result-title">
          <div class="replay-evidence__header">
            <div>
              <h3 id="activity-result-title">腕部活动识别结果</h3>
              <p>一个 20 秒真实自由生活三轴窗口；四类概率独立显示。</p>
            </div>
            <StatusBadge tone="info">研究版 · 未完成外部验证</StatusBadge>
          </div>
          <div class="activity-result-summary">
            <div>
              <span>最高概率候选</span>
              <strong>{{ activityLabelText(preview.activity_result.predicted_label) }}</strong>
            </div>
            <div>
              <span>来源映射标签</span>
              <strong>{{ activityLabelText(preview.case.activity_label ?? 'other_unknown') }}</strong>
            </div>
          </div>
          <div class="model-evidence-grid">
            <div>
              <span>走路</span>
              <strong>{{ (preview.activity_result.probabilities.walking * 100).toFixed(1) }}%</strong>
            </div>
            <div>
              <span>进食候选</span>
              <strong>{{ (preview.activity_result.probabilities.eating_candidate * 100).toFixed(1) }}%</strong>
            </div>
            <div>
              <span>睡眠或躺卧候选</span>
              <strong>{{ (preview.activity_result.probabilities.sleep_or_lying_candidate * 100).toFixed(1) }}%</strong>
            </div>
            <div>
              <span>其他或未知</span>
              <strong>{{ (preview.activity_result.probabilities.other_unknown * 100).toFixed(1) }}%</strong>
            </div>
          </div>
        </section>

        <div v-if="preview" class="replay-messages" role="note">
          <p v-for="message in preview.messages" :key="message">{{ message }}</p>
        </div>

        <dl class="replay-provenance" aria-label="当前案例来源">
          <div>
            <dt>案例来源</dt>
            <dd>{{ selectedCase?.source_name ?? '未选择' }}</dd>
          </div>
          <div>
            <dt>真实性类别</dt>
            <dd>{{ selectedCase ? truthLabels[selectedCase.truth_category] : '未分类' }}</dd>
          </div>
          <div>
            <dt>固定来源版本</dt>
            <dd :title="selectedCase?.fixed_version">{{ selectedCase?.fixed_version.slice(0, 12) ?? '暂无' }}</dd>
          </div>
        </dl>
      </AppCard>

      <AppCard id="provenance" class="provenance-card" aria-labelledby="provenance-title">
        <template #header>
          <div class="app-card__heading">
            <span class="app-card__icon" aria-hidden="true">
              <IconFileSearch :size="20" :stroke-width="1.8" />
            </span>
            <div>
              <h2 id="provenance-title" class="card-title">数据与来源</h2>
              <p>每个案例都必须保留来源和真实性说明。</p>
            </div>
          </div>
        </template>

        <dl class="provenance-list">
          <div>
            <dt>当前案例</dt>
            <dd>{{ selectedCase?.case_id ?? '未选择' }}</dd>
          </div>
          <div>
            <dt>来源数据集</dt>
            <dd>{{ selectedCase?.source_name ?? '暂无' }}</dd>
          </div>
          <div>
            <dt>真实性类别</dt>
            <dd>{{ selectedCase ? truthLabels[selectedCase.truth_category] : '未分类' }}</dd>
          </div>
          <div>
            <dt>模型 manifest</dt>
            <dd>{{ selectedCase ? `${selectedCase.allowed_models.length} 个可用范围` : '未加载' }}</dd>
          </div>
        </dl>

        <div class="integrity-alert" role="note">
          <IconShieldCheck :size="22" :stroke-width="1.7" aria-hidden="true" />
          <p>
            只有实际导入并登记来源的数据才会进入回放。年轻参与者完成的受控模拟跌倒不会被描述成真实老人跌倒。
          </p>
        </div>
      </AppCard>
    </div>

    <AppCard id="models" class="models-card" aria-labelledby="models-title">
      <template #header>
        <div class="app-card__heading">
          <span class="app-card__icon" aria-hidden="true">
            <IconActivityHeartbeat :size="20" :stroke-width="1.8" />
          </span>
          <div>
            <h2 id="models-title" class="card-title">三模型中心</h2>
            <p>三个模型独立输出，不把不同含义的分数直接平均成健康风险。</p>
          </div>
        </div>
        <StatusBadge :tone="connectedModelCount ? 'info' : 'neutral'">
          {{ connectedModelCount }} / 3 已登记
        </StatusBadge>
      </template>

      <div class="model-list">
        <article
          v-for="model in modelSummaries"
          :id="model.id"
          :key="model.id"
          class="model-row"
        >
          <span class="model-row__icon" aria-hidden="true">
            <component :is="model.icon" :size="22" :stroke-width="1.7" />
          </span>
          <div class="model-row__content">
            <div class="model-row__title">
              <h3>{{ model.name }}</h3>
              <span>{{ model.purpose }}</span>
            </div>
            <p>{{ model.description }}</p>
          </div>
          <dl class="model-row__meta">
            <div>
              <dt>主要输入</dt>
              <dd>{{ model.input }}</dd>
            </div>
            <div>
              <dt>当前输出</dt>
              <dd>{{ model.version ? `v${model.version}` : '暂无' }}</dd>
            </div>
          </dl>
          <StatusBadge :tone="model.tone">{{ model.status }}</StatusBadge>
        </article>
      </div>
    </AppCard>
  </AppShell>
</template>
