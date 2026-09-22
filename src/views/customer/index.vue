<template>
  <ele-page>
    <ele-card class="search-card" :body-style="{ padding: '16px 20px' }">
      <div class="search-row">
        <div class="search-item">
          <span class="search-label">客户名称</span>
          <el-input
            v-model="query.name"
            clearable
            placeholder="请输入客户名称"
            @keyup.enter="search"
          />
        </div>
        <div class="search-item">
          <span class="search-label">联系人</span>
          <el-input
            v-model="query.contact"
            clearable
            placeholder="请输入联系人"
            @keyup.enter="search"
          />
        </div>
        <div class="search-item">
          <span class="search-label">状态</span>
          <el-select
            v-model="query.status"
            clearable
            placeholder="请选择状态"
            style="width: 100%"
          >
            <el-option label="启用" :value="1" />
            <el-option label="停用" :value="0" />
          </el-select>
        </div>
        <div class="search-btns">
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </div>
      </div>
    </ele-card>

    <ele-card
      class="table-card"
      :body-style="{
        paddingTop: '20px',
        minHeight: 'calc(100vh - 210px)'
      }"
    >
      <el-button class="create-btn" type="primary" @click="openEdit()">
        新建客户
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
        <template #status="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '启用' : '停用' }}
          </el-tag>
        </template>
        <template #action="{ row }">
          <div class="table-actions">
            <el-link type="primary" :underline="false" @click="openEdit(row)">
              编辑
            </el-link>
            <el-link
              type="primary"
              :underline="false"
              @click="openTickets(row)"
            >
              历史工单
            </el-link>
          </div>
        </template>
      </ele-pro-table>
    </ele-card>
    <CustomerEditDrawer
      v-model="editVisible"
      :customer-id="editingId"
      @done="reload"
    />
    <CustomerTicketsDrawer
      v-model="ticketsVisible"
      :customer-id="ticketCustomerId"
      :customer-name="ticketCustomerName"
    />
  </ele-page>
</template>

<script setup>
  import { reactive, ref } from 'vue';
  import { pageCustomers } from '@/api/customer';
  import CustomerEditDrawer from './components/customer-edit-drawer.vue';
  import CustomerTicketsDrawer from './components/customer-tickets-drawer.vue';

  const tableRef = ref(null);
  const editVisible = ref(false);
  const editingId = ref(null);
  const ticketsVisible = ref(false);
  const ticketCustomerId = ref(null);
  const ticketCustomerName = ref('');
  const query = reactive({
    name: '',
    contact: '',
    status: undefined
  });

  const columns = [
    { prop: 'name', label: '名称', minWidth: 140 },
    { prop: 'contactName', label: '联系人', minWidth: 100 },
    { prop: 'phone', label: '电话', minWidth: 130 },
    { prop: 'email', label: '邮箱', minWidth: 180 },
    { prop: 'industry', label: '所属行业', minWidth: 120 },
    { prop: 'userName', label: '登录账号', minWidth: 120 },
    { prop: 'status', label: '状态', width: 90, slot: 'status' },
    { columnKey: 'action', label: '操作', width: 160, slot: 'action', fixed: 'right' }
  ];

  const datasource = async ({ page, limit, where }) => {
    const params = {
      page,
      pageSize: limit,
      name: where?.name || '',
      contact: where?.contact || ''
    };
    if (where?.status === 0 || where?.status === 1) {
      params.status = where.status;
    }
    return pageCustomers(params);
  };

  const currentWhere = () => ({
    name: query.name,
    contact: query.contact,
    status: query.status
  });

  const search = () => {
    tableRef.value?.reload?.({ page: 1, where: currentWhere() });
  };

  const resetSearch = () => {
    query.name = '';
    query.contact = '';
    query.status = undefined;
    tableRef.value?.reload?.({ page: 1, where: currentWhere() });
  };

  const reload = () => tableRef.value?.reload?.();

  const openEdit = (row) => {
    editingId.value = row?.id ?? null;
    editVisible.value = true;
  };

  const openTickets = (row) => {
    ticketCustomerId.value = row.id;
    ticketCustomerName.value = row.name || '';
    ticketsVisible.value = true;
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
  .search-label {
    flex: none;
    color: var(--el-text-color-regular);
    font-size: 14px;
    white-space: nowrap;
  }
  .search-btns {
    margin-left: auto;
    display: flex;
    align-items: center;
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
