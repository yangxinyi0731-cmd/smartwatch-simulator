import { computed, onMounted, onUnmounted, readonly, ref } from 'vue'

import type {
  BatchReplayTaskListResponse,
  BatchReplayTaskResponse,
} from '../api/generated'

const ACTIVE_STATES = new Set(['QUEUED', 'RUNNING'])
const POLL_INTERVAL_MS = 750
const REQUEST_TIMEOUT_MS = 8_000

async function requestJson<T>(url: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  try {
    const response = await fetch(url, {
      ...init,
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...init.headers,
      },
      signal: controller.signal,
    })
    const payload: unknown = await response.json()
    if (!response.ok) throw new Error(`request failed: ${response.status}`)
    return payload as T
  } finally {
    window.clearTimeout(timeout)
  }
}

export function useBatchReplays() {
  const latestTask = ref<BatchReplayTaskResponse | null>(null)
  const isLoading = ref(true)
  const isCreating = ref(false)
  const errorMessage = ref('')
  let pollTimer: number | null = null
  let stopped = false

  function clearPoll() {
    if (pollTimer !== null) window.clearTimeout(pollTimer)
    pollTimer = null
  }

  function schedulePoll() {
    clearPoll()
    if (!latestTask.value || !ACTIVE_STATES.has(latestTask.value.state) || stopped) return
    pollTimer = window.setTimeout(() => void refreshTask(latestTask.value!.task_id), POLL_INTERVAL_MS)
  }

  async function refreshTask(taskId: string) {
    try {
      latestTask.value = await requestJson<BatchReplayTaskResponse>(
        `/api/batch-replays/${encodeURIComponent(taskId)}`,
      )
      errorMessage.value = ''
    } catch {
      if (!stopped) errorMessage.value = '批量任务状态暂时读取失败，稍后会继续尝试。'
    } finally {
      schedulePoll()
    }
  }

  async function refreshLatest() {
    isLoading.value = true
    try {
      const list = await requestJson<BatchReplayTaskListResponse>('/api/batch-replays?limit=1')
      if (list.items.length) {
        await refreshTask(list.items[0].task_id)
      } else {
        latestTask.value = null
      }
      errorMessage.value = ''
    } catch {
      if (!stopped) errorMessage.value = '批量任务清单暂时读取失败，可以稍后重试。'
    } finally {
      isLoading.value = false
    }
  }

  async function create(caseIds: string[]) {
    if (!caseIds.length || isCreating.value) return
    isCreating.value = true
    errorMessage.value = ''
    clearPoll()
    try {
      latestTask.value = await requestJson<BatchReplayTaskResponse>('/api/batch-replays', {
        method: 'POST',
        body: JSON.stringify({
          client_request_id: `ui-${crypto.randomUUID()}`,
          case_ids: caseIds,
        }),
      })
      schedulePoll()
    } catch {
      errorMessage.value = '批量任务创建失败；案例集合可能已变化，或本地服务暂不可用。'
    } finally {
      isCreating.value = false
    }
  }

  onMounted(() => void refreshLatest())
  onUnmounted(() => {
    stopped = true
    clearPoll()
  })

  return {
    latestTask: readonly(latestTask),
    isLoading: readonly(isLoading),
    isCreating: readonly(isCreating),
    isActive: computed(() => Boolean(latestTask.value && ACTIVE_STATES.has(latestTask.value.state))),
    errorMessage: readonly(errorMessage),
    create,
    refreshLatest,
  }
}
