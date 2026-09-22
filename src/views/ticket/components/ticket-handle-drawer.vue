<template>
  <ele-drawer
    :model-value="modelValue"
    :title="continued ? '继续处理' : '开始处理'"
    size="720px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-loading="loading">
      <div class="block-title">用户提问</div>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="问题标题" :span="2">{{ detail.title || '-' }}</el-descriptions-item>
        <el-descriptions-item label="客户">{{ detail.customerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分类 / 优先级">
          {{ detail.categoryName || '-' }} / {{ detail.priorityName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="产品">{{ detail.product || '-' }}</el-descriptions-item>
        <el-descriptions-item label="具体服务">{{ detail.serviceName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="问题描述" :span="2">
          {{ detail.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="block-title">问题附件</div>
      <TicketMediaUpload
        v-if="questionMedia.length"
        readonly
        :ticket-id="ticketId"
        :model-value="questionMedia"
      />
      <div v-else class="muted">暂无附件</div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" class="reply-form">
        <el-form-item label="处理记录" prop="reply">
          <el-input
            v-model="form.reply"
            type="textarea"
            :rows="3"
            placeholder="请填写处理记录，客户可以查看"
          />
        </el-form-item>
        <el-form-item label="解决方案" prop="solution">
          <el-input
            v-model="form.solution"
            type="textarea"
            :rows="3"
            placeholder="请填写解决方案"
          />
        </el-form-item>
        <el-form-item label="内部备注">
          <el-input
            v-model="form.internalNote"
            type="textarea"
            :rows="2"
            placeholder="仅内部可见，客户看不到"
          />
        </el-form-item>
        <el-form-item label="预计解决时间">
          <el-date-picker
            v-model="form.estimatedResolveAt"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选填"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="实际解决时间">
          <el-date-picker
            v-model="form.actualResolveAt"
            type="datetime"
            value-format="YYYY-MM-DD HH:mm:ss"
            placeholder="选填，解决后可再补"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="解决结果">
          <el-input
            v-model="form.resolution"
            type="textarea"
            :rows="2"
            placeholder="工单解决后必填，处理中可以先写"
          />
        </el-form-item>
        <el-form-item label="相关附件">
          <TicketMediaUpload ref="mediaRef" />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">确认</el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { computed, reactive, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { getTicket, submitHandleReply } from '@/api/ticket';
  import TicketMediaUpload from './ticket-media-upload.vue';

  const props = defineProps({
    modelValue: Boolean,
    ticketId: { type: [Number, null], default: null },
    continued: { type: Boolean, default: false }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const loading = ref(false);
  const saving = ref(false);
  const formRef = ref(null);
  const mediaRef = ref(null);
  const detail = ref({});
  const questionMedia = computed(() =>
    (detail.value.attachments || []).filter((item) => item.kind === 'image' || item.kind === 'video')
  );
  const form = reactive({
    reply: '',
    solution: '',
    internalNote: '',
    estimatedResolveAt: '',
    actualResolveAt: '',
    resolution: ''
  });
  const rules = {
    reply: [{ required: true, message: '请填写处理记录', trigger: 'blur' }],
    solution: [{ required: true, message: '请填写解决方案', trigger: 'blur' }]
  };

  const load = async () => {
    if (!props.ticketId) return;
    loading.value = true;
    form.reply = '';
    form.solution = '';
    form.internalNote = '';
    form.estimatedResolveAt = '';
    form.actualResolveAt = '';
    form.resolution = '';
    try {
      detail.value = (await getTicket(props.ticketId)) || {};
      form.reply = detail.value.handlerReply || '';
      form.solution = detail.value.handlerSolution || '';
      form.estimatedResolveAt = detail.value.estimatedResolveAt || '';
      form.actualResolveAt = detail.value.actualResolveAt || '';
      form.resolution = detail.value.resolution || '';
    } catch (e) {
      EleMessage.error(e.message || '加载失败');
    } finally {
      loading.value = false;
    }
  };

  watch(
    () => props.modelValue,
    (visible) => {
      if (visible) load();
    }
  );

  const submit = async () => {
    const valid = await formRef.value?.validate?.().catch(() => false);
    if (!valid) return;
    saving.value = true;
    try {
      await submitHandleReply(props.ticketId, {
        reply: form.reply,
        solution: form.solution,
        internalNote: form.internalNote,
        estimatedResolveAt: form.estimatedResolveAt || null,
        actualResolveAt: form.actualResolveAt || null,
        resolution: form.resolution,
        attachments: mediaRef.value?.getFiles?.() || []
      });
      EleMessage.success('已提交给客户');
      emit('update:modelValue', false);
      emit('done');
    } catch (e) {
      EleMessage.error(e.message || '提交失败');
    } finally {
      saving.value = false;
    }
  };
</script>

<style scoped>
  .block-title {
    margin: 16px 0 8px;
    font-weight: 600;
  }
  .block-title:first-child {
    margin-top: 0;
  }
  .reply-form {
    margin-top: 16px;
  }
  .muted {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
</style>
