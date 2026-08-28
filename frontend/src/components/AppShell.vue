<script setup lang="ts">
import {
  IconActivityHeartbeat,
  IconAlertTriangle,
  IconBrain,
  IconDatabase,
  IconFileAnalytics,
  IconFileSearch,
  IconLayoutDashboard,
  IconPlayerPlay,
} from '@tabler/icons-vue'

import AppButton from './AppButton.vue'
import StatusBadge from './StatusBadge.vue'

defineProps<{
  connectionLabel: string
  connectionTone: 'neutral' | 'info' | 'success' | 'warning' | 'danger'
  connectionDetail: string
  isRefreshing: boolean
}>()

const emit = defineEmits<{
  refresh: []
}>()

const navigation = [
  { label: '系统总览', href: '#overview', icon: IconLayoutDashboard, current: true },
  { label: '案例库', icon: IconDatabase, disabled: true },
  { label: '实时回放', href: '#replay', icon: IconPlayerPlay },
  {
    label: '三模型中心',
    href: '#models',
    icon: IconBrain,
    children: [
      { label: '跌倒检测', href: '#model-fall' },
      { label: '规律异常', href: '#model-routine' },
      { label: '活动识别', href: '#model-activity' },
    ],
  },
  { label: '告警记录', icon: IconAlertTriangle, disabled: true },
  { label: '测试报告', icon: IconFileAnalytics, disabled: true },
  { label: '数据与来源', href: '#provenance', icon: IconFileSearch },
]
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>

  <div class="page app-layout">
    <aside class="navbar navbar-vertical app-sidebar" aria-label="主导航">
      <div class="app-sidebar__inner">
        <a class="app-brand" href="#overview" aria-label="模拟智能手表系统总览">
          <span class="app-brand__mark" aria-hidden="true">
            <IconActivityHeartbeat :size="24" :stroke-width="1.8" />
          </span>
          <span>
            <strong>模拟智能手表</strong>
            <small>三模型研究平台</small>
          </span>
        </a>

        <nav class="app-nav" aria-label="功能导航">
          <ul class="app-nav__list">
            <li v-for="item in navigation" :key="item.label" class="app-nav__item">
              <span v-if="item.disabled" class="app-nav__link is-disabled" aria-disabled="true">
                <component :is="item.icon" :size="19" :stroke-width="1.8" aria-hidden="true" />
                <span>{{ item.label }}</span>
                <small>未开放</small>
              </span>

              <a
                v-else
                class="app-nav__link"
                :class="{ 'is-current': item.current }"
                :href="item.href"
                :aria-current="item.current ? 'page' : undefined"
              >
                <component :is="item.icon" :size="19" :stroke-width="1.8" aria-hidden="true" />
                <span>{{ item.label }}</span>
              </a>

              <ul v-if="item.children" class="app-nav__sublist">
                <li v-for="child in item.children" :key="child.label">
                  <a :href="child.href">{{ child.label }}</a>
                </li>
              </ul>
            </li>
          </ul>
        </nav>

        <div class="app-sidebar__status">
          <p>当前阶段</p>
          <strong>本地数据闭环</strong>
          <span>{{ connectionDetail }}</span>
        </div>
      </div>
    </aside>

    <div class="page-wrapper app-workspace">
      <header class="navbar navbar-expand-md app-topbar" aria-label="系统工具栏">
        <div class="container-xl app-topbar__inner">
          <div>
            <span class="app-topbar__label">研究演示环境</span>
            <span class="app-topbar__separator" aria-hidden="true"></span>
            <span class="app-topbar__meta">本地 Windows 运行</span>
          </div>
          <div class="app-topbar__status" aria-live="polite">
            <StatusBadge :tone="connectionTone">{{ connectionLabel }}</StatusBadge>
            <AppButton
              intent="neutral"
              emphasis="outline"
              :busy="isRefreshing"
              @click="emit('refresh')"
            >
              {{ isRefreshing ? '检查中' : '刷新状态' }}
            </AppButton>
          </div>
        </div>
      </header>

      <main id="main-content" class="page-body app-main" tabindex="-1">
        <div class="container-xl">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>
