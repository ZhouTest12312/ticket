<template>
  <ele-page>
    <ele-card class="search-card" :body-style="{ padding: '16px 20px' }">
      <div class="search-row">
        <div class="search-item">
          <span class="search-label">工单号</span>
          <el-input
            v-model="query.ticketNo"
            clearable
            placeholder="请输入工单号"
            @keyup.enter="search"
          />
        </div>
        <div class="search-item">
          <span class="search-label">工单标题</span>
          <el-input
            v-model="query.keyword"
            clearable
            placeholder="问题标题"
            @keyup.enter="search"
          />
        </div>
        <div class="search-item">
          <span class="search-label">工单状态</span>
          <el-select v-model="query.status" clearable placeholder="全部状态" style="width: 100%">
            <el-option
              v-for="item in options.statuses"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </div>
        <div class="search-item">
          <span class="search-label">优先级</span>
          <el-select v-model="query.priorityId" clearable placeholder="全部优先级" style="width: 100%">
            <el-option
              v-for="item in options.priorities"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </div>
        <div class="search-item">
          <span class="search-label">处理人</span>
          <el-select v-model="query.assigneeId" clearable filterable placeholder="全部处理人" style="width: 100%">
            <el-option
              v-for="item in options.users"
              :key="item.id"
              :label="personLabel(item)"
              :value="item.id"
            />
          </el-select>
        </div>
        <div class="search-item">
          <span class="search-label">时限</span>
          <el-select v-model="query.overdue" clearable placeholder="全部" style="width: 100%">
            <el-option label="即将超时" :value="2" />
            <el-option label="已超时" :value="1" />
          </el-select>
        </div>
        <div class="search-btns">
          <el-button type="primary" @click="search">查询</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </div>
      </div>
    </ele-card>

    <ele-card :body-style="{ paddingTop: '16px', minHeight: 'calc(100vh - 260px)' }">
      <el-button v-if="canCreateTicket" class="create-btn" type="primary" @click="openCreate">
        新建工单
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
        <template #title="{ row }">
          <el-link type="primary" :underline="false" @click="openDetail(row)">
            {{ row.title }}
          </el-link>
        </template>
        <template #status="{ row }">
          <ele-dot v-bind="statusDot(row.status)" :text="row.statusLabel" />
          <el-tag
            v-if="row.slaState === 'overdue' && row.status !== 'overdue'"
            class="sla-tag"
            type="danger"
            size="small"
          >
            已超时
          </el-tag>
          <el-tag v-else-if="row.slaState === 'warning'" class="sla-tag" type="warning" size="small">
            即将超时
          </el-tag>
          <el-tag v-if="row.pendingConfirm" class="sla-tag" type="info" size="small">待确认</el-tag>
          <el-tag v-if="row.followedUp" class="sla-tag" type="success" size="small">已回访</el-tag>
        </template>
        <template #duration="{ row }">
          <span>{{ row.durationText || '-' }}</span>
        </template>
        <template #wait="{ row }">
          <span v-if="row.status === 'processing' || !row.waitText">-</span>
          <span v-else :class="{ 'countdown-danger': row.waitLevel === 'danger' }">
            {{ row.waitText }}
          </span>
        </template>
        <template #owner="{ row }">
          {{ row.assigneeName || '未分派' }}
        </template>
        <template #collaborators="{ row }">
          {{ row.collaboratorNames || '-' }}
        </template>
        <template #action="{ row }">
          <div class="table-actions">
            <el-link
              v-for="item in outerActions(row)"
              :key="item.key"
              type="primary"
              :underline="false"
              @click="onCommand(row, item.key)"
            >
              {{ item.label }}
            </el-link>
            <el-dropdown
              v-if="menuActions(row).length"
              class="more-dropdown"
              trigger="click"
              @command="(command) => onCommand(row, command)"
            >
              <el-link class="more-link" type="primary" :underline="false">更多</el-link>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="item in menuActions(row)"
                    :key="item.key"
                    :command="item.key"
                  >
                    {{ item.label }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </template>
      </ele-pro-table>
    </ele-card>

    <TicketDetailDrawer
      v-model="detailVisible"
      :ticket-id="detailId"
      :records-only="detailRecords"
    />
    <TicketHandleDrawer
      v-model="handleVisible"
      :ticket-id="handleTicketId"
      :continued="handleContinued"
      @done="reload"
    />
    <TicketActionDrawer
      v-model="actionVisible"
      :ticket-id="actionTicketId"
      :action="actionKey"
      @done="reload"
    />
    <TicketEditDrawer v-model="editVisible" :ticket-id="editId" @done="reload" />
  </ele-page>
</template>

<script setup>
  import { computed, onMounted, reactive, ref } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { useUserStore } from '@/store/modules/user';
  import { pageTickets, changeTicketStatus, ticketOptions, refreshTicketMenuBadge } from '@/api/ticket';
  import { statusDot } from './status-dot';
  import TicketDetailDrawer from './components/ticket-detail-drawer.vue';
  import TicketHandleDrawer from './components/ticket-handle-drawer.vue';
  import TicketActionDrawer from './components/ticket-action-drawer.vue';
  import TicketEditDrawer from './components/ticket-edit-drawer.vue';

  const userStore = useUserStore();

  const tableRef = ref(null);
  const detailVisible = ref(false);
  const detailRecords = ref(false);
  const detailId = ref(null);
  const actionVisible = ref(false);
  const actionTicketId = ref(null);
  const actionKey = ref('');
  const handleVisible = ref(false);
  const handleTicketId = ref(null);
  const handleContinued = ref(false);
  const editVisible = ref(false);
  const editId = ref(null);
  const personLabel = (item) => {
    const groups = (item.groupNames || []).filter(Boolean);
    return groups.length ? `${item.name}（${groups.join('、')}）` : item.name;
  };
  const options = reactive({ statuses: [], priorities: [], users: [] });
  const query = reactive({
    keyword: '',
    ticketNo: '',
    status: '',
    priorityId: undefined,
    assigneeId: undefined,
    overdue: undefined
  });

  const searchedStatus = ref('');
  const pageStatuses = ref([]);
  const actionWidth = ref(120);

  const measureActionWidth = (labelGroups) => {
    const widthOf = (labels) => {
      const text = labels.reduce((sum, label) => sum + [...label].length * 14, 0);
      const gaps = Math.max(labels.length - 1, 0) * 17;
      return text + gaps + 32;
    };
    return Math.max(72, ...labelGroups.map(widthOf));
  };

  const columns = computed(() => {
    const cols = [
      { prop: 'ticketNo', label: '工单号', minWidth: 150 },
      { prop: 'title', label: '工单标题', minWidth: 160, slot: 'title' },
      { prop: 'customerName', label: '客户', minWidth: 120 },
      { prop: 'categoryName', label: '分类', width: 110 },
      { prop: 'priorityName', label: '优先级', width: 90 },
      { prop: 'status', label: '工单状态', minWidth: 150, slot: 'status' },
      { prop: 'statusChangedAt', label: '状态变化时间', minWidth: 160 },
      { prop: 'durationText', label: '处理时长', minWidth: 160, slot: 'duration' },
      { prop: 'waitText', label: '响应倒计时', minWidth: 160, slot: 'wait' },
      { prop: 'assigneeName', label: '当前负责人', minWidth: 110, slot: 'owner' },
      { prop: 'collaboratorNames', label: '协作者', minWidth: 120, slot: 'collaborators' },
      { prop: 'creatorName', label: '创建人', minWidth: 100 },
      { prop: 'sourceLabel', label: '来源', minWidth: 110 },
      { prop: 'createdAt', label: '创建时间', minWidth: 160 },
      { prop: 'updatedAt', label: '更新时间', minWidth: 160 },
      {
        columnKey: 'action',
        label: '操作',
        width: actionWidth.value,
        slot: 'action',
        fixed: 'right',
        showOverflowTooltip: false
      }
    ];
    const onlyProcessing =
      pageStatuses.value.length > 0 &&
      pageStatuses.value.every((status) => status === 'processing');
    if (searchedStatus.value === 'processing' || onlyProcessing) {
      return cols.filter((col) => col.prop !== 'waitText');
    }
    return cols;
  });

  const datasource = async ({ page, limit, where }) => {
    const params = {
      page,
      pageSize: limit,
      keyword: where?.keyword || '',
      ticketNo: where?.ticketNo || '',
      status: where?.status || ''
    };
    if (where?.priorityId) params.priorityId = where.priorityId;
    if (where?.assigneeId) params.assigneeId = where.assigneeId;
    if (where?.overdue) params.overdue = where.overdue;
    const data = await pageTickets(params);
    const records = data?.records || [];
    pageStatuses.value = records.map((item) => item.status);
    const nextWidth = measureActionWidth(
      records.map((row) => {
        const labels = outerActions(row).map((item) => item.label);
        if (menuActions(row).length) labels.push('更多');
        return labels;
      })
    );
    if (actionWidth.value !== nextWidth) actionWidth.value = nextWidth;
    return data;
  };

  const currentWhere = () => ({ ...query });

  const search = () => {
    searchedStatus.value = query.status || '';
    tableRef.value?.reload?.({ page: 1, where: currentWhere() });
  };

  const resetSearch = () => {
    query.keyword = '';
    query.ticketNo = '';
    query.status = '';
    query.priorityId = undefined;
    query.assigneeId = undefined;
    query.overdue = undefined;
    search();
  };

  const reload = () => {
    tableRef.value?.reload?.();
    refreshTicketMenuBadge();
  };

  const openDetail = (row, records = false) => {
    detailId.value = row.id;
    detailRecords.value = records;
    detailVisible.value = true;
  };

  const isAdmin = computed(() => (userStore.roles || []).includes('admin'));
  const canCreateTicket = computed(
    () =>
      isAdmin.value ||
      (userStore.roles || []).includes('cs') ||
      (userStore.authorities || []).includes('ticket:create')
  );
  const canFollowup = computed(
    () =>
      isAdmin.value ||
      (userStore.roles || []).includes('cs') ||
      (userStore.authorities || []).includes('ticket:followup')
  );
  const currentUserId = computed(() => userStore.info?.userId);
  const isOwner = (row) => row.assigneeId && row.assigneeId === currentUserId.value;
  const isManager = (row) => isAdmin.value || isOwner(row);
  const isCollaborator = (row) => (row.collaboratorIds || []).includes(currentUserId.value);
  const collaboratorOnly = (row) => isCollaborator(row) && !isAdmin.value && !isOwner(row);

  const rowActions = (row) => {
    const status = row.status === 'overdue' ? 'processing' : row.status;
    const items = [{ key: 'view', label: '查看' }];
    if (status === 'unassigned' && isAdmin.value) {
      items.push({ key: 'edit', label: '编辑' }, { key: 'assign', label: '派发' });
    }
    if (status === 'pending' && isManager(row)) {
      items.push(
        { key: 'start', label: '开始处理' },
        { key: 'transfer', label: '转派' },
        { key: 'collab', label: '添加协作者' }
      );
    }
    if (['processing', 'reopened'].includes(status)) {
      if (isManager(row)) {
        items.push(
          { key: 'processing', label: '继续处理' },
          { key: 'transfer', label: '转派' },
          { key: 'collab', label: '添加协作者' },
          { key: 'waiting', label: '标记等待客户' },
          { key: 'resolved', label: '标记已解决' }
        );
      } else if (collaboratorOnly(row)) {
        items.push({ key: 'processing', label: '继续处理' });
      }
    }
    if (status === 'waiting_customer' && (isManager(row) || collaboratorOnly(row))) {
      items.push({ key: 'processing', label: '继续处理' });
    }
    if (status === 'closed' && canFollowup.value) {
      items.push({ key: 'followup', label: '回访' });
    }
    return items;
  };

  const outerActions = (row) => {
    const items = rowActions(row);
    if (items.length <= 3) {
      return items;
    }
    return items.filter((item) => item.key === 'view');
  };

  const menuActions = (row) => {
    const items = rowActions(row);
    if (items.length <= 3) {
      return [];
    }
    return items.filter((item) => item.key !== 'view');
  };

  const openCreate = () => {
    editId.value = null;
    editVisible.value = true;
  };

  const openEdit = (row) => {
    editId.value = row.id;
    editVisible.value = true;
  };

  const openHandle = (row) => {
    handleTicketId.value = row.id;
    handleContinued.value = true;
    handleVisible.value = true;
  };

  const onCommand = async (row, command) => {
    try {
      if (command === 'view') {
        openDetail(row, false);
        return;
      }
      if (command === 'edit') {
        openEdit(row);
        return;
      }
      if (command === 'processing') {
        openHandle(row);
        return;
      }
      if (command === 'start') {
        await changeTicketStatus(row.id, 'processing');
        EleMessage.success('已开始处理');
        reload();
        return;
      }
      if (command === 'waiting') {
        await changeTicketStatus(row.id, 'waiting_customer');
        EleMessage.success('已标记等待客户');
        reload();
        return;
      }
      if (command === 'resolved') {
        await changeTicketStatus(row.id, 'resolved');
        EleMessage.success('已标记解决');
        reload();
        return;
      }
    } catch (e) {
      EleMessage.error(e.message || '操作失败');
      return;
    }
    actionTicketId.value = row.id;
    actionKey.value = command;
    actionVisible.value = true;
  };

  onMounted(async () => {
    refreshTicketMenuBadge();
    try {
      const data = await ticketOptions();
      options.statuses = data.statuses || [];
      options.priorities = data.priorities || [];
      options.users = data.users || [];
    } catch (e) {
      EleMessage.error(e.message || '加载筛选项失败');
    }
  });
</script>

<style scoped>
  .search-card {
    margin-bottom: 12px;
  }
  .search-row {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px 16px;
    align-items: center;
  }
  .search-item {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }
  .search-item :deep(.el-input),
  .search-item :deep(.el-select) {
    flex: 1;
    min-width: 0;
  }
  .search-label {
    flex: none;
    color: var(--el-text-color-regular);
    font-size: 14px;
    white-space: nowrap;
  }
  .search-btns {
    grid-column: 4;
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }
  .work-tag {
    cursor: pointer;
  }
  .sla-tag {
    margin-left: 6px;
  }
  .countdown-danger {
    color: var(--el-color-danger);
  }
  .el-button + .el-button {
    margin-left: 0 !important;
  }
  :deep(.el-link + .el-link) {
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid var(--el-border-color);
  }
  .create-btn {
    margin-bottom: 12px;
  }
  .table-actions {
    display: inline-flex;
    align-items: center;
    flex-wrap: nowrap;
    white-space: nowrap;
    width: max-content;
  }
  .table-actions > :not(:first-child) {
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid var(--el-border-color);
  }
  :deep(.el-table__cell:has(.table-actions) .cell) {
    overflow: visible;
    white-space: nowrap;
  }
  .table-actions :deep(.more-dropdown) {
    display: inline-flex;
    align-items: center;
    font-size: 14px;
    line-height: 24px;
    vertical-align: middle;
  }
  .table-actions :deep(.more-link) {
    font-size: 14px;
    line-height: 24px;
    height: 24px;
  }
</style>
