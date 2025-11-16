<template>
  <!-- Top Bar -->
  <header class="absolute inset-x-0 top-0 z-50 p-6">
    <div class="container mx-auto flex items-center justify-between px-4">
      <!-- Brand with shimmer effect -->
      <h1
        @click="$router.push('/')"
        class="cursor-pointer relative text-3xl font-extrabold tracking-tight md:text-4xl overflow-hidden"
      >
        <span class="relative inline-block text-white"> Tanba </span>
      </h1>

      <!-- Actions -->
      <div class="flex items-center gap-3">
        <!-- History Sheet -->
        <Sheet v-model:open="isHistoryOpen">
          <SheetTrigger as-child>
            <Button variant="outline" class="gap-2">
              <History class="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent
            side="right"
            class="w-full max-w-md bg-white/10 backdrop-blur-xl border-white/20 p-6 overflow-auto"
          >
            <div class="flex items-center justify-between pb-4">
              <div>
                <p class="text-sm uppercase tracking-wide text-white/70">История проверок</p>
                <p class="text-lg font-semibold text-white">
                  {{ hasSessions ? `Последние ${sessions.length}` : 'Нет данных' }}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                class="gap-2 rounded-full border border-white/10 bg-white/5 text-white hover:bg-white/10"
                :disabled="isRefetchingSessions"
                @click="refetchSessions"
              >
                <Loader2 v-if="isRefetchingSessions" class="h-4 w-4 animate-spin" />
                <History v-else class="h-4 w-4" />
                Обновить
              </Button>
            </div>

            <div
              v-if="isLoadingSessions"
              class="flex flex-col items-center gap-2 py-12 text-white/70"
            >
              <Loader2 class="h-6 w-6 animate-spin text-white" />
              <span class="text-sm">Загружаем предыдущие сессии…</span>
            </div>

            <div v-else class="grid flex-1 auto-rows-min gap-3 py-4">
              <div
                v-for="session in sessions"
                :key="session.id"
                @click="handleSessionClick(session.id)"
                class="cursor-pointer rounded-xl border border-white/20 bg-white/10 backdrop-blur-sm p-4 shadow-sm transition hover:border-white/40"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <div>
                    <p class="text-sm font-medium text-white">Сессия №{{ session.id }}</p>
                    <p class="text-xs text-white/60">{{ formatSessionDate(session.createdAt) }}</p>
                  </div>
                  <span
                    :class="[
                      'inline-flex items-center rounded-md px-2 py-1 text-xs font-medium',
                      getStatusMeta(session.status).classes,
                    ]"
                  >
                    {{ getStatusMeta(session.status).label }}
                  </span>
                </div>
                <p class="text-xs text-white/70">Документов: {{ session.totalDocuments }}</p>
              </div>
              <p v-if="!hasSessions" class="py-10 text-center text-sm text-white/60">
                Пока нет предыдущих сессий
              </p>
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Button } from '@/core/components/ui/button'
import { Sheet, SheetContent, SheetTrigger } from '@/core/components/ui/sheet'
import { useSessionsList } from '@/modules/session/composables/session.composables'
import { SessionStatus, type SessionDto } from '@/modules/session/models/session.models'

/* icons */
import { History, Loader2 } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const isHistoryOpen = ref(false)
const sessionsQuery = useSessionsList({ page: 1, size: 10 })

const sessions = computed<SessionDto[]>(() => sessionsQuery.data.value ?? [])
const hasSessions = computed(() => sessions.value.length > 0)
const isLoadingSessions = computed(() => sessionsQuery.isLoading.value && !sessions.value.length)
const isRefetchingSessions = computed(() => sessionsQuery.isRefetching.value)

const refetchSessions = () => {
  sessionsQuery.refetch()
}

watch(isHistoryOpen, (open) => {
  if (open) {
    refetchSessions()
  }
})

function formatSessionDate(dateString: string) {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMinutes = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMinutes < 1) return 'Только что'
  if (diffMinutes < 60) return `${diffMinutes} мин назад`
  if (diffHours < 24) return `${diffHours} ч назад`
  if (diffDays < 7) return `${diffDays} дн назад`
  return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function getStatusMeta(status?: SessionStatus) {
  switch (status) {
    case SessionStatus.SUCCESS:
      return {
        label: 'Завершено',
        classes: 'bg-emerald-500/20 text-emerald-200',
      }
    case SessionStatus.FAILED:
      return {
        label: 'Ошибка',
        classes: 'bg-rose-500/20 text-rose-200',
      }
    default:
      return {
        label: 'Обработка',
        classes: 'bg-amber-500/20 text-amber-200',
      }
  }
}

const router = useRouter()
function handleSessionClick(sessionId: string) {
  router.push(`/sessions/${sessionId}`)
}
</script>

<style scoped></style>
