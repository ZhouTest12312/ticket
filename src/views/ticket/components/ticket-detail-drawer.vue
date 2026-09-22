<template>
  <ele-drawer
    :model-value="modelValue"
    :title="drawerTitle"
    size="860px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-loading="loading">
      <el-descriptions v-if="!recordsOnly" :column="2" border>
        <el-descriptions-item label="状态">
          <ele-dot v-bind="statusDot(detail.status)" :text="detail.statusLabel || '-'" />
          <el-tag
            v-if="detail.slaState === 'overdue' && detail.status !== 'overdue'"
            class="sla-tag"
            type="danger"
            size="small"
          >
            已超时
          </el-tag>
          <el-tag
            v-else-if="detail.slaState === 'warning'"
            class="sla-tag"
            type="warning"
            size="small"
          >
            即将超时
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前负责人">
          {{ detail.assigneeName || '未分派' }}
          <span v-if="detail.groupName"> / {{ detail.groupName }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态变化时间">
          {{ detail.statusChangedAt || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ detail.createdAt || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ detail.updatedAt || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="处理时限">
          {{ detail.deadline || '-' }}
          <span v-if="detail.slaHours">（{{ detail.slaHours }}小时）</span>
        </el-descriptions-item>
        <el-descriptions-item label="客户">{{ detail.customerName || '-' }}</el-descriptions-item>
        <el-descriptions-item label="分类 / 优先级">
          {{ detail.categoryName || '-' }} / {{ detail.priorityName || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="产品">{{ detail.product || '-' }}</el-descriptions-item>
        <el-descriptions-item label="订单">{{ detail.orderNo || '-' }}</el-descriptions-item>
        <el-descriptions-item label="具体服务">{{ detail.serviceName || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="showAssignedFields" label="期望完成">
          {{ detail.expectedFinishAt || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="showAssignedFields" label="预计解决">
          {{ detail.estimatedResolveAt || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="showAssignedFields" label="实际解决">
          {{ detail.actualResolveAt || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="showAssignedFields" label="解决结果" :span="2">
          {{ detail.resolution || '-' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="showAssignedFields" label="客户评价" :span="2">
          <div v-if="detail.rating" class="eval-block">
            <el-rate
              :model-value="detail.rating"
              disabled
              show-score
              score-template="{value} 星"
            />
            <div v-if="detail.evaluation && detail.evaluation !== '客户确认结案'">
              {{ detail.evaluation }}
            </div>
          </div>
          <span v-else>-</span>
        </el-descriptions-item>
        <template v-if="showFollowupFields">
          <el-descriptions-item label="回访状态">
            <el-tag v-if="detail.followedUp" type="success" size="small">已回访</el-tag>
            <span v-else>未回访</span>
          </el-descriptions-item>
          <el-descriptions-item label="回访时间">
            {{ detail.followupAt || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="回访人">
            {{ detail.followupUserName || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="回访方式">
            {{ detail.followupMethod || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="回访结果" :span="2">
            {{ detail.followupResult || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="回访备注" :span="2">
            {{ detail.followupRemark || '-' }}
          </el-descriptions-item>
        </template>
        <el-descriptions-item v-if="showAssignedFields" label="协作者" :span="2">
          {{ collaboratorText }}
        </el-descriptions-item>
        <el-descriptions-item label="问题描述" :span="2">
          {{ detail.description || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="!recordsOnly && mediaFiles.length" class="block">
        <div class="block-title">附件</div>
        <TicketMediaUpload
          readonly
          :ticket-id="ticketId"
          :model-value="mediaFiles"
        />
      </div>

      <div v-if="visibleLogs.length || !recordsOnly" class="block">
        <el-timeline v-if="visibleLogs.length" class="log-timeline">
          <el-timeline-item
            v-for="item in visibleLogs"
            :key="item.id"
            color="#1890ff"
            hide-timestamp
          >
            <div class="log-head">
              <span class="log-time">{{ item.timeText }}</span>
              <el-tag class="log-tag" size="small" effect="plain">{{ item.actionLabel }}</el-tag>
              <el-tag
                v-for="role in item.operatorRoles"
                :key="role"
                class="log-tag"
                size="small"
                effect="plain"
              >
                {{ role }}
              </el-tag>
            </div>
            <div class="log-grid">
              <div class="log-field">
                <span class="log-label">处理人：</span>
                <span class="log-person">{{ item.operatorName || '系统' }}</span>
              </div>
              <div class="log-field">
                <span class="log-label">处理人岗位：</span>
                <span class="log-value">{{ item.roleText }}</span>
              </div>
              <div class="log-field log-field-full">
                <span class="log-label">理由：</span>
                <span class="log-value">{{ item.content || '-' }}</span>
              </div>
              <div v-if="item.media" class="log-field log-field-full">
                <el-image
                  v-if="item.media.kind === 'image'"
                  class="log-image"
                  :src="item.media.url"
                  :preview-src-list="recordImages"
                  :initial-index="imageIndex(item.media.url)"
                  fit="cover"
                  preview-teleported
                />
                <video
                  v-else
                  class="log-image"
                  :src="item.media.url"
                  controls
                />
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <div v-else class="muted">暂无记录</div>
        <el-button v-if="hasMoreLogs" class="more-logs" link type="primary" @click="showMoreLogs">
          展示更多
        </el-button>
      </div>
    </div>
  </ele-drawer>
</template>

<script setup>
  import { computed, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { useUserStore } from '@/store/modules/user';
  import { getTicket } from '@/api/ticket';
  import { statusDot } from '../status-dot';
  import TicketMediaUpload from './ticket-media-upload.vue';

  const props = defineProps({
    modelValue: Boolean,
    ticketId: { type: [Number, null], default: null },
    recordsOnly: { type: Boolean, default: false }
  });
  const emit = defineEmits(['update:modelValue', 'done']);
  const userStore = useUserStore();

  const PAGE_SIZE = 5;
  const loading = ref(false);
  const detail = ref({});
  const visibleCount = ref(PAGE_SIZE);
  const showAssignedFields = computed(() => detail.value.status && detail.value.status !== 'unassigned');
  const isCustomer = computed(() => (userStore.roles || []).includes('customer'));
  const showFollowupFields = computed(
    () =>
      showAssignedFields.value &&
      !isCustomer.value &&
      typeof detail.value.followedUp !== 'undefined'
  );
  const drawerTitle = computed(() => {
    if (props.recordsOnly) {
      return detail.value.title ? `处理记录 - ${detail.value.title}` : '处理记录';
    }
    return detail.value.title ? `工单详情 - ${detail.value.title}` : '工单详情';
  });

  const collaboratorText = computed(() => {
    const list = detail.value.collaborators || [];
    return list.map((item) => item.name).join('、') || '-';
  });
  const mediaFiles = computed(() =>
    (detail.value.attachments || []).filter((item) => item.kind === 'image' || item.kind === 'video')
  );

  const logItems = computed(() => {
    const logs = [...(detail.value.logs || [])];
    const files = [...(detail.value.attachments || [])];
    const used = new Set();
    const rows = logs.map((item) => {
      let media = null;
      const matched = String(item.content || '').match(/^上传(图片|视频)：(.+)$/);
      if (item.action === 'attachment' && matched) {
        const kind = matched[1] === '图片' ? 'image' : 'video';
        const filename = matched[2].trim();
        const found = files.find(
          (file) =>
            !used.has(file.id) &&
            file.kind === kind &&
            file.filename === filename &&
            file.url
        );
        if (found) {
          used.add(found.id);
          media = found;
        }
      }
      return {
        ...item,
        media,
        timeText: String(item.createdAt || '-').replace(/-/g, '/'),
        operatorRoles: item.operatorRoles || [],
        roleText: (item.operatorRoles || []).join('、') || '-'
      };
    });
    return rows.reverse();
  });
  const recordImages = computed(() =>
    logItems.value.filter((item) => item.media?.kind === 'image').map((item) => item.media.url)
  );
  const imageIndex = (url) => {
    const index = recordImages.value.indexOf(url);
    return index < 0 ? 0 : index;
  };
  const visibleLogs = computed(() => logItems.value.slice(0, visibleCount.value));
  const hasMoreLogs = computed(() => visibleCount.value < logItems.value.length);
  const showMoreLogs = () => {
    visibleCount.value += PAGE_SIZE;
  };

  const load = async () => {
    if (!props.ticketId) return;
    loading.value = true;
    try {
      const data = await getTicket(props.ticketId);
      detail.value = data || {};
    } catch (e) {
      EleMessage.error(e.message || '加载失败');
    } finally {
      loading.value = false;
    }
  };

  watch(
    () => props.modelValue,
    (v) => {
      if (v) {
        visibleCount.value = PAGE_SIZE;
        load();
      }
    }
  );
</script>

<style scoped>
  .block {
    margin-top: 16px;
  }
  .block-title {
    margin-bottom: 8px;
    font-weight: 600;
  }
  .actions,
  .panel {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .panel {
    margin-top: 12px;
  }
  .panel-col {
    flex-direction: column;
    align-items: stretch;
  }
  .sla-tag {
    margin-left: 8px;
  }
  .eval-block {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .muted {
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }
  .more-logs {
    margin-top: 4px;
    padding-left: 0;
  }
  .log-timeline {
    padding-left: 4px;
  }
  .log-timeline :deep(.el-timeline-item__node) {
    width: 12px;
    height: 12px;
    left: -1px;
    background-color: #1890ff;
    border-color: #1890ff;
  }
  .log-timeline :deep(.el-timeline-item__tail) {
    left: 4px;
    border-left: 2px solid #e4e7ed;
  }
  .log-timeline :deep(.el-timeline-item__wrapper) {
    padding-left: 22px;
    top: -4px;
  }
  .log-timeline :deep(.el-timeline-item) {
    padding-bottom: 22px;
  }
  .log-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
    min-height: 22px;
  }
  .log-time {
    color: #606266;
    font-size: 13px;
    line-height: 22px;
  }
  .log-tag {
    height: 22px;
    padding: 0 8px;
    border: none;
    border-radius: 11px;
    background: #e6f4ff;
    color: #1890ff;
  }
  .log-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 24px;
    margin-top: 10px;
  }
  .log-field-full {
    grid-column: 1 / -1;
  }
  .log-label {
    color: #909399;
    font-size: 13px;
  }
  .log-value {
    color: #303133;
    font-size: 13px;
    word-break: break-all;
  }
  .log-person {
    color: #1890ff;
    font-size: 13px;
  }
  .log-image {
    width: 96px;
    height: 96px;
    margin-top: 8px;
    border-radius: 4px;
    cursor: zoom-in;
    background: #f5f7fa;
  }
  .file-row {
    line-height: 28px;
  }
  .el-button + .el-button {
    margin-left: 0 !important;
  }
</style>
