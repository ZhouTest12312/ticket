<template>
  <ele-drawer
    :model-value="modelValue"
    :title="title"
    size="760px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="drawer-search">
      <el-input
        v-model="query.name"
        clearable
        placeholder="请输入名称"
        @keyup.enter="search"
      />
      <el-select v-model="query.status" clearable placeholder="状态">
        <el-option label="启用" :value="1" />
        <el-option label="停用" :value="0" />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>
    <el-button class="create-btn" type="primary" @click="openEdit()">
      新建字典项
    </el-button>
    <ele-pro-table
      v-if="typeCode"
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
          <el-link type="danger" :underline="false" @click="handleDelete(row)">
            删除
          </el-link>
        </div>
      </template>
    </ele-pro-table>
    <DictEditDrawer
      v-model="editVisible"
      :item-id="editingId"
      :type-code="typeCode"
      @done="reload"
    />
  </ele-drawer>
</template>

<script setup>
  import { computed, reactive, ref } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { ElMessageBox } from 'element-plus/es';
  import { deleteDictItem, pageDictItems } from '@/api/dict';
  import DictEditDrawer from './dict-edit-drawer.vue';

  const props = defineProps({
    modelValue: Boolean,
    typeCode: { type: String, default: '' },
    typeName: { type: String, default: '' }
  });
  const emit = defineEmits(['update:modelValue']);

  const title = computed(() =>
    props.typeName ? `${props.typeName} - 字典项` : '字典项'
  );
  const tableRef = ref(null);
  const editVisible = ref(false);
  const editingId = ref(null);
  const query = reactive({
    name: '',
    status: undefined
  });

  const columns = [
    { prop: 'name', label: '名称', minWidth: 160 },
    { prop: 'sort', label: '排序', width: 90 },
    { prop: 'status', label: '状态', width: 100, slot: 'status' },
    { columnKey: 'action', label: '操作', width: 140, slot: 'action' }
  ];

  const currentWhere = () => ({
    name: query.name,
    status: query.status
  });

  const datasource = async ({ page, limit, where }) => {
    return pageDictItems({
      page,
      pageSize: limit,
      typeCode: props.typeCode,
      name: where?.name || '',
      status: where?.status
    });
  };

  const search = () => {
    tableRef.value?.reload?.({ page: 1, where: currentWhere() });
  };

  const resetSearch = () => {
    query.name = '';
    query.status = undefined;
    tableRef.value?.reload?.({ page: 1, where: currentWhere() });
  };

  const reload = () => tableRef.value?.reload?.();

  const openEdit = (row) => {
    editingId.value = row?.id ?? null;
    editVisible.value = true;
  };

  const handleDelete = (row) => {
    ElMessageBox.confirm(`确定删除「${row.name}」吗？`, '系统提示', {
      type: 'warning',
      draggable: true
    })
      .then(async () => {
        await deleteDictItem(row.id);
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
  .drawer-search {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }
  .drawer-search .el-input,
  .drawer-search .el-select {
    width: 180px;
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
