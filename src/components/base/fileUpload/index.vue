<template>
  <div>
    <el-upload
      v-show="progress == 0"
      ref="uploadRef"
      action=""
      :headers="headers"
      :show-file-list="false"
      :http-request="fileUpload"
      :before-upload="handleBeforeUpload"
      :on-success="handlePreview"
      :on-progress="handleProgress"
      class="upload"
      :limit="1"
      accept=".xls,.xlsx,.xlsm"
    >
      <el-row class="uploadArea" align="middle">
        <el-icon :size="30" color="#bbbbbb" style="margin-right: 10px">
          <Plus />
        </el-icon>
        <div>
          <div class="uploadText">添加导入文件</div>
          <div class="formatText">
            只能上传csv,xls,xlsx文件,文件大小建议不超过3Mb
          </div>
        </div>
      </el-row>
    </el-upload>
    <!-- 文件上传进度显示 -->
    <el-row
      v-show="progress !== 0"
      class="progress"
      justify="space-between"
      align="middle"
    >
      <el-row class="progress-doc">
        <el-icon :size="30" color="#ffffff"><DocumentRemove /></el-icon>
      </el-row>
      <div class="progress-main">
        <div>{{ fileName }}</div>
        <div class="fileSize">{{ fileSize }}</div>
        <el-progress
          style="flex: 1"
          :text-inside="true"
          :stroke-width="16"
          :percentage="progress"
        />
      </div>
      <el-icon
        v-if="progress == 100 && !importing"
        style="cursor: pointer"
        :size="25"
        @click="clearFile"
      >
        <Close />
      </el-icon>
    </el-row>
  </div>
</template>
<script setup>
  import { imgUpload } from '@/utils/uploadImg';
  import { getToken } from '@/utils/token-util';
  import { Rank, Plus, Close, DocumentRemove } from '@element-plus/icons-vue';

  const emits = defineEmits(['update:modelValue', 'update']);

  const props = defineProps({
    needUrl: {
      type: Boolean,
      default: false
    }
  });

  // 批量导入相关状态
  const batchImportVisible = ref(false);
  const importing = ref(false);
  const uploadRef = ref();
  const importResult = ref(null);
  const importRecords = ref([]);

  // 文件上传相关状态
  const progress = ref(0);
  const fileName = ref('');
  const fileSize = ref('');
  const uploadedFile = ref(null); // 保存已上传的文件
  const headers = reactive({
    Authorization: 'Bearer ' + getToken()
  });

  /* 下载导入课次模板 */
  const downloadTemplate = () => {
    if (templateUrl.value) {
      xhrequest(templateUrl.value, function (blob, type) {
        downloadBlob(blob, `${templateFileName.value}.xlsx`);
      });
    } else {
      EleMessage.error('暂无导入模板');
    }
  };

  // 下载文件
  async function xhrequest(url, callback) {
    let DownUrl = url;
    let data = await fetch(DownUrl)
      .then((response) => response.blob())
      .then((res) => {
        //获取文件格式
        var index = DownUrl.lastIndexOf('.');
        //获取文件后缀判断文件格式
        var fileType = DownUrl.substr(index + 1);
        let blod = new Blob([res]);
        if (typeof callback == 'function') {
          callback(blod, fileType);
        }
      });
    return data;
  }

  const downloadBlob = (blob, fileName) => {
    try {
      const href = window.URL.createObjectURL(blob); //创建下载的链接
      if (window.navigator.msSaveBlob) {
        window.navigator.msSaveBlob(blob, fileName);
      } else {
        // 谷歌浏览器 创建a标签 添加download属性下载
        const downloadElement = document.createElement('a');
        downloadElement.href = href;
        downloadElement.target = '_blank';
        downloadElement.download = fileName;
        document.body.appendChild(downloadElement);
        downloadElement.click(); // 点击下载
        document.body.removeChild(downloadElement); // 下载完成移除元素
        window.URL.revokeObjectURL(href); // 释放掉blob对象
      }
    } catch (e) {
      console.log('下载失败', e);
    }
  };

  const fileType = ['xlsx', 'xls', '.xlsm'];
  // 上传前校检格式和大小
  const handleBeforeUpload = (file) => {
    // 校检文件类型
    if (fileType.length) {
      let fileExtension = '';
      if (file.name.lastIndexOf('.') > -1) {
        fileExtension = file.name.slice(file.name.lastIndexOf('.') + 1);
      }
      const isTypeOk = fileType.some((type) => {
        if (file.type.indexOf(type) > -1) return true;
        if (fileExtension && fileExtension.indexOf(type) > -1) return true;
        return false;
      });
      if (!isTypeOk) {
        message.error(`文件格式不正确, 请上传${fileType.join('/')}格式文件!`);
        return false;
      }
    }
    // 校检文件大小
    if (file.size > 1024 * 1024 * 10) {
      message.error(`上传文件大小不能超过10MB!`);
      return false;
    }
    return true;
  };

  // 文件上传成功的函数（用于文件上传成功之后的逻辑处理）
  const handlePreview = (file, fileArr) => {
    importing.value = false;
    emits('update', file);
  };

  const resultInfo = ref({});
  const uploadResult = (option) => {
    resultInfo.value = option;
  };

  const needUrl = ref(props.needUrl);
  // 开始上传文件
  const fileUpload = (opt) => {
    fileName.value = opt.file.name;
    const fileSizeInBytes = opt.file.size;
    if (fileSizeInBytes < 1024 * 1024) {
      fileSize.value = (fileSizeInBytes / 1024).toFixed(2) + 'kb';
    } else {
      fileSize.value = (fileSizeInBytes / (1024 * 1024)).toFixed(2) + 'mb';
    }
    progress.value = 0;
    if (needUrl.value) {
      imgUpload(opt);
    } else {
      emits('update', opt.file);
    }
  };

  const showLoading = ref(false);
  // 上传进度处理
  const handleProgress = (file, fileArr) => {
    progress.value = file.progress;
    showLoading.value = file.progress == 100 ? true : false;
  };

  // 清除文件
  const clearFile = () => {
    progress.value = 0;
    fileName.value = '';
    fileSize.value = '';
    uploadedFile.value = null;
    importing.value = false;
    importResult.value = null;
    uploadRef.value?.clearFiles();
    emits('update', null);
  };
</script>
<style lang="scss" scoped>
  .title {
    display: flex;
    justify-content: space-between;
    padding-top: 20px;
    background-color: #ffffff;
    top: 0;
    position: sticky;
    z-index: 1;

    .input-with-select {
      width: 200px;
    }
  }

  .upload {
    cursor: pointer;
    color: var(--el-color-primary);
  }

  .upload {
    width: 100%;

    :deep(.el-upload) {
      width: 100%;
    }
  }

  .uploadArea {
    width: 100%;
    padding: 15px 20px;
    border-radius: 16px;
    box-sizing: border-box;
    background-color: rgba(194, 194, 194, 0.03);
    border: 2px dashed #bbbbbb;
    margin-bottom: 10px;

    .uploadText {
      color: #999;
      font-size: 14px;
      margin-bottom: 5px;
    }

    .formatText {
      font-size: 12px;
      color: rgba(223, 84, 44, 1);
    }
  }

  .progress {
    width: 100%;
    background-color: #f8f8f8;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 15px;

    &-doc {
      width: 60px;
      height: 60px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #a7abb0;
    }

    &-main {
      flex: 1;
      margin: 0 40px 0 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      font-size: 14px;

      .fileSize {
        font-size: 12px;
        color: #666;
      }
    }
  }

  ::v-deep .el-upload {
    width: 100%;
  }

  .main_table {
    margin: 20px 0;
  }

  .delectColor {
    color: red;
  }

  .isDelete {
    color: #ddd;
  }

  ::v-deep .el-tag--plain.el-tag--info {
    color: #9182cc !important;
    border: 1px solid #9182cc !important;
  }

  :deep(.el-tag) {
    white-space: normal;
    height: auto;
    line-height: 18px;
  }

  .result-stats {
    margin-top: 30px;
    font-size: 16px;
    color: #303133;
    line-height: 1.8;
    text-align: center;
    letter-spacing: 0.5px;

    .total-count {
      font-size: 20px;
      font-weight: 700;
      color: #303133;
      margin: 0 4px;
    }

    .success-count {
      font-size: 18px;
      font-weight: 600;
      color: #67c23a;
      margin: 0 4px;
    }

    .failed-count {
      font-size: 18px;
      font-weight: 600;
      color: #f56c6c;
      margin: 0 4px;
    }
  }

  .loading {
    flex: 1;
  }

  .result {
    line-height: 30px;
    font-size: 14px;
    padding: 60px 30px 0;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
  }
</style>
