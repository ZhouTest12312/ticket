<template>
  <ele-page>
    <ele-card
      :body-style="{
        paddingTop: '20px',
        minHeight: 'calc(100vh - 130px)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between'
      }"
    >
      <ele-pro-table
        ref="tableRef"
        row-key="id"
        :columns="columns"
        :datasource="datasource"
        :tools="false"
        :border="true"
        :sticky="true"
        :response="{ dataName: 'records', countName: 'total' }"
        :pagination="{ style: { margin: '0 0 0 auto' }, size: 'small' }"
      >
        <template #toolbar>
          <div class="toolbar-actions">
            <el-button v-if="canWrite" type="primary" @click="openEdit()">
              新建角色
            </el-button>
          </div>
        </template>
        <template #isSystem="{ row }">
          {{ row.isSystem ? '是' : '否' }}
        </template>
        <template #action="{ row }">
          <div class="table-actions">
            <el-link
              v-if="canWrite"
              type="primary"
              :underline="false"
              @click="openEdit(row)"
            >
              编辑
            </el-link>
            <el-link
              v-if="canWrite && !row.isSystem"
              type="danger"
              :underline="false"
              @click="handleDelete(row)"
            >
              删除
            </el-link>
            <el-tooltip
              v-else-if="canWrite && row.isSystem"
              content="系统角色不可删除"
              placement="top"
            >
              <span class="action-disabled">删除</span>
            </el-tooltip>
          </div>
        </template>
      </ele-pro-table>
    </ele-card>
    <RoleEditDrawer
      v-model="drawerVisible"
      :role-id="editingId"
      @done="reload"
    />
  </ele-page>
</template>

<script setup>
  import { computed, ref } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { ElMessageBox } from 'element-plus/es';
  import { useUserStore } from '@/store/modules/user';
  import { deleteRole, pageRoles } from '@/api/role';
  import RoleEditDrawer from './components/role-edit-drawer.vue';

  const userStore = useUserStore();
  const canWrite = computed(() =>
    (userStore.authorities || []).includes('role:write')
  );

  const tableRef = ref(null);
  const drawerVisible = ref(false);
  const editingId = ref(null);

  const columns = [
    { prop: 'name', label: '名称', minWidth: 120 },
    { prop: 'code', label: '编码', minWidth: 120 },
    { prop: 'isSystem', label: '系统角色', width: 100, slot: 'isSystem' },
    { prop: 'description', label: '描述', minWidth: 180 },
    { columnKey: 'action', label: '操作', width: 140, slot: 'action', fixed: 'right' }
  ];

  const datasource = async ({ page, limit, where }) => {
    return pageRoles({
      page,
      pageSize: limit,
      keyword: where?.keyword || ''
    });
  };

  const openEdit = (row) => {
    editingId.value = row?.id ?? null;
    drawerVisible.value = true;
  };

  const reload = () => tableRef.value?.reload?.();

  const handleDelete = async (row) => {
    try {
      await ElMessageBox.confirm(`确定删除角色「${row.name}」吗？`, '提示', {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      });
    } catch {
      return;
    }
    try {
      await deleteRole(row.id);
      EleMessage.success('删除成功');
      reload();
    } catch (e) {
      EleMessage.error(e?.message || '删除失败');
    }
  };
</script>

<style scoped lang="scss">
  .el-button + .el-button {
    margin-left: 0 !important;
  }
  .toolbar-actions {
    display: flex;
    gap: 8px;
  }
  .table-actions {
    display: inline-flex;
    align-items: center;
    flex-wrap: wrap;
  }
  .table-actions :deep(.el-link:not(:first-child)) {
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid var(--el-border-color);
  }
  .action-disabled {
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid var(--el-border-color);
    color: var(--el-text-color-disabled);
    font-size: 14px;
    cursor: not-allowed;
    user-select: none;
  }
</style>
