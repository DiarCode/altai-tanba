<!-- /pages/HomeTanba.vue -->
<script setup lang="ts">
import BackgroundImage from '@/core/assets/background-2.jpg'
import { useColorMode } from '@vueuse/core'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

/* shadcn-vue primitives (New York v4 registry) */
import { Button } from '@/core/components/ui/button'

/* icons */
import { cn } from '@/core/lib/tailwind.utils'
import { CheckCircle2, FileText, Loader2, Upload, X } from 'lucide-vue-next'
import HomeNavbar from '@/modules/home/components/home-navbar.vue'
import { useCreateSession } from '@/modules/session/composables/session.composables'

/* theme */
useColorMode({ initialValue: 'dark' })

/* upload state */
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<File[]>([])
const isDragging = ref(false)
const router = useRouter()
const createSessionMutation = useCreateSession()
const isUploading = computed(() => createSessionMutation.isPending.value)

/* sessions */

/* helpers */
const hasFiles = computed(() => selectedFiles.value.length > 0)
const triggerFileInput = () => fileInput.value?.click()

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files) return
  addFiles(Array.from(target.files))
}
function handleDrop(e: DragEvent) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer?.files ?? [])
  addFiles(files)
}
function addFiles(files: File[]) {
  const valid = files.filter(
    (f) =>
      f.type === 'application/pdf' ||
      f.type === 'application/zip' ||
      f.name.endsWith('.pdf') ||
      f.name.endsWith('.zip'),
  )
  selectedFiles.value = [...selectedFiles.value, ...valid]
}
function removeFile(i: number) {
  selectedFiles.value.splice(i, 1)
}
function formatFileSize(bytes: number) {
  if (bytes === 0) return '0 Б'
  const k = 1024,
    sizes = ['Б', 'КБ', 'МБ', 'ГБ']
  const idx = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, idx)).toFixed(1)} ${sizes[idx]}`
}
async function handleUpload() {
  if (!hasFiles.value || isUploading.value) return
  try {
    const session = await createSessionMutation.mutateAsync(selectedFiles.value)
    selectedFiles.value = []
    router.push(`/sessions/${session.id}`)
  } catch (error) {
    console.error('[sessions] failed to create session', error)
  }
}
</script>

<template>
  <div class="relative min-h-screen bg-background text-foreground transition-colors">
    <!-- Background -->
    <div class="pointer-events-none fixed inset-0 z-10">
      <img
        :src="BackgroundImage"
        alt=""
        class="h-full w-full object-cover opacity-20 mix-blend-soft-light"
      />
      <div
        class="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(56,189,248,0.20)_0,transparent_45%),radial-gradient(circle_at_80%_80%,rgba(79,70,229,0.22)_0,transparent_45%)]"
      />
      <div
        class="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-size-[120px_120px]"
      />
    </div>

    <HomeNavbar />

    <!-- Main -->
    <main class="container mx-auto max-w-[1200px] px-6 py-16">
      <div class="flex h-screen flex-col items-center justify-center -mt-20">
        <!-- Welcome -->
        <div class="mb-10 text-center w-full max-w-3xl z-10">
          <h2 class="text-3xl font-bold md:text-5xl text-white">
            Проверка документов без ручной рутины
          </h2>
          <p class="mx-auto max-w-[56ch] mt-6 text-base text-white/70 leading-relaxed">
            Компьютерное зрение выделяет подписи, печати и QR в чертежах и актах — быстрее, точнее,
            прозрачнее.
          </p>
        </div>

        <!-- Hero panel -->
        <section
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
          :class="
            cn(
              'w-full max-w-3xl overflow-hidden rounded-[42px] transition-all border border-white/50 bg-white/10 p-6 shadow-xl backdrop-blur-xl md:p-12',
              isDragging ? 'border-primary bg-primary/5 border-dashed' : 'border-white/30',
            )
          "
        >
          <!-- Upload area -->

          <div class="flex flex-col items-center justify-center gap-6 p-12 text-center">
            <div
              @click="triggerFileInput"
              class="cursor-pointer rounded-full bg-white/10 p-6 backdrop-blur-sm hover:bg-white/5"
            >
              <Upload class="h-10 w-10 text-white" />
            </div>

            <input
              ref="fileInput"
              id="file-upload"
              class="hidden"
              type="file"
              multiple
              accept=".pdf,.zip"
              @change="handleFileSelect"
            />

            <p class="text-sm text-white/60">PDF или ZIP до 100MB</p>
          </div>

          <!-- Selected list -->
          <div v-if="hasFiles" class="px-6 pb-6 space-y-2">
            <div class="mb-3 text-sm font-medium text-white">
              {{ selectedFiles.length }} {{ selectedFiles.length === 1 ? 'файл' : 'файла' }}
            </div>
            <div
              v-for="(file, i) in selectedFiles"
              :key="file.name + i"
              class="flex items-center justify-between gap-3 rounded-lg border border-white/30 bg-white/10 backdrop-blur-sm p-3"
            >
              <div class="flex min-w-0 flex-1 items-center gap-3">
                <FileText class="h-4 w-4 text-white/80" />
                <span class="truncate text-sm text-white">{{ file.name }}</span>
                <span class="shrink-0 text-xs text-white/60">{{ formatFileSize(file.size) }}</span>
              </div>
              <Button
                variant="ghost"
                size="icon"
                class="h-8 w-8 hover:bg-white/20"
                @click="removeFile(i)"
                aria-label="Удалить файл"
              >
                <X class="h-4 w-4 text-white/80" />
              </Button>
            </div>
          </div>

          <!-- Upload CTA -->
          <div v-if="hasFiles" class="mt-8 text-center">
            <Button
              size="lg"
              class="gap-2 px-12 py-6 text-base bg-white/90 text-black hover:bg-white font-semibold"
              :disabled="isUploading"
              @click="handleUpload"
            >
              <Loader2 v-if="isUploading" class="h-5 w-5 animate-spin" />
              <template v-else>
                <CheckCircle2 class="h-5 w-5" />
              </template>
              {{ isUploading ? 'Анализируем…' : 'Начать проверку' }}
            </Button>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.animate-shimmer {
  animation: shimmer 3s infinite;
}
</style>
