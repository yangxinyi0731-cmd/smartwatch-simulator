import { onMounted, onUnmounted, readonly, ref } from 'vue'

import type { ReportListResponse, ReportSummaryItem } from '../api/generated'

const REQUEST_TIMEOUT_MS = 8_000

export function useReports() {
  const reports = ref<ReportSummaryItem[]>([])
  const disclaimers = ref<string[]>([])
  const isLoading = ref(true)
  const errorMessage = ref('')
  let controller: AbortController | null = null
  let stopped = false

  async function refresh() {
    controller?.abort()
    const currentController = new AbortController()
    controller = currentController
    isLoading.value = true
    errorMessage.value = ''
    const timeout = window.setTimeout(() => currentController.abort(), REQUEST_TIMEOUT_MS)

    try {
      const response = await fetch('/api/reports', {
        cache: 'no-store',
        headers: { Accept: 'application/json' },
        signal: currentController.signal,
      })
      const payload: unknown = await response.json()
      if (!response.ok) throw new Error(`request failed: ${response.status}`)
      if (stopped || controller !== currentController) return
      const catalog = payload as ReportListResponse
      reports.value = catalog.items
      disclaimers.value = catalog.disclaimers
    } catch (error) {
      if (stopped || controller !== currentController) return
      errorMessage.value =
        error instanceof DOMException && error.name === 'AbortError'
          ? '测试报告读取超时，可以稍后重试。'
          : '测试报告暂时读取失败，可以稍后重试。'
    } finally {
      window.clearTimeout(timeout)
      if (controller === currentController) {
        controller = null
        isLoading.value = false
      }
    }
  }

  onMounted(() => void refresh())
  onUnmounted(() => {
    stopped = true
    controller?.abort()
  })

  return {
    reports: readonly(reports),
    disclaimers: readonly(disclaimers),
    isLoading: readonly(isLoading),
    errorMessage: readonly(errorMessage),
    refresh,
  }
}
