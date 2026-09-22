<template>
  <div>
    <ele-upload-list
      v-model="images"
      action=""
      :limit="limit"
      :tools="true"
      :headers="headers"
      :multiple="multiple"
      @upload="onUpload1"
      @remove="onRemove1"
      @retry="(item) => onUpload1(item, true)"
      @editUpload="handleEditUpload1"
      :accept="accept"
      :drag="drag"
    >
      <template #icon>
        <div style="line-height: 1">
          <el-icon class="ele-upload-icon">
            <Plus />
          </el-icon>
          <div style="color: #999; font-size: 12px; margin-top: 4px"
            >{{upText}}</div
          >
        </div>
      </template></ele-upload-list
    >
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
  import { Pointer, Remove, Plus } from '@element-plus/icons-vue';
  import { EleMessage } from 'ele-admin-plus';
  import { ElMessageBox } from 'element-plus/es';
  const headers = reactive({
    Authorization: 'Bearer ' + getToken()
  });
  const emits = defineEmits(['uploadImage']);
  const props = defineProps({
    limit: {
      type: Number,
      default: 1
    },
    size: {
      type: Number,
      default: 3
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    drag: {
      type: Boolean,
      default: false,
    },
    accept: {
      type: String,
      default: '.jpg,.jpeg,.png'
    },
    upText: {
      type: String,
      default: '点击上传图片',
    },
    /** 已有图片 URL，编辑回显 */
    imageurl: {
      type: [String, Array],
      default: ''
    }
  });
  const fileType = props.accept.includes('mp3') ? ['mp3'] : ['png', 'jpg', 'jpeg'];
  const images = ref([]);
  const imagePathList = ref([]);

  function normalizeImageUrls(value) {
    if (!value) {
      return [];
    }
    if (Array.isArray(value)) {
      return value.filter(Boolean).map((item) => String(item).trim()).filter(Boolean);
    }
    const url = String(value).trim();
    return url ? [url] : [];
  }

  function toUploadItem(url, index = 0) {
    return {
      key: `preset-${index}-${url}`,
      url,
      status: 'done',
      name: url.split('/').pop() || 'image'
    };
  }

  function syncImagesFromProp(value) {
    const urls = normalizeImageUrls(value);
    images.value = urls.map((url, index) => toUploadItem(url, index));
    imagePathList.value = [...urls];
  }

  watch(
    () => props.imageurl,
    (value) => {
      syncImagesFromProp(value);
    },
    { immediate: true }
  );

  // 上传图片修改-进度条和封面-------------------------------------改写
  const onUpload1 = async (item, retry) => {
    if (!item.file) {
      return;
    }
    // 校检文件类型
    if (fileType.length) {
      let fileExtension = '';
      if (item.file.name.lastIndexOf('.') > -1) {
        fileExtension = item.file.name.slice(
          item.file.name.lastIndexOf('.') + 1
        );
      }
      const isTypeOk = fileType.some((type) => {
        if (item.file.type.indexOf(type) > -1) return true;
        if (fileExtension && fileExtension.indexOf(type) > -1) return true;
        return;
      });
      if (!isTypeOk) {
        EleMessage.error(
          `文件格式不正确, 请上传${fileType.join('/')}格式文件!`
        );
        return;
      }
    }
    if (item.file.size <= 0) {
      EleMessage.error(`请正确上传${ props.accept.includes('jpg') ? '图片' : '文件' }`);
      return;
    }
    if (item.file.size / 1024 / 1024 > props?.size) {
      EleMessage.error(`${ props.accept.includes('jpg') ? '图片' : '文件' }大小不能超过 ${props?.size}MB`);
      return;
    }
    if (!retry) {
      images.value.push({ ...item });
    }
    const fileItem = images.value.find((t) => t.key === item.key);
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
        // 根据images.value中的name与res.name对比来确定插入位置
        const targetIndex = images.value.findIndex(t => t.name === res.name);
        if (targetIndex !== -1) {
          imagePathList.value.splice(targetIndex, 0, res.url);
        } else {
          imagePathList.value.push(res.url);
        }
        emits('uploadImage', imagePathList.value);
      }
    };
    imgUpload(obj);
  };
  /** 删除事件 */
  const onRemove1 = (item) => {
    const index = images.value.indexOf(item);
    images.value.splice(images.value.indexOf(item), 1);
    if (item?.url) {
      imagePathList.value.splice(imagePathList.value.indexOf(item?.url), 1);
    } else {
      imagePathList.value.splice(index, 1);
    }
    emits("uploadImage", imagePathList.value);
  };
  /** 修改时上传事件 */
  const handleEditUpload1 = ({ item, newItem }) => {
    // item 是点击修改按钮对应的 item 数据
    // newItem 是选择文件后返回的新的数据
    // 需要把新的数据更新到旧的数据上
    if (newItem.file.size / 1024 / 1024 > props?.size) {
      EleMessage.error(`${ props.accept.includes('jpg') ? '图片' : '文件' }大小不能超过 ${props?.size}MB`);
      return;
    }
    const index = images.value.indexOf(item);
    const oldItem = images.value.find((t) => t.key === item.key);
    oldItem.status = 'uploading';
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
          oldItem.url = void 0;
          oldItem.name = newItem.name;
          oldItem.file = newItem.file;
          imagePathList.value.splice(index, 1, res.url);
          emits('uploadImage', imagePathList.value);
        }
      };
      imgUpload(obj);
      // 可以在这里使用 newItem 中的 file 上传到后端
    }
  };
  defineExpose({
    setImage: (imagesList) => {
      images.value = imagesList || [];
      imagePathList.value = (imagesList || []).map((item) => item.url).filter(Boolean);
    }
  });
</script>
<style></style>
