<template>
  <ele-upload-list
    v-model="files"
    :class="{ 'is-readonly': readonly }"
    :readonly="readonly"
    :button-style="readonly ? false : undefined"
    :multiple="true"
    :limit="9"
    accept="image/*,video/*"
    :sortable="!readonly"
    :tools="!readonly"
    @upload="(item) => onUpload(item)"
    @retry="(item) => onUpload(item, true)"
    @remove="onRemove"
    @editUpload="onEditUpload"
  >
    <template #thumbnail="{ item }">
      <div class="media-thumb">
        <video v-if="item.kind === 'video'" :src="item.url" muted class="ele-upload-image" />
        <img v-else :src="item.url" alt="" class="ele-upload-image" />
        <div v-if="readonly" class="media-zoom">
          <el-icon><ZoomIn /></el-icon>
        </div>
      </div>
    </template>
  </ele-upload-list>
</template>

<script setup>
  import { ref, watch } from 'vue';
  import { ZoomIn } from '@element-plus/icons-vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { ElMessageBox } from 'element-plus/es';
  import {
    deleteTicketAttachment,
    saveTicketAttachment,
    uploadLocalMedia
  } from '@/api/ticket';

  const props = defineProps({
    modelValue: { type: Array, default: () => [] },
    ticketId: { type: [Number, null], default: null },
    readonly: { type: Boolean, default: false }
  });
  const emit = defineEmits(['update:modelValue', 'change']);

  const files = ref([]);

  const toItem = (file) => ({
    key: file.id ? `saved-${file.id}` : file.key,
    id: file.id,
    name: file.filename || file.name || '',
    url: file.url,
    status: 'done',
    kind: file.kind
  });

  watch(
    () => props.modelValue,
    (list) => {
      if (!props.readonly && !props.ticketId) return;
      files.value = (list || [])
        .filter((item) => item.kind === 'image' || item.kind === 'video')
        .map(toItem);
    },
    { immediate: true }
  );

  const publish = () => {
    const rows = files.value
      .filter((item) => item.url)
      .map((item) => ({
        id: item.id,
        url: item.url,
        filename: item.name,
        kind: item.kind
      }));
    emit('update:modelValue', rows);
    emit('change', rows);
  };

  const onUpload = async (item, retry) => {
    if (!item?.file) return;
    const type = item.file.type || '';
    const kind = type.startsWith('image/')
      ? 'image'
      : type.startsWith('video/')
        ? 'video'
        : '';
    if (!kind) {
      EleMessage.error('请上传图片或视频');
      return;
    }
    if (!retry) {
      files.value.push({ ...item, kind, status: 'uploading', progress: 0 });
    }
    const fileItem = files.value.find((row) => row.key === item.key);
    if (!fileItem) return;
    fileItem.status = 'uploading';
    fileItem.kind = kind;
    try {
      const uploaded = await uploadLocalMedia(item.file);
      fileItem.url = uploaded.url;
      fileItem.name = uploaded.filename || item.file.name;
      fileItem.kind = uploaded.kind || kind;
      fileItem.status = 'done';
      fileItem.progress = 100;
      if (props.ticketId) {
        const saved = await saveTicketAttachment(props.ticketId, {
          url: fileItem.url,
          filename: fileItem.name,
          kind: fileItem.kind
        });
        fileItem.id = saved?.id;
      }
      publish();
    } catch (e) {
      fileItem.status = 'exception';
      EleMessage.error(e.message || '上传失败');
    }
  };

  const onEditUpload = ({ item, newItem }) => {
    const oldItem = files.value.find((row) => row.key === item.key);
    if (!oldItem) return;
    onUpload({ ...newItem, key: oldItem.key }, true);
  };

  const onRemove = (item) => {
    ElMessageBox.confirm('确定要删除吗?', '系统提示', {
      type: 'warning',
      draggable: true
    })
      .then(async () => {
        const index = files.value.findIndex((row) => row.key === item.key);
        if (index !== -1) files.value.splice(index, 1);
        if (item.id && props.ticketId) {
          try {
            await deleteTicketAttachment(item.id);
          } catch (e) {
            EleMessage.error(e.message || '删除失败');
          }
        }
        publish();
      })
      .catch(() => {});
  };

  defineExpose({
    getFiles: () =>
      files.value
        .filter((item) => item.url)
        .map((item) => ({
          url: item.url,
          filename: item.name,
          kind: item.kind
        }))
  });
</script>

<style scoped>
  .media-thumb {
    position: relative;
    width: 100%;
    height: 100%;
  }
  .media-thumb :deep(.ele-upload-image) {
    object-fit: contain;
    background: var(--el-fill-color-lighter);
  }
  .media-zoom {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 22px;
    background: rgba(0, 0, 0, 0.45);
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none;
  }
  .is-readonly :deep(.ele-upload-item:hover) .media-zoom {
    opacity: 1;
  }
</style>
