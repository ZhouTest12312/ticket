<!-- 用户信息 -->
<template>
  <ele-dropdown
    :items="[
      {
        title: t(`${loginUser.name}(${loginUser.jobNumber})`),
        command: 'profile',
        icon: UserOutlined
      },
      {
        title: t('layout.header.password'),
        command: 'password',
        icon: LockOutlined,
        iconStyle: { transform: 'translateY(-1px)' }
      },
      {
        title: t('layout.header.logout'),
        command: 'logout',
        icon: LogoutOutlined,
        divided: true
      }
    ]"
    :icon-props="{ size: 15 }"
    :popper-options="{
      modifiers: [{ name: 'offset', options: { offset: [0, 5] } }]
    }"
    @command="onUserDropClick"
  >
    <div class="header-avatar">
      <el-avatar
        :size="28"
        :src="avatarUser"
        style="transform: translateY(-1px)"
      />
      <div
        class="hidden-sm-and-down"
        style="margin-left: 4px; line-height: 1.5"
      >
        {{ loginUser.name }}({{ loginUser.jobNumber }})
      </div>
      <el-icon :size="13" style="margin: 0 -4px 0 2px">
        <ArrowDown />
      </el-icon>
    </div>
  </ele-dropdown>
  <!-- 修改密码弹窗 -->
  <password-modal v-model="passwordVisible" />
</template>

<script setup>
  import { computed, ref, unref } from 'vue';
  import { useRouter } from 'vue-router';
  import { useI18n } from 'vue-i18n';
  import { ElMessageBox } from 'element-plus/es';
  import {
    ArrowDown,
    UserOutlined,
    LockOutlined,
    LogoutOutlined
  } from '@/components/icons';
  import { useUserStore } from '@/store/modules/user';
  import avatarUser from '@/assets/login/avatar.jpg';
  import { logout } from '@/utils/common';
  import PasswordModal from './password-modal.vue';

  const { t } = useI18n();
  const { push, currentRoute } = useRouter();
  const userStore = useUserStore();

  /** 是否显示修改密码弹窗 */
  const passwordVisible = ref(false);

  /** 当前用户信息 */
 const loginUser = computed(() => userStore.info ? userStore.info : JSON.parse(localStorage.getItem('info'))?JSON.parse(localStorage.getItem('info')):{});

  /** 用户信息下拉点击 */
  const onUserDropClick = (command) => {
    if (command === 'password') {
      passwordVisible.value = true;
    } else if (command === 'profile') {
      // push('/user/profile');
    } else if (command === 'logout') {
      // 退出登录
      ElMessageBox.confirm(
        t('layout.logout.message'),
        t('layout.logout.title'),
        { type: 'warning', draggable: true }
      )
        .then(() => {
          logout(false, unref(currentRoute).fullPath);
        })
        .catch(() => {});
    }
  };
</script>

<style lang="scss" scoped>
  .header-avatar {
    display: flex;
    align-items: center;
    position: relative;
    height: 100%;
    outline: none;
  }
</style>
