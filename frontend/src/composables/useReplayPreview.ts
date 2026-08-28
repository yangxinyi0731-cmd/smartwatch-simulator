import { computed, onUnmounted, readonly, ref, watch, type Ref } from 'vue'

import type { ReplayPreviewResponse } from '../api/generated'

export type ReplayPhase = 'idle' | 'loading' | 'ready' | 'running' | 'paused' | 'completed' | 'error'

const REQUEST_TIMEOUT_MS = 15_000

export function useReplayPreview(caseId: Ref<string>) {
  const preview = ref<ReplayPreviewResponse | null>(null)
  const phase = ref<ReplayPhase>('idle')
  const cursorMs = ref(0)
  const speed = ref(4)
  const errorMessage = ref('')
  let requestController: AbortController | null = null
  let animationFrame: number | null = null
  let lastFrameAt: number | null = null
  let stopped = false

  const effectiveDurationMs = computed(() => {
    if (!preview.value) return 0
    if (preview.value.duration_ms > 0) return preview.value.duration_ms
    return preview.value.routine_days.length * 1_000
  })

  const progress = computed(() =>
    effectiveDurationMs.value > 0
      ? Math.min(1, cursorMs.value / effectiveDurationMs.value)
      : 0,
  )

  const currentFallWindow = computed(() => {
    const windows = preview.value?.fall_windows ?? []
    let current = null
    for (const window of windows) {
      if (window.start_offset_ms > cursorMs.value) break
      current = window
    }
    return current
  })

  const visibleAlarmEpisodes = computed(() =>
    (preview.value?.fall_alarm_episodes ?? []).filter(
      (episode) => episode.start_offset_ms <= cursorMs.value,
    ),
  )

  const currentRoutineDay = computed(() => {
    const days = preview.value?.routine_days ?? []
    if (days.length === 0) return null
    const index = Math.min(days.length - 1, Math.floor(cursorMs.value / 1_000))
    return days[index]
  })

  function stopAnimation() {
    if (animationFrame !== null) {
      window.cancelAnimationFrame(animationFrame)
      animationFrame = null
    }
    lastFrameAt = null
  }

  function tick(now: number) {
    if (phase.value !== 'running') return
    if (lastFrameAt === null) lastFrameAt = now
    const elapsed = now - lastFrameAt
    lastFrameAt = now
    cursorMs.value = Math.min(
      effectiveDurationMs.value,
      cursorMs.value + elapsed * speed.value,
    )
    if (cursorMs.value >= effectiveDurationMs.value) {
      phase.value = 'completed'
      stopAnimation()
      return
    }
    animationFrame = window.requestAnimationFrame(tick)
  }

  function start() {
    if (!preview.value || effectiveDurationMs.value <= 0) return
    if (phase.value === 'completed') cursorMs.value = 0
    phase.value = 'running'
    errorMessage.value = ''
    stopAnimation()
    animationFrame = window.requestAnimationFrame(tick)
  }

  function pause() {
    if (phase.value !== 'running') return
    phase.value = 'paused'
    stopAnimation()
  }

  function reset() {
    stopAnimation()
    cursorMs.value = 0
    if (preview.value) phase.value = 'ready'
  }

  async function load() {
    requestController?.abort()
    stopAnimation()
    preview.value = null
    cursorMs.value = 0
    errorMessage.value = ''
    if (!caseId.value) {
      phase.value = 'idle'
      return
    }

    const controller = new AbortController()
    requestController = controller
    phase.value = 'loading'
    const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
    try {
      const response = await fetch(
        `/api/cases/${encodeURIComponent(caseId.value)}/replay-preview`,
        {
          cache: 'no-store',
          headers: { Accept: 'application/json' },
          signal: controller.signal,
        },
      )
      const payload: unknown = await response.json()
      if (!response.ok) throw new Error(`request failed: ${response.status}`)
      if (stopped || requestController !== controller) return
      preview.value = payload as ReplayPreviewResponse
      phase.value = 'ready'
    } catch (error) {
      if (stopped || requestController !== controller) return
      phase.value = 'error'
      errorMessage.value =
        error instanceof DOMException && error.name === 'AbortError'
          ? '案例回放数据读取超时，请重试。'
          : '案例回放数据读取失败，请核对本地服务和数据文件。'
    } finally {
      window.clearTimeout(timeout)
      if (requestController === controller) requestController = null
    }
  }

  watch(caseId, () => void load(), { immediate: true })
  onUnmounted(() => {
    stopped = true
    requestController?.abort()
    stopAnimation()
  })

  return {
    preview: readonly(preview),
    phase: readonly(phase),
    cursorMs: readonly(cursorMs),
    speed,
    errorMessage: readonly(errorMessage),
    effectiveDurationMs,
    progress,
    currentFallWindow,
    visibleAlarmEpisodes,
    currentRoutineDay,
    start,
    pause,
    reset,
    reload: load,
  }
}
