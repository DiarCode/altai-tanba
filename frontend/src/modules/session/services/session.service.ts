import { isAxiosError } from 'axios'

import { apiClient } from '@/core/config/axios-instance.config'

import type {
  DocumentAnalysisStatusDto,
  ListSessionsParams,
  SessionDocumentDetailsDto,
  SessionDocumentDto,
  SessionDocumentsQueryParams,
  SessionDto,
} from '../models/session.models'

export class SessionServiceError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public originalError?: Error,
  ) {
    super(message)
    this.name = 'SessionServiceError'
    Object.setPrototypeOf(this, SessionServiceError.prototype)
  }
}

type SessionId = string | number
type DocumentId = string | number
type SessionCreationPayload = File[] | FormData

class SessionService {
  private readonly baseUrl = '/sessions'
  private readonly analysisUrl = '/document-analysis'

  private handleError(error: unknown, fallbackMessage: string): never {
    if (isAxiosError(error)) {
      const statusCode = error.response?.status
      const message =
        (error.response?.data as { message?: string })?.message ?? error.message ?? fallbackMessage

      throw new SessionServiceError(message, statusCode, error)
    }

    throw new SessionServiceError(fallbackMessage, 500, error as Error)
  }

  async listSessions(params?: ListSessionsParams): Promise<SessionDto[]> {
    try {
      const response = await apiClient.get<SessionDto[]>(this.baseUrl, {
        params,
      })
      return response.data
    } catch (error) {
      this.handleError(error, 'Не удалось получить список сессий.')
    }
  }

  async getSession(sessionId: SessionId): Promise<SessionDto> {
    try {
      const response = await apiClient.get<SessionDto>(`${this.baseUrl}/${sessionId}`)
      return response.data
    } catch (error) {
      this.handleError(error, 'Не удалось загрузить данные сессии.')
    }
  }

  async listSessionDocuments(
    sessionId: SessionId,
    params?: SessionDocumentsQueryParams,
  ): Promise<SessionDocumentDto[]> {
    try {
      const response = await apiClient.get<SessionDocumentDto[]>(
        `${this.baseUrl}/${sessionId}/documents`,
        {
          params,
        },
      )
      return response.data
    } catch (error) {
      this.handleError(error, 'Не удалось получить документы сессии.')
    }
  }

  async getSessionDocument(
    sessionId: SessionId,
    documentId: DocumentId,
  ): Promise<SessionDocumentDetailsDto> {
    try {
      const response = await apiClient.get<SessionDocumentDetailsDto>(
        `${this.baseUrl}/${sessionId}/documents/${documentId}`,
      )
      return response.data
    } catch (error) {
      this.handleError(error, 'Не удалось загрузить данные документа.')
    }
  }

  async createSession(payload: SessionCreationPayload): Promise<SessionDto> {
    try {
      const formData = payload instanceof FormData ? payload : this.buildFormData(payload)

      const response = await apiClient.post<SessionDto>(this.baseUrl, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    } catch (error) {
      this.handleError(error, 'Не удалось создать сессию.')
    }
  }

  async getDocumentAnalysisStatus(documentId: DocumentId): Promise<DocumentAnalysisStatusDto> {
    try {
      const response = await apiClient.get<DocumentAnalysisStatusDto>(
        `${this.analysisUrl}/status/${documentId}`,
      )
      return response.data
    } catch (error) {
      this.handleError(error, 'Не удалось получить статус анализа документа.')
    }
  }

  private buildFormData(files: File[]): FormData {
    const formData = new FormData()

    if (!files.length) {
      throw new SessionServiceError('Нужно добавить хотя бы один файл.')
    }

    files.forEach((file) => formData.append('files', file))
    return formData
  }
}

export const sessionService = new SessionService()
