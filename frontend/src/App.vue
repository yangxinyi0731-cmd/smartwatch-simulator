<script setup lang="ts">
import type { Component } from 'vue'
import {
  IconActivityHeartbeat,
  IconAlertTriangle,
  IconCalendarStats,
  IconDatabaseOff,
  IconDeviceWatch,
  IconFileSearch,
  IconPlayerPlay,
  IconShieldCheck,
  IconTimeline,
  IconWaveSine,
  IconWalk,
} from '@tabler/icons-vue'

import AppCard from './components/AppCard.vue'
import AppShell from './components/AppShell.vue'
import EmptyState from './components/EmptyState.vue'
import StatusBadge from './components/StatusBadge.vue'

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
}

const systemStatus: Array<{
  label: string
  value: string
  detail: string
  tone: BadgeTone
}> = [
  { label: '前端界面', value: '已就绪', detail: 'Vue 3 · Tabler', tone: 'success' },
  { label: 'FastAPI 后端', value: '未连接', detail: '尚未开始', tone: 'warning' },
  { label: 'SQLite 数据库', value: '未连接', detail: '尚未开始', tone: 'warning' },
  { label: '测试案例', value: '0 个', detail: '尚未导入', tone: 'neutral' },
]

const modelSummaries: ModelSummary[] = [
  {
    id: 'model-fall',
    name: '腕部跌倒检测',
    purpose: '事件识别',
    description: '读取腕部六轴 IMU 窗口，识别刚刚发生的受控模拟跌倒候选，不预测未来跌倒。',
    input: '50 Hz · 4 秒 · 200 × 6',
    status: '待接入',
    tone: 'warning',
    icon: IconAlertTriangle,
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
  },
]

const replayOutputs = [
  { label: '六轴 / 三轴波形', status: '暂无数据', icon: IconWaveSine },
  { label: '活动时间线', status: '暂无数据', icon: IconTimeline },
  { label: '告警事件', status: '暂无数据', icon: IconActivityHeartbeat },
]
</script>

<template>
  <AppShell>
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
          <StatusBadge tone="neutral">暂无数据</StatusBadge>
        </template>

        <div class="replay-layout">
          <section class="device-status" aria-labelledby="device-status-title">
            <div class="device-status__screen" aria-hidden="true">
              <IconDeviceWatch :size="34" :stroke-width="1.6" />
              <strong>--:--</strong>
              <span>回放未开始</span>
            </div>
            <h3 id="device-status-title">设备与回放状态</h3>
            <dl>
              <div>
                <dt>采样流</dt>
                <dd>未连接</dd>
              </div>
              <div>
                <dt>当前窗口</dt>
                <dd>暂无</dd>
              </div>
              <div>
                <dt>回放进度</dt>
                <dd>未开始</dd>
              </div>
            </dl>
          </section>

          <div class="replay-content">
            <EmptyState
              title="尚未选择测试案例"
              description="案例库还没有导入数据，因此不显示随机波形、假进度或模型分数。"
            >
              <template #icon>
                <IconDatabaseOff :size="30" :stroke-width="1.7" />
              </template>
            </EmptyState>

            <div class="output-list" aria-label="回放输出状态">
              <div v-for="output in replayOutputs" :key="output.label" class="output-list__row">
                <component :is="output.icon" :size="18" :stroke-width="1.7" aria-hidden="true" />
                <span>{{ output.label }}</span>
                <strong>{{ output.status }}</strong>
              </div>
            </div>
          </div>
        </div>

        <dl class="replay-provenance" aria-label="当前案例来源">
          <div>
            <dt>案例来源</dt>
            <dd>未选择</dd>
          </div>
          <div>
            <dt>真实性类别</dt>
            <dd>未分类</dd>
          </div>
          <div>
            <dt>文件校验</dt>
            <dd>暂无</dd>
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
            <dd>未选择</dd>
          </div>
          <div>
            <dt>来源数据集</dt>
            <dd>暂无</dd>
          </div>
          <div>
            <dt>真实性类别</dt>
            <dd>未分类</dd>
          </div>
          <div>
            <dt>模型 manifest</dt>
            <dd>未加载</dd>
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
        <StatusBadge tone="neutral">当前均未运行</StatusBadge>
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
              <dd>暂无</dd>
            </div>
          </dl>
          <StatusBadge :tone="model.tone">{{ model.status }}</StatusBadge>
        </article>
      </div>
    </AppCard>
  </AppShell>
</template>
