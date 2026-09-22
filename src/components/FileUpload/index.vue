<template>
  <div>
    <ele-upload-list
      ref="uploadListRef"
      v-model="filesList"
      :tools="true"
      action=""
      :limit="limit"
      :multiple="multiple"
      :headers="headers"
      :accept="accept"
      :drag="drag"
      @upload="onUpload"
      @editUpload="handleEditUpload"
      @remove="onRemove"
    >
      <template #icon>
        <div style="line-height: 1">
          <el-icon class="ele-upload-icon">
            <Plus />
          </el-icon>
          <div style="color: #999; font-size: 12px; margin-top: 4px">{{drag ? '点击/拖拽上传图片' : '点击上传文件'}}</div>
        </div>
      </template>
      <template #thumbnail="{ item }">
        <el-image v-if="isFileType(item.url, 'image')" :src="item.url" :preview-src-list="[item.url]" fit="contain" style="width: 100%; height: 100%;" @click.stop></el-image>
        <div v-else class="ele-upload-thumbnail" @click.stop="handlePreview(item)">
          <el-icon :size="22">
            <video-camera v-if="isFileType(item.url, 'video')" />
            <Headset v-if="isFileType(item.url, 'audio')" />
            <document v-else />
          </el-icon>
          <div>{{ item.name }}</div>
        </div>
        <div class="ele-upload-tools custom-upload-tools">
          <div class="ele-upload-tool" @click.stop="handlePreview(item)">
            <i class="el-icon ele-upload-tool-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="4"><path d="M24 40C38 40 45 28 45 24C45 20 38 8 24 8C10 8 3 20 3 24C3 28 10 40 24 40Z"></path><path d="M24 32C28 32 32 28 32 24C32 20 28 16 24 16C20 16 16 20 16 24C16 28 20 32 24 32Z"></path>
              </svg>
            </i>
            <div class="ele-upload-tool-text">
              {{ (isFileType(item.url, 'image') || isFileType(item.url, 'video') || isFileType(item.url, 'pdf')) ? "预览" : "下载" }}
            </div>
          </div>
          <div class="ele-upload-tool" @click.stop="handleEdit(item)">
            <i class="el-icon ele-upload-tool-icon">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 42H44"></path><path d="M11 25V33H19L41 11 33 3 11 25Z"></path>
              </svg>
            </i>
            <div class="ele-upload-tool-text">修改</div>
          </div>
        </div>
      </template>
    </ele-upload-list>
    <ele-modal v-model="playerVisible" destroy-on-close title="视频预览">
      <ele-xg-player :config="playerConfig" />
    </ele-modal>
    <ele-image-viewer
      v-model="showImageViewer"
      :url-list="urlList"
      :initial-index="0"
    />
  </div>
</template>
<script setup>
  import { getToken } from '@/utils/token-util';
  import { imgUpload } from '@/utils/uploadImg';
  import {
    reactive,
    ref,
    defineEmits,
    defineProps,
    watch,
    toRaw,
    computed
  } from 'vue';
  import { Pointer, Remove ,Plus, VideoCamera, Headset, Document, Picture } from '@element-plus/icons-vue';
  import { EleMessage } from 'ele-admin-plus';
  import { ElMessageBox } from 'element-plus/es';
  const props = defineProps({
    fileList: Array,
    size: {
      type: Number,
      default: 5
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    drag: {
      type: Boolean,
      default: false,
    },
    limit: {
      type: Number,
      default: 1
    },
    accept: {
      type: String,
      default: '.jpg,.jpeg,.png',
    }
  });
  const emits = defineEmits(['uploadFile']);

  const uploadListRef = ref(null);
  const filesList = ref([]);
  const headers = reactive({
    Authorization: 'Bearer ' + getToken()
  });
  /* 是否打开视频预览弹窗 */
  const playerVisible = ref(false);

  /* 视频播放器配置 */
  const playerConfig = reactive({
    lang: 'zh-cn',
    fluid: true,
    url: void 0,
    volume: 0,
    autoplay: true
  });

  const showImageViewer = ref(false);
  const urlList = ref([]);

  // 上传文件
  const onUpload = async (item, retry) => {
    if (!item.file) {
      return;
    }
    const extension = item.name?.split('.').pop().toLowerCase();
    if (props.accept.indexOf(extension) === -1) {
      EleMessage.error(`文件格式不正确, 请上传${props.accept}格式文件!`);
      return;
    }
    if (item.file.size / 1024 / 1024 > props.size) {
      EleMessage.error(`文件大小不能超过 ${props.size}MB`);
      return;
    }
    if (!retry) {
      filesList.value.push({ ...item });
    }
    const fileItem = filesList.value.find((t) => t.key === item.key);
    fileItem.status = 'uploading';
    fileItem.progress = 0;
    const obj = {
      headers: {
        Authorization: headers
      },
      withCredentials: false,
      file: item.file,
      data: {},
      method: 'post',
      filename: 'file',
      action: '',
      onError: (err) => {
        fileItem.status = 'exception';
        EleMessage.error('上传失败');
      },
      onProgress: (evt) => {
        fileItem.progress = evt.progress;
        if (fileItem.progress === 100) {
          setTimeout(() => {
            fileItem.status = 'done';
          }, 500);
        }
      },
      onSuccess: (res) => {
        // 修改为直接发送当前文件列表
        fileItem.url = res.url;
        const currentFiles = filesList.value.map(file => ({
          url: file.url,
          name: file.name
        })).filter(file => file.url); // 过滤掉没有url的文件
        emits('uploadFile', currentFiles);
      }
    };
    imgUpload(obj);
  };
  /** 删除事件 */
  const onRemove = (item) => {
    ElMessageBox.confirm('确定要删除吗?', '系统提示', {
      type: 'warning',
      draggable: true
    })
    .then(() => {
      filesList.value.splice(filesList.value.indexOf(item), 1);
      // 修改为直接发送当前文件列表
      const currentFiles = filesList.value.map(file => ({
        url: file.url,
        name: file.name
      })).filter(file => file.url); // 过滤掉没有url的文件
      emits('uploadFile', currentFiles);
    })
    .catch(() => {});
  };
  /** 修改时上传事件 */
  const handleEditUpload = ({ item, newItem }) => {
    // item 是点击修改按钮对应的 item 数据
    // newItem 是选择文件后返回的新的数据
    // 需要把新的数据更新到旧的数据上
    const extension = newItem.name?.split('.').pop().toLowerCase();
    if (props.accept.indexOf(extension) === -1) {
      EleMessage.error(`文件格式不正确, 请上传${props.accept}格式文件!`);
      return;
    }
    if (newItem.file.size / 1024 / 1024 > props.size) {
      EleMessage.error(`文件大小不能超过 ${props.size}MB`);
      return;
    }
    const oldItem = filesList.value.find((t) => t.key === item.key);
    oldItem.status = 'uploading';
    oldItem.progress = 0;
    if (oldItem) {
      const obj = {
        headers: {
          Authorization: headers
        },
        withCredentials: false,
        file: newItem.file,
        data: {},
        method: 'post',
        filename: 'file',
        action: '',
        onError: (err) => {
          oldItem.status = 'exception';
          EleMessage.error('上传失败');
        },
        onProgress: (evt) => {
          oldItem.progress = evt.progress;
          if (oldItem.progress === 100) {
            setTimeout(() => {
              oldItem.status = 'done';
            }, 500);
          }
        },
        onSuccess: (res) => {
          oldItem.url = res.url;
          oldItem.name = newItem.name;
          oldItem.file = newItem.file;
          // 修改为直接发送当前文件列表
          const currentFiles = filesList.value.map(file => ({
            url: file.url,
            name: file.name
          })).filter(file => file.url); // 过滤掉没有url的文件
          emits('uploadFile', currentFiles);
        }
      };
      imgUpload(obj);
      // 可以在这里使用 newItem 中的 file 上传到后端
    }
  };

  const handlePreview = item => {
    // 图片预览
    if (isFileType(item.url, 'image')) {
      showImageViewer.value = true;
      urlList.value = [item.url];
      return;
    }
    // 视频预览
    if (isFileType(item.url, 'video')) {
      playerVisible.value = true;
      playerConfig.url = item.url;
      return;
    }
    window.open(item.url);
  };

  const handleEdit = item => {
    uploadListRef.value.handleItemEdit(item);
  }

  const isFileType = (url, type) => {
    const fileTypes = {
      'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'],
      'video': ['.mp4', '.avi', '.wmv', '.mov', '.flv', '.mkv'],
      'pdf': ['.pdf', '.PDF'],
      'audio': ['.mp3'],
    }
    const extension = url?.split('.').pop().toLowerCase();
    return fileTypes[type]?.includes(`.${extension}`);
  }

  watch(
    () => props.fileList,
    (newValue, oldValue) => {
      if(newValue){
        // !!!这个地方后端返回的时候需要给name，如果没有name那么文件列表则不会显示名字，当然如果不需要回显的话是没有影响的
        filesList.value = newValue;
      }else{
        filesList.value = [];
      }
    },{ immediate: true ,deep:true}
  );
</script>

<style lang="scss" scoped>
:deep(.ele-upload-tools) {
  display: none !important;
}
:deep(.ele-upload-tools.custom-upload-tools) {
  display: flex !important;
}
</style>
