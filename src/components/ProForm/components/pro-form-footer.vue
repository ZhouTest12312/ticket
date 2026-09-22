<template>
  <ElFormItem v-bind="footerProps || {}">
    <template
      v-for="name in Object.keys(footerSlots || {}).filter(
        (k) =>
          k !== 'footer' &&
          !!(footerSlots && footerSlots[k] && $slots[footerSlots[k]])
      )"
      #[name]="slotProps"
    >
      <slot :name="footerSlots?.[name]" v-bind="slotProps || {}"></slot>
    </template>
    <div
      :style="{
        flex: 1,
        display: 'flex',
        alignItems: 'center',
        ...(footerStyle || {})
      }"
    >
      <slot name="footer">
        <ElButton
          type="primary"
          v-bind="submitButtonProps || {}"
          @click="submit"
        >
          {{ submitText }}
        </ElButton>
        <ElButton v-bind="resetButtonProps || {}" @click="reset">
          {{ resetText }}
        </ElButton>
      </slot>
      <slot name="footerExtra"></slot>
    </div>
  </ElFormItem>
</template>

<script setup>
  defineProps({
    /** 底栏ElFormItem属性 */
    footerProps: Object,
    /** 底栏ElFormItem插槽 */
    footerSlots: Object,
    /** 底栏样式 */
    footerStyle: Object,
    /** 提交按钮文本 */
    submitText: String,
    /** 重置按钮文本 */
    resetText: String,
    /** 提交按钮属性 */
    submitButtonProps: Object,
    /** 重置按钮属性 */
    resetButtonProps: Object
  });

  const emit = defineEmits(['submit', 'reset']);

  /** 提交 */
  const submit = () => {
    emit('submit');
  };

  /** 重置 */
  const reset = () => {
    emit('reset');
  };
</script>
