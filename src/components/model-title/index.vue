<template>
  <el-row justify="space-between" v-bind="$attrs">
    <el-space>
      <img v-if="hasIcon" class="img" src="@/assets/order/title_sign.png" />
      <el-row class="title" :style="color">
        <div v-if="required" class="title_tag">*</div>
        <div :style="$attrs.titleStyle">{{ title }}</div>
      </el-row>
    </el-space>
    <slot name="right"></slot>
  </el-row>
</template>

<script setup>
  import { color } from 'echarts/core';

  const props = defineProps({
    title: String,
    required: {
      type: Boolean,
      default: false
    },
    hasIcon: {
      type: Boolean,
      default: true
    },
    color: {
      type: String,
      default: '#0096ff'
    }
  });
</script>
<style lang="scss" scoped>
  .img {
    width: 16px;
    height: 16px;
  }
  .title {
    font-family:
      PingFangSC,
      PingFang SC;
    font-weight: 600;
    font-size: 14px;
    color: #0096ff;
    line-height: 22px;
    .title_tag {
      color: #f5222d;
      font-size: 16px;
    }
  }
</style>
