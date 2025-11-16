import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { type MaybeRef, computed, unref } from 'vue'

import {
  DocumentAnalysisState,
  type ChatResponseDto,
  type DocumentAnalysisStatusDto,
  type DocumentChatPayload,
  type ListSessionsParams,
  type SessionDocumentsLabelsMap,
  type SessionDocumentsQueryParams,
  type SessionDto,
} from '../models/session.models'
import { SessionServiceError, sessionService } from '../services/session.service'

export const SESSION_QUERY_KEYS = {
  all: ['sessions'] as const,
  list: ['sessions', 'list'] as const,
  detail: ['sessions', 'detail'] as const,
  documents: ['sessions', 'documents'] as const,
  documentDetails: ['sessions', 'document-details'] as const,
  analysis: ['sessions', 'document-analysis'] as const,
  labelsMap: ['sessions', 'labels-map'] as const,
} as const

export function useSessionsList(params?: MaybeRef<ListSessionsParams | undefined>) {
  const resolvedParams = computed(() => unref(params) ?? {})

  return useQuery<SessionDocumentsLabelsMap>({
    queryKey: computed(() => [...SESSION_QUERY_KEYS.list, resolvedParams.value]),
    queryFn: () => sessionService.listSessions(resolvedParams.value),
  })
}

export function useSession(sessionId: MaybeRef<string | number | undefined>) {
  const resolvedId = computed(() => unref(sessionId))

  return useQuery({
    queryKey: computed(() => [...SESSION_QUERY_KEYS.detail, resolvedId.value]),
    queryFn: () => {
      if (!resolvedId.value) {
        throw new SessionServiceError('Не передан идентификатор сессии.')
      }
      return sessionService.getSession(resolvedId.value)
    },
    enabled: computed(() => Boolean(resolvedId.value)),
  })
}

export interface UseSessionDocumentsConfig {
  refetchInterval?: number | false
}

export function useSessionDocuments(
  sessionId: MaybeRef<string | number | undefined>,
  params?: MaybeRef<SessionDocumentsQueryParams | undefined>,
  config?: MaybeRef<UseSessionDocumentsConfig | undefined>,
) {
  const resolvedId = computed(() => unref(sessionId))
  const resolvedParams = computed(() => unref(params) ?? {})
  const resolvedConfig = computed(() => unref(config))

  return useQuery({
    queryKey: computed(() => [
      ...SESSION_QUERY_KEYS.documents,
      resolvedId.value,
      resolvedParams.value,
    ]),
    queryFn: () => {
      if (!resolvedId.value) {
        throw new SessionServiceError('Не передан идентификатор сессии.')
      }
      return sessionService.listSessionDocuments(resolvedId.value, resolvedParams.value)
    },
    enabled: computed(() => Boolean(resolvedId.value)),
    refetchInterval: resolvedConfig.value?.refetchInterval,
  })
}

export function useSessionDocumentDetails(
  sessionId: MaybeRef<string | number | undefined>,
  documentId: MaybeRef<string | number | undefined>,
) {
  const resolvedSessionId = computed(() => unref(sessionId))
  const resolvedDocumentId = computed(() => unref(documentId))

  return useQuery({
    queryKey: computed(() => [
      ...SESSION_QUERY_KEYS.documentDetails,
      resolvedSessionId.value,
      resolvedDocumentId.value,
    ]),
    queryFn: () => {
      if (!resolvedSessionId.value || !resolvedDocumentId.value) {
        throw new SessionServiceError('Не удалось определить идентификаторы документа.')
      }
      return sessionService.getSessionDocument(resolvedSessionId.value, resolvedDocumentId.value)
    },
    enabled: computed(() => Boolean(resolvedSessionId.value && resolvedDocumentId.value)),
  })
}

export function useDocumentAnalysisStatus(
  documentId: MaybeRef<string | number | undefined>,
  extraEnabled?: MaybeRef<boolean | undefined>,
) {
  const resolvedDocumentId = computed(() => unref(documentId))
  const resolvedEnabled = computed(() => unref(extraEnabled) ?? true)

  return useQuery({
    queryKey: computed(() => [...SESSION_QUERY_KEYS.analysis, resolvedDocumentId.value]),
    queryFn: async () => {
      if (!resolvedDocumentId.value) {
        throw new SessionServiceError('Не найден идентификатор документа.')
      }
      try {
        return await sessionService.getDocumentAnalysisStatus(resolvedDocumentId.value)
      } catch (error) {
        console.warn('[sessions] document analysis unavailable', error)
        return {
          status: DocumentAnalysisState.NOT_FOUND,
          documentId: String(resolvedDocumentId.value),
          message:
            error instanceof SessionServiceError
              ? error.message
              : 'Сервис анализа временно недоступен.',
        } satisfies DocumentAnalysisStatusDto
      }
    },
    enabled: computed(() => Boolean(resolvedDocumentId.value) && resolvedEnabled.value),
    refetchInterval: (query) =>
      query.state.data?.status === DocumentAnalysisState.PROCESSING ? 5000 : false,
    retry: false,
  })
}

export function useCreateSession() {
  const queryClient = useQueryClient()

  return useMutation<SessionDto, SessionServiceError, File[] | FormData>({
    mutationFn: (payload) => sessionService.createSession(payload),
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: SESSION_QUERY_KEYS.list })
      queryClient.invalidateQueries({
        queryKey: [...SESSION_QUERY_KEYS.detail, session.id],
      })
    },
  })
}

export interface UseSessionLabelsMapOptions {
  enabled?: MaybeRef<boolean | undefined>
}

export function useSessionDocumentsLabelsMap(
  sessionId: MaybeRef<string | number | undefined>,
  options?: MaybeRef<UseSessionLabelsMapOptions | undefined>,
) {
  const resolvedId = computed(() => unref(sessionId))
  const resolvedOptions = computed(() => unref(options))
  const enabled = computed(() => {
    const optionEnabled =
      resolvedOptions.value?.enabled !== undefined ? unref(resolvedOptions.value.enabled) : true
    return Boolean(resolvedId.value) && optionEnabled
  })

  return useQuery({
    queryKey: computed(() => [...SESSION_QUERY_KEYS.labelsMap, resolvedId.value]),
    queryFn: () => {
      if (!resolvedId.value) {
        throw new SessionServiceError('Не передан идентификатор сессии.')
      }
      return sessionService.getSessionDocumentsLabelsMap(resolvedId.value)
    },
    enabled,
  })
}

export function useDocumentChat(documentId: MaybeRef<string | number | undefined>) {
  const resolvedDocumentId = computed(() => unref(documentId))

  return useMutation<ChatResponseDto, SessionServiceError, DocumentChatPayload>({
    mutationFn: (payload) => {
      if (!resolvedDocumentId.value) {
        throw new SessionServiceError('Не удалось определить документ для чата.')
      }
      return sessionService.sendDocumentChatMessage(resolvedDocumentId.value, payload)
    },
  })
}
