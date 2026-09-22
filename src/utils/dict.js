import { ref, toRefs } from 'vue';

/**
 * 获取字典数据
 */
export function useDict(...args) {
  const res = ref({});
  return (() => {
    args.forEach((d) => {
      res.value[d] = [];
    });
    return toRefs(res.value);
  })();
}
