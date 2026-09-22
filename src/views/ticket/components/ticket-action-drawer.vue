<template>
  <ele-drawer
    :model-value="modelValue"
    :title="title"
    size="560px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="action === 'assign' || action === 'transfer'" class="panel panel-col">
      <el-select v-model="owner.groupId" filterable placeholder="请选择处理组" style="width: 100%" @change="onGroupChange">
        <el-option v-for="item in groupOptions" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select
        v-model="owner.assigneeId"
        clearable
        filterable
        :placeholder="action === 'transfer' ? '可选择其他部门人员，不选则自动分配组内其他成员' : '不选则自动分配组内成员'"
        style="width: 100%"
      >
        <el-option v-for="item in groupMembers" :key="item.id" :label="personLabel(item)" :value="item.id" />
      </el-select>
    </div>
    <div v-else-if="action === 'collab'" class="panel">
      <el-select v-model="collabIds" multiple filterable placeholder="选择协作者" style="width: 100%">
        <el-option v-for="item in collabUsers" :key="item.id" :label="personLabel(item)" :value="item.id" />
      </el-select>
    </div>
    <div v-else-if="action === 'note'" class="panel panel-col">
      <el-input v-model="note.content" type="textarea" :rows="3" placeholder="处理记录或内部备注" />
      <el-checkbox v-model="note.internal">内部备注</el-checkbox>
      <el-date-picker
        v-model="note.estimatedResolveAt"
        type="datetime"
        value-format="YYYY-MM-DD HH:mm:ss"
        placeholder="预计解决时间"
        style="width: 100%"
      />
    </div>
    <div v-else-if="action === 'resolve'" class="panel panel-col">
      <el-input v-model="resolveForm.resolution" type="textarea" :rows="3" placeholder="请填写解决结果" />
      <el-date-picker
        v-model="resolveForm.actualResolveAt"
        type="datetime"
        value-format="YYYY-MM-DD HH:mm:ss"
        placeholder="实际解决时间，默认当前"
        style="width: 100%"
      />
    </div>
    <div v-else-if="action === 'confirm'" class="panel panel-col">
      <div class="rate-row">
        <span class="rate-label">服务星级</span>
        <el-rate v-model="rating" :max="5" show-text :texts="rateTexts" />
      </div>
      <el-input
        v-model="evaluation"
        type="textarea"
        :rows="3"
        placeholder="评价描述，选填"
      />
    </div>
    <div v-else-if="action === 'close'" class="panel panel-col">
      <el-input v-model="resolveForm.resolution" type="textarea" :rows="3" placeholder="请填写解决结果" />
      <el-date-picker
        v-model="resolveForm.actualResolveAt"
        type="datetime"
        value-format="YYYY-MM-DD HH:mm:ss"
        placeholder="实际解决时间，默认当前"
        style="width: 100%"
      />
      <el-input v-model="evaluation" placeholder="关闭说明，选填" />
    </div>
    <div v-else-if="action === 'reopen'">
      <el-input v-model="reopenReason" placeholder="不认可原因" />
    </div>
    <div v-else-if="action === 'followup'" class="panel panel-col">
      <el-date-picker
        v-model="followup.followupAt"
        type="datetime"
        value-format="YYYY-MM-DD HH:mm:ss"
        placeholder="回访时间"
        style="width: 100%"
      />
      <el-select v-model="followup.followupUserId" filterable placeholder="回访人" style="width: 100%">
        <el-option
          v-for="item in followupUsers"
          :key="item.id"
          :label="personLabel(item)"
          :value="item.id"
        />
      </el-select>
      <el-select v-model="followup.method" placeholder="回访方式" style="width: 100%">
        <el-option v-for="item in followupMethods" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="followup.result" placeholder="回访结果" style="width: 100%">
        <el-option v-for="item in followupResults" :key="item" :label="item" :value="item" />
      </el-select>
      <el-input
        v-model="followup.remark"
        type="textarea"
        :rows="3"
        placeholder="回访备注，例如沟通内容、是否还有其他问题"
      />
    </div>
    <div v-else-if="action === 'escalate'" class="panel">
      <el-select
        v-model="escalateUserId"
        clearable
        filterable
        placeholder="默认升级给本组负责人"
        style="width: 240px"
      >
        <el-option
          v-for="item in options.escalationTargets"
          :key="item.id"
          :label="item.name"
          :value="item.id"
        />
      </el-select>
      <el-input v-model="escalateReason" placeholder="升级说明" style="width: 220px" />
    </div>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">确定</el-button>
    </template>
  </ele-drawer>
</template>

<script setup>
  import { computed, reactive, ref, watch } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { useUserStore } from '@/store/modules/user';
  import {
    addTicketNote,
    assignTicket,
    confirmTicket,
    closeTicket,
    escalateTicket,
    followupTicket,
    getTicket,
    reopenTicket,
    resolveTicket,
    setCollaborators,
    ticketOptions,
    transferTicket
  } from '@/api/ticket';

  const props = defineProps({
    modelValue: Boolean,
    ticketId: { type: [Number, null], default: null },
    action: { type: String, default: '' }
  });
  const emit = defineEmits(['update:modelValue', 'done']);
  const userStore = useUserStore();

  const titles = {
    assign: '派发',
    transfer: '转派',
    collab: '协作者',
    note: '处理记录',
    resolve: '标记解决',
    confirm: '客户确认',
    close: '关闭工单',
    reopen: '重新打开',
    followup: '回访',
    escalate: '升级'
  };
  const followupMethods = ['电话', '微信', '上门'];
  const followupResults = ['满意', '一般', '不满意', '问题复发'];
  const personLabel = (item) => {
    const groups = (item.groupNames || []).filter(Boolean);
    return groups.length ? `${item.name}（${groups.join('、')}）` : item.name;
  };
  const title = computed(() => titles[props.action] || '操作');
  const groupOptions = computed(() =>
    props.action === 'transfer'
      ? options.groups.filter((item) => item.name !== '管理组')
      : options.groups
  );
  const groupMembers = computed(() => {
    if (props.action === 'transfer') {
      return options.users.filter((item) => {
        const codes = item.roleCodes || [];
        if (!item.staff || codes.includes('customer') || codes.includes('admin')) return false;
        return item.id !== currentAssigneeId.value;
      });
    }
    const group = options.groups.find((item) => item.id === owner.groupId);
    const roleIds = group?.roleIds || [];
    return options.users.filter((item) => (item.roleIds || []).some((id) => roleIds.includes(id)));
  });
  const collabUsers = computed(() =>
    options.users.filter((item) => {
      const codes = item.roleCodes || [];
      if (!item.staff || codes.includes('customer')) return false;
      return item.id !== currentAssigneeId.value;
    })
  );
  const followupUsers = computed(() =>
    options.users.filter((item) => {
      const codes = item.roleCodes || [];
      return codes.includes('admin') || codes.includes('cs');
    })
  );

  const saving = ref(false);
  const options = reactive({ users: [], groups: [], escalationTargets: [] });
  const owner = reactive({ assigneeId: undefined, groupId: undefined });
  const currentAssigneeId = ref(null);
  const collabIds = ref([]);
  const note = reactive({ content: '', internal: false, estimatedResolveAt: '' });
  const resolveForm = reactive({ resolution: '', actualResolveAt: '' });
  const evaluation = ref('');
  const rating = ref(0);
  const rateTexts = ['很差', '较差', '一般', '满意', '非常满意'];
  const reopenReason = ref('');
  const followup = reactive({
    followupAt: '',
    followupUserId: undefined,
    method: '',
    result: '',
    remark: ''
  });
  const escalateUserId = ref(undefined);
  const escalateReason = ref('');

  const pad = (n) => String(n).padStart(2, '0');
  const nowText = () => {
    const d = new Date();
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  };

  const reset = () => {
    owner.assigneeId = undefined;
    owner.groupId = undefined;
    collabIds.value = [];
    note.content = '';
    note.internal = false;
    note.estimatedResolveAt = '';
    resolveForm.resolution = '';
    resolveForm.actualResolveAt = '';
    evaluation.value = '';
    rating.value = 0;
    reopenReason.value = '';
    followup.followupAt = '';
    followup.followupUserId = undefined;
    followup.method = '';
    followup.result = '';
    followup.remark = '';
    escalateUserId.value = undefined;
    escalateReason.value = '';
  };

  const load = async () => {
    reset();
    if (!props.ticketId) return;
    const [data, opt] = await Promise.all([getTicket(props.ticketId), ticketOptions()]);
    options.users = opt.users || [];
    options.groups = opt.groups || [];
    options.escalationTargets = opt.escalationTargets || [];
    const currentGroup = options.groups.find((item) => item.id === data.groupId);
    currentAssigneeId.value = data.assigneeId || null;
    owner.groupId =
      props.action === 'transfer' && currentGroup?.name === '管理组'
        ? undefined
        : data.groupId || undefined;
    owner.assigneeId = props.action === 'transfer' ? undefined : data.assigneeId || undefined;
    collabIds.value = (data.collaborators || []).map((item) => item.id);
    resolveForm.resolution = data.resolution || '';
    resolveForm.actualResolveAt = data.actualResolveAt || '';
    if (props.action === 'followup') {
      followup.followupAt = data.followupAt || nowText();
      followup.followupUserId =
        data.followupUserId || userStore.info?.userId || undefined;
      followup.method = data.followupMethod || '';
      followup.result = data.followupResult || '';
      followup.remark = data.followupRemark || '';
    }
  };

  watch(
    () => props.modelValue,
    (visible) => {
      if (visible) {
        load().catch((e) => EleMessage.error(e.message || '加载失败'));
      }
    }
  );

  const onGroupChange = () => {
    if (!groupMembers.value.some((item) => item.id === owner.assigneeId)) {
      owner.assigneeId = undefined;
    }
  };

  const submit = async () => {
    saving.value = true;
    try {
      const id = props.ticketId;
      if (props.action === 'assign' || props.action === 'transfer') {
        if (!owner.groupId) {
          EleMessage.error('请选择处理组');
          return;
        }
        const req = props.action === 'transfer' ? transferTicket : assignTicket;
        await req(id, {
          groupId: owner.groupId,
          assigneeId: owner.assigneeId || null
        });
      } else if (props.action === 'collab') {
        await setCollaborators(id, collabIds.value);
      } else if (props.action === 'note') {
        await addTicketNote(id, {
          content: note.content,
          internal: note.internal,
          estimatedResolveAt: note.estimatedResolveAt || null
        });
      } else if (props.action === 'resolve') {
        await resolveTicket(id, {
          resolution: resolveForm.resolution,
          actualResolveAt: resolveForm.actualResolveAt || null
        });
      } else if (props.action === 'confirm') {
        await confirmTicket(id, {
          evaluation: evaluation.value,
          rating: rating.value || null
        });
      } else if (props.action === 'close') {
        if (!resolveForm.resolution.trim()) {
          EleMessage.error('请填写解决结果');
          return;
        }
        await closeTicket(id, {
          resolution: resolveForm.resolution,
          actualResolveAt: resolveForm.actualResolveAt || null,
          remark: evaluation.value
        });
      } else if (props.action === 'reopen') {
        await reopenTicket(id, { reason: reopenReason.value });
      } else if (props.action === 'followup') {
        if (!followup.followupAt) {
          EleMessage.error('请选择回访时间');
          return;
        }
        if (!followup.followupUserId) {
          EleMessage.error('请选择回访人');
          return;
        }
        if (!followup.method) {
          EleMessage.error('请选择回访方式');
          return;
        }
        if (!followup.result) {
          EleMessage.error('请选择回访结果');
          return;
        }
        await followupTicket(id, {
          followupAt: followup.followupAt,
          followupUserId: followup.followupUserId,
          method: followup.method,
          result: followup.result,
          remark: followup.remark
        });
      } else if (props.action === 'escalate') {
        await escalateTicket(id, {
          assigneeId: escalateUserId.value || null,
          reason: escalateReason.value
        });
      }
      EleMessage.success('操作成功');
      emit('update:modelValue', false);
      emit('done');
    } catch (e) {
      EleMessage.error(e.message || '操作失败');
    } finally {
      saving.value = false;
    }
  };
</script>

<style scoped>
  .panel {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .panel-col {
    flex-direction: column;
    align-items: stretch;
  }
  .rate-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .rate-label {
    flex: none;
    color: var(--el-text-color-regular);
  }
</style>
