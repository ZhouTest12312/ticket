<template>
  <ele-drawer
    :model-value="modelValue"
    :title="group?.id ? '修改分组' : '新建分组'"
    size="520px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="分组名称" prop="name">
        <el-input v-model="form.name" maxlength="64" placeholder="例如技术组" />
      </el-form-item>
      <el-form-item label="包含角色" prop="roleIds">
        <el-checkbox-group v-model="form.roleIds" @change="onRolesChange">
          <el-checkbox v-for="item in roles" :key="item.id" :value="item.id">
            {{ item.name }}
          </el-checkbox>
        </el-checkbox-group>
        <div class="hint">一个角色只能属于一个组。勾选后会从其他组移出。</div>
      </el-form-item>
      <el-form-item v-if="needLeader" label="负责人" prop="leaderId">
        <el-select
          v-model="form.leaderId"
          clearable
          filterable
          placeholder="请选择本组负责人"
          style="width: 100%"
        >
          <el-option
            v-for="item in memberOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <div class="hint">一个组只能有一个负责人，负责人可处理本组全部工单并接收升级。</div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { computed, reactive, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { pageRoles } from '@/api/role';
  import { pageUsers } from '@/api/userRole';
  import { createHandlerGroup, updateHandlerGroup } from '@/api/group';

  const props = defineProps({
    modelValue: Boolean,
    group: { type: Object, default: null }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const saving = ref(false);
  const roles = ref([]);
  const users = ref([]);
  const form = reactive({ name: '', roleIds: [], leaderId: undefined });
  const rules = {
    name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }]
  };
  const needLeader = computed(() => form.name.trim() !== '管理组');
  const memberOptions = computed(() =>
    users.value
      .filter((item) =>
        (item.roles || []).some((role) => form.roleIds.map(Number).includes(Number(role.id)))
      )
      .map((item) => ({
        id: Number(item.id),
        name: item.displayName || item.username
      }))
  );

  const onRolesChange = () => {
    if (!memberOptions.value.some((item) => item.id === form.leaderId)) {
      form.leaderId = undefined;
    }
  };

  const load = async () => {
    form.name = props.group?.name || '';
    form.roleIds = [...(props.group?.roleIds || [])];
    form.leaderId =
      props.group?.name === '管理组' || props.group?.leaderId == null
        ? undefined
        : Number(props.group.leaderId);
    const [roleData, userData] = await Promise.all([
      pageRoles({ page: 1, pageSize: 200 }),
      pageUsers({ page: 1, pageSize: 200 })
    ]);
    roles.value = (roleData.records || []).filter((item) => item.code !== 'customer');
    users.value = userData.records || [];
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
    const valid = await formRef.value?.validate?.().catch(() => false);
    if (!valid) return;
    saving.value = true;
    try {
      const payload = {
        name: form.name,
        roleIds: form.roleIds,
        leaderId: needLeader.value ? form.leaderId || null : null
      };
      if (props.group?.id) {
        await updateHandlerGroup(props.group.id, payload);
      } else {
        await createHandlerGroup(payload);
      }
      EleMessage.success('保存成功');
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
  :deep(.el-checkbox) {
    margin-right: 16px;
  }
</style>
