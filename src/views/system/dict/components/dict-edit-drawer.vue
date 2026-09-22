<template>
  <ele-drawer
    :model-value="modelValue"
    :title="itemId ? '编辑字典项' : '新建字典项'"
    size="480px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" maxlength="128" placeholder="请输入名称" />
      </el-form-item>
      <el-form-item label="排序" prop="sort">
        <el-input-number v-model="form.sort" :min="0" :max="9999" />
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
  import { createDictItem, getDictItem, updateDictItem } from '@/api/dict';

  const props = defineProps({
    modelValue: Boolean,
    itemId: { type: [Number, null], default: null },
    typeCode: { type: String, required: true }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const saving = ref(false);
  const form = reactive({
    name: '',
    sort: 0,
    status: 1
  });
  const rules = {
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
    sort: [{ required: true, message: '请输入排序', trigger: 'change' }],
    status: [{ required: true, message: '请选择状态', trigger: 'change' }]
  };

  const resetForm = () => {
    form.name = '';
    form.sort = 0;
    form.status = 1;
  };

  const load = async () => {
    if (!props.itemId) {
      resetForm();
    } else {
      const detail = await getDictItem(props.itemId);
      form.name = detail.name || '';
      form.sort = detail.sort ?? 0;
      form.status = detail.status ?? 1;
    }
    await nextTick();
    formRef.value?.clearValidate?.();
  };

  watch(
    () => props.modelValue,
    (visible) => {
      if (visible) {
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
      const payload = {
        typeCode: props.typeCode,
        name: form.name,
        sort: form.sort,
        status: form.status
      };
      if (props.itemId) {
        await updateDictItem(props.itemId, payload);
        EleMessage.success('保存成功');
      } else {
        await createDictItem(payload);
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
