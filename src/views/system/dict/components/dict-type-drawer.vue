<template>
  <ele-drawer
    :model-value="modelValue"
    :title="dictId ? '修改字典' : '新建字典'"
    size="480px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="字典类型" prop="name">
        <el-input v-model="form.name" maxlength="64" placeholder="请输入字典类型" />
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
  import { createDictType, updateDictType } from '@/api/dict';

  const props = defineProps({
    modelValue: Boolean,
    dictId: { type: [Number, null], default: null },
    dictName: { type: String, default: '' }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const saving = ref(false);
  const form = reactive({ name: '' });
  const rules = {
    name: [{ required: true, message: '请输入字典类型', trigger: 'blur' }]
  };

  watch(
    () => props.modelValue,
    async (visible) => {
      if (!visible) return;
      form.name = props.dictId ? props.dictName : '';
      await nextTick();
      formRef.value?.clearValidate?.();
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
      if (props.dictId) {
        await updateDictType(props.dictId, { name: form.name });
        EleMessage.success('保存成功');
      } else {
        await createDictType({ name: form.name });
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
