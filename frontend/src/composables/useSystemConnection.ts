import { onMounted, onUnmounted, readonly, ref } from 'vue'

export type ConnectionPhase = 'checking' | 'connecting' | 'connected' | 'degraded' | 'offline'

export interface SystemStatus {
  event: 'system.status'
  service: {
    name: string
    version: string
    state: 'ready' | 'degraded'
  }
  database: {
    engine: 'sqlite'
    state: 'ready' | 'unavailable'
    schema_version: number | null
  }
  cases: {
    count: number | null
    state: 'empty' | 'available' | 'unavailable'
  }
  realtime: {
    transport: 'websocket'
    path: string
  }
  checked_at: string
  message: string
}

const HEALTH_TIMEOUT_MS = 5_000
const RETRY_DELAYS_MS = [1_000, 2_000, 5_000, 10_000]

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isSystemStatus(value: unknown): value is SystemStatus {
  if (!isRecord(value) || !isRecord(value.service) || !isRecord(value.database)) {
    return false
  }
  if (!isRecord(value.cases) || !isRecord(value.realtime)) {
    return false
  }

  return (
    value.event === 'system.status' &&
    typeof value.service.name === 'string' &&
    typeof value.service.version === 'string' &&
    (value.service.state === 'ready' || value.service.state === 'degraded') &&
    value.database.engine === 'sqlite' &&
    (value.database.state === 'ready' || value.database.state === 'unavailable') &&
    (typeof value.database.schema_version === 'number' || value.database.schema_version === null) &&
    ((typeof value.cases.count === 'number' && Number.isInteger(value.cases.count) && value.cases.count >= 0) ||
      value.cases.count === null) &&
    (value.cases.state === 'empty' ||
      value.cases.state === 'available' ||
      value.cases.state === 'unavailable') &&
    value.realtime.transport === 'websocket' &&
    typeof value.realtime.path === 'string' &&
    value.realtime.path.startsWith('/') &&
    typeof value.checked_at === 'string' &&
    typeof value.message === 'string'
  )
}

function websocketUrl(path: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${path}`
}

export function useSystemConnection() {
  const phase = ref<ConnectionPhase>('checking')
  const status = ref<SystemStatus | null>(null)
  const errorMessage = ref('')
  const isRefreshing = ref(false)

  let requestController: AbortController | null = null
  let requestGeneration = 0
  let retryAttempt = 0
  let retryTimer: number | null = null
  let socket: WebSocket | null = null
  let stopped = false

  function clearRetryTimer() {
    if (retryTimer !== null) {
      window.clearTimeout(retryTimer)
      retryTimer = null
    }
  }

  function closeSocket() {
    const currentSocket = socket
    socket = null
    if (currentSocket) {
      currentSocket.onopen = null
      currentSocket.onmessage = null
      currentSocket.onerror = null
      currentSocket.onclose = null
      currentSocket.close()
    }
  }

  function scheduleRefresh() {
    if (stopped || retryTimer !== null) {
      return
    }

    const delay = RETRY_DELAYS_MS[Math.min(retryAttempt, RETRY_DELAYS_MS.length - 1)]
    retryAttempt += 1
    retryTimer = window.setTimeout(() => {
      retryTimer = null
      void refresh()
    }, delay)
  }

  function connectRealtime(path: string) {
    closeSocket()
    phase.value = 'connecting'
    errorMessage.value = ''

    const currentSocket = new WebSocket(websocketUrl(path))
    socket = currentSocket

    currentSocket.onmessage = (event) => {
      if (socket !== currentSocket) {
        return
      }

      try {
        const payload: unknown = JSON.parse(String(event.data))
        if (!isSystemStatus(payload)) {
          throw new Error('invalid system status')
        }

        status.value = payload
        retryAttempt = 0
        if (payload.service.state === 'ready' && payload.database.state === 'ready') {
          phase.value = 'connected'
          errorMessage.value = ''
        } else {
          phase.value = 'degraded'
          errorMessage.value = payload.message
          scheduleRefresh()
        }
      } catch {
        phase.value = 'degraded'
        errorMessage.value = '实时通道返回了无法识别的状态，页面正在重新检查。'
        currentSocket.close()
      }
    }

    currentSocket.onerror = () => {
      currentSocket.close()
    }

    currentSocket.onclose = () => {
      if (stopped || socket !== currentSocket) {
        return
      }

      socket = null
      phase.value = status.value?.service.state === 'ready' ? 'degraded' : 'offline'
      errorMessage.value = '实时通道已断开，页面正在自动重连。'
      scheduleRefresh()
    }
  }

  async function refresh() {
    clearRetryTimer()
    requestController?.abort()
    closeSocket()

    const generation = ++requestGeneration
    const controller = new AbortController()
    requestController = controller
    phase.value = status.value ? 'connecting' : 'checking'
    errorMessage.value = ''
    isRefreshing.value = true

    const timeout = window.setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS)
    try {
      const response = await fetch('/api/health', {
        cache: 'no-store',
        headers: { Accept: 'application/json' },
        signal: controller.signal,
      })
      const payload: unknown = await response.json()

      if (generation !== requestGeneration) {
        return
      }
      if (!isSystemStatus(payload)) {
        throw new Error('invalid health response')
      }

      status.value = payload
      if (!response.ok || payload.service.state !== 'ready' || payload.database.state !== 'ready') {
        phase.value = 'degraded'
        errorMessage.value = payload.message
        scheduleRefresh()
        return
      }

      connectRealtime(payload.realtime.path)
    } catch (error) {
      if (generation !== requestGeneration) {
        return
      }
      if (error instanceof DOMException && error.name === 'AbortError' && stopped) {
        return
      }

      phase.value = 'offline'
      status.value = null
      errorMessage.value = '未检测到本地后端。请先启动后端服务，页面会自动重试。'
      scheduleRefresh()
    } finally {
      window.clearTimeout(timeout)
      if (generation === requestGeneration) {
        isRefreshing.value = false
        requestController = null
      }
    }
  }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      void refresh()
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    void refresh()
  })

  onUnmounted(() => {
    stopped = true
    requestGeneration += 1
    clearRetryTimer()
    requestController?.abort()
    closeSocket()
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })

  return {
    phase: readonly(phase),
    status: readonly(status),
    errorMessage: readonly(errorMessage),
    isRefreshing: readonly(isRefreshing),
    refresh,
  }
}
