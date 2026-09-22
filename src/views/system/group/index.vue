<template>
  <ele-page>
    <ele-card class="search-card" :body-style="{ padding: '16px 20px' }">
      <div class="search-row">
        <div class="search-item">
          <span class="search-label">分组名称</span>
          <el-input
            v-model="query.name"
            clearable
            placeholder="请输入分组名称"
            @keyup.enter="search"
          />
        </div>
        <div class="search-btns">
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </div>
      </div>
    </ele-card>
    <ele-card class="table-card" :body-style="{ paddingTop: '20px', minHeight: 'calc(100vh - 210px)' }">
      <el-button class="create-btn" type="primary" @click="openEdit()">新建分组</el-button>
      <ele-pro-table
        ref="tableRef"
        row-key="id"
        :columns="columns"
        :datasource="datasource"
        :toolbar="false"
        :tools="false"
        :border="true"
        :response="{ dataName: 'records', countName: 'total' }"
        :pagination="{ style: { margin: '0 0 0 auto' }, size: 'small' }"
      >
        <template #roles="{ row }">
          {{ (row.roles || []).map((item) => item.name).join('、') || '-' }}
        </template>
        <template #leader="{ row }">
          {{ row.name === '管理组' ? '-' : row.leaderName || '-' }}
        </template>
        <template #action="{ row }">
          <div class="table-actions">
            <el-link type="primary" :underline="false" @click="openEdit(row)">修改</el-link>
            <el-link
              v-if="row.name !== '管理组'"
              type="danger"
              :underline="false"
              @click="handleDelete(row)"
            >
              删除
            </el-link>
          </div>
        </template>
      </ele-pro-table>
    </ele-card>
    <GroupEditDrawer v-model="editVisible" :group="editing" @done="reload" />
  </ele-page>
</template>

<script setup>
  import { reactive, ref } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { ElMessageBox } from 'element-plus/es';
  import { deleteHandlerGroup, listHandlerGroups } from '@/api/group';
  import GroupEditDrawer from './components/group-edit-drawer.vue';

  const tableRef = ref(null);
  const editVisible = ref(false);
  const editing = ref(null);
  const query = reactive({ name: '' });
  const columns = [
    { prop: 'index', label: '序号', width: 70, align: 'center' },
    { prop: 'name', label: '分组名称', minWidth: 140 },
    { prop: 'roles', label: '包含角色', minWidth: 180, slot: 'roles' },
    { prop: 'leaderName', label: '负责人', minWidth: 120, slot: 'leader' },
    { columnKey: 'action', label: '操作', width: 140, slot: 'action' }
  ];

  const datasource = async ({ page, limit, where }) => {
    const all = await listHandlerGroups();
    const keyword = String(where?.name || '').trim();
    const filtered = (all || []).filter(
      (item) => !keyword || String(item.name || '').includes(keyword)
    );
    const start = Math.max(page - 1, 0) * limit;
    return {
      records: filtered.slice(start, start + limit).map((item, offset) => ({
        ...item,
        index: start + offset + 1
      })),
      total: filtered.length
    };
  };

  const search = () => tableRef.value?.reload?.({ page: 1, where: { name: query.name } });
  const resetSearch = () => {
    query.name = '';
    tableRef.value?.reload?.({ page: 1, where: { name: '' } });
  };
  const reload = () => tableRef.value?.reload?.();
  const openEdit = (row) => {
    editing.value = row || null;
    editVisible.value = true;
  };
  const handleDelete = (row) => {
    ElMessageBox.confirm(`确定删除分组「${row.name}」吗？`, '提示', { type: 'warning' })
      .then(async () => {
        await deleteHandlerGroup(row.id);
        EleMessage.success('删除成功');
        reload();
      })
      .catch((e) => {
        if (e === 'cancel' || e === 'close') return;
        EleMessage.error(e.message || '删除失败');
      });
  };
</script>

<style scoped>
  .search-card {
    margin-bottom: 12px;
  }
  .search-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 12px 16px;
  }
  .search-item {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1 1 220px;
    min-width: 220px;
    max-width: 360px;
  }
  .search-item :deep(.el-input) {
    flex: 1;
  }
  .search-label {
    flex: none;
    color: var(--el-text-color-regular);
    font-size: 14px;
    white-space: nowrap;
  }
  .search-btns {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
  .create-btn {
    margin-bottom: 12px;
  }
  .el-button + .el-button {
    margin-left: 0 !important;
  }
  .table-actions {
    display: inline-flex;
    align-items: center;
  }
  .table-actions :deep(.el-link:not(:first-child)) {
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid var(--el-border-color);
  }
</style>
