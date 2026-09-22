<template>
  <div class="my-editor">
    <ele-loading :loading="loading">
      <Toolbar
        v-if="showToolbar"
        :editor="editor"
        :defaultConfig="toolbarConfig"
        style="border-bottom: 1px solid #ccc"
      />
      <Editor
        v-model="localHtml"
        :defaultConfig="editorConfig"
        :style="{ height: height + 'px' }"
        @onCreated="handleCreated"
      />
    </ele-loading>
  </div>
</template>

<script setup>
  import { shallowRef, ref, watch, onBeforeUnmount, nextTick } from 'vue';
  import '@wangeditor/editor/dist/css/style.css';
  import { Editor, Toolbar } from '@wangeditor/editor-for-vue';
  import { imgUpload } from '@/utils/uploadImg';
  import { EleMessage, EleLoading } from 'ele-admin-plus/es';

  const props = defineProps({
    modelValue: {
      type: String,
      default: ''
    },
    showToolbar: {
      type: Boolean,
      default: true
    },
    height: {
      type: [String, Number],
      default: '400' // 默认高度
    },
    autoFocus: {
      type: Boolean,
      default: false // 是否自动聚焦
    },
    config: {
      type: Object,
      default: () => ({})
    },
    disabled: {
      type: Boolean,
      default: false
    }
  });

  const emit = defineEmits(['update:modelValue', 'onCreated']);

  // 状态
  const localHtml = ref(props.modelValue);
  const editor = shallowRef(null);
  const loading = ref(false);
  const uploadNum = ref(0);

  // 同步外部值变化到内部状态 - 防止失焦问题
  let externalUpdateTimer = null;
  watch(
    () => props.modelValue,
    (val, oldVal) => {
      // 只有当值真正发生变化时才更新，避免不必要的重新渲染
      if (val !== localHtml.value && editor.value) {
        // 清除之前的定时器
        if (externalUpdateTimer) clearTimeout(externalUpdateTimer);

        // 延迟执行外部更新，避免频繁触发
        externalUpdateTimer = setTimeout(() => {
          // 保存当前光标位置
          const selection = editor.value.getSelection();
          const currentHtml = localHtml.value;

          // 检查是否应该更新 - 避免在编辑器输入时触发更新
          const shouldUpdate =
            !editor.value.isFocused() ||
            (val !== currentHtml &&
              Math.abs(val.length - currentHtml.length) > 10); // 内容长度变化较大时才更新

          if (shouldUpdate) {
            isInternalUpdate = true; // 标记为内部更新
            localHtml.value = val;

            // 恢复光标位置（如果可能的话）
            // nextTick(() => {
            //   if (selection && editor.value) {
            //     try {
            //       // editor.value.restoreSelection(selection);
            //     } catch (e) {
            //       // 如果恢复失败，不处理
            //     }
            //   }
            // });
          }
        }, 50); // 50ms延迟，避免频繁更新
      }
    }
  );

  // 同步内部值变化到外部 - 添加防抖防止频繁触发
  let updateTimer = null;
  let isInternalUpdate = false; // 标记是否为内部更新

  watch(localHtml, (val) => {
    // 如果是外部值变化触发的内部更新，不触发emit
    if (isInternalUpdate) {
      isInternalUpdate = false;
      return;
    }

    if (updateTimer) clearTimeout(updateTimer);
    updateTimer = setTimeout(() => {
      emit('update:modelValue', val);
    }, 100); // 100ms防抖延迟
  });

  // 配置项
  const toolbarConfig = ref({
    excludeKeys: [
      'group-video',
      'insertImage',
      'codeBlock',
      'insertTable',
      'todo',
      'group-more-style',
      'blockquote'
    ],
    ...props.config
  });
  const editorConfig = ref({
    placeholder: '请输入内容...',
    mode: props.mode,
    autoFocus: props.autoFocus,
    readOnly: props.disabled,
    MENU_CONF: {
      uploadImage: {
        server: '',
        base64LimitSize: 0,
        customUpload: async (file, insertFn) => {
          const MAX_SIZE = 5 * 1024 * 1024; // 5MB
          if (file.size > MAX_SIZE) {
            EleMessage.error('图片大小不能超过 5MB');
            return;
          }
          uploadNum.value++;
          if (uploadNum.value === 1) loading.value = true;

          const params = {
            file,
            onProgress: (percent) => {},
            onError: (error) => {
              uploadNum.value--;
              if (uploadNum.value === 0) loading.value = false;
              EleMessage.error('上传失败，请重试');
            },
            onSuccess: (res) => {
              uploadNum.value--;
              if (uploadNum.value === 0) {
                loading.value = false;
                EleMessage.success('上传成功');
              }
              insertFn(res.url, '', '');
            }
          };
          imgUpload(params);
        }
      }
    }
  });

  // 生命周期
  const handleCreated = (e) => {
    editor.value = e;
    emit('onCreated', e);
  };

  // 组件卸载时清理定时器
  onBeforeUnmount(() => {
    if (updateTimer) {
      clearTimeout(updateTimer);
      updateTimer = null;
    }
    if (externalUpdateTimer) {
      clearTimeout(externalUpdateTimer);
      externalUpdateTimer = null;
    }
  });
</script>

<style lang="scss" scoped>
  .my-editor {
    position: relative;
  }
  .w-e-full-screen-container {
    z-index: 99999999;
  }
  :deep(.w-e-text-placeholder) {
    top: 11px;
  }
</style>
