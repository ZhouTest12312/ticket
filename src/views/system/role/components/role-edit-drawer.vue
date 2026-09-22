<template>
  <ele-drawer
    :model-value="modelValue"
    :title="roleId ? '编辑角色' : '新建角色'"
    size="780px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="编码" prop="code">
        <el-input
          v-model="form.code"
          :disabled="!!roleId"
          maxlength="64"
          placeholder="如 demo"
        />
      </el-form-item>
      <el-form-item label="名称" prop="name">
        <el-input
          v-model="form.name"
          maxlength="128"
          placeholder="请输入角色名称"
        />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="2"
          placeholder="请输入角色描述"
        />
      </el-form-item>
      <el-form-item
        v-for="group in permissionGroups"
        :key="group.module"
        :label="moduleLabel(group.module)"
        :prop="`modulePerms.${group.module}`"
        :rules="modulePermRules(group.module)"
      >
        <el-checkbox-group
          v-model="form.modulePerms[group.module]"
          @change="() => onModulePermChange(group.module)"
        >
          <el-checkbox
            v-for="item in group.items"
            :key="item.id"
            :value="item.id"
          >
            {{ item.name }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">
        保存
      </el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { nextTick, reactive, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import {
    createRole,
    getRole,
    listPermissions,
    updateRole
  } from '@/api/role';

  const props = defineProps({
    modelValue: Boolean,
    roleId: { type: [Number, null], default: null }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const saving = ref(false);
  const permissionGroups = ref([]);
  const form = reactive({
    code: '',
    name: '',
    description: '',
    modulePerms: {}
  });
  const rules = {
    code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }]
  };

  const moduleLabels = {
    meta: '基础配置',
    system: '系统管理',
    ticket: '工单管理'
  };

  const moduleLabel = (module) => moduleLabels[module] || module;

  const modulePermRules = (module) => [
    {
      type: 'array',
      required: true,
      min: 1,
      message: `请至少选择一项${moduleLabel(module)}权限`,
      // 避免打开/回填时误触发；提交与勾选变更时再校验
      trigger: []
    }
  ];

  const initModulePerms = (groups, selectedIds = []) => {
    const selected = new Set((selectedIds || []).map((id) => Number(id)));
    const next = {};
    (groups || []).forEach((g) => {
      next[g.module] = (g.items || [])
        .map((i) => Number(i.id))
        .filter((id) => selected.has(id));
    });
    form.modulePerms = next;
  };

  const collectPermissionIds = () => {
    const ids = [];
    Object.values(form.modulePerms || {}).forEach((arr) => {
      (arr || []).forEach((id) => ids.push(Number(id)));
    });
    return [...new Set(ids)];
  };

  const onModulePermChange = (module) => {
    formRef.value?.validateField?.(`modulePerms.${module}`);
  };

  const clearValidate = async () => {
    await nextTick();
    formRef.value?.clearValidate?.();
  };

  const resetForm = (groups = permissionGroups.value) => {
    form.code = '';
    form.name = '';
    form.description = '';
    initModulePerms(groups, []);
  };

  const load = async () => {
    const groups = await listPermissions();
    permissionGroups.value = groups || [];
    if (!props.roleId) {
      resetForm(groups);
    } else {
      const detail = await getRole(props.roleId);
      form.code = detail.code;
      form.name = detail.name;
      form.description = detail.description || '';
      initModulePerms(groups, detail.permissionIds || []);
    }
    await clearValidate();
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
        code: form.code,
        name: form.name,
        description: form.description,
        permissionIds: collectPermissionIds()
      };
      if (props.roleId) {
        await updateRole(props.roleId, payload);
      } else {
        await createRole(payload);
      }
      EleMessage.success(
        props.roleId
          ? '保存成功'
          : '角色已创建。请到「用户管理」给用户勾选该角色后才会生效'
      );
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
  :deep(.el-checkbox-group) {
    display: grid;
    grid-template-columns: 1fr 1fr;
    column-gap: 28px;
    row-gap: 14px;
    width: 100%;
    padding: 4px 0 8px;
  }

  :deep(.el-checkbox) {
    display: flex;
    margin-right: 0;
    margin-bottom: 0;
    height: auto;
    min-height: 22px;
    line-height: 22px;
    white-space: normal;
    align-items: flex-start;
  }

  :deep(.el-checkbox .el-checkbox__label) {
    line-height: 22px;
    padding-left: 10px;
  }

  :deep(.el-form-item) {
    margin-bottom: 22px;
  }
</style>
