<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    multiple
    :clearable="clearable"
    @change="updateValue"
    v-bind="$attrs"
  >
    <template #header>
      <el-checkbox
        v-model="checkCampusAll"
        :indeterminate="indeterminate"
        @change="handleCheckAll"
      >
        全部
      </el-checkbox>
    </template>
    <el-option
      v-for="item in selectList"
      :key="item[keyName]"
      :label="item[labelName]"
      :value="item[keyName]"
    />
  </el-select>
</template>

<script setup>
  import { ref, computed, onActivated } from 'vue';
  const emit = defineEmits(['update:modelValue', 'change']);
  const props = defineProps({
    // 选中数据
    modelValue: {
      type: Array,
      default: () => []
    },
    /** 下拉数组 */
    selectList: {
      type: Array,
      default: () => []
    },
    /** 键名 */
    keyName: {
      type: String,
      default: 'key'
    },
    /** 显示值名称 */
    labelName: {
      type: String,
      default: 'label'
    },
    // 提示文本
    placeholder: {
      type: String,
      default: '请选择'
    },
    // 清空
    clearable: {
      type: Boolean,
      default: true
    }
  });
  //   全选状态
  const checkCampusAll = computed(() => {
    if (props?.modelValue?.length === 0) {
      return false;
    }
    if (props?.modelValue?.length === props?.selectList?.length) {
      return true;
    }
  });
  //   是否半选
  const indeterminate = computed(() => {
    if (props?.modelValue?.length === 0) {
      return false;
    } else if (props?.modelValue?.length === props?.selectList?.length) {
      return false;
    } else {
      return true;
    }
  });
  //   全选事件
  const handleCheckAll = (val) => {
    indeterminate.value = false;
    if (val) {
      const list = props?.selectList.map((v) => v[props?.keyName]);
      updateValue(list);
    } else {
      updateValue([]);
    }
  };
  /** 更新选中数据 */
  const updateValue = (value) => {
    emit('update:modelValue', value);
    emit('change', value, checkCampusAll.value);
  };
  watch(
    () => props.selectList,
    (val) => {
      const ids = props?.selectList.map((v) => v[props?.keyName]);
      const commonItems = props?.modelValue.filter((item) =>
        ids.includes(item)
      );
      if (JSON.stringify(commonItems) !== JSON.stringify(props?.modelValue)) {
        updateValue(commonItems);
      }
    },
    { deep: true }
  );
</script>
