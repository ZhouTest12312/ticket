<template>
  <ele-page>
    <ele-card class="search-card" :body-style="{ padding: '16px 20px' }">
      <div class="search-row">
        <div class="search-item">
          <span class="search-label">用户</span>
          <el-input
            v-model="query.keyword"
            clearable
            placeholder="用户名或显示名"
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
      <el-button v-if="canWrite" class="create-btn" type="primary" @click="openEdit()">
        新建用户
      </el-button>
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
        <template #groups="{ row }">
          {{ (row.groups || []).map((item) => item.name).join('、') || '-' }}
        </template>
        <template #action="{ row }">
          <el-link v-if="canWrite" type="primary" :underline="false" @click="openEdit(row)">
            修改
          </el-link>
        </template>
      </ele-pro-table>
    </ele-card>
    <UserEditDrawer v-model="editVisible" :user="editing" @done="reload" />
  </ele-page>
</template>

<script setup>
  import { computed, reactive, ref } from 'vue';
  import { useUserStore } from '@/store/modules/user';
  import { pageUsers } from '@/api/userRole';
  import UserEditDrawer from './components/user-edit-drawer.vue';

  const userStore = useUserStore();
  const canWrite = computed(() => (userStore.authorities || []).includes('user:write'));
  const tableRef = ref(null);
  const editVisible = ref(false);
  const editing = ref(null);
  const query = reactive({ keyword: '' });
  const columns = [
    { prop: 'username', label: '用户名', minWidth: 120 },
    { prop: 'displayName', label: '显示名', minWidth: 120 },
    { prop: 'roles', label: '角色', minWidth: 180, slot: 'roles' },
    { prop: 'groups', label: '所属分组', minWidth: 160, slot: 'groups' },
    { columnKey: 'action', label: '操作', width: 90, slot: 'action' }
  ];

  const datasource = ({ page, limit, where }) =>
    pageUsers({
      page,
      pageSize: limit,
      keyword: where?.keyword ?? ''
    });

  const search = () => tableRef.value?.reload?.({ page: 1, where: { keyword: query.keyword } });
  const resetSearch = () => {
    query.keyword = '';
    tableRef.value?.reload?.({ page: 1, where: { keyword: '' } });
  };
  const reload = () => tableRef.value?.reload?.();
  const openEdit = (row) => {
    editing.value = row || null;
    editVisible.value = true;
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
</style>
