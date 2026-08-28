<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  samples: readonly { offset_ms: number; values: readonly number[] }[]
  channels: readonly string[]
  units: readonly string[]
  durationMs: number
  cursorMs: number
}>()

const width = 800
const height = 156
const padding = 14
const colors = ['#4fb9dc', '#138b59', '#d95b68', '#8067a8', '#c98d24', '#168d82']

const panels = computed(() => {
  const groups = props.channels.length >= 6
    ? [
        { title: '三轴加速度', indices: [0, 1, 2] },
        { title: '三轴角速度', indices: [3, 4, 5] },
      ]
    : [{ title: '三轴加速度', indices: props.channels.map((_, index) => index) }]

  return groups.map((group) => {
    const values = props.samples.flatMap((sample) =>
      group.indices.map((index) => Math.abs(sample.values[index] ?? 0)),
    )
    const maximum = Math.max(1e-6, ...values)
    const plotWidth = width - padding * 2
    const plotHeight = height - padding * 2
    const lines = group.indices.map((channelIndex) => ({
      channel: props.channels[channelIndex] ?? `c${channelIndex}`,
      unit: props.units[channelIndex] ?? '',
      color: colors[channelIndex % colors.length],
      points: props.samples
        .map((sample) => {
          const x = padding + (sample.offset_ms / Math.max(1, props.durationMs)) * plotWidth
          const value = sample.values[channelIndex] ?? 0
          const y = padding + plotHeight / 2 - (value / maximum) * (plotHeight / 2 - 3)
          return `${x.toFixed(2)},${y.toFixed(2)}`
        })
        .join(' '),
    }))
    return { ...group, maximum, lines }
  })
})

const cursorX = computed(() =>
  padding + (Math.min(props.cursorMs, props.durationMs) / Math.max(1, props.durationMs)) * (width - padding * 2),
)
</script>

<template>
  <div class="waveform-stack">
    <section v-for="panel in panels" :key="panel.title" class="waveform-panel">
      <div class="waveform-panel__header">
        <strong>{{ panel.title }}</strong>
        <div class="waveform-legend" aria-label="通道图例">
          <span v-for="line in panel.lines" :key="line.channel">
            <i :style="{ backgroundColor: line.color }" aria-hidden="true"></i>
            {{ line.channel }} · {{ line.unit }}
          </span>
        </div>
      </div>
      <svg
        class="waveform-chart"
        :viewBox="`0 0 ${width} ${height}`"
        role="img"
        :aria-label="`${panel.title}真实回放波形，纵轴范围正负 ${panel.maximum.toFixed(2)}`"
      >
        <line :x1="padding" :x2="width - padding" :y1="height / 2" :y2="height / 2" class="waveform-chart__baseline" />
        <polyline
          v-for="line in panel.lines"
          :key="line.channel"
          :points="line.points"
          :stroke="line.color"
          class="waveform-chart__line"
        />
        <line :x1="cursorX" :x2="cursorX" :y1="padding" :y2="height - padding" class="waveform-chart__cursor" />
      </svg>
    </section>
  </div>
</template>
