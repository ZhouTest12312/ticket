<template>
  <ele-drawer
    :model-value="modelValue"
    title="分配角色"
    size="420px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="user" class="user-line">
      用户：{{ user.displayName }}（{{ user.username }}）
    </div>
    <el-checkbox-group v-model="roleIds">
      <el-checkbox v-for="r in roleOptions" :key="r.id" :label="r.id">
        {{ r.name }} ({{ r.code }})
      </el-checkbox>
    </el-checkbox-group>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">
        保存
      </el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { pageRoles } from '@/api/role';
  import { assignUserRoles } from '@/api/userRole';

  const props = defineProps({
    modelValue: Boolean,
    user: { type: Object, default: null }
  });
  const emit = defineEmits(['update:modelValue', 'done']);

  const roleOptions = ref([]);
  const roleIds = ref([]);
  const saving = ref(false);

  watch(
    () => props.modelValue,
    async (v) => {
      if (!v) return;
      try {
        const data = await pageRoles({ page: 1, pageSize: 200 });
        roleOptions.value = data.records || [];
        roleIds.value = (props.user?.roles || []).map((r) => r.id);
      } catch (e) {
        EleMessage.error(e.message || '加载角色失败');
      }
    }
  );

  const submit = async () => {
    if (!props.user) return;
    saving.value = true;
    try {
      await assignUserRoles(props.user.id, roleIds.value);
      EleMessage.success('分配成功');
      emit('update:modelValue', false);
      emit('done');
    } catch (e) {
      EleMessage.error(e.message || '分配失败');
    } finally {
      saving.value = false;
    }
  };
</script>

<style scoped>
  .user-line {
    margin-bottom: 16px;
  }
</style>
