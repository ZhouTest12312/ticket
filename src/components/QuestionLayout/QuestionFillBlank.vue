<template>
  <div class="blank-container">
    <div
      v-for="opt in questionInfo.optionList"
      :key="opt.label"
      :class="['opt-item', { 'is-correct': opt.isCorrect }]"
    >
      <div class="answer">
        <span>空格{{ opt.sortNum }}：</span>
        <span class="primary-text" v-html="opt.answerContent"></span>
      </div>
      <!-- 按选项展示 -->
      <!-- <div v-if="opt.isCorrect" class="correct-tag">正确，{{ opt.maxScore }}分</div> -->
      <!-- 按对错展示 -->
      <div class="correct-tag">正确，{{ getRightScore(opt) }}分</div>
      <div class="wrong-tag">错误，{{ getWrongScore(opt) }}分</div>
    </div>
  </div>
</template>

<script setup>
  // import { watch } from 'vue';
  const props = defineProps({
    questionInfo: {
      type: Object,
      default: () => ({})
    }
  });

  const getRightScore = (opt) => {
    const scoreList = props.questionInfo.getScoreList || [];
    const score = scoreList.find((item) => item.sortNum === opt.sortNum);
    return score?.rightScore || '-';
  };
  const getWrongScore = (opt) => {
    const scoreList = props.questionInfo.getScoreList || [];
    const score = scoreList.find((item) => item.sortNum === opt.sortNum);
    return score?.wrongScore || 0;
  };

  // watch(
  //   () => props.questionInfo,
  //   (newVal) => {
  //     console.log(newVal);
  //     const scoreMap = {};
  //     if (newVal.getScoreList && newVal.getScoreList.length > 0) {
  //       newVal.getScoreList.forEach((item) => {
  //         scoreMap[item.sortNum] = item;
  //       });
  //     }
  //     newVal.optionList.forEach((item) => {
  //       item.rightScore = scoreMap[item.sortNum]?.rightScore || '';
  //       item.wrongScore = scoreMap[item.sortNum]?.wrongScore || 0;
  //     });
  //   },
  //   {
  //     deep: true,
  //     immediate: true
  //   }
  // );
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
