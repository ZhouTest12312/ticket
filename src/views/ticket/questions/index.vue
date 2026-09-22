<template>
  <ele-page>
    <ele-card :body-style="{ paddingTop: '16px', minHeight: 'calc(100vh - 160px)' }">
      <el-button v-if="!isAdmin" class="create-btn" type="primary" @click="askVisible = true">
        我要提问
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
          <ele-dot v-bind="statusDot(row.status)" :text="row.statusLabel" />
          <el-tag v-if="row.status === 'waiting_customer'" class="wait-tag" type="warning" size="small">
            请补充材料
          </el-tag>
        </template>
        <template #action="{ row }">
          <div class="table-actions">
            <el-link type="primary" :underline="false" @click="openReply(row)">查看处理</el-link>
            <el-link
              v-if="canSupplement(row)"
              type="primary"
              :underline="false"
              @click="openSupplement(row)"
            >
              补充信息
            </el-link>
            <el-link
              v-if="row.status === 'unassigned'"
              type="primary"
              :underline="false"
              @click="openEdit(row)"
            >
              编辑
            </el-link>
            <el-link
              v-if="row.status === 'resolved' && canConfirmAsCustomer(row)"
              type="success"
              :underline="false"
              @click="confirmClose(row)"
            >
              确认结案
            </el-link>
            <el-link
              v-if="row.status === 'resolved' && canConfirmAsCustomer(row)"
              type="danger"
              :underline="false"
              @click="reopenQuestion(row)"
            >
              重新打开
            </el-link>
            <el-link
              v-if="canRate(row)"
              type="warning"
              :underline="false"
              @click="openRate(row)"
            >
              评价
            </el-link>
          </div>
        </template>
      </ele-pro-table>
    </ele-card>

    <ele-drawer
      v-model="askVisible"
      title="提交问题"
      size="560px"
      :destroy-on-close="true"
    >
      <el-form ref="askFormRef" :model="askForm" :rules="askRules" label-width="88px">
        <el-form-item label="问题标题" prop="title">
          <el-input v-model="askForm.title" maxlength="200" placeholder="请简要描述问题" />
        </el-form-item>
        <el-form-item label="详细描述" prop="description">
          <el-input
            v-model="askForm.description"
            type="textarea"
            :rows="4"
            placeholder="请说明现象、复现步骤等"
          />
        </el-form-item>
        <el-form-item label="分类" prop="categoryId">
          <el-select v-model="askForm.categoryId" placeholder="请选择分类" style="width: 100%">
            <el-option
              v-for="item in options.categories"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priorityId">
          <el-select v-model="askForm.priorityId" placeholder="请选择优先级" style="width: 100%">
            <el-option
              v-for="item in options.priorities"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="产品" prop="product">
          <el-select v-model="askForm.product" filterable placeholder="请选择产品" style="width: 100%">
            <el-option
              v-for="item in options.products"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="具体服务" prop="serviceName">
          <el-select
            v-model="askForm.serviceName"
            filterable
            placeholder="请选择具体服务"
            style="width: 100%"
          >
            <el-option
              v-for="item in options.services"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="附件">
          <TicketMediaUpload ref="mediaRef" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="askVisible = false">取消</el-button>
        <el-button type="primary" :loading="asking" @click="submitAsk">提交</el-button>
      </template>
    </ele-drawer>

    <ele-drawer v-model="replyVisible" title="处理内容" size="680px" :destroy-on-close="true">
      <div v-loading="replyLoading">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="状态">{{ reply.statusLabel || '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理人">{{ reply.assigneeName || '未分派' }}</el-descriptions-item>
          <el-descriptions-item label="问题标题">{{ reply.title || '-' }}</el-descriptions-item>
          <el-descriptions-item label="问题描述">{{ reply.description || '-' }}</el-descriptions-item>
        </el-descriptions>
        <template v-if="thread.questionFiles.length">
          <div class="block-title">问题附件</div>
          <TicketMediaUpload readonly :ticket-id="reply.id" :model-value="thread.questionFiles" />
        </template>
        <template v-if="thread.customerNotes.length">
          <div class="block-title">客户补充</div>
          <div class="note-list">
            <div v-for="item in thread.customerNotes" :key="item.id" class="note-card customer">
              <div class="note-head">
                <el-tag size="small" type="success">客户</el-tag>
                <span class="muted">{{ item.time }} {{ item.name }}</span>
              </div>
              <div class="note-text">{{ item.content }}</div>
              <TicketMediaUpload
                v-if="item.files.length"
                readonly
                :ticket-id="reply.id"
                :model-value="item.files"
              />
            </div>
          </div>
        </template>
        <div class="block-title">技术处理</div>
        <div class="note-card staff">
          <div class="note-head">
            <el-tag size="small">技术</el-tag>
            <span class="muted">{{ reply.assigneeName || '未分派' }}</span>
          </div>
          <div class="note-text">处理回答：{{ reply.handlerReply || '暂无' }}</div>
          <div class="note-text">解决方案：{{ reply.handlerSolution || '暂无' }}</div>
          <TicketMediaUpload
            v-if="thread.solutionFiles.length"
            readonly
            :ticket-id="reply.id"
            :model-value="thread.solutionFiles"
          />
          <div v-for="item in thread.staffNotes" :key="item.id" class="staff-extra">
            <div class="muted">{{ item.time }} {{ item.name }}</div>
            <div class="note-text">{{ item.content }}</div>
            <TicketMediaUpload
              v-if="item.files.length"
              readonly
              :ticket-id="reply.id"
              :model-value="item.files"
            />
          </div>
        </div>
        <template v-if="reply.rating">
          <div class="block-title">客户评价</div>
          <div class="eval-block">
            <el-rate
              :model-value="reply.rating"
              disabled
              show-score
              score-template="{value} 星"
            />
            <div
              v-if="reply.evaluation && reply.evaluation !== '客户确认结案'"
              class="note-text"
            >
              {{ reply.evaluation }}
            </div>
          </div>
        </template>
      </div>
    </ele-drawer>

    <ele-drawer
      v-model="confirmVisible"
      :title="confirmMode === 'rate' ? '服务评价' : '确认结案'"
      size="480px"
      :destroy-on-close="true"
    >
      <div class="confirm-tip">
        <template v-if="confirmMode === 'rate'">
          工单已关闭，请为本次服务打分。评价提交后不可修改。
        </template>
        <template v-else>
          确认结案后工单将关闭，不能再补充。服务星级和评价描述可不填，关闭后仍可再评价。
        </template>
      </div>
      <el-form label-width="88px">
        <el-form-item :label="'服务星级'" :required="confirmMode === 'rate'">
          <el-rate v-model="confirmForm.rating" :max="5" show-text :texts="rateTexts" />
        </el-form-item>
        <el-form-item label="评价描述">
          <el-input
            v-model="confirmForm.evaluation"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            placeholder="请描述本次服务体验，选填"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="confirmVisible = false">取消</el-button>
        <el-button type="primary" :loading="confirming" @click="submitConfirm">
          {{ confirmMode === 'rate' ? '提交评价' : '确认结案' }}
        </el-button>
      </template>
    </ele-drawer>

    <ele-drawer v-model="editVisible" title="编辑问题" size="560px" :destroy-on-close="true">
      <el-form label-width="88px">
        <el-form-item label="问题标题">
          <el-input v-model="editForm.title" maxlength="200" placeholder="请输入问题标题" />
        </el-form-item>
        <el-form-item label="详细描述">
          <el-input v-model="editForm.description" type="textarea" :rows="4" placeholder="请描述问题" />
        </el-form-item>
        <el-form-item label="附件">
          <TicketMediaUpload ref="editMediaRef" :ticket-id="editId" :model-value="editFiles" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editing" @click="submitEdit">保存</el-button>
      </template>
    </ele-drawer>

    <ele-drawer v-model="supplementVisible" title="补充信息" size="560px" :destroy-on-close="true">
      <el-form label-width="88px">
        <el-form-item label="补充说明">
          <el-input
            v-model="supplementRemark"
            type="textarea"
            :rows="4"
            placeholder="请补充当前问题的进展或资料"
          />
        </el-form-item>
        <el-form-item label="附件">
          <TicketMediaUpload ref="supplementMediaRef" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="supplementVisible = false">取消</el-button>
        <el-button type="primary" :loading="supplementing" @click="submitSupplement">确定</el-button>
      </template>
    </ele-drawer>
  </ele-page>
</template>

<script setup>
  import { computed, onMounted, reactive, ref } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { ElMessageBox } from 'element-plus/es';
  import { useUserStore } from '@/store/modules/user';
  import {
    askTicket,
    customerFeedback,
    getTicket,
    pageMyTickets,
    ticketOptions,
    updateTicket
  } from '@/api/ticket';
  import TicketMediaUpload from '../components/ticket-media-upload.vue';
  import { statusDot } from '../status-dot';

  const userStore = useUserStore();
  const isAdmin = computed(() => (userStore.roles || []).includes('admin'));
  const currentUserId = computed(() => userStore.info?.userId);
  const canConfirmAsCustomer = (row) =>
    !isAdmin.value && row.customerUserId && row.customerUserId === currentUserId.value;
  const canRate = (row) =>
    canConfirmAsCustomer(row) && row.status === 'closed' && !row.rating;
  const canSupplement = (row) =>
    ['unassigned', 'pending', 'processing', 'waiting_customer', 'resolved', 'reopened'].includes(
      row.status
    );

  const tableRef = ref(null);
  const askFormRef = ref(null);
  const mediaRef = ref(null);
  const supplementMediaRef = ref(null);
  const askVisible = ref(false);
  const asking = ref(false);
  const replyVisible = ref(false);
  const replyLoading = ref(false);
  const reply = ref({});
  const thread = computed(() => {
    const logs = reply.value.logs || [];
    const files = (reply.value.attachments || [])
      .filter((item) => item.kind === 'image' || item.kind === 'video')
      .map((item) => ({ ...item }));
    const used = new Set();
    const questionFiles = [];
    const customerNotes = [];
    const staffNotes = [];
    const solutionFiles = [];
    let bucket = [];
    let phase = '';
    const takeFile = (log) => {
      const matched = String(log.content || '').match(/^上传(图片|视频)：(.+)$/);
      if (!matched) return null;
      const kind = matched[1] === '图片' ? 'image' : 'video';
      const file = files.find(
        (item) =>
          !used.has(item.id) &&
          item.kind === kind &&
          item.filename === matched[2] &&
          (item.uploaderId == null || item.uploaderId === log.operatorId)
      );
      if (!file) return null;
      used.add(file.id);
      return file;
    };
    logs.forEach((log) => {
      if (log.action === 'internal') return;
      if (log.action === 'ask') {
        phase = 'ask';
        return;
      }
      if (log.action === 'attachment') {
        const file = takeFile(log);
        if (!file) return;
        if (phase === 'ask') questionFiles.push(file);
        else bucket.push(file);
        return;
      }
      phase = '';
      if (log.action !== 'record' || !log.content) return;
      const mine = bucket.filter(
        (file) => file.uploaderId == null || file.uploaderId === log.operatorId
      );
      bucket = bucket.filter((file) => !mine.includes(file));
      if (String(log.content).startsWith('处理回答：')) {
        solutionFiles.push(...mine);
        return;
      }
      const note = {
        id: log.id,
        operatorId: log.operatorId,
        name: log.operatorName || '',
        time: log.createdAt,
        content: log.content,
        files: mine
      };
      customerNotes.push(note);
    });
    bucket.forEach((file) => {
      if (file.fromCustomer) {
        const note = [...customerNotes].reverse().find((item) => item.operatorId === file.uploaderId);
        if (note) note.files.push(file);
        else questionFiles.push(file);
      } else {
        solutionFiles.push(file);
      }
    });
    files
      .filter((file) => !used.has(file.id))
      .forEach((file) => {
        if (file.fromCustomer) questionFiles.push(file);
        else solutionFiles.push(file);
      });
    return { questionFiles, customerNotes, staffNotes, solutionFiles };
  });
  const supplementVisible = ref(false);
  const supplementing = ref(false);
  const supplementRemark = ref('');
  const supplementId = ref(null);
  const actionWidth = ref(160);
  const measureActionWidth = (labelGroups) => {
    const widthOf = (labels) => {
      const text = labels.reduce((sum, label) => sum + [...label].length * 14, 0);
      const gaps = Math.max(labels.length - 1, 0) * 17;
      return text + gaps + 32;
    };
    return Math.max(88, ...labelGroups.map(widthOf));
  };
  const questionActionLabels = (row) => {
    const labels = ['查看处理'];
    if (canSupplement(row)) labels.push('补充信息');
    if (row.status === 'unassigned') labels.push('编辑');
    if (row.status === 'resolved') labels.push('确认结案', '重新打开');
    if (canRate(row)) labels.push('评价');
    return labels;
  };
  const options = reactive({
    categories: [],
    priorities: [],
    products: [],
    services: []
  });
  const columns = computed(() => {
    const cols = [
      { prop: 'ticketNo', label: '工单号', minWidth: 140 },
      { prop: 'title', label: '问题标题', minWidth: 180 },
      { prop: 'statusLabel', label: '处理状态', minWidth: 110, slot: 'status' },
      { prop: 'assigneeName', label: '处理人', minWidth: 100 },
      { prop: 'priorityName', label: '优先级', width: 90 },
      { prop: 'createdAt', label: '提交时间', minWidth: 160 },
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
    if (isAdmin.value) {
      cols.splice(2, 0, { prop: 'customerName', label: '客户', minWidth: 120 });
    }
    return cols;
  });
  const askForm = reactive({
    title: '',
    description: '',
    categoryId: undefined,
    priorityId: undefined,
    product: '',
    serviceName: ''
  });
  const askRules = {
    title: [{ required: true, message: '请输入问题标题', trigger: 'blur' }],
    description: [{ required: true, message: '请输入详细描述', trigger: 'blur' }],
    categoryId: [{ required: true, message: '请选择分类', trigger: 'change' }],
    priorityId: [{ required: true, message: '请选择优先级', trigger: 'change' }],
    product: [{ required: true, message: '请选择产品', trigger: 'change' }],
    serviceName: [{ required: true, message: '请选择具体服务', trigger: 'change' }]
  };

  const datasource = async ({ page, limit }) => {
    const data = await pageMyTickets({ page, pageSize: limit });
    const records = data.records || [];
    const nextWidth = measureActionWidth(records.map((row) => questionActionLabels(row)));
    if (actionWidth.value !== nextWidth) actionWidth.value = nextWidth;
    return { records, total: data.total || 0 };
  };

  const reload = () => tableRef.value?.reload?.();

  const submitAsk = async () => {
    const valid = await askFormRef.value?.validate?.().catch(() => false);
    if (!valid) return;
    asking.value = true;
    try {
      await askTicket({
        ...askForm,
        attachments: mediaRef.value?.getFiles?.() || []
      });
      EleMessage.success('提问成功，已生成工单');
      askVisible.value = false;
      Object.assign(askForm, {
        title: '',
        description: '',
        categoryId: undefined,
        priorityId: undefined,
        product: '',
        serviceName: ''
      });
      reload();
    } catch (e) {
      EleMessage.error(e.message || '提交失败');
    } finally {
      asking.value = false;
    }
  };

  const editVisible = ref(false);
  const editing = ref(false);
  const editId = ref(null);
  const editFiles = ref([]);
  const editMediaRef = ref(null);
  const editForm = reactive({ title: '', description: '' });

  const openEdit = async (row) => {
    editId.value = row.id;
    editVisible.value = true;
    editForm.title = '';
    editForm.description = '';
    editFiles.value = [];
    try {
      const detail = (await getTicket(row.id)) || {};
      editForm.title = detail.title || '';
      editForm.description = detail.description || '';
      editFiles.value = detail.attachments || [];
    } catch (e) {
      EleMessage.error(e.message || '加载失败');
    }
  };

  const submitEdit = async () => {
    if (!editForm.title.trim() || !editForm.description.trim()) {
      EleMessage.error('请填写标题和描述');
      return;
    }
    editing.value = true;
    try {
      await updateTicket(editId.value, {
        title: editForm.title.trim(),
        description: editForm.description.trim(),
        attachments: (editMediaRef.value?.getFiles?.() || []).filter((item) => !item.id)
      });
      EleMessage.success('已保存');
      editVisible.value = false;
      reload();
    } catch (e) {
      EleMessage.error(e.message || '保存失败');
    } finally {
      editing.value = false;
    }
  };

  const confirmVisible = ref(false);
  const confirming = ref(false);
  const confirmId = ref(null);
  const confirmMode = ref('confirm');
  const confirmForm = reactive({ rating: 0, evaluation: '' });
  const rateTexts = ['很差', '较差', '一般', '满意', '非常满意'];

  const openConfirmDrawer = (row, mode) => {
    confirmId.value = row.id;
    confirmMode.value = mode;
    confirmForm.rating = 0;
    confirmForm.evaluation = '';
    confirmVisible.value = true;
  };

  const confirmClose = (row) => openConfirmDrawer(row, 'confirm');
  const openRate = (row) => openConfirmDrawer(row, 'rate');

  const submitConfirm = async () => {
    if (confirmMode.value === 'rate' && !confirmForm.rating) {
      EleMessage.error('请选择服务星级');
      return;
    }
    confirming.value = true;
    try {
      const payload = {
        result: confirmMode.value === 'rate' ? 'rate' : 'confirmed',
        remark: confirmForm.evaluation.trim()
      };
      if (confirmForm.rating) payload.rating = confirmForm.rating;
      await customerFeedback(confirmId.value, payload);
      EleMessage.success(confirmMode.value === 'rate' ? '评价已提交' : '工单已关闭');
      confirmVisible.value = false;
      reload();
    } catch (e) {
      EleMessage.error(e.message || '操作失败');
    } finally {
      confirming.value = false;
    }
  };

  const reopenQuestion = (row) => {
    ElMessageBox.prompt('请填写重新打开的原因', '重新打开', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '请说明还需要处理的问题',
      inputValidator: (value) => (value && value.trim() ? true : '请填写重新打开原因')
    })
      .then(async ({ value }) => {
        await customerFeedback(row.id, { result: 'rejected', remark: value.trim() });
        EleMessage.success('已重新打开');
        reload();
      })
      .catch((e) => {
        if (e === 'cancel' || e === 'close') return;
        EleMessage.error(e.message || '操作失败');
      });
  };

  const openReply = async (row) => {
    replyVisible.value = true;
    replyLoading.value = true;
    reply.value = {};
    try {
      reply.value = (await getTicket(row.id)) || {};
    } catch (e) {
      EleMessage.error(e.message || '加载失败');
    } finally {
      replyLoading.value = false;
    }
  };

  const openSupplement = (row) => {
    supplementId.value = row.id;
    supplementRemark.value = '';
    supplementVisible.value = true;
  };

  const submitSupplement = async () => {
    if (!supplementRemark.value.trim()) {
      EleMessage.error('请填写补充说明');
      return;
    }
    supplementing.value = true;
    try {
      await customerFeedback(supplementId.value, {
        result: 'supplement',
        remark: supplementRemark.value.trim(),
        attachments: supplementMediaRef.value?.getFiles?.() || []
      });
      EleMessage.success('已补充');
      supplementVisible.value = false;
      reload();
    } catch (e) {
      EleMessage.error(e.message || '反馈失败');
    } finally {
      supplementing.value = false;
    }
  };

  onMounted(async () => {
    try {
      const data = await ticketOptions();
      options.categories = data.categories || [];
      options.priorities = data.priorities || [];
      options.products = (data.products || []).map((item) =>
        typeof item === 'string' ? item : item.name
      );
      options.services = (data.services || []).map((item) =>
        typeof item === 'string' ? item : item.name
      );
    } catch (e) {
      EleMessage.error(e.message || '加载选项失败');
    }
  });
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
    max-width: 320px;
  }
  .search-label {
    flex: none;
    color: var(--el-text-color-regular);
    white-space: nowrap;
  }
  .search-btns {
    margin-left: auto;
    display: flex;
    gap: 8px;
  }
  .wait-tag {
    margin-left: 6px;
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
  .table-actions :deep(.el-link) {
    flex: none;
  }
  .table-actions :deep(.el-link:not(:first-child)) {
    margin-left: 8px;
    padding-left: 8px;
    border-left: 1px solid var(--el-border-color);
  }
  :deep(.el-table__cell:has(.table-actions) .cell) {
    overflow: visible;
    white-space: nowrap;
  }
  .block-title {
    margin: 16px 0 8px;
    font-weight: 600;
  }
  .confirm-tip {
    margin-bottom: 16px;
    color: var(--el-text-color-regular);
    line-height: 1.6;
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
  .note-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .note-card {
    padding: 10px 12px;
    border-radius: 6px;
  }
  .note-card.customer {
    background: #f6ffed;
    border: 1px solid #b7eb8f;
  }
  .note-card.staff {
    background: #e6f4ff;
    border: 1px solid #91caff;
  }
  .note-head {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  .note-text {
    line-height: 22px;
    white-space: pre-wrap;
  }
  .staff-extra {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px dashed #91caff;
  }

</style>
