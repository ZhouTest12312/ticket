<!-- 路由出口 -->
<template>
  <router-view v-slot="{ Component }">
    <keep-alive
      v-if="TAB_KEEP_ALIVE && tabBar"
      :include="keepAliveInclude"
      :max="10"
    >
      <component :is="Component" />
    </keep-alive>
    <component v-else :is="Component" />
  </router-view>
</template>

<script setup>
  import { storeToRefs } from 'pinia';
  import { useThemeStore } from '@/store/modules/theme';
  import { TAB_KEEP_ALIVE } from '@/config/setting';

  const { keepAliveInclude, tabBar } = storeToRefs(useThemeStore());
</script>

<script>
  export default {
    name: 'RouterLayout'
  };
</script>
