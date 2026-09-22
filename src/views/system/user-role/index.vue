<template>
  <div />
</template>

<script setup>
  import { onMounted } from 'vue';
  import { useRouter } from 'vue-router';

  // 用户赋权已合并进角色管理，旧路由重定向
  const router = useRouter();
  onMounted(() => {
    router.replace('/system/role');
  });
</script>
