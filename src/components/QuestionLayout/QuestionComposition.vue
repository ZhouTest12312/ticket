<template>
  <div class="blank-container">
    <!-- <div
      v-for="(opt, index) in questionInfo.optionList"
      :key="opt.label"
      :class="['opt-item', { 'is-correct': opt.isCorrect }]"
    >
      <div class="answer">
        <span>空格{{ index + 1 }}：</span>
        <span class="primary-text">{{ opt.answerContent }}</span>
      </div> -->
    <!-- 按选项展示 -->
    <!-- <div v-if="opt.isCorrect" class="correct-tag">正确，{{ opt.maxScore }}分</div> -->
    <!-- 按对错展示 -->
    <div class="correct-tag">正确，{{ rightScore }}分</div>
    <div class="wrong-tag">错误，{{ wrongScore || 0 }}分</div>
    <!-- </div> -->
  </div>
</template>

<script setup>
  import { computed } from 'vue';
  const props = defineProps({
    questionInfo: {
      type: Object,
      default: () => ({})
    }
  });

  const rightScore = computed(() => {
    if (
      props.questionInfo &&
      props.questionInfo.getScoreList &&
      props.questionInfo.getScoreList.length > 0
    ) {
      return props.questionInfo.getScoreList.reduce((prev, current) => {
        return prev + current.rightScore;
      }, 0);
    }
    return '';
  });
  const wrongScore = computed(() => {
    if (
      props.questionInfo &&
      props.questionInfo.getScoreList &&
      props.questionInfo.getScoreList.length > 0
    ) {
      return props.questionInfo.getScoreList.reduce((prev, current) => {
        return prev + current.wrongScore;
      }, 0);
    }
    return '';
  });
</script>

<style lang="scss" scoped>
  .opt-item {
    background: #f8f9fb;
    padding: 12px 15px;
    margin-bottom: 8px;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid transparent;
  }
  .correct-tag {
    color: #67c23a;
    font-size: 12px;
  }
  .wrong-tag {
    color: #ff5f57;
    font-size: 12px;
  }
  .primary-text {
    color: var(--el-color-primary);
  }
</style>
