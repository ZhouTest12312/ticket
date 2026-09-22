<template>
  <ele-drawer
    :model-value="modelValue"
    :title="title"
    size="720px"
    :destroy-on-close="true"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <ele-pro-table
      v-if="customerId"
      row-key="id"
      :columns="columns"
      :datasource="datasource"
      :tools="false"
      :border="true"
      :response="{ dataName: 'records', countName: 'total' }"
      :pagination="{ style: { margin: '0 0 0 auto' }, size: 'small' }"
    />
  </ele-drawer>
</template>

<script setup>
  import { computed } from 'vue';
  import { pageCustomerTickets } from '@/api/customer';

  const props = defineProps({
    modelValue: Boolean,
    customerId: { type: [Number, null], default: null },
    customerName: { type: String, default: '' }
  });
  const emit = defineEmits(['update:modelValue']);

  const title = computed(() =>
    props.customerName ? `历史工单 - ${props.customerName}` : '历史工单'
  );

  const columns = [
    { prop: 'title', label: '标题', minWidth: 180 },
    { prop: 'statusLabel', label: '状态', width: 100 },
    { prop: 'createdAt', label: '创建时间', minWidth: 170 }
  ];

  const datasource = async ({ page, limit }) => {
    return pageCustomerTickets(props.customerId, {
      page,
      pageSize: limit
    });
  };
</script>
