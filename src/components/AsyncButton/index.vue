<!-- 带有 loading 状态控制的按钮组件 -->
<template>
  <el-button v-bind="attrs" :loading="loading" @click="handleClick">
    <slot></slot>
  </el-button>
</template>

<script setup>
  import { ref, useAttrs } from 'vue';
  import { isFunction } from 'lodash-es';

  defineOptions({
    inheritAttrs: false
  });

  const props = defineProps({
    onSubmit: Function
  });

  const attrs = useAttrs();
  const emits = defineEmits(['click']);
  const loading = ref(false);

  const handleClick = async (e) => {
    if (loading.value) return;

    if (!props.onSubmit || !isFunction(props.onSubmit)) {
      emits('click', e);
      return;
    }

    loading.value = true;
    try {
      // 通过done回调结束loading状态
      let resolveDone;
      const donePromise = new Promise((resolve) => {
        resolveDone = resolve;
      });

      const result = props.onSubmit(() => resolveDone(true), e); // 兼容onSubmit 返回 Promise 对象 来结束loading状态

      if (result && isFunction(result.then)) {
        await result;
      } else {
        await donePromise;
      }
    } finally {
      loading.value = false;
    }
  };
</script>
