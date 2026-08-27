<script setup lang="ts">
const modelCards = [
  {
    index: '01',
    name: '腕部跌倒检测',
    description: '读取 50 Hz 六轴 IMU 的 4 秒窗口，识别受控模拟跌倒候选。',
    input: '200 × 6',
    status: '待接入',
  },
  {
    index: '02',
    name: '个人规律异常',
    description: '学习用餐、午睡与散步规律，发现时间、次数、时长和缺失异常。',
    input: '多日事件',
    status: '待重构',
  },
  {
    index: '03',
    name: '腕部活动识别',
    description: '把三轴加速度翻译成走路、进食候选和睡眠或躺卧候选。',
    input: '400 × 3',
    status: '待训练',
  },
]

const navigation = [
  { href: '#overview', label: '守望台总览', current: true },
  { href: '#models', label: '三模型中心', current: false },
  { href: '#next-step', label: '下一步说明', current: false },
]
</script>

<template>
  <a class="skip-link" href="#main-content">跳到主要内容</a>

  <div class="app-shell">
    <aside class="sidebar" aria-label="项目导航">
      <div class="brand-lockup">
        <span class="brand-mark" aria-hidden="true">
          <span class="brand-mark__hand"></span>
        </span>
        <div>
          <p class="brand-kicker">WATCH / 001</p>
          <p class="brand-name">守望台</p>
        </div>
      </div>

      <nav class="primary-nav" aria-label="主导航">
        <a
          v-for="item in navigation"
          :key="item.href"
          :href="item.href"
          :aria-current="item.current ? 'page' : undefined"
          class="nav-link"
        >
          <span class="nav-link__dot" aria-hidden="true"></span>
          {{ item.label }}
        </a>
      </nav>

      <div class="sidebar-note">
        <p class="eyebrow">当前阶段</p>
        <p class="sidebar-note__title">第 1 步 · 平台骨架</p>
        <p>当前页面只展示界面结构，尚未连接后端、数据或模型。</p>
      </div>
    </aside>

    <main id="main-content" class="main-content">
      <header class="topbar">
        <div>
          <p class="eyebrow">老年人 AI 模拟智能手表</p>
          <h1>先看懂，再相信每一次判断。</h1>
        </div>
        <div class="build-badge" role="status">
          <span class="status-dot status-dot--idle" aria-hidden="true"></span>
          开发骨架 · 后端未连接
        </div>
      </header>

      <section id="overview" class="overview-grid" aria-labelledby="overview-title">
        <h2 id="overview-title" class="visually-hidden">模拟手表总览</h2>

        <article class="watch-stage" aria-labelledby="watch-title">
          <div class="stage-header">
            <div>
              <p class="eyebrow">模拟手表</p>
              <h2 id="watch-title">24 小时守护轨道</h2>
            </div>
            <span class="truth-badge">当前无数据</span>
          </div>

          <div class="watch-scene">
            <div class="watch-device" aria-label="尚未连接数据的虚拟智能手表">
              <span class="watch-crown" aria-hidden="true"></span>
              <div class="watch-screen">
                <div class="orbit" aria-hidden="true">
                  <span class="orbit__marker"></span>
                </div>
                <div class="watch-readout">
                  <p class="watch-readout__label">演示时间</p>
                  <p class="watch-readout__time">--:--</p>
                  <div class="watch-readout__rule"></div>
                  <p class="watch-readout__state">尚未选择测试案例</p>
                </div>
              </div>
            </div>

            <div class="watch-legend" aria-label="守护轨道图例">
              <div>
                <span class="legend-swatch legend-swatch--routine" aria-hidden="true"></span>
                <span>日常规律</span>
              </div>
              <div>
                <span class="legend-swatch legend-swatch--review" aria-hidden="true"></span>
                <span>需要关注</span>
              </div>
              <div>
                <span class="legend-swatch legend-swatch--alert" aria-hidden="true"></span>
                <span>紧急告警</span>
              </div>
            </div>
          </div>
        </article>

        <aside class="trace-panel" aria-labelledby="trace-title">
          <div class="stage-header stage-header--compact">
            <div>
              <p class="eyebrow">系统状态</p>
              <h2 id="trace-title">当前接入情况</h2>
            </div>
          </div>

          <dl class="trace-list">
            <div class="trace-row">
              <dt>前端界面</dt>
              <dd><span class="status-dot status-dot--ready" aria-hidden="true"></span>已建立</dd>
            </div>
            <div class="trace-row">
              <dt>FastAPI 后端</dt>
              <dd><span class="status-dot status-dot--idle" aria-hidden="true"></span>第 2 步</dd>
            </div>
            <div class="trace-row">
              <dt>SQLite 数据库</dt>
              <dd><span class="status-dot status-dot--idle" aria-hidden="true"></span>第 2 步</dd>
            </div>
            <div class="trace-row">
              <dt>真实测试案例</dt>
              <dd><span class="status-dot status-dot--idle" aria-hidden="true"></span>尚未导入</dd>
            </div>
          </dl>

          <div class="integrity-note">
            <span class="integrity-note__mark" aria-hidden="true">真</span>
            <p>没有数据时就显示“没有数据”，不会用随机数字伪装成真实模型结果。</p>
          </div>
        </aside>
      </section>

      <section id="models" class="models-section" aria-labelledby="models-title">
        <div class="section-heading">
          <div>
            <p class="eyebrow">三模型中心</p>
            <h2 id="models-title">每个模型都有清楚的工作边界</h2>
          </div>
          <p class="section-heading__summary">第 1 步只建立位置和说明，不展示未经运行的指标。</p>
        </div>

        <div class="model-grid">
          <article v-for="model in modelCards" :key="model.index" class="model-card">
            <div class="model-card__topline">
              <span class="model-index">{{ model.index }}</span>
              <span class="model-status">{{ model.status }}</span>
            </div>
            <h3>{{ model.name }}</h3>
            <p>{{ model.description }}</p>
            <dl class="model-meta">
              <div>
                <dt>主要输入</dt>
                <dd>{{ model.input }}</dd>
              </div>
              <div>
                <dt>当前输出</dt>
                <dd>暂无</dd>
              </div>
            </dl>
          </article>
        </div>
      </section>

      <section id="next-step" class="next-step" aria-labelledby="next-step-title">
        <div class="next-step__number" aria-hidden="true">02</div>
        <div>
          <p class="eyebrow">下一步（尚未开始）</p>
          <h2 id="next-step-title">让页面和后端第一次真正说上话</h2>
          <p>
            第 2 步将建立 FastAPI、SQLite 和 WebSocket。完成后，这里的“后端未连接”会变成真实健康检查结果。
          </p>
        </div>
      </section>
    </main>
  </div>
</template>
