import { isAxiosError } from 'axios'

import { apiClient } from '@/core/config/axios-instance.config'

import {
  CATEGORIES_FORMATTED,
  type DocumentAnalysisStatusDto,
  type LabelsDetection,
  type LabelsPositionPayload,
  type ListSessionsParams,
  type RawLabelsAnnotation,
  type RawLabelsPagePayload,
  type RawLabelsPositionPayload,
  type SessionDocumentDetailsDto,
  type SessionDocumentDto,
  type SessionDocumentsQueryParams,
  type SessionDto,
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
type SessionDocumentDetailsResponse = Omit<SessionDocumentDetailsDto, 'labelsPosition'> & {
  labelsPosition?: RawLabelsPositionPayload | null
}

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
      const response = await apiClient.get<SessionDocumentDetailsResponse>(
        `${this.baseUrl}/${sessionId}/documents/${documentId}`,
      )
      return this.normalizeDocumentDetails(response.data)
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

  private normalizeDocumentDetails(raw: SessionDocumentDetailsResponse): SessionDocumentDetailsDto {
    return {
      ...raw,
      labelsPosition: this.normalizeLabelsPosition(raw.labelsPosition),
    }
  }

  private normalizeLabelsPosition(
    payload?: RawLabelsPositionPayload | null,
  ): LabelsPositionPayload | null {
    if (!payload) return null

    const [documentKey] = Object.keys(payload)
    if (!documentKey) return null

    const documentPayload = payload[documentKey]
    if (!documentPayload || !documentPayload.artifacts) {
      return null
    }

    const detections: LabelsPositionPayload['detections'] = {}

    Object.entries(documentPayload).forEach(([key, value]) => {
      if (!key.startsWith('page_')) return
      const pageIndex = Number(key.replace('page_', ''))
      if (!Number.isFinite(pageIndex)) return

      const pagePayload = value as RawLabelsPagePayload
      detections[pageIndex] = this.transformPageAnnotations(pagePayload)
    })

    return {
      artifacts: documentPayload.artifacts,
      detections,
    }
  }

  private transformPageAnnotations(page: RawLabelsPagePayload): LabelsDetection[] {
    if (!page?.annotations?.length || !page.page_size) {
      return []
    }

    const { width, height } = page.page_size
    if (!width || !height) {
      return []
    }

    return page.annotations.flatMap((annotationRecord) => {
      return Object.values(annotationRecord)
        .map((annotation) => this.normalizeAnnotation(annotation, width, height))
        .filter((annotation): annotation is LabelsDetection => Boolean(annotation))
    })
  }

  private normalizeAnnotation(
    annotation: RawLabelsAnnotation,
    width: number,
    height: number,
  ): LabelsDetection | null {
    if (!annotation?.bbox || !width || !height) {
      return null
    }

    const { bbox, category, area, confidence } = annotation

    const normalizedCategory = CATEGORIES_FORMATTED[category as keyof typeof CATEGORIES_FORMATTED]

    return {
      category: normalizedCategory,
      area,
      x: bbox.x / width,
      y: bbox.y / height,
      width: bbox.width / width,
      height: bbox.height / height,
      confidence: Math.round(confidence * 100) / 100,
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
