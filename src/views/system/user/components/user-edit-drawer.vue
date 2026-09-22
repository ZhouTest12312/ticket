<template>
  <ele-drawer
    :model-value="modelValue"
    :title="user?.id ? '修改用户' : '新建用户'"
    size="520px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="form.username"
          maxlength="64"
          :disabled="!!user?.id"
          placeholder="请输入用户名"
        />
      </el-form-item>
      <el-form-item label="显示名" prop="displayName">
        <el-input v-model="form.displayName" maxlength="64" placeholder="请输入显示名" />
      </el-form-item>
      <el-form-item v-if="!user?.id" label="密码" prop="password">
        <el-input v-model="form.password" maxlength="64" placeholder="默认 admin123" />
      </el-form-item>
      <el-form-item label="角色" prop="roleIds">
        <el-checkbox-group v-model="form.roleIds">
          <el-checkbox
            v-for="item in roles"
            :key="item.id"
            :value="item.id"
            :disabled="item.code === 'admin' && adminLocked"
          >
            {{ item.name }}{{ item.code === 'admin' ? '（仅限一人）' : '' }}
          </el-checkbox>
        </el-checkbox-group>
        <div class="hint">所属分组：{{ groupText }}。权限只来自勾选的角色。</div>
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
  import { listHandlerGroups } from '@/api/group';
  import { createUser, updateUser } from '@/api/userRole';

  const props = defineProps({
    modelValue: Boolean,
    user: { type: Object, default: null }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const formRef = ref(null);
  const saving = ref(false);
  const roles = ref([]);
  const groups = ref([]);
  const form = reactive({
    username: '',
    displayName: '',
    password: 'admin123',
    roleIds: []
  });
  const rules = {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    displayName: [{ required: true, message: '请输入显示名', trigger: 'blur' }]
  };

  const adminLocked = computed(() => {
    const adminRole = roles.value.find((item) => item.code === 'admin');
    if (!adminRole) return false;
    const ownsAdmin = (props.user?.roles || []).some((item) => item.code === 'admin');
    return !ownsAdmin;
  });

  const groupText = computed(() => {
    const selected = new Set(form.roleIds);
    const names = groups.value
      .filter((group) => (group.roleIds || []).some((id) => selected.has(id)))
      .map((group) => group.name);
    return names.length ? names.join('、') : '未分组';
  });

  const load = async () => {
    form.username = props.user?.username || '';
    form.displayName = props.user?.displayName || '';
    form.password = props.user?.id ? '' : 'admin123';
    form.roleIds = (props.user?.roles || []).map((item) => item.id);
    const [roleData, groupData] = await Promise.all([
      pageRoles({ page: 1, pageSize: 200 }),
      listHandlerGroups().catch(() => [])
    ]);
    roles.value = roleData.records || [];
    groups.value = groupData || [];
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
      if (props.user?.id) {
        await updateUser(props.user.id, {
          displayName: form.displayName,
          roleIds: form.roleIds,
          status: props.user.status ?? 1
        });
      } else {
        await createUser({
          username: form.username,
          displayName: form.displayName,
          password: form.password || 'admin123',
          roleIds: form.roleIds
        });
      }
      EleMessage.success(props.user?.id ? '保存成功' : '创建成功，默认密码为 admin123');
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
