<template>
  <el-tree
    ref="treeRef"
    :data="data"
    :props="treeProps"
    :filter-node-method="filterNodeMethod"
    :node-key="nodeKey"
    :default-expanded-keys="defaultExpandedKeys"
    :default-expand-all="defaultExpandAll"
    :show-checkbox="multiple"
    :check-strictly="checkStrictly"
    :check-on-click-node="checkOnClickNode"
    @node-click="onNodeClick"
    @check="onCheck"
  >
    <template #default="{ data }">
      <slot :data="data">
        <span>{{ data.departmentName }}</span>
        <el-tag
          v-if="data.departmentGroup != 0"
          size="small"
          effect="plain"
          class="tip-badge"
        >
          {{ data.departmentGroup == 1 ? '运营团队' : '销售团队' }}
        </el-tag>
        <el-tag
          v-if="data.departmentType != 0"
          size="small"
          effect="plain"
          class="tip-badge"
        >
          {{ data.departmentType == 1 ? '运营大区' : '业务大区' }}
        </el-tag>
        <el-tag
          v-if="data.mainProductLineName"
          size="small"
          effect="plain"
          class="tip-badge"
        >
          {{ data.mainProductLineName }}
        </el-tag>
      </slot>
    </template>
  </el-tree>
</template>

<script setup>
  import { ref, watch, nextTick } from 'vue';

  const props = defineProps({
    data: { type: Array, default: () => [] },
    nodeKey: { type: String, default: 'id' },
    treeProps: {
      type: Object,
      default: () => ({ label: 'label', children: 'children' })
    },
    filterNodeMethod: { type: Function, default: () => true },
    multiple: { type: Boolean, default: false },
    checkedKeys: { type: Array, default: () => [] },
    checkStrictly: { type: Boolean, default: false },
    checkOnClickNode: { type: Boolean, default: false },
    defaultExpandedKeys: { type: Array, default: () => [] },
    defaultExpandAll: { type: Boolean, default: false }
  });

  const emit = defineEmits(['node-click', 'update:checkedKeys', 'check']);

  const treeRef = ref();

  const onNodeClick = (data, node, comp) => {
    emit('node-click', data, node, comp);
  };

  const onCheck = (data, info) => {
    emit('update:checkedKeys', info.checkedKeys);
    emit('check', data, info);
  };

  watch(
    () => props.checkedKeys,
    (v) => {
      if (props.multiple) treeRef.value?.setCheckedKeys(v || []);
    },
    { immediate: true }
  );

  watch(
    () => props.data,
    async () => {
      if (!props.multiple) return;
      await nextTick();
      treeRef.value?.setCheckedKeys(props.checkedKeys || []);
    },
    { deep: true }
  );

  watch(
    () => props.defaultExpandedKeys,
    (keys) => {
      const tree = treeRef.value;
      const ids = Array.isArray(keys) ? keys : [];
      for (const id of ids) {
        let node = tree?.getNode?.(id);
        if (!node) node = tree?.getNode?.(String(id));
        if (!node && id != null) node = tree?.getNode?.(Number(id));
        let parent = node?.parent;
        while (parent) {
          parent.expanded = true;
          parent = parent.parent;
        }
        if (node) node.expanded = true;
      }
    },
    { immediate: true }
  );

  defineExpose({
    filter: (val) => treeRef.value?.filter?.(val),
    setCurrentKey: (key) => treeRef.value?.setCurrentKey?.(key),
    getCheckedKeys: (leafOnly) => treeRef.value?.getCheckedKeys?.(leafOnly),
    setCheckedKeys: (keys) => treeRef.value?.setCheckedKeys?.(keys),
    getTreeRef: () => treeRef.value
  });
</script>

<style scoped>
  .tip-badge {
    margin-left: 8px;
  }
</style>
