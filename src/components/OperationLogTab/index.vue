<template>
  <div class="operation-log-tab">
    <div class="filter-toolbar">
      <div class="filter-left">
        <span class="filter-label">操作日期</span>
        <el-date-picker
          v-model="dateRange"
          class="filter-date"
          type="daterange"
          unlink-panels
          range-separator="~"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :teleported="true"
          :popper-class="datePopperClass"
          clearable
          @change="handleFilterChange"
        />
      </div>
      <div class="filter-right">
        <span class="filter-label">排序</span>
        <el-select
          v-model="sortOrder"
          class="filter-sort"
          @change="handleFilterChange"
        >
          <el-option
            v-for="opt in sortOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>
    </div>

    <div v-loading="loading" class="timeline-panel">
      <el-timeline v-if="logs.length" class="log-timeline">
        <el-timeline-item
          v-for="(item, index) in logs"
          :key="`${item.time}-${index}`"
          :timestamp="formatLogTime(item.time)"
          placement="top"
          type="primary"
          hollow
        >
          <div class="log-card">
            <div class="log-summary">{{ item.summaryLine || item.text }}</div>
            <div
              v-for="(line, lineIdx) in visibleDetailLines(item)"
              :key="lineIdx"
              class="log-detail-line"
            >
              {{ line }}
            </div>
            <el-link
              v-if="item.hiddenDetailCount > 0 && !expandedMap[index]"
              :underline="false"
              type="primary"
              class="expand-link"
              @click="toggleExpand(index)"
            >
              展开更多（{{ item.hiddenDetailCount }}）
            </el-link>
            <el-link
              v-if="item.hiddenDetailCount > 0 && expandedMap[index]"
              :underline="false"
              type="primary"
              class="expand-link"
              @click="toggleExpand(index)"
            >
              收起
            </el-link>
          </div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else class="log-empty" description="暂无操作记录" />
    </div>
  </div>
</template>

<script setup>
  import { ref, watch, reactive } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';

  const props = defineProps({
    /** 加载日志：(params) => Promise<{ records, total }> */
    loadLogs: {
      type: Function,
      required: true
    },
    /** 实体 ID 变化时重新加载 */
    entityId: {
      type: String,
      default: ''
    },
    datePopperClass: {
      type: String,
      default: 'operation-log-date-popper'
    },
    pageSize: {
      type: Number,
      default: 100
    }
  });

  const dateRange = ref([]);
  const sortOrder = ref('desc');
  const sortOptions = [
    { label: '按创建时间由近及远', value: 'desc' },
    { label: '按创建时间由远及近', value: 'asc' }
  ];

  const loading = ref(false);
  const logs = ref([]);
  const expandedMap = reactive({});

  function formatLogTime(time) {
    if (!time) {
      return '';
    }
    return String(time).replace(/-/g, '/').slice(0, 19);
  }

  function visibleDetailLines(item) {
    const index = logs.value.indexOf(item);
    const lines = item.detailLines || [];
    if (item.hiddenDetailCount > 0 && !expandedMap[index]) {
      return lines.slice(0, Math.max(0, lines.length - item.hiddenDetailCount));
    }
    return lines;
  }

  function toggleExpand(index) {
    expandedMap[index] = !expandedMap[index];
  }

  async function fetchLogs() {
    if (!props.entityId) {
      logs.value = [];
      return;
    }
    loading.value = true;
    try {
      const res = await props.loadLogs({
        page: 1,
        size: props.pageSize,
        startDate: dateRange.value?.[0] || undefined,
        endDate: dateRange.value?.[1] || undefined,
        sortOrder: sortOrder.value
      });
      logs.value = res.records || [];
      Object.keys(expandedMap).forEach((k) => delete expandedMap[k]);
    } catch (e) {
      EleMessage.error(e.message || '加载操作记录失败');
      logs.value = [];
    } finally {
      loading.value = false;
    }
  }

  function handleFilterChange() {
    fetchLogs();
  }

  watch(
    () => props.entityId,
    () => {
      fetchLogs();
    },
    { immediate: true }
  );

  defineExpose({ reload: fetchLogs });
</script>

<style lang="scss" scoped>
  .operation-log-tab {
    padding: 0px 0 4px;
  }

  .filter-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding:0 0px 12px 0px;
    border-radius: 8px;
  }

  .filter-left,
  .filter-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .filter-label {
    flex-shrink: 0;
    font-size: 13px;
    color: #606266;
    line-height: 32px;
  }

  .filter-date {
    width: 260px;
  }

  .filter-sort {
    width: 180px;
  }

  .timeline-panel {
    min-height: 160px;
    padding: 0px 8px 8px 4px;
  }

  .log-timeline {
    padding-left: 2px;

    :deep(.el-timeline-item__timestamp) {
      margin-bottom: 8px;
      padding: 0 ;
      font-size: 13px;
      font-weight: 500;
      color: #909399;
      line-height: 20px;
    }

    :deep(.el-timeline-item__node) {
      width: 10px;
      height: 10px;
      left: 0;
      border-width: 2px;
    }

    :deep(.el-timeline-item__node--primary) {
      border-color: #0096ff;
    }

    :deep(.el-timeline-item__tail) {
      left: 4px;
      border-left-color: #d6e4ff;
    }

    :deep(.el-timeline-item__wrapper) {
      padding-left: 20px;
    }

    :deep(.el-timeline-item) {
      padding-bottom: 20px;
    }

    :deep(.el-timeline-item:last-child) {
      padding-bottom: 0;
    }
  }

  .log-card {
    background: #fff;
    border-radius: 8px;
    transition: border-color 0.2s, box-shadow 0.2s;

    &:hover {
      border-color: #d6e4ff;
      box-shadow: 0 2px 8px rgba(0, 150, 255, 0.06);
    }
  }

  .log-summary {
    font-size: 14px;
    line-height: 22px;
    color: #303133;
    word-break: break-all;
  }

  .log-detail-line {
    margin-top: 4px;
    font-size: 13px;
    line-height: 20px;
    color: #606266;
    word-break: break-all;
  }

  .expand-link {
    display: inline-block;
    margin-top: 6px;
    font-size: 13px;
  }

  .log-empty {
    padding: 32px 0;
  }
</style>

<style lang="scss">
  .operation-log-date-popper.el-picker__popper {
    border-radius: 8px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
    border: 1px solid #e4e7ed;

    .el-picker-panel {
      border-radius: 8px;
    }

    .el-date-range-picker {
      --el-datepicker-active-color: #0096ff;
      --el-datepicker-hover-text-color: #0096ff;
    }

    .el-date-table td.in-range .el-date-table-cell {
      background-color: #ecf5ff;
    }

    .el-date-table td.start-date .el-date-table-cell,
    .el-date-table td.end-date .el-date-table-cell {
      background-color: #0096ff;
    }
  }
</style>
