<script setup lang="ts">
import { cn } from '@/core/lib/tailwind.utils'
import { computed } from 'vue'
// If you DIDN'T enable auto-import via resolver, uncomment next line:
// import { motion } from 'motion-v'

interface Props {
  /** Original React `children` — here explicit as `text` */
  text: string
  /** HTML tag or component */
  as?: string | object
  /** Tailwind classes */
  class?: string
  /** seconds */
  duration?: number
  /** px per character for the shine width */
  spread?: number
}

const props = withDefaults(defineProps<Props>(), {
  as: 'p',
  duration: 2,
  spread: 2,
})

const dynamicSpread = computed(() => props.text.length * props.spread)
</script>

<template>
  <!-- If using auto-import, you can write <motion.[tag]> directly -->
  <component
    :is="`motion.${(props.as as string) || 'p'}`"
    v-motion="{
      initial: { backgroundPositionX: '100%' },
      enter: { backgroundPositionX: '0%' },
      transition: { duration: duration, repeat: Infinity, ease: 'linear' },
    }"
    :class="
      cn(
        'relative inline-block bg-[length:250%_100%,auto] bg-clip-text text-transparent',
        '[--base-color:#a1a1aa] [--base-gradient-color:#000]',
        '[--bg:linear-gradient(90deg,#0000_calc(50%-var(--spread)),var(--base-gradient-color),#0000_calc(50%+var(--spread)))]',
        '[background-repeat:no-repeat,padding-box]',
        'dark:[--base-color:#71717a] dark:[--base-gradient-color:#ffffff]',
        'dark:[--bg:linear-gradient(90deg,#0000_calc(50%-var(--spread)),var(--base-gradient-color),#0000_calc(50%+var(--spread)))]',
        $props.class,
      )
    "
    :initial="{ backgroundPositionX: '100%' }"
    :animate="{ backgroundPositionX: '0%' }"
    :transition="{
      duration: props.duration,
      repeat: Infinity,
      easing: 'linear',
    }"
    :style="{
      '--spread': `${dynamicSpread}px`,
      backgroundImage: `var(--bg), linear-gradient(var(--base-color), var(--base-color))`,
    }"
  >
    {{ props.text }}
  </component>
</template>
