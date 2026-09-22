<template>
  <div class="answer-container">
    <!-- <div class="question-stem" v-html="questionInfo.topicDescribe"></div> -->

    <!-- 题干图片组 -->
    <!-- <div
      class="topic-img"
      v-if="questionInfo.topicImages && questionInfo.topicImages.length > 0"
      :class="`img-count-${questionInfo.topicImages.length}`"
    >
      <div
        class="topic-img-item"
        v-for="(item, index) in questionInfo.topicImages"
        :key="index"
      >
        <el-image
          :src="item.url"
          :preview-src-list="questionInfo.topicImages.map((img) => img.url)"
          :initial-index="index"
          fit="contain"
          hide-on-click-modal
        />
      </div>
    </div> -->

    <div class="opt-item" v-if="questionInfo.subQuestionObject">
      <!-- 子题目描述 -->
      <div v-html="questionInfo.subQuestionObject?.topicDescribe"></div>

      <!-- 子题目图片组 -->
      <div
        class="topic-img"
        v-if="
          questionInfo.subQuestionObject?.imageList &&
          questionInfo.subQuestionObject?.imageList.length > 0
        "
        :class="`img-count-${questionInfo.subQuestionObject?.imageList.length}`"
      >
        <div
          class="topic-img-item"
          v-for="(img, index) in questionInfo.subQuestionObject?.imageList"
          :key="index"
        >
          <el-image
            :src="img"
            :preview-src-list="questionInfo.subQuestionObject?.imageList"
            :initial-index="index"
            fit="contain"
            hide-on-click-modal
          />
        </div>
      </div>

      <!-- 参考答案 -->
      <div class="answer-box">
        <div class="answer-title">参考答案</div>
        <div
          class="answer"
          v-for="(opt, index) in questionInfo.subQuestionObject?.optionList"
          :key="index"
        >
          <span class="primary-text" v-html="opt?.answerContent"></span>
        </div>
      </div>

      <div>
        <!-- 按选项展示 -->
        <!-- <div class="correct-tag">正确，{{ questionInfo.maxScore }}分</div> -->
        <!-- 按对错展示 -->
        <div class="correct-tag">正确，{{ rightScore }}分</div>
        <div class="wrong-tag">错误，{{ wrongScore || 0 }}分</div>
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

  const rightScore = computed(() => {
    if (
      props.questionInfo.subQuestionObject &&
      props.questionInfo.getScoreList?.length > 0
    ) {
      const findScore = props.questionInfo.getScoreList.find(
        (item) => item.selectId === props.questionInfo.subQuestionObject.topicId
      );
      if (findScore) {
        return findScore.rightScore;
      }
      return '';
    }
    return '';
  });

  const wrongScore = computed(() => {
    if (
      props.questionInfo.subQuestionObject &&
      props.questionInfo.getScoreList?.length > 0
    ) {
      const findScore = props.questionInfo.getScoreList.find(
        (item) => item.selectId === props.questionInfo.subQuestionObject.topicId
      );
      if (findScore) {
        return findScore.wrongScore;
      }
      return '';
    }
    return '';
  });
</script>

<style lang="scss" scoped>
  .question-stem {
    font-size: 16px;
    line-height: 1.6;
    margin-top: 24px;
    margin-bottom: 24px;
    color: #333;
  }

  .topic-img {
    margin-bottom: 24px;
    display: grid;
    gap: 12px;
    max-width: 650px;

    &.img-count-1 {
      grid-template-columns: 1fr;
      max-width: 400px;

      .topic-img-item {
        aspect-ratio: auto;
        background: transparent;
        border: none;

        :deep(.el-image) {
          max-height: 300px;
          .el-image__inner {
            object-position: left center;
          }
        }
      }
    }

    &.img-count-2 {
      grid-template-columns: repeat(2, 1fr);
    }

    &.img-count-3,
    &.img-count-5 {
      grid-template-columns: repeat(3, 1fr);
    }

    &.img-count-4 {
      grid-template-columns: repeat(2, 1fr);
      max-width: 450px;
    }

    &-item {
      width: 100%;
      aspect-ratio: 4 / 3;
      border: 1px solid #ebeef5;
      border-radius: 6px;
      background-color: #fafafa;
      overflow: hidden;
      display: flex;
      justify-content: center;
      align-items: center;

      :deep(.el-image) {
        width: 100%;
        height: 100%;

        .el-image__inner {
          width: 100%;
          height: 100%;
          cursor: zoom-in;
          transition: transform 0.3s ease;
        }

        .el-image__inner:hover {
          transform: scale(1.03);
        }
      }
    }
  }

  .opt-item {
    background: #f8f9fb;
    padding: 12px 15px;
    margin-bottom: 8px;
    border-radius: 4px;
    font-size: 14px;
    border: 1px solid transparent;
    .correct-tag {
      color: #67c23a;
      font-size: 12px;
    }
    .wrong-tag {
      color: #ff5f57;
      font-size: 12px;
    }
  }

  .answer-box {
    background-color: #fff;
    border-radius: 8px;
    padding: 12px;
    .answer-title {
      font-size: 14px;
      font-weight: bold;
    }
    .answer {
      .primary-text {
        display: inline-block;
        max-width: 100%;
        :deep(img) {
          max-width: 100%;
          height: auto;
          display: inline-block;
          vertical-align: middle;
        }
      }
    }
  }
</style>
