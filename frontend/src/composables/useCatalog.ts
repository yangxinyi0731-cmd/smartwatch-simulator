import { computed, onMounted, onUnmounted, readonly, ref } from 'vue'

import type {
  CaseListItem,
  CaseListResponse,
  ModelListItem,
  ModelListResponse,
} from '../api/generated'

const PAGE_SIZE = 50
const REQUEST_TIMEOUT_MS = 8_000

async function fetchJson<T>(url: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(url, {
    cache: 'no-store',
    headers: { Accept: 'application/json' },
    signal,
  })
  const payload: unknown = await response.json()
  if (!response.ok) {
    throw new Error(`request failed: ${response.status}`)
  }
  return payload as T
}

export function useCatalog() {
  const cases = ref<CaseListItem[]>([])
  const models = ref<ModelListItem[]>([])
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
      const [firstPage, modelCatalog] = await Promise.all([
        fetchJson<CaseListResponse>(`/api/cases?page=1&page_size=${PAGE_SIZE}&sort_by=case_id&sort_order=asc`, currentController.signal),
        fetchJson<ModelListResponse>('/api/models', currentController.signal),
      ])
      const remainingPages = Array.from(
        { length: Math.max(0, firstPage.total_pages - 1) },
        (_, index) => index + 2,
      )
      const additionalPages = await Promise.all(
        remainingPages.map((page) =>
          fetchJson<CaseListResponse>(
            `/api/cases?page=${page}&page_size=${PAGE_SIZE}&sort_by=case_id&sort_order=asc`,
            currentController.signal,
          ),
        ),
      )
      if (stopped || controller !== currentController) return

      cases.value = [firstPage, ...additionalPages].flatMap((page) => page.items)
      models.value = modelCatalog.items
    } catch (error) {
      if (stopped || controller !== currentController) return
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        errorMessage.value = '案例和模型清单暂时读取失败，可以稍后重试。'
      } else {
        errorMessage.value = '案例和模型清单读取超时，可以稍后重试。'
      }
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
    cases: readonly(cases),
    models: readonly(models),
    isLoading: readonly(isLoading),
    errorMessage: readonly(errorMessage),
    hasData: computed(() => cases.value.length > 0 || models.value.length > 0),
    refresh,
  }
}
