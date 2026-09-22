<template>
  <ele-drawer
    :model-value="modelValue"
    :title="customerId ? '编辑客户' : '新建客户'"
    size="560px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" maxlength="128" placeholder="请输入客户名称" />
      </el-form-item>
      <el-form-item label="联系人" prop="contactName">
        <el-input
          v-model="form.contactName"
          maxlength="64"
          placeholder="请输入联系人"
        />
      </el-form-item>
      <el-form-item label="电话" prop="phone">
        <el-input v-model="form.phone" maxlength="11" placeholder="请输入电话" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" maxlength="128" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="所属行业" prop="industry">
        <el-input
          v-model="form.industry"
          maxlength="64"
          placeholder="如 教育培训"
        />
      </el-form-item>
      <el-form-item label="登录账号">
        <el-select
          v-model="form.userId"
          clearable
          filterable
          placeholder="绑定客户角色账号，用于查看进度和确认"
          style="width: 100%"
        >
          <el-option
            v-for="item in portalUsers"
            :key="item.id"
            :label="`${item.displayName || item.username}（${item.username}）`"
            :value="item.id"
          />
        </el-select>
        <div class="hint">客户用这个账号登录后，只能看到本客户的工单，并确认或补充。</div>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="form.status">
          <el-radio :value="1">启用</el-radio>
          <el-radio :value="0">停用</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { nextTick, reactive, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { createCustomer, getCustomer, pageCustomers, updateCustomer } from '@/api/customer';
  import { pageUsers } from '@/api/userRole';

  const props = defineProps({
    modelValue: Boolean,
    customerId: { type: [Number, null], default: null }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const saving = ref(false);
  const portalUsers = ref([]);
  const form = reactive({
    name: '',
    contactName: '',
    phone: '',
    email: '',
    industry: '',
    status: 1,
    userId: undefined
  });

  const rules = {
    name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
    contactName: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
    phone: [
      { required: true, message: '请输入电话', trigger: 'blur' },
      {
        pattern: /^[\d\-+() ]{6,11}$/,
        message: '请输入有效电话',
        trigger: 'blur'
      }
    ],
    email: [
      { required: true, message: '请输入邮箱', trigger: 'blur' },
      { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
    ],
    industry: [{ required: true, message: '请输入所属行业', trigger: 'blur' }],
    status: [{ required: true, message: '请选择状态', trigger: 'change' }]
  };                                                    

  const resetForm = () => {
    form.name = '';
    form.contactName = '';
    form.phone = '';
    form.email = '';
    form.industry = '';
    form.status = 1;
    form.userId = undefined;
  };

  const load = async () => {
    if (!props.customerId) {
      resetForm();
    } else {
      const detail = await getCustomer(props.customerId);
      form.name = detail.name || '';
      form.contactName = detail.contactName || '';
      form.phone = detail.phone || '';
      form.email = detail.email || '';
      form.industry = detail.industry || '';
      form.status = detail.status === 0 ? 0 : 1;
      form.userId = detail.userId || undefined;
    }
    const [userData, customerData] = await Promise.all([
      pageUsers({ page: 1, pageSize: 200 }).catch(() => ({ records: [] })),
      pageCustomers({ page: 1, pageSize: 200 }).catch(() => ({ records: [] }))
    ]);
    const taken = new Set(
      (customerData.records || [])
        .filter((item) => item.userId && item.id !== props.customerId)
        .map((item) => item.userId)
    );
    portalUsers.value = (userData.records || []).filter(
      (item) =>
        (item.roles || []).some((role) => role.code === 'customer') && !taken.has(item.id)
    );
    await nextTick();
    formRef.value?.clearValidate?.();
  };

  watch(
    () => props.modelValue,
    (v) => {
      if (v) {
        load().catch((e) => EleMessage.error(e.message || '加载失败'));
      } else {
        formRef.value?.clearValidate?.();
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
      const payload = {
        name: form.name,
        contactName: form.contactName,
        phone: form.phone,
        email: form.email,
        industry: form.industry,
        status: form.status,
        userId: form.userId || null
      };
      if (props.customerId) {
        await updateCustomer(props.customerId, payload);
        EleMessage.success('保存成功');
      } else {
        await createCustomer(payload);
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

<style scoped>
  .hint {
    width: 100%;
    margin-top: 6px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
    line-height: 1.5;
  }
</style>

