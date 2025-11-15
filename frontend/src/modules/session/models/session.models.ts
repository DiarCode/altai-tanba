export enum SessionStatus {
  PROCESSING = 'PROCESSING',
  FAILED = 'FAILED',
  SUCCESS = 'SUCCESS',
}

export enum SessionDocumentStatus {
  PENDING = 'PENDING',
  SUCCESSFUL = 'SUCCESSFUL',
  FAILED = 'FAILED',
}

export interface SessionDto {
  id: string
  totalDocuments: number
  createdAt: string
  updatedAt: string
  status?: SessionStatus
}

export interface SessionDocumentVerificationDto {
  hasQR: boolean
  hasStamp: boolean
  hasSignature: boolean
}

export interface SessionDocumentDto {
  id: string
  documentUrl: string
  originalName: string
  status: SessionDocumentStatus
  createdAt: string
  updatedAt: string
  verification?: SessionDocumentVerificationDto | null
}

export interface LabelsDetection {
  category: string
  x: number
  y: number
  width: number
  height: number
  area: number
  confidence: number
}

export interface LabelsPageArtifact {
  pageIndex: number
  imageUrl: string
  labeledImageUrl?: string | null
}

export interface LabelsArtifacts {
  originalPdfUrl: string
  labeledPdfUrl?: string | null
  pages: LabelsPageArtifact[]
}

export interface LabelsPositionPayload {
  artifacts: LabelsArtifacts
  detections: Record<number, LabelsDetection[]>
}

export interface SessionDocumentDetailsDto extends SessionDocumentDto {
  labeledDocumentUrl?: string | null
  labelsPosition?: LabelsPositionPayload | null
}

export interface ListSessionsParams {
  page?: number
  size?: number
  status?: SessionStatus
}

export interface SessionDocumentsQueryParams {
  page?: number
  size?: number
  status?: SessionDocumentStatus
}

export enum DocumentAnalysisState {
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  NOT_FOUND = 'NOT_FOUND',
}

export interface DocumentAnalysisStatusDto {
  status: DocumentAnalysisState
  documentId: string
  fraudSentences?: string[] | null
  mistakeWords?: string[] | null
  documentType?: string | null
  documentSummary?: string | null
  errorLog?: string | null
  message?: string | null
}
