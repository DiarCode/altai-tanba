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
        <Sheet>
          <SheetTrigger as-child>
            <Button variant="outline" class="gap-2">
              <History class="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent
            side="right"
            class="w-full max-w-md bg-white/10 backdrop-blur-xl border-white/20 p-6"
          >
            <div class="grid flex-1 auto-rows-min gap-3 py-4">
              <div
                v-for="s in sessions"
                :key="s.id"
                class="rounded-xl border border-white/20 bg-white/10 backdrop-blur-sm p-4 shadow-sm"
              >
                <div class="mb-2 flex items-center justify-between gap-3">
                  <span class="text-sm font-medium text-foreground">{{ s.date }}</span>
                  <span
                    :class="[
                      'inline-flex rounded-md px-2 py-1 text-xs font-medium',
                      s.status === 'completed'
                        ? 'bg-green-500/20 text-green-700 dark:text-green-300'
                        : 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-300',
                    ]"
                  >
                    {{ s.status === 'completed' ? 'Завершено' : 'Обработка' }}
                  </span>
                </div>
                <p class="text-xs text-muted-foreground">Файлов: {{ s.fileCount }}</p>
              </div>
              <p
                v-if="sessions.length === 0"
                class="py-10 text-center text-sm text-muted-foreground"
              >
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

/* icons */
import { History } from 'lucide-vue-next'
import { ref } from 'vue'

interface Session {
  id: string
  title: string
  date: string
  fileCount: number
  status: 'completed' | 'processing'
}
const sessions = ref<Session[]>([
  {
    id: '1',
    title: 'Финансовые отчёты за 4 квартал',
    date: '2 дня назад',
    fileCount: 12,
    status: 'completed',
  },
  {
    id: '2',
    title: 'Медицинские исследования',
    date: '1 неделю назад',
    fileCount: 8,
    status: 'completed',
  },
  {
    id: '3',
    title: 'Проверка юридических документов',
    date: '2 недели назад',
    fileCount: 5,
    status: 'processing',
  },
])
</script>

<style scoped></style>
