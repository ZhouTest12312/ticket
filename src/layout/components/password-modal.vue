<!-- 修改密码弹窗 -->
<template>
  <ele-modal
    form
    :width="420"
    title="修改密码"
    :append-to-body="true"
    :model-value="modelValue"
    @update:modelValue="updateModelValue"
    @closed="onCancel"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent=""
    >
      <el-form-item label="旧密码" prop="oldPwd">
        <el-input
          show-password
          type="password"
          :maxlength="20"
          v-model="form.oldPwd"
          placeholder="请输入旧密码"
        />
      </el-form-item>
      <el-form-item label="新密码" prop="newPwd">
        <el-input
          show-password
          type="password"
          :maxlength="20"
          v-model="form.newPwd"
          placeholder="请输入新密码"
        />
      </el-form-item>
      <el-form-item label="确认密码" prop="password2">
        <el-input
          show-password
          type="password"
          :maxlength="20"
          v-model="form.password2"
          placeholder="请再次输入新密码"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="updateModelValue(false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="onOk">
        保存
      </el-button>
    </template>
  </ele-modal>
</template>

<script setup>
  import { ref, reactive } from 'vue';
  import { EleMessage } from 'ele-admin-plus/es';
  import { useFormData } from '@/utils/use-form-data';
  import { updatePassword } from '@/api/layout';
  import CryptoJS from 'crypto-js';
  const emit = defineEmits(['update:modelValue']);

  defineProps({
    modelValue: Boolean
  });

  /** 提交loading */
  const loading = ref(false);

  /** 表单实例 */
  const formRef = ref(null);

  /** 表单数据 */
  const [form, resetFields] = useFormData({
    oldPwd: '',
    newPwd: '',
    password2: ''
  });

  /** 表单验证规则 */
  const rules = reactive({
    oldPwd: [
      {
        required: true,
        message: '请输入旧密码',
        type: 'string',
        trigger: 'blur'
      }
    ],
    newPwd: [
      {
        required: true,
        message: '请输入新密码',
        type: 'string',
        trigger: 'blur'
      }
    ],
    password2: [
      {
        required: true,
        message: '请再次输入新密码',
        type: 'string',
        trigger: 'blur'
      },
      {
        type: 'string',
        trigger: 'blur',
        validator: (_rule, value, callback) => {
          if (value && value !== form.newPwd) {
            return callback(new Error('两次输入密码不一致'));
          }
          callback();
        }
      }
    ]
  });

  /** 更新modelValue */
  const updateModelValue = (value) => {
    emit('update:modelValue', value);
  };

  /** 保存修改 */
  const onOk = () => {
    formRef.value?.validate?.((valid) => {
      if (!valid) {
        return;
      }
      loading.value = true;
      updatePassword({
        oldPwd: CryptoJS.MD5(String(form.oldPwd)).toString(),
        newPwd: CryptoJS.MD5(String(form.newPwd)).toString()
      })
        .then((msg) => {
          loading.value = false;
          EleMessage.success(msg);
          updateModelValue(false);
        })
        .catch((e) => {
          loading.value = false;
          EleMessage.error(e.message);
        });
    });
  };

  /** 关闭回调 */
  const onCancel = () => {
    resetFields();
    formRef.value?.clearValidate?.();
    loading.value = false;
  };
</script>
