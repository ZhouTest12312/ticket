<template>
  <ele-drawer
    :model-value="modelValue"
    :title="ticketId ? '编辑工单' : '新建工单'"
    size="640px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px">
      <el-form-item label="问题标题" prop="title">
        <el-input v-model="form.title" maxlength="200" placeholder="请输入问题标题" />
      </el-form-item>
      <el-form-item label="详细描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请描述问题现象、影响范围"
        />
      </el-form-item>
      <el-form-item label="问题分类" prop="categoryId">
        <el-select v-model="form.categoryId" placeholder="请选择分类" style="width: 100%">
          <el-option
            v-for="item in options.categories"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="优先级" prop="priorityId">
        <el-select v-model="form.priorityId" placeholder="请选择优先级" style="width: 100%">
          <el-option
            v-for="item in options.priorities"
            :key="item.id"
            :label="`${item.name}（${item.slaHours}小时）`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="关联客户" prop="customerId">
        <el-select
          v-model="form.customerId"
          filterable
          placeholder="请选择已绑定登录账号的客户"
          style="width: 100%"
        >
          <el-option
            v-for="item in options.customers"
            :key="item.id"
            :label="item.label || item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="产品" prop="product">
        <el-select
          v-model="form.product"
          filterable
          placeholder="请选择产品"
          style="width: 100%"
        >
          <el-option
            v-for="item in productChoices"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="订单" prop="orderNo">
        <el-input v-model="form.orderNo" maxlength="64" placeholder="请输入订单号" />
      </el-form-item>
      <el-form-item label="具体服务" prop="serviceName">
        <el-select
          v-model="form.serviceName"
          filterable
          placeholder="请选择具体服务"
          style="width: 100%"
        >
          <el-option
            v-for="item in serviceChoices"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="期望完成时间">
        <el-date-picker
          v-model="form.expectedFinishAt"
          type="datetime"
          value-format="YYYY-MM-DD HH:mm:ss"
          placeholder="请选择期望完成时间"
          style="width: 100%"
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
      <el-form-item v-if="!ticketId" label="附件">
        <TicketMediaUpload ref="mediaRef" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { computed, nextTick, reactive, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import {
    createTicket,
    getTicket,
    saveTicketAttachment,
    ticketOptions,
    updateTicket
  } from '@/api/ticket';
  import TicketMediaUpload from './ticket-media-upload.vue';

  const props = defineProps({
    modelValue: Boolean,
    ticketId: { type: [Number, null], default: null }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const mediaRef = ref(null);
  const saving = ref(false);
  const options = reactive({
    categories: [],
    priorities: [],
    customers: [],
    products: [],
    services: []
  });
  const form = reactive({
    title: '',
    description: '',
    categoryId: undefined,
    priorityId: undefined,
    customerId: undefined,
    product: '',
    orderNo: '',
    serviceName: '',
    expectedFinishAt: '',
    estimatedResolveAt: ''
  });

  const choiceNames = (list, current) => {
    const names = (list || []).map((item) => item.name);
    if (current && !names.includes(current)) {
      return [current, ...names];
    }
    return names;
  };
  const productChoices = computed(() => choiceNames(options.products, form.product));
  const serviceChoices = computed(() => choiceNames(options.services, form.serviceName));
  const rules = {
    title: [{ required: true, message: '请输入问题标题', trigger: 'blur' }],
    description: [{ required: true, message: '请输入详细描述', trigger: 'blur' }],
    categoryId: [{ required: true, message: '请选择问题分类', trigger: 'change' }],
    priorityId: [{ required: true, message: '请选择优先级', trigger: 'change' }],
    customerId: [{ required: true, message: '请关联客户', trigger: 'change' }],
    product: [{ required: true, message: '请选择产品', trigger: 'change' }],
    orderNo: [{ required: true, message: '请输入订单号', trigger: 'blur' }],
    serviceName: [{ required: true, message: '请选择具体服务', trigger: 'change' }]
  };

  const resetForm = () => {
    form.title = '';
    form.description = '';
    form.categoryId = undefined;
    form.priorityId = undefined;
    form.customerId = undefined;
    form.product = '';
    form.orderNo = '';
    form.serviceName = '';
    form.expectedFinishAt = '';
    form.estimatedResolveAt = '';
  };

  const payload = () => ({
    title: form.title,
    description: form.description,
    categoryId: form.categoryId,
    priorityId: form.priorityId,
    customerId: form.customerId,
    product: form.product,
    orderNo: form.orderNo,
    serviceName: form.serviceName,
    expectedFinishAt: form.expectedFinishAt || null,
    estimatedResolveAt: form.estimatedResolveAt || null
  });

  const load = async () => {
    const data = await ticketOptions();
    options.categories = data.categories || [];
    options.priorities = data.priorities || [];
    options.customers = data.customers || [];
    options.products = data.products || [];
    options.services = data.services || [];
    if (!props.ticketId) {
      resetForm();
    } else {
      const detail = await getTicket(props.ticketId);
      form.title = detail.title || '';
      form.description = detail.description || '';
      form.categoryId = detail.categoryId;
      form.priorityId = detail.priorityId;
      form.customerId = detail.customerId;
      form.product = detail.product || '';
      form.orderNo = detail.orderNo || '';
      form.serviceName = detail.serviceName || '';
      form.expectedFinishAt = detail.expectedFinishAt || '';
      form.estimatedResolveAt = detail.estimatedResolveAt || '';
    }
    await nextTick();
    formRef.value?.clearValidate?.();
  };

  watch(
    () => props.modelValue,
    (v) => {
      if (v) {
        load().catch((e) => EleMessage.error(e.message || '加载失败'));
      }
    }
  );

  const submit = async () => {
    try {
      await formRef.value?.validate?.();
    } catch {
      return;
    }
    saving.value = true;
    try {
      if (props.ticketId) {
        await updateTicket(props.ticketId, payload());
        EleMessage.success('保存成功');
      } else {
        const created = await createTicket(payload());
        const files = mediaRef.value?.getFiles?.() || [];
        for (const item of files) {
          await saveTicketAttachment(created.id, item);
        }
        EleMessage.success('创建成功');
      }
      emit('update:modelValue', false);
      emit('done');
    } catch (e) {
      EleMessage.error(e.message || '保存失败');
    } finally {
      saving.value = false;
    }
  };
</script>
