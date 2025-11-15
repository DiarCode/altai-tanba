<!-- /pages/Session.vue -->
<script setup lang="ts">
import BackgroundImage from '@/core/assets/background-2.jpg'
import { Button } from '@/core/components/ui/button'
import HomeNavbar from '@/modules/home/components/home-navbar.vue'
import { useSession, useSessionDocuments } from '@/modules/session/composables/session.composables'
import type { SessionDocumentDto } from '@/modules/session/models/session.models'
import { useColorMode } from '@vueuse/core'
import {
  ArrowLeft,
  Download,
  FileText,
  Loader2,
  PenTool,
  QrCode,
  Stamp,
  XCircle,
} from 'lucide-vue-next'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const router = useRouter()
const route = useRoute()
const sessionId = computed(() => route.params.id as string)

const sessionQuery = useSession(sessionId)
const documentsQuery = useSessionDocuments(sessionId, undefined, { refetchInterval: 5000 })

const session = computed(() => sessionQuery.data.value ?? null)
const documents = computed<SessionDocumentDto[]>(() => documentsQuery.data.value ?? [])
const isLoading = computed(() => sessionQuery.isLoading.value)

const completedCount = computed(() => {
  return documents.value.filter((d) => d.status === 'SUCCESSFUL' || d.status === 'FAILED').length
})

const progressPercentage = computed(() => {
  if (!session.value?.totalDocuments) return 0
  return Math.round((completedCount.value / session.value.totalDocuments) * 100)
})

const isComplete = computed(() => {
  if (!session.value) return false
  return completedCount.value >= session.value.totalDocuments
})

function formatDate(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Сейчас'
  if (diffMins < 60) return `${diffMins}м`
  if (diffHours < 24) return `${diffHours}ч`
  if (diffDays < 7) return `${diffDays}д`
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function handleDownloadReport() {
  // Заглушка для отчёта по сессии — подставишь свой реальный URL/API
  window.open(`/sessions/${sessionId.value}/report`, '_blank')
}

const onDocClick = (docId: string) => {
  const doc = documents.value.find((d) => d.id === docId)
  if (doc && doc.status === 'SUCCESSFUL') {
    router.push(`/sessions/${sessionId.value}/documents/${doc.id}`)
  }
}
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-[#030712] text-white">
    <!-- Brighter background with soft glow & grid -->
    <div class="pointer-events-none fixed inset-0 z-10">
      <img
        :src="BackgroundImage"
        alt=""
        class="h-full w-full object-cover opacity-10 mix-blend-soft-light"
      />
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.20)_0,transparent_45%),radial-gradient(circle_at_80%_80%,rgba(79,70,229,0.22)_0,transparent_45%)]"
      />
      <div
        class="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-size-[120px_120px]"
      />
    </div>

    <HomeNavbar class="relative z-30" />

    <!-- Main content -->
    <main class="container relative z-20 mx-auto flex min-h-screen flex-col gap-16 px-4 pb-16 pt-8">
      <!-- Loading state -->
      <div
        v-if="isLoading"
        class="flex flex-1 flex-col items-center justify-center gap-4 text-slate-300"
      >
        <Loader2 class="h-7 w-7 animate-spin text-[#386BED]" />
      </div>

      <!-- Session content -->
      <template v-else-if="session">
        <!-- Hero section -->
        <section
          v-motion
          :initial="{ opacity: 0, y: 40 }"
          :enter="{ opacity: 1, y: 0, transition: { duration: 500 } }"
          class="flex flex-col items-start gap-10 md:flex-row md:items-center md:justify-between"
        >
          <div class="max-w-2xl">
            <div
              class="mb-4 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm text-cyan-100"
            >
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Цифровой инспектор · Сессия проверки
            </div>
            <h1
              class="text-4xl font-bold leading-tight tracking-tight sm:text-5xl md:text-6xl lg:text-7xl"
            >
              <span
                class="bg-linear-to-r from-white via-cyan-100 to-blue-200 bg-clip-text text-transparent"
              >
                Проверка пакета документов
              </span>
            </h1>

            <div class="mt-4 flex flex-wrap items-center gap-3 text-sm text-slate-200/80">
              <span class="flex items-center gap-2">
                <span class="h-1.5 w-1.5 rounded-full bg-slate-400" />
                Обновлено: {{ formatDate(session.updatedAt) }}
              </span>
              <span class="flex items-center gap-2">
                <span class="h-1.5 w-1.5 rounded-full bg-slate-400" />
                Документов: {{ session.totalDocuments }}
              </span>
              <span class="flex items-center gap-2">
                <span
                  class="h-1.5 w-1.5 rounded-full"
                  :class="isComplete ? 'bg-emerald-400' : 'bg-amber-300'"
                />
                {{ isComplete ? 'Все документы проверены' : 'Проверка продолжается' }}
              </span>
            </div>
          </div>

          <!-- Progress card -->
          <div class="relative w-full max-w-xs shrink-0 md:max-w-sm">
            <div
              class="absolute -inset-6 rounded-3xl bg-linear-to-br from-cyan-400/30 via-blue-500/25 to-indigo-600/25 blur-3xl"
            />
            <div
              class="relative flex h-full w-full flex-col items-center justify-between rounded-3xl border border-cyan-500/20 bg-slate-900/80 px-6 py-6 backdrop-blur-3xl shadow-[0_40px_120px_rgba(15,23,42,0.9)]"
            >
              <div class="w-full">
                <p class="font-medium text-cyan-100/90">Прогресс проверки</p>
                <p class="mt-1 text-xs text-slate-300">
                  {{ completedCount }} из {{ session.totalDocuments }} документов обработано
                </p>
              </div>

              <div class="flex flex-col items-center justify-center py-6">
                <div class="relative size-42">
                  <svg class="h-full w-full -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="42"
                      class="stroke-slate-700/60"
                      stroke-width="8"
                      fill="transparent"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="42"
                      class="stroke-cyan-400"
                      stroke-width="8"
                      fill="transparent"
                      stroke-linecap="round"
                      :stroke-dasharray="2 * Math.PI * 42"
                      :stroke-dashoffset="(2 * Math.PI * 42 * (100 - progressPercentage)) / 100"
                    />
                  </svg>
                  <div
                    class="absolute inset-0 flex flex-col items-center justify-center text-center"
                  >
                    <span class="text-3xl font-bold text-white"> {{ progressPercentage }}% </span>
                    <span class="mt-0.5 text-[11px] text-slate-300">готово</span>
                  </div>
                </div>
              </div>

              <div class="flex w-full items-center justify-between gap-3">
                <div class="text-[11px] text-slate-300 flex gap-4">
                  <div class="flex items-center gap-1.5">
                    <span class="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    <span
                      >Успешно:
                      {{ documents.filter((d) => d.status === 'SUCCESSFUL').length }}</span
                    >
                  </div>
                  <div class="mt-1 flex items-center gap-1.5">
                    <span class="h-1.5 w-1.5 rounded-full bg-rose-400" />
                    <span>Ошибки: {{ documents.filter((d) => d.status === 'FAILED').length }}</span>
                  </div>
                </div>

                <Button size="sm" variant="ghost" @click="handleDownloadReport">
                  <Download class="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </section>

        <!-- Documents grid -->
        <section class="flex-1">
          <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="(doc, index) in documents"
              :key="doc.id"
              v-motion
              :initial="{ opacity: 0, y: 30 }"
              :enter="{ opacity: 1, y: 0, transition: { duration: 400, delay: index * 40 } }"
              :hover="{ y: -8, scale: 1.02 }"
              class="group relative flex cursor-pointer flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-900/75 backdrop-blur-2xl shadow-[0_24px_80px_rgba(15,23,42,0.95)] transition-all duration-300"
              @click="onDocClick(doc.id)"
            >
              <!-- Header (smaller) -->
              <div
                class="flex h-40 items-center justify-center bg-linear-to-br from-white/10 via-cyan-500/10 to-slate-900/40"
              >
                <FileText
                  class="h-16 w-16 text-white/60 transition-transform duration-300 group-hover:scale-110 group-hover:text-cyan-300"
                />
              </div>

              <!-- Body -->
              <div class="flex flex-1 flex-col gap-4 p-5">
                <h3 class="text-base font-semibold leading-snug text-white line-clamp-2">
                  {{ doc.originalName }}
                </h3>

                <!-- Status row -->
                <div class="flex items-center justify-between text-sm">
                  <div class="flex items-center gap-2">
                    <span
                      :class="[
                        'h-2 w-2 rounded-full',
                        doc.status === 'PENDING' && 'bg-slate-400',
                        doc.status === 'SUCCESSFUL' && 'bg-emerald-400',
                        doc.status === 'FAILED' && 'bg-rose-500',
                      ]"
                    />
                    <span class="text-slate-100">
                      {{
                        doc.status === 'PENDING'
                          ? 'Обработка'
                          : doc.status === 'SUCCESSFUL'
                            ? 'Готово'
                            : 'Ошибка'
                      }}
                    </span>
                  </div>
                  <span class="text-xs text-slate-400">
                    {{ formatDate(doc.updatedAt) }}
                  </span>
                </div>

                <!-- Verification grid (compact) -->
                <div v-if="doc.verification" class="grid grid-cols-3 gap-2 text-xs">
                  <div
                    class="flex h-12 flex-col items-center justify-center rounded-2xl border border-white/5 bg-slate-900/80"
                    :class="doc.verification.hasQR ? 'border-cyan-400/40 bg-cyan-500/10' : ''"
                  >
                    <QrCode
                      class="h-5 w-5"
                      :class="doc.verification.hasQR ? 'text-cyan-300' : 'text-white/35'"
                    />
                    <span
                      class="mt-0.5 text-[10px]"
                      :class="doc.verification.hasQR ? 'text-cyan-100' : 'text-slate-400'"
                    >
                      QR
                    </span>
                  </div>
                  <div
                    class="flex h-12 flex-col items-center justify-center rounded-2xl border border-white/5 bg-slate-900/80"
                    :class="
                      doc.verification.hasStamp ? 'border-emerald-400/40 bg-emerald-500/10' : ''
                    "
                  >
                    <Stamp
                      class="h-5 w-5"
                      :class="doc.verification.hasStamp ? 'text-emerald-300' : 'text-white/35'"
                    />
                    <span
                      class="mt-0.5 text-[10px]"
                      :class="doc.verification.hasStamp ? 'text-emerald-100' : 'text-slate-400'"
                    >
                      Печать
                    </span>
                  </div>
                  <div
                    class="flex h-12 flex-col items-center justify-center rounded-2xl border border-white/5 bg-slate-900/80"
                    :class="
                      doc.verification.hasSignature ? 'border-amber-400/40 bg-amber-500/10' : ''
                    "
                  >
                    <PenTool
                      class="h-5 w-5"
                      :class="doc.verification.hasSignature ? 'text-amber-300' : 'text-white/35'"
                    />
                    <span
                      class="mt-0.5 text-[10px]"
                      :class="doc.verification.hasSignature ? 'text-amber-100' : 'text-slate-400'"
                    >
                      Подпись
                    </span>
                  </div>
                </div>
              </div>

              <!-- Pending overlay -->
              <div
                v-if="doc.status === 'PENDING'"
                class="pointer-events-none absolute inset-0 flex items-center justify-center rounded-3xl bg-black/75 backdrop-blur-xl"
              >
                <Loader2 class="h-10 w-10 animate-spin text-cyan-300" />
              </div>
            </div>
          </div>
        </section>
      </template>

      <!-- Error state -->
      <div v-else class="flex flex-1 items-center justify-center">
        <div
          class="rounded-3xl bg-rose-500/15 p-12 text-center backdrop-blur-3xl shadow-[0_50px_160px_rgba(0,0,0,0.9)]"
        >
          <XCircle class="mx-auto mb-4 h-16 w-16 text-rose-300" />
          <h3 class="text-3xl font-bold text-white">Сессия не найдена</h3>
          <Button
            variant="outline"
            class="mt-6 gap-2 rounded-2xl border-white/20 bg-white/5 px-6 py-3 text-base text-white transition-all hover:bg-white/10"
            @click="$router.push('/')"
          >
            <ArrowLeft class="h-5 w-5" />
            На главную
          </Button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped></style>
