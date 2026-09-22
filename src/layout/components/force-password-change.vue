<template>
  <ele-modal
    :model-value="modelValue"
    :width="520"
    :append-to-body="true"
    :destroy-on-close="true"
    title="安全提示"
    @update:modelValue="updateModelValue"
  >
    <div style="margin-bottom: 12px; color: var(--el-text-color-primary); line-height: 1.6">
      您的密码安全程度较低，为了保障您的数据安全和隐私，请尽快修改密码
    </div>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="96px" @submit.prevent="">
      <el-form-item label="新密码" prop="newPwd">
        <el-input
          v-model="form.newPwd"
          show-password
          type="password"
          :maxlength="20"
          placeholder="不少于8位，必须含有大小写英文、数字"
        />
      </el-form-item>
      <el-form-item label="确认新密码" prop="password2">
        <el-input
          v-model="form.password2"
          show-password
          type="password"
          :maxlength="20"
          placeholder="再次输入新密码"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button :loading="loading" @click="onSkip">暂时跳过</el-button>
      <el-button type="primary" :loading="loading" @click="onOk">确定</el-button>
    </template>
  </ele-modal>
</template>

<script setup>
  import { ref, reactive } from 'vue'
  import { EleMessage } from 'ele-admin-plus/es'
  import CryptoJS from 'crypto-js'
  import { updatePassword } from '@/api/layout'

  const props = defineProps({ modelValue: Boolean })
  const emit = defineEmits(['update:modelValue','success','skip'])

  const formRef = ref(null)
  const form = reactive({ newPwd: '', password2: '' })
  const loading = ref(false)

  const rules = {
    newPwd: [
      { required: true, message: '请输入新密码', trigger: 'blur', type: 'string' },
      {
        pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[\S]{8,20}$/,
        message: '密码必须为8-20位,含有大小写英文、数字',
        trigger: 'blur'
      }
    ],
    password2: [
      { required: true, message: '请再次输入新密码', trigger: 'blur', type: 'string' },
      {
        validator: (_r, v, cb) => {
          if (v !== form.newPwd) return cb(new Error('新密码与确认密码不一致'))
          cb()
        },
        trigger: 'blur'
      }
    ]
  }

  const updateModelValue = (v) => emit('update:modelValue', v)

  const onSkip = () => {
    try {
      // 标记本会话已跳过，避免同一会话内再次弹出
      sessionStorage.setItem('skipPwdChange','1')
      // 不清 oldPwdMd5，避免刷新前再次弹
    } catch {}
    emit('skip')
    updateModelValue(false)
  }

  const onOk = () => {
    formRef.value?.validate?.((valid) => {
      if (!valid) return
      const oldPwdMd5 = sessionStorage.getItem('oldPwdMd5') || ''
      // if (!oldPwdMd5) {
      //   EleMessage.error('未获取到旧密码信息，请重新登录')
      //   updateModelValue(false)
      //   return
      // }
      loading.value = true
      updatePassword({  newPwd: CryptoJS.MD5(String(form.newPwd)).toString() })
        .then(() => {
          loading.value = false
          EleMessage.success('设置成功')
          try {
            sessionStorage.removeItem('mustChangePwd')
            sessionStorage.removeItem('oldPwdMd5')
          } catch {}
          emit('success')
          updateModelValue(false)
        })
        .catch((e) => {
          loading.value = false
          EleMessage.error(e?.message || '设置失败')
        })
    })
  }
</script>

<style scoped>
</style>