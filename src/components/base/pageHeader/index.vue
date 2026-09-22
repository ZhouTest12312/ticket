<template>
  <ele-card
    :body-style="{ padding: '16px' }"
    shadow="always"
    class="questionCard"
  >
    <div class="headerCard">
      <img class="headerCard-icon" :src="imgUrl" />
      <div class="headerCard-content">
        <div class="headerCard-content-top">{{ title }}</div>
        <div class="headerCard-content-bottom">
          <div>{{ explain }}</div>
          <slot></slot>
        </div>
        <slot name="extend"></slot>
      </div>
      <slot name="extend-right"></slot>
    </div>
  </ele-card>
</template>

<script setup>
  const props = defineProps({
    imgUrl: String,
    title: String,
    explain: String
  });
</script>

<style lang="scss" scoped>
  .questionCard {
    border-radius: 0;
  }
  .headerCard {
    display: flex;
    margin-right: 12px;
    &-icon {
      width: 56px;
      height: 56px;
      margin-right: 12px;
    }
    &-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      &-top {
        font-family:
          PingFangSC,
          PingFang SC;
        font-weight: 600;
        font-size: 18px;
        color: var(--el-color-primary);
      }
      &-bottom {
        font-family:
          PingFangSC,
          PingFang SC;
        font-weight: 400;
        font-size: 14px;
        color: var(--el-color-primary);
        display: flex;
        align-items: center;
      }
    }
  }
</style>
