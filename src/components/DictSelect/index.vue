<!-- 字典下拉表单 -->
<template>
  <el-select
    :key="selectKey"
    v-model="computedValue"
    clearable
    :disabled="disabled || loading"
    :loading="loading"
    :multiple="multiple"
    :collapse-tags="multiple && collapseTags"
    :collapse-tags-tooltip="multiple && collapseTagsTooltip"
    :max-collapse-tags="multiple && collapseTags ? maxCollapseTags : undefined"
    :placeholder="loading ? '加载中...' : placeholder"
  >
    <template v-if="multiple && showCheckAll" #header>
      <el-checkbox
        v-model="checkAll"
        :indeterminate="indeterminate"
        @change="handleCheckAll"
      >
        全部
      </el-checkbox>
    </template>
    <el-option
      v-for="item of selectOptions"
      :key="item.value"
      :value="item.value"
      :label="item.label"
    />
  </el-select>
</template>

<script setup>
  import { ref, computed, watch, nextTick } from 'vue';
  import { dictItemList } from '@/api/dictionary';
  import { resolveDictCodeAlias } from '@/utils/dictCodeAlias';

  const props = defineProps({
    modelValue: {
      type: [String, Number, Array],
      default: undefined
    },
    label: {
      type: String,
      default: ''
    },
    valueType: {
      type: String,
      default: 'dictItemValue'
    }, // dictItemValue | dictCode
    dictType: {
      type: String,
      default: ''
    },
    placeholder: {
      type: String,
      default: '请选择'
    },
    disabled: {
      type: Boolean,
      default: false
    },
    /** 是否多选 */
    multiple: {
      type: Boolean,
      default: false
    },
    /** 多选时是否折叠标签 */
    collapseTags: {
      type: Boolean,
      default: true
    },
    /** 多选折叠时 hover 展示全部 */
    collapseTagsTooltip: {
      type: Boolean,
      default: true
    },
    /** 多选折叠时最多显示的标签数 */
    maxCollapseTags: {
      type: Number,
      default: 1
    },
    /** 多选时是否显示全选选项 */
    showCheckAll: {
      type: Boolean,
      default: false
    }
  });

  const emit = defineEmits([
    'update:modelValue',
    'update:label',
    'update:options'
  ]);

  const selectOptions = ref([]);
  const rawDictItems = ref([]);
  const loading = ref(false);
  /** 字典加载完成后递增，强制 el-select 在 options 就绪后重新挂载以正确回显 label */
  const selectKey = ref(0);

  const toOptionValue = (item) => {
    const raw =
      props.valueType === 'dictCode' ? item.dictCode : item.dictItemValue;
    return raw === null || raw === undefined ? '' : String(raw);
  };

  /** 将外部传入的 code 解析为当前 valueType 下的 option value（兼容 dictCode / dictItemValue 混用） */
  const resolveOptionValue = (input) => {
    if (input === null || input === undefined || input === '') return '';
    const aliased = resolveDictCodeAlias(props.dictType, input);
    const text = String(aliased);
    const matched = selectOptions.value.find((item) => item.value === text);
    if (matched) return matched.value;
    const raw = rawDictItems.value.find(
      (item) =>
        String(item.dictItemValue ?? '') === text ||
        String(item.dictCode ?? '') === text
    );
    if (!raw) return text;
    return toOptionValue(raw);
  };

  const emitLabelFromValue = (value) => {
    if (props.multiple) {
      const arr = Array.isArray(value) ? value : [];
      const labels = arr
        .map((val) => selectOptions.value.find((item) => item.value === val)?.label)
        .filter(Boolean);
      emit('update:label', labels.join('、'));
      return;
    }
    const text = value === null || value === undefined ? '' : String(value);
    if (!text) {
      emit('update:label', '');
      return;
    }
    emit(
      'update:label',
      selectOptions.value.find((item) => item.value === text)?.label || ''
    );
  };

  const reconcileModelValue = () => {
    if (!selectOptions.value.length) return;
    if (props.multiple) {
      const current = Array.isArray(props.modelValue) ? props.modelValue : [];
      const normalized = current.map((item) => resolveOptionValue(item));
      const changed =
        normalized.length !== current.length ||
        normalized.some((val, index) => val !== String(current[index] ?? ''));
      if (changed) {
        emit('update:modelValue', normalized);
      }
      emitLabelFromValue(changed ? normalized : current.map((item) => resolveOptionValue(item)));
      return;
    }
    const current = props.modelValue;
    if (current === null || current === undefined || current === '') {
      emit('update:label', '');
      return;
    }
    const normalized = resolveOptionValue(current);
    if (normalized !== String(current)) {
      emit('update:modelValue', normalized);
    }
    emitLabelFromValue(normalized);
  };

  const getData = async () => {
    if (!props.dictType) {
      selectOptions.value = [];
      rawDictItems.value = [];
      emit('update:options', []);
      emit('update:label', '');
      return;
    }
    loading.value = true;
    try {
      const res = await dictItemList(props.dictType);
      if (res?.code === 200 && Array.isArray(res?.data)) {
        rawDictItems.value = res.data;
        selectOptions.value = res.data
          .map((item) => ({
            ...item,
            value: toOptionValue(item),
            label: item.dictItemName || ''
          }))
          .filter((item) => item.value !== '');
        emit('update:options', selectOptions.value);
        await nextTick();
        reconcileModelValue();
        selectKey.value += 1;
      } else {
        selectOptions.value = [];
        rawDictItems.value = [];
        emit('update:options', []);
        emit('update:label', '');
      }
    } catch {
      selectOptions.value = [];
      rawDictItems.value = [];
      emit('update:options', []);
      emit('update:label', '');
    } finally {
      loading.value = false;
    }
  };

  watch(
    () => props.dictType,
    () => {
      getData();
    },
    { immediate: true }
  );

  watch(
    () => props.modelValue,
    () => {
      if (!selectOptions.value.length) return;
      emitLabelFromValue(
        props.multiple
          ? (Array.isArray(props.modelValue) ? props.modelValue : []).map((item) =>
              resolveOptionValue(item)
            )
          : resolveOptionValue(props.modelValue)
      );
    },
    { deep: true }
  );

  /** 全选状态 */
  const checkAll = computed({
    get() {
      const val = props.modelValue;
      const arr = Array.isArray(val) ? val : [];
      if (arr.length === 0) return false;
      return arr.length === selectOptions.value.length;
    },
    set() {}
  });

  /** 半选状态 */
  const indeterminate = computed(() => {
    const val = props.modelValue;
    const arr = Array.isArray(val) ? val : [];
    if (arr.length === 0 || arr.length === selectOptions.value.length) return false;
    return arr.length > 0;
  });

  /** 全选事件 */
  const handleCheckAll = (val) => {
    if (val) {
      const allValues = selectOptions.value.map((item) => item.value);
      emit('update:modelValue', allValues);
    } else {
      emit('update:modelValue', []);
    }
  };

  const computedValue = computed({
    get() {
      if (props.multiple) {
        const v = props.modelValue;
        if (Array.isArray(v)) {
          return v.map((item) => resolveOptionValue(item)).filter(Boolean);
        }
        if (v === '' || v === null || v === undefined) return [];
        return [resolveOptionValue(v)].filter(Boolean);
      }
      if (props.modelValue === null || props.modelValue === undefined || props.modelValue === '') {
        return '';
      }
      return resolveOptionValue(props.modelValue);
    },
    set(newValue) {
      if (props.multiple) {
        const arr = (Array.isArray(newValue) ? newValue : []).map((item) =>
          String(item)
        );
        emit('update:modelValue', arr);
        emitLabelFromValue(arr);
      } else {
        const value =
          newValue === null || newValue === undefined ? '' : String(newValue);
        emit('update:modelValue', value);
        emitLabelFromValue(value);
      }
    }
  });
</script>
