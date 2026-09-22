<template>
  <div class="options-container">
    <div
      v-for="(opt, index) in questionInfo.selectList"
      :key="opt.sortNum"
      :class="['opt-item', { 'is-correct': opt.isOk }]"
    >
      <div class="opt-item-content">
        <span class="opt-item-sort">{{ opt.sortNum }}.</span>
        <span class="opt-item-content-text" v-html="opt.content"></span>
      </div>
      <div>
        <!-- 按选项展示 -->
        <!-- <div v-if="opt.isCorrect" class="correct-tag">正确，{{ questionInfo.maxScore }}分</div> -->
        <!-- 按对错展示 -->
        <template v-if="scoreType === 1">
          <div v-if="opt.isOk" class="opt-item-score">
            <div class="correct-tag"
              >正确，{{
                questionInfo?.getScoreList[0]?.rightScore || ''
              }}分</div
            >
            <div class="wrong-tag"
              >错误，{{
                questionInfo?.getScoreList[0]?.wrongScore || 0
              }}分</div
            >
          </div>
        </template>
        <div v-else class="opt-item-score">
          <div class="correct-tag" v-if="opt.isOk"
            >正确，{{
              questionInfo?.getScoreList[index]?.rightScore || ''
            }}分</div
          >
          <div class="wrong-tag" v-else
            >错误，{{
              questionInfo?.getScoreList[index]?.wrongScore || 0
            }}分</div
          >
        </div>
      </div>
    </div>
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

  // 赋分方式 1=按题赋分，2=按空格/选项赋分
  const scoreType = computed(() => {
    if (
      props.questionInfo.getScoreList &&
      props.questionInfo.getScoreList.length > 0
    ) {
      return props.questionInfo.getScoreList[0]?.scoreType || '';
    } else {
      return '';
    }
  });
</script>

<style lang="scss" scoped>
  .opt-item {
    background: #f8f9fb;
    padding: 12px 15px;
    margin-bottom: 8px;
    border-radius: 4px;
    font-size: 14px;
    display: flex;
    justify-content: space-between;
    border: 1px solid transparent;
  }
  .opt-item.is-correct {
    background: #f0f9eb;
    border-color: #e1f3d8;
  }
  .correct-tag {
    color: #67c23a;
    font-size: 12px;
  }
  .wrong-tag {
    color: #ff5f57;
    font-size: 12px;
  }
  .opt-item-content {
    display: flex;
    align-items: flex-start;
    text-align: justify;
    :deep(p) {
      margin: 0;
    }
    :deep(span) {
      background-color: transparent !important;
    }
    .opt-item-sort {
      margin-right: 8px;
    }
    .opt-item-content-text {
      :deep(img) {
        width: 100% !important;
        object-fit: contain !important;
      }
    }
  }

  .opt-item-score {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: flex-end;
    margin-left: 10px;
    .correct-tag {
      color: #67c23a;
      font-size: 12px;
      white-space: nowrap;
    }
    .wrong-tag {
      color: #ff5f57;
      font-size: 12px;
      white-space: nowrap;
    }
  }
</style>
