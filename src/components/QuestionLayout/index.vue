<template>
  <div class="question-main" ref="questionStemRef">
    <!-- 题目头部信息 -->
    <div class="question-header">
      <div :class="['question-type-tag', questionClassName]">{{
        questionType
      }}</div>
      <div class="question-id">{{ questionInfo.topicCode }}</div>
    </div>
    <div class="q-body">
      <div class="question-stem" v-html="questionInfo.topicDescribe"></div>

      <!-- 题干图片组 -->
      <div
        class="topic-img"
        v-if="questionInfo.imageList && questionInfo.imageList.length > 0"
        :class="`img-count-${questionInfo.imageList.length}`"
      >
        <div
          class="topic-img-item"
          v-for="(item, index) in questionInfo.imageList"
          :key="index"
        >
          <el-image
            :src="item"
            :preview-src-list="questionInfo.imageList"
            :initial-index="index"
            fit="contain"
            hide-on-click-modal
          />
        </div>
      </div>

      <!-- 题目组的时候需要展示解答题题干 -->
      <!-- <template v-if="questionInfo.topicType === 5">
        <div class="question-stem" v-html="questionInfo.topicDescribe"></div>
        <div
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
        </div>
      </template> -->
      <QuestionChoice
        v-if="[0, 1].includes(questionInfo.topicType)"
        :question-info="questionInfo"
      />
      <QuestionFillBlank
        v-if="[2].includes(questionInfo.topicType)"
        :question-info="questionInfo"
      />
      <QuestionComposition
        v-if="[4].includes(questionInfo.topicType)"
        :question-info="questionInfo"
      />
      <QuestionAnswer
        v-if="questionInfo.topicType === 3"
        :question-info="questionInfo"
      />
    </div>
  </div>
</template>

<script setup>
  // 组件
  import { computed, nextTick, onMounted, ref, watch } from 'vue';
  import QuestionChoice from './QuestionChoice.vue';
  import QuestionFillBlank from './QuestionFillBlank.vue';
  import QuestionAnswer from './QuestionAnswer.vue';
  import QuestionComposition from './QuestionComposition.vue';
  import katex from 'katex';
  import 'katex/dist/katex.min.css';

  // 工具
  import { questionTypeList } from '@/utils/constants';

  const questionClassNameMap = {
    0: 'single-choice',
    1: 'multiple-choice',
    2: 'fill-in-blank',
    3: 'question-answer',
    4: 'composition',
    5: 'question-group'
  };

  const props = defineProps({
    questionInfo: {
      type: Object,
      default: () => ({})
    }
  });

  const questionStemRef = ref(null);
  const renderFormula = () => {
    if (!questionStemRef.value) return;

    // 获取容器内所有公式节点（wangEditor v5 标识为 data-w-e-type="formula"）
    const formulaNodes = questionStemRef.value.querySelectorAll(
      '[data-w-e-type="formula"]'
    );

    formulaNodes.forEach((node) => {
      // 避免重复渲染（如果已经渲染过，KaTeX通常会生成 .katex 结构的子元素）
      if (node.querySelector('.katex')) return;

      const latex = node.getAttribute('data-value');
      if (latex) {
        try {
          // 使用 KaTeX 渲染
          katex.render(latex, node, {
            throwOnError: false, // 渲染失败时不抛出错误，而是显示源码
            displayMode: false // false=行内公式，true=块级公式
          });
        } catch (err) {
          console.error('公式渲染失败:', err);
        }
      }
    });
  };

  onMounted(() => {
    renderFormula();
  });

  watch(
    () => props.questionInfo,
    () => {
      nextTick(() => {
        renderFormula();
      });
    },
    { deep: true }
  );

  const questionType = computed(() => {
    return (
      questionTypeList.find(
        (item) => item.value === props.questionInfo.topicType
      )?.label || '未知'
    );
  });

  const questionClassName = computed(() => {
    return (
      questionClassNameMap[props.questionInfo.topicType] || 'single-choice'
    );
  });
</script>

<style lang="scss" scoped>
  .question-main {
    flex: 1;
    background: #fff;
    // border-radius: 4px;
    border-radius: 0 !important;
    padding: 20px;
    box-shadow: 0 2px 10px 0 rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .question-header {
    display: flex;
    align-items: center;

    .question-type-tag {
      padding: 4px 12px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;

      &.single-choice,
      &.multiple-choice {
        background-color: #10b981;
        color: white;
      }

      &.fill-in-blank {
        background-color: #6155f5;
        color: white;
      }

      &.question-answer {
        background-color: #cb30e0;
        color: white;
      }

      &.composition {
        background-color: #00c8b3;
        color: white;
      }

      &.question-group {
        background-color: #ff8d28;
        color: white;
      }
    }

    .question-id {
      font-size: 14px;
      color: #666;
      margin: 0 16px;
    }
  }
  .q-body {
    font-size: 15px;
    line-height: 1.8;
    color: #333;
    .question-stem {
      font-size: 16px;
      line-height: 1.6;
      margin-top: 24px;
      margin-bottom: 24px;
      color: #333;
      text-align: justify;
      :deep(img) {
        width: 100% !important;
        object-fit: contain !important;
      }
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
  }
</style>
