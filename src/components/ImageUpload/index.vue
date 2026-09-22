<template>
  <div>
    <ele-upload-list
      v-model="images"
      action=""
      :limit="limit"
      :tools="!disabled"
      :headers="headers"
      :sortable="!disabled"
      @upload="onUpload"
      @remove="onRemove"
      @editUpload="handleEditUpload"
      accept=".jpg,.jpeg,.png"
      :class="{ 'is-disabled': disabled }"
    >
      <template #icon>
        <div style="line-height: 1">
          <el-icon class="ele-upload-icon">
            <Plus />
          </el-icon>
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            点击上传图片
          </div>
        </div>
      </template>
    </ele-upload-list>
  </div>
</template>

<script setup>
  import { getToken } from '@/utils/token-util';
  import { imgUpload } from '@/utils/uploadImg';
  import { reactive, ref, defineEmits, defineProps, watch } from 'vue';
  import { Plus } from '@element-plus/icons-vue';
  import { EleMessage } from 'ele-admin-plus';
  import { ElMessageBox } from 'element-plus/es';

  const props = defineProps({
    // 单文件字符串，多文件数组，直接使用v-model绑定
    modelValue: {
      type: [String, Array],
      default: () => []
    },
    uploadSize: {
      type: Number,
      default: 3
    },
    uploadDimensions: {
      type: Number,
      default: null
    },
    // 最小宽度限制（像素）
    minWidth: {
      type: Number,
      default: null
    },
    // 最小高度限制（像素）
    minHeight: {
      type: Number,
      default: null
    },
    // 最大上传数量，单图为1多图为非1
    limit: {
      type: Number,
      default: 1
    },
    // 是否禁用（已校审状态下禁止上传/删除/编辑）
    disabled: {
      type: Boolean,
      default: false
    }
  });

  const emits = defineEmits(['uploadImage', 'update:modelValue']);

  const images = ref([]);
  const headers = reactive({
    Authorization: 'Bearer ' + getToken()
  });
  const fileType = ['png', 'jpg', 'jpeg'];
  const uploadSize = ref(props.uploadSize);
  const uploadDimensions = ref(props.uploadDimensions);
  const minWidth = ref(props.minWidth);
  const minHeight = ref(props.minHeight);

  const emitChange = () => {
    const validUrls = images.value
      .filter((item) => item.status === 'done' || item.url)
      .map((item) => item.url);

    const result = props.limit === 1 ? validUrls[0] || '' : validUrls;

    emits('update:modelValue', result);
    emits('uploadImage', result);
  };

  // 上传图片修改-进度条和封面
  const onUpload = async (item, retry) => {
    if (props.disabled) return;
    if (!item.file) {
      return;
    }
    // 校检文件类型
    if (fileType.length) {
      let fileExtension = '';
      if (item.file.name.lastIndexOf('.') > -1) {
        fileExtension = item.file.name
          .slice(item.file.name.lastIndexOf('.') + 1)
          .toLowerCase();
      }
      const isTypeOk = fileType.some((type) => {
        if (item.file.type.indexOf(type) > -1) return true;
        if (fileExtension && fileExtension.indexOf(type) > -1) return true;
        return false;
      });
      if (!isTypeOk) {
        EleMessage.error(
          `文件格式不正确, 请上传 ${fileType.join('/')} 格式文件!`
        );
        return;
      }
    }

    if (item.file.size / 1024 / 1024 > uploadSize.value) {
      EleMessage.error(`图片大小不能超过 ${uploadSize.value}MB`);
      return;
    }

    // 尺寸判断
    if (uploadDimensions.value || minWidth.value || minHeight.value) {
      const allowUpload = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const img = new Image();
          img.onload = () => {
            // 精确尺寸判断
            if (uploadDimensions.value) {
              if (
                img.width != uploadDimensions.value ||
                img.height != uploadDimensions.value
              ) {
                EleMessage.error(
                  `请上传尺寸为 ${uploadDimensions.value}*${uploadDimensions.value} 的图片`
                );
                resolve(false);
                return;
              }
            }
            // 最小宽度判断
            if (minWidth.value && img.width < minWidth.value) {
              EleMessage.error(`图片宽度不能小于 ${minWidth.value}px`);
              resolve(false);
              return;
            }
            // 最小高度判断
            if (minHeight.value && img.height < minHeight.value) {
              EleMessage.error(`图片高度不能小于 ${minHeight.value}px`);
              resolve(false);
              return;
            }
            resolve(true);
          };
          img.src = e.target.result;
        };
        reader.readAsDataURL(item.file);
      });
      if (!allowUpload) {
        return;
      }
    }

    if (!retry) {
      images.value.push({ ...item });
    }
    const fileItem = images.value.find((t) => t.key === item.key);
    if (!fileItem) return;

    fileItem.status = 'uploading';
    fileItem.progress = 0;

    const obj = {
      headers: { ...headers },
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
        fileItem.url = res.url;
        emitChange();
      }
    };
    imgUpload(obj);
  };

  /** 删除事件 */
  const onRemove = (item) => {
    if (props.disabled) return;
    ElMessageBox.confirm('确定要删除吗?', '系统提示', {
      type: 'warning',
      draggable: true
    })
      .then(() => {
        const index = images.value.indexOf(item);
        if (index !== -1) {
          images.value.splice(index, 1);
          emitChange();
        }
      })
      .catch(() => {});
  };

  /** 修改时上传事件 */
  const handleEditUpload = ({ item, newItem }) => {
    if (props.disabled) return;
    const oldItem = images.value.find((t) => t.key === item.key);
    if (oldItem) {
      oldItem.status = 'uploading';
      oldItem.progress = 0;
      const obj = {
        headers: { ...headers },
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
          emitChange();
        }
      };
      imgUpload(obj);
    }
  };

  // 数据回显
  watch(
    () => props.modelValue,
    (newModelValue) => {
      if (Array.isArray(newModelValue)) {
        // 多张
        images.value = newModelValue.map((url) => ({
          key: url || Math.random().toString(),
          url: url,
          status: 'done'
        }));
      } else if (
        typeof newModelValue === 'string' &&
        newModelValue.trim() !== ''
      ) {
        // 单张
        images.value = [
          {
            key: newModelValue,
            url: newModelValue,
            status: 'done'
          }
        ];
      } else {
        images.value = [];
      }
    },
    { immediate: true, deep: true }
  );
</script>
<style scoped>
  .is-disabled {
    pointer-events: none;
    opacity: 0.6;
  }
</style>
