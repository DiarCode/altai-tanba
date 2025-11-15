<!-- /pages/SessionDocument.vue -->
<script setup lang="ts">
import TestPdf from '@/core/assets/test.pdf'
import { Button } from '@/core/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/core/components/ui/sheet'
import { useColorMode } from '@vueuse/core'
import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Download,
  Info,
  Loader2,
  MessageCircle,
  PenTool,
  QrCode,
  RotateCw,
  ScanText,
  Stamp,
  ZoomIn,
  ZoomOut,
} from 'lucide-vue-next'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

useColorMode({ initialValue: 'dark' })

const route = useRoute()
const router = useRouter()

const sessionId = route.params.sessionId ?? route.params.id
const documentId = route.params.documentId ?? route.params.docId ?? route.params.documentId

interface DetectionOut {
  category: string
  x: number
  y: number
  width: number
  height: number
  area: number
  confidence: number
}

interface PageArtifacts {
  pageIndex: number
  imageUrl: string
  labeledImageUrl?: string | null
}

interface DocumentArtifacts {
  originalPdfUrl: string
  labeledPdfUrl?: string | null
  pages: PageArtifacts[]
}

interface LabelsDTO {
  artifacts: DocumentArtifacts
  detections: Record<number, DetectionOut[]>
}

interface SessionDocumentDTO {
  id: string
  documentUrl: string
  labeledUrl?: string
  originalName: string
  status: 'PENDING' | 'SUCCESSFUL' | 'FAILED'
  createdAt: string
  updatedAt: string
  verification?: {
    hasQR: boolean
    hasStamp: boolean
    hasSignature: boolean
  }
  labels: LabelsDTO
  type: string
  mistakes: string[]
  frauds: string[]
  summary: string
}

const isLoading = ref(true)
const documentData = ref<SessionDocumentDTO | null>(null)
const activePageIndex = ref(0)
const zoomLevel = ref(1)

// Detection visibility toggles
const showQR = ref(true)
const showSignature = ref(true)
const showStamp = ref(true)

// --- Computed helpers ---
const hasData = computed(() => !!documentData.value)

const currentPage = computed<PageArtifacts | null>(() => {
  if (!documentData.value) return null
  return documentData.value.labels.artifacts.pages[activePageIndex.value] ?? null
})

// Filtered detections based on toggle states
const filteredDetections = computed(() => {
  if (!documentData.value || !currentPage.value) return []

  const detections = documentData.value.labels.detections[currentPage.value.pageIndex] || []

  return detections.filter((det) => {
    const category = det.category.toLowerCase()
    if (category.includes('qr') && !showQR.value) return false
    if ((category.includes('sign') || category.includes('подп')) && !showSignature.value)
      return false
    if ((category.includes('stamp') || category.includes('печать')) && !showStamp.value)
      return false
    return true
  })
})

const allDetections = computed<DetectionOut[]>(() => {
  if (!documentData.value) return []
  const detectionsObj = documentData.value.labels.detections
  return Object.values(detectionsObj).flat()
})

const detectionStats = computed(() => {
  const base = {
    total: 0,
    byCategory: {} as Record<string, number>,
    qr: 0,
    stamp: 0,
    signature: 0,
  }

  for (const det of allDetections.value) {
    base.total++
    const key = det.category.toLowerCase()
    base.byCategory[key] = (base.byCategory[key] ?? 0) + 1

    if (key.includes('qr')) base.qr++
    if (key.includes('stamp') || key.includes('печать')) base.stamp++
    if (key.includes('sign') || key.includes('подп')) base.signature++
  }

  return base
})

function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Style for detection box (assuming x,y,width,height are normalized 0–1)
function getBoxStyle(det: DetectionOut) {
  return {
    left: `${det.x * 100}%`,
    top: `${det.y * 100}%`,
    width: `${det.width * 100}%`,
    height: `${det.height * 100}%`,
  }
}

function getCategoryColor(category: string) {
  const cat = category.toLowerCase()
  if (cat.includes('qr')) return '#38BDF8'
  if (cat.includes('stamp') || cat.includes('печать')) return '#3DD68C'
  if (cat.includes('sign') || cat.includes('подп')) return '#FBBF24'
  return '#F97066'
}

function getCategoryIcon(category: string) {
  const cat = category.toLowerCase()
  if (cat.includes('qr')) return QrCode
  if (cat.includes('stamp') || cat.includes('печать')) return Stamp
  if (cat.includes('sign') || cat.includes('подп')) return PenTool
  return AlertTriangle
}

// Navigation functions
function onPrevPage() {
  if (activePageIndex.value <= 0) return
  activePageIndex.value--
}

function onNextPage() {
  if (
    !documentData.value ||
    activePageIndex.value >= documentData.value.labels.artifacts.pages.length - 1
  )
    return
  activePageIndex.value++
}

function zoomIn() {
  if (zoomLevel.value >= 3) return
  zoomLevel.value += 0.25
}

function zoomOut() {
  if (zoomLevel.value <= 0.5) return
  zoomLevel.value -= 0.25
}

function resetZoom() {
  zoomLevel.value = 1
}

function handleDownloadOriginal() {
  if (documentData.value?.documentUrl) {
    window.open(documentData.value.documentUrl, '_blank')
  }
}

function handleDownloadLabeled() {
  if (documentData.value?.labeledUrl) {
    window.open(documentData.value.labeledUrl, '_blank')
  }
}

// --- Tiny fake QA chat (only last Q&A shown) ---
const question = ref('')
const chatLoading = ref(false)
const lastQA = ref<{ question: string; answer: string } | null>(null)

async function handleAskQuestion() {
  if (!question.value.trim() || !documentData.value) return
  const q = question.value.trim()
  question.value = ''
  chatLoading.value = true

  // Fake "AI" answer based on summary
  const baseSummary = documentData.value.summary
  const answer =
    `На основе анализа документа: ${baseSummary.slice(0, 220)}... ` +
    `Все ответы носят ознакомительный характер, проверьте критичные моменты вручную.`

  await new Promise((r) => setTimeout(r, 600))
  lastQA.value = { question: q, answer }
  chatLoading.value = false
}

// --- Fake loading of document details ---
async function fetchDocumentDetails() {
  isLoading.value = true
  try {
    await new Promise((r) => setTimeout(r, 700))

    const nowIso = new Date().toISOString()

    // Create mock pages with image URLs
    const mockPages: PageArtifacts[] = [
      {
        pageIndex: 0,
        imageUrl: 'https://picsum.photos/seed/doc-page-1/800/1100.jpg',
        labeledImageUrl: null,
      },
      {
        pageIndex: 1,
        imageUrl: 'https://picsum.photos/seed/doc-page-2/800/1100.jpg',
        labeledImageUrl: null,
      },
      {
        pageIndex: 2,
        imageUrl: 'https://picsum.photos/seed/doc-page-3/800/1100.jpg',
        labeledImageUrl: null,
      },
    ]

    const labels: LabelsDTO = {
      artifacts: {
        originalPdfUrl: TestPdf,
        labeledPdfUrl: undefined,
        pages: mockPages,
      },
      detections: {
        0: [
          {
            category: 'qr_code',
            x: 0.08,
            y: 0.78,
            width: 0.16,
            height: 0.12,
            area: 0.019,
            confidence: 0.97,
          },
          {
            category: 'stamp',
            x: 0.62,
            y: 0.75,
            width: 0.22,
            height: 0.13,
            area: 0.028,
            confidence: 0.94,
          },
          {
            category: 'signature',
            x: 0.42,
            y: 0.82,
            width: 0.16,
            height: 0.09,
            area: 0.014,
            confidence: 0.91,
          },
        ],
        1: [
          {
            category: 'signature',
            x: 0.35,
            y: 0.85,
            width: 0.18,
            height: 0.1,
            area: 0.018,
            confidence: 0.89,
          },
          {
            category: 'qr_code',
            x: 0.72,
            y: 0.12,
            width: 0.14,
            height: 0.11,
            area: 0.015,
            confidence: 0.93,
          },
        ],
        2: [
          {
            category: 'stamp',
            x: 0.15,
            y: 0.25,
            width: 0.2,
            height: 0.15,
            area: 0.03,
            confidence: 0.96,
          },
        ],
      },
    }

    documentData.value = {
      id: String(documentId ?? '1'),
      documentUrl: TestPdf,
      originalName: 'Договор поставки №17/2024.pdf',
      status: 'SUCCESSFUL',
      createdAt: nowIso,
      updatedAt: nowIso,
      verification: {
        hasQR: true,
        hasStamp: true,
        hasSignature: true,
      },
      labels,
      type: 'Договор поставки',
      mistakes: [
        'Отсутствует ссылка на приложение с полной спецификацией товара.',
        'Не указаны сроки предоставления закрывающих документов.',
      ],
      frauds: ['Обнаружено несоответствие ИИН в шапке договора и в блоке подписантов.'],
      summary:
        'Документ является договором поставки между двумя контрагентами. Основные условия: предмет договора — поставка оборудования, расчёты по безналичному расчёту, используется авансовая схема. QR-код и печать присутствуют, подпись визуально соответствует типовой подписи уполномоченного лица.',
    }
  } catch (e) {
    console.error('Failed to load document details', e)
  } finally {
    isLoading.value = false
  }
}

function goBack() {
  router.push(`/sessions/${sessionId}`)
}

onMounted(() => {
  fetchDocumentDetails()
})
</script>

<template>
  <div class="flex h-screen w-screen flex-col bg-[#0a0f1f] text-white">
    <!-- Brighter background with electric blue accents -->
    <div class="pointer-events-none fixed inset-0 z-10">
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(56,107,237,0.15)_0,transparent_40%),radial-gradient(circle_at_80%_70%,rgba(56,107,237,0.15)_0,transparent_40%)]"
      />
      <div
        class="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[length:140px_140px]"
      />
    </div>

    <main class="flex-1 flex flex-col p-4">
      <!-- Loading state -->
      <div
        v-if="isLoading"
        class="flex flex-1 flex-col items-center justify-center gap-4 text-slate-300"
      >
        <Loader2 class="h-7 w-7 animate-spin text-[#386BED]" />
        <p class="text-base text-slate-400">Загружаем детали документа…</p>
      </div>

      <!-- Content -->
      <template v-else-if="hasData && documentData">
        <!-- Header row -->
        <header class="mb-4 flex items-center gap-3 shrink-0">
          <Button variant="ghost" size="icon" class="rounded-xl" @click="goBack">
            <ArrowLeft class="h-5 w-5" />
          </Button>

          <div class="flex-1 space-y-1">
            <h1 class="text-lg font-semibold text-white sm:text-xl md:text-2xl">
              {{ documentData.type }}
            </h1>
          </div>

          <div class="flex items-center gap-4">
            <div class="flex flex-wrap items-center gap-2 text-sm text-slate-500">
              <span>{{ documentData.originalName }}</span>
              <span class="h-1 w-1 rounded-full bg-slate-600" />
              <span>{{ formatDate(documentData.updatedAt) }}</span>
            </div>

            <div class="flex items-center gap-3">
              <!-- Sheet trigger for document details -->
              <Sheet>
                <SheetTrigger as-child>
                  <Button variant="ghost" size="sm" class="rounded-xl">
                    <ScanText class="h-4 w-4 mr-2" />
                    Аналитика
                  </Button>
                </SheetTrigger>
                <SheetContent class="min-w-lg p-4 overflow-y-auto bg-[#0a0f1f] text-white">
                  <SheetHeader>
                    <SheetTitle class="text-xl font-semibold text-white">
                      {{ documentData.originalName }}
                    </SheetTitle>
                  </SheetHeader>

                  <div class="space-y-5 pb-6">
                    <!-- Q&A chat on top -->
                    <div
                      class="flex flex-col gap-3 rounded-2xl bg-slate-900/90 p-4 ring-1 ring-white/10"
                    >
                      <div class="flex items-center justify-between">
                        <div class="flex items-center gap-2 text-slate-100">
                          <MessageCircle class="h-4 w-4 text-[#386BED]" />
                          <span class="text-base font-medium">Вопрос по документу</span>
                        </div>
                      </div>

                      <div
                        v-if="lastQA"
                        class="space-y-2 rounded-[12px] bg-slate-950/80 p-3 text-sm"
                      >
                        <div class="text-sky-200">
                          <span class="text-[11px] uppercase tracking-wide text-slate-400">
                            Вы:
                          </span>
                          <p class="mt-1">{{ lastQA.question }}</p>
                        </div>
                        <div class="mt-1 border-t border-slate-800 pt-2 text-slate-200">
                          <span class="text-[11px] uppercase tracking-wide text-slate-500">
                            Ответ ассистента:
                          </span>
                          <p class="mt-1">
                            {{ lastQA.answer }}
                          </p>
                        </div>
                      </div>

                      <form class="flex items-center gap-2" @submit.prevent="handleAskQuestion">
                        <div
                          class="flex-1 rounded-full border border-slate-700/80 bg-slate-950/80 px-3 py-2 text-sm text-slate-200 focus-within:border-[#2D91ED]"
                        >
                          <input
                            v-model="question"
                            type="text"
                            placeholder="Спросить, например: «Где самые рискованные места договора?»"
                            class="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
                          />
                        </div>
                        <Button
                          type="submit"
                          size="icon"
                          class="flex h-9 w-9 items-center justify-center rounded-full bg-[linear-gradient(135deg,#2964EB,#2D91ED)] text-white shadow-[0_12px_40px_rgba(56,107,237,0.7)] transition hover:scale-105 active:scale-95"
                          :disabled="chatLoading || !question.trim()"
                        >
                          <span v-if="!chatLoading" class="flex">
                            <CheckCircle2 class="h-4 w-4" />
                          </span>
                          <span v-else class="flex">
                            <Loader2 class="h-4 w-4 animate-spin" />
                          </span>
                        </Button>
                      </form>
                    </div>

                    <!-- Stats row -->
                    <div class="grid grid-cols-3 gap-3">
                      <div
                        class="flex flex-col gap-1 rounded-[14px] bg-slate-900/80 p-3 ring-1 ring-white/10"
                      >
                        <div class="flex items-center justify-between">
                          <span class="text-sm uppercase tracking-wide text-slate-400"> QR </span>
                          <QrCode class="h-5 w-5 text-[#38BDF8]" />
                        </div>
                        <div class="text-xl font-semibold text-slate-50">
                          {{ detectionStats.qr }}
                        </div>
                      </div>

                      <div
                        class="flex flex-col gap-1 rounded-[14px] bg-slate-900/80 p-3 ring-1 ring-white/10"
                      >
                        <div class="flex items-center justify-between">
                          <span class="text-sm uppercase tracking-wide text-slate-400">
                            Печати
                          </span>
                          <Stamp class="h-5 w-5 text-[#3DD68C]" />
                        </div>
                        <div class="text-xl font-semibold text-slate-50">
                          {{ detectionStats.stamp }}
                        </div>
                      </div>

                      <div
                        class="flex flex-col gap-1 rounded-[14px] bg-slate-900/80 p-3 ring-1 ring-white/10"
                      >
                        <div class="flex items-center justify-between">
                          <span class="text-sm uppercase tracking-wide text-slate-400">
                            Подписи
                          </span>
                          <PenTool class="h-5 w-5 text-[#FBBF24]" />
                        </div>
                        <div class="text-xl font-semibold text-slate-50">
                          {{ detectionStats.signature }}
                        </div>
                      </div>
                    </div>

                    <!-- Summary card -->
                    <div
                      class="flex flex-col gap-2 rounded-[16px] bg-slate-900/80 p-4 ring-1 ring-white/10"
                    >
                      <div class="flex items-center gap-2 text-slate-100">
                        <Info class="h-4 w-4 text-[#38BDF8]" />
                        <span class="font-medium text-base">Краткое резюме</span>
                      </div>
                      <p class="text-base leading-relaxed text-slate-200">
                        {{ documentData.summary }}
                      </p>
                    </div>

                    <!-- Mistakes & frauds -->
                    <div class="space-y-3">
                      <div
                        v-if="documentData.mistakes.length"
                        class="rounded-[16px] bg-slate-900/80 p-4 ring-1 ring-[#F5A524]/30"
                      >
                        <div class="mb-2 flex items-center gap-2 text-amber-300">
                          <AlertTriangle class="h-4 w-4" />
                          <span class="font-medium text-base"
                            >Замечания ({{ documentData.mistakes.length }})</span
                          >
                        </div>
                        <ul class="space-y-2 text-base text-slate-200">
                          <li
                            v-for="(m, idx) in documentData.mistakes"
                            :key="idx"
                            class="flex gap-2"
                          >
                            <span
                              class="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-300"
                            />
                            <span>{{ m }}</span>
                          </li>
                        </ul>
                      </div>

                      <div
                        v-if="documentData.frauds.length"
                        class="rounded-[16px] bg-slate-900/80 p-4 ring-1 ring-[#F97066]/35"
                      >
                        <div class="mb-2 flex items-center gap-2 text-rose-300">
                          <AlertTriangle class="h-4 w-4" />
                          <span class="font-medium text-base"
                            >Подозрения на мошенничество ({{ documentData.frauds.length }})</span
                          >
                        </div>
                        <ul class="space-y-2 text-base text-slate-200">
                          <li v-for="(f, idx) in documentData.frauds" :key="idx" class="flex gap-2">
                            <span class="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-rose-400" />
                            <span>{{ f }}</span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </header>

        <!-- Controls -->
        <div class="flex justify-center gap-2 mb-4">
          <div class="flex items-center gap-1 rounded-full bg-slate-900/70 px-2 py-1 text-sm">
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 rounded-full"
              @click="onPrevPage"
              :disabled="activePageIndex <= 0"
            >
              <ArrowLeft class="h-3 w-3" />
            </Button>
            <span class="px-2 text-white">
              {{ activePageIndex + 1 }} / {{ documentData.labels.artifacts.pages.length }}
            </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 rounded-full"
              @click="onNextPage"
              :disabled="activePageIndex >= documentData.labels.artifacts.pages.length - 1"
            >
              <ArrowLeft class="h-3 w-3 rotate-180" />
            </Button>
          </div>

          <div class="flex items-center gap-1 rounded-full bg-slate-900/70 px-2 py-1 text-sm">
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 rounded-full"
              @click="zoomOut"
              :disabled="zoomLevel <= 0.5"
            >
              <ZoomOut class="h-3 w-3" />
            </Button>
            <span class="px-1 text-white"> {{ Math.round(zoomLevel * 100) }}% </span>
            <Button
              variant="ghost"
              size="icon"
              class="h-6 w-6 rounded-full"
              @click="zoomIn"
              :disabled="zoomLevel >= 3"
            >
              <ZoomIn class="h-3 w-3" />
            </Button>
            <Button variant="ghost" size="icon" class="h-6 w-6 rounded-full" @click="resetZoom">
              <RotateCw class="h-3 w-3" />
            </Button>
          </div>
        </div>

        <!-- Two sections layout with full width/height -->
        <div class="grid flex-1 min-h-0 w-full gap-4 md:grid-cols-2">
          <!-- 1) Original document (image) -->
          <section
            class="flex h-full w-full flex-col rounded-[18px] bg-[rgba(8,12,26,0.95)] p-3 shadow-[0_18px_45px_rgba(0,0,0,0.7)]"
          >
            <div class="mb-2 flex items-center justify-between text-sm">
              <div class="flex items-center gap-2">
                <p class="text-base">Оригинал</p>
                <Download
                  @click="handleDownloadOriginal"
                  class="size-4 cursor-pointer text-slate-500"
                />
              </div>
            </div>

            <div class="relative flex-1 overflow-hidden rounded-[14px] bg-slate-950/70">
              <!-- Image Object -->
              <div class="relative h-full w-full flex items-center justify-center overflow-auto">
                <div
                  v-if="currentPage"
                  class="relative inline-block"
                  :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center' }"
                >
                  <img
                    :src="currentPage.imageUrl"
                    :alt="`Page ${currentPage.pageIndex + 1}`"
                    class="block max-h-full max-w-full object-contain"
                  />
                </div>
              </div>
            </div>
          </section>

          <!-- 2) Labeled document with boxes -->
          <section
            class="flex h-full w-full flex-col rounded-[18px] bg-[rgba(8,12,26,0.95)] p-3 shadow-[0_18px_45px_rgba(0,0,0,0.7)]"
          >
            <div class="mb-2 flex items-center justify-between text-sm">
              <div class="flex items-center gap-2">
                <p class="text-base">Обработанный</p>
                <Download
                  @click="handleDownloadLabeled"
                  class="size-4 cursor-pointer text-slate-500"
                />
              </div>

              <!-- Detection type toggles -->
              <div class="flex flex-wrap gap-2 text-xs">
                <button
                  @click="showQR = !showQR"
                  :class="[
                    'flex items-center gap-1 rounded-full px-2 py-1 transition-all',
                    showQR
                      ? 'bg-[#38BDF8]/20 text-[#38BDF8] ring-1 ring-[#38BDF8]/40'
                      : 'bg-white/5 text-white/50',
                  ]"
                >
                  <QrCode class="h-3 w-3" />
                  QR ({{ detectionStats.qr }})
                </button>
                <button
                  @click="showSignature = !showSignature"
                  :class="[
                    'flex items-center gap-1 rounded-full px-2 py-1 transition-all',
                    showSignature
                      ? 'bg-[#FBBF24]/20 text-[#FBBF24] ring-1 ring-[#FBBF24]/40'
                      : 'bg-white/5 text-white/50',
                  ]"
                >
                  <PenTool class="h-3 w-3" />
                  Подписи ({{ detectionStats.signature }})
                </button>
                <button
                  @click="showStamp = !showStamp"
                  :class="[
                    'flex items-center gap-1 rounded-full px-2 py-1 transition-all',
                    showStamp
                      ? 'bg-[#3DD68C]/20 text-[#3DD68C] ring-1 ring-[#3DD68C]/40'
                      : 'bg-white/5 text-white/50',
                  ]"
                >
                  <Stamp class="h-3 w-3" />
                  Печати ({{ detectionStats.stamp }})
                </button>
              </div>
            </div>

            <div class="relative flex-1 overflow-hidden rounded-[14px] bg-slate-950/70">
              <!-- Labeled Image with Detections -->
              <div class="relative h-full w-full flex items-center justify-center overflow-auto">
                <div
                  v-if="currentPage"
                  class="relative inline-block"
                  :style="{ transform: `scale(${zoomLevel})`, transformOrigin: 'top center' }"
                >
                  <img
                    :src="currentPage.imageUrl"
                    :alt="`Page ${currentPage.pageIndex + 1}`"
                    class="block max-h-full max-w-full object-contain"
                  />

                  <!-- Detection overlays -->
                  <div class="pointer-events-none absolute inset-0">
                    <div
                      v-for="(det, idx) in filteredDetections"
                      :key="idx"
                      class="absolute rounded-lg border-2 transition-all"
                      :style="[
                        getBoxStyle(det),
                        {
                          borderColor: getCategoryColor(det.category),
                          backgroundColor: getCategoryColor(det.category) + '33',
                        },
                      ]"
                    >
                      <div
                        class="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-[rgba(5,8,20,0.95)] px-2 py-0.5 text-[10px] font-medium shadow-lg"
                        :style="{ color: getCategoryColor(det.category) }"
                      >
                        <component
                          :is="getCategoryIcon(det.category)"
                          class="inline h-3 w-3 mr-1 align-middle"
                        />
                        {{ det.category }}
                        <span class="ml-1 text-[8px] opacity-75">
                          {{ Math.round(det.confidence * 100) }}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </template>

      <!-- Fallback if no data -->
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-3 text-center text-slate-300"
      >
        <AlertTriangle class="h-7 w-7 text-amber-400" />
        <p class="text-base text-slate-300">Не удалось загрузить данные документа.</p>
        <Button
          size="sm"
          variant="outline"
          class="mt-1 rounded-full border-white/20 bg-white/5 px-4 py-2 text-sm text-slate-100 hover:bg-white/10"
          @click="fetchDocumentDetails"
        >
          Повторить
        </Button>
      </div>
    </main>
  </div>
</template>

<style scoped>
/* Custom scrollbar for document viewers */
.overflow-auto::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.overflow-auto::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

.overflow-auto::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.overflow-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
