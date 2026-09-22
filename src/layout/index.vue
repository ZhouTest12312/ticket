<template>
  <ele-pro-layout
    :menus="menus"
    :tabs="tabs"
    :collapse="collapse"
    :compact="compact"
    :maximized="maximized"
    :tab-bar="tabBar ? (tabInHeader ? 'header' : true) : false"
    :breadcrumb="layout === 'default' && (!tabBar || !tabInHeader)"
    :layout="layout"
    :sidebar-layout="sidebarLayout"
    :header-style="headerStyle"
    :sidebar-style="sidebarStyle"
    :tab-style="tabStyle"
    :fixed-header="fixedHeader"
    :fixed-sidebar="fixedSidebar"
    :fixed-body="fixedBody"
    :fluid="fluid"
    :logo-in-header="logoInHeader"
    :colorful-icon="colorfulIcon"
    :unique-opened="uniqueOpened"
    :fixed-home="fixedHome"
    :home-path="HOME_PATH"
    :redirectPath="REDIRECT_PATH"
    :locale="locale"
    :i18n="i18n"
    :tab-sortable="!mobileDevice"
    :tab-context-menu="{
      iconProps: { size: 15 },
      popperOptions: { strategy: 'fixed' }
    }"
    :tab-context-menus="tabContext"
    :nav-trigger="layout === 'top' ? void 0 : menuItemTrigger"
    :box-trigger="menuItemTrigger"
    :keep-alive="TAB_KEEP_ALIVE"
    :transition-name="transitionName"
    :ellipsis-props="{ hideTimeout: 800 }"
    :responsive="responsive"
    @update:collapse="updateCollapse"
    @update:maximized="updateMaximized"
    @tabAdd="addPageTab"
    @tabClick="onTabClick"
    @tabRemove="removePageTab"
    @tabContextMenu="onTabContextMenu"
    @tabSortChange="setPageTabs"
    @bodySizeChange="onBodySizeChange"
    class="admin-layout"
    append-to="body"
  >
    <router-layout class="min_class" />
    <!-- logo -->

    <template #logoTitle>
      <div class="logoBox" :class="{ 'logoBox--ticket': isTicketBrand }">
        <template v-if="isTicketBrand">
          <img src="@/assets/ticket-logo.svg" class="logo logo--ticket" alt="" />
          <div v-if="!collapse" class="brandWord">
            <span class="brandWord__name">客户工单管理系统</span>
          </div>
        </template>
        <template v-else>
          <img src="@/assets/logo.png" class="logo" />
          <img v-if="!collapse" src="@/assets/company.png" class="logoTitle" />
          <div v-if="!collapse && envTest" class="logotext">| {{ envTest }}</div>
        </template>
      </div>
    </template>
    <!-- 顶栏左侧按钮 -->
    <template #left="{ sidebar }">
      <!-- 折叠侧栏 -->

      <layout-tool v-if="sidebar" @click="updateCollapse(!collapse)">
        <el-icon style="transform: scale(1.14)">
          <MenuUnfoldOutlined v-if="collapse" />
          <MenuFoldOutlined v-else />
        </el-icon>
      </layout-tool>
      <!-- 返回 -->
      <layout-tool
        v-if="layout !== 'top' && layout !== 'mix' && !(tabBar && tabInHeader)"
        class="hidden-sm-and-down"
        @click="handleBack()"
      >
        <el-icon style="transform: scale(1.2)">
          <ArrowLeft />
        </el-icon>
      </layout-tool>
      <!-- 刷新 -->
      <layout-tool
        v-if="layout !== 'top' && layout !== 'mix' && !(tabBar && tabInHeader)"
        class="hidden-sm-and-down"
        @click="torefresh()"
      >
        <el-icon style="transform: scale(1.09)">
          <ReloadOutlined />
        </el-icon>
      </layout-tool>
    </template>
    <!-- 顶栏右侧按钮 -->
    <template #right>
      <!-- 全屏切换 -->
      <!-- <layout-tool class="hidden-sm-and-down" @click="toggleFullscreen">
        <el-icon style="transform: scale(1.18)">
          <CompressOutlined v-if="isFullscreen" style="stroke-width: 4" />
          <ExpandOutlined v-else style="stroke-width: 4" />
        </el-icon>
      </layout-tool> -->
      <!-- 语言切换 -->
      <!-- <layout-tool :class="{ 'hidden-sm-and-down': tabBar && tabInHeader }">
        <i18n-icon :icon-style="{ transform: 'scale(1.15)' }" />
      </layout-tool> -->
      <!-- 消息通知 -->
      <layout-tool :class="{ 'hidden-sm-and-down': tabBar && tabInHeader }">
        <header-notice />
      </layout-tool>
      <!-- 用户信息 -->
      <layout-tool>
        <header-user />
      </layout-tool>
      <!-- 主题设置 -->
      <layout-tool @click="openSetting">
        <el-icon>
          <MoreOutlined />
        </el-icon>
      </layout-tool>
    </template>
    <!-- 页签栏右侧下拉菜单 -->
    <template v-if="tabBar && !tabInHeader" #tabExtra="{ active }">
      <tab-dropdown
        :items="tabExtra"
        :dropdown-props="{
          iconProps: { size: 15 },
          popperOptions: { strategy: 'fixed' }
        }"
        @menuClick="(key) => onTabDropdownMenu(key, active)"
      />
    </template>
    <!-- 折叠双侧栏一级 -->
    <template #boxBottom>
      <div :style="{ flexShrink: 0, padding: roundedTheme ? '4px 8px' : 0 }">
        <layout-tool style="height: 32px" @click="updateCompact(!compact)">
          <el-icon style="transform: scale(1.05)">
            <MenuUnfoldOutlined v-if="compact" />
            <MenuFoldOutlined v-else />
          </el-icon>
        </layout-tool>
      </div>
    </template>
    <!-- 全局页脚 -->
    <!-- <template #footer>
      <page-footer />
    </template> -->
    <!-- 菜单图标 -->
    <template #icon="{ icon, item }">
      <el-icon v-if="icon" v-bind="item.meta?.props?.iconProps || {}">
        <component :is="icon" :style="item.meta?.props?.iconStyle" />
      </el-icon>
    </template>
    <!-- 页签标题 -->
    <template #tabTitle="{ label, item }">
      <el-icon
        v-if="item.meta?.icon"
        class="ele-tab-icon"
        v-bind="item.meta?.props?.iconProps || {}"
      >
        <component :is="item.meta.icon" :style="item.meta?.props?.iconStyle" />
      </el-icon>
      <span :style="item.meta?.icon ? { paddingLeft: '4px' } : {}">
        {{ label }}
      </span>
    </template>
  </ele-pro-layout>
  <!-- 主题设置抽屉 -->
  <setting-drawer v-model="settingVisible" />
  <force-password-change
    v-model="forcePwdVisible"
    @success="onForcePwdDone"
    @skip="onForcePwdSkip"
  />
</template>

<script setup>
  import { ref, computed, onMounted, onUnmounted } from 'vue';
  import { ElNotification } from 'element-plus';
  import { useRouter } from 'vue-router';
  import { storeToRefs } from 'pinia';
  import { useI18n } from 'vue-i18n';
  import { isResetPwd } from '@/api/layout';
  import {
    LayoutTool,
    TabDropdown,
    requestFullscreen,
    exitFullscreen,
    checkFullscreen,
    EleMessage
  } from 'ele-admin-plus/es';
  import {
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    ReloadOutlined,
    ExpandOutlined,
    CompressOutlined,
    MoreOutlined,
    CloseOutlined,
    ArrowLeftOutlined,
    ArrowRightOutlined,
    MinusCircleOutlined,
    CloseCircleOutlined,
    ArrowLeft
  } from '@/components/icons';
  import {
    PROJECT_NAME,
    HOME_PATH,
    REDIRECT_PATH,
    TAB_KEEP_ALIVE
  } from '@/config/setting';
  import { useUserStore } from '@/store/modules/user';
  import { useThemeStore } from '@/store/modules/theme';
  import { useMobileDevice } from '@/utils/use-mobile';
  import { usePageTab } from '@/utils/use-page-tab';
  import RouterLayout from '@/components/RouterLayout/index.vue';
  import HeaderUser from './components/header-user.vue';
  import HeaderNotice from './components/header-notice.vue';
  import I18nIcon from './components/i18n-icon.vue';
  import PageFooter from './components/page-footer.vue';
  import SettingDrawer from './components/setting-drawer.vue';
  import ForcePasswordChange from './components/force-password-change.vue';
  import { logout } from '@/utils/common';
  import { isTicketApiEnabled } from '@/api/ticketAuth';
  import { refreshTicketMenuBadge } from '@/api/ticket';

  const isTicketBrand = computed(() => isTicketApiEnabled());

  const { push, path } = useRouter();
  const route = useRouter();

  const key = computed(() => {
    return Math.random();
  });
  const { t, locale } = useI18n();
  const {
    addPageTab,
    removePageTab,
    removeAllPageTab,
    removeLeftPageTab,
    removeRightPageTab,
    removeOtherPageTab,
    reloadPageTab,
    handleBack,
    setPageTabs
  } = usePageTab();
  const torefresh = () => {
    window.location.reload(); // 修改为强制刷新页面
  };
  const { mobileDevice } = useMobileDevice();
  const userStore = useUserStore();
  const themeStore = useThemeStore();

  /** 菜单数据 */
  const { menus } = storeToRefs(userStore);

  // const menus1 = ref([]);
  // menus.value.forEach((element, index) => {
  //   element.meta.icon = element.meta.icon == '#' ? '' : element.meta.icon;
  //   element.children?.forEach((j) => {
  //     j.meta.icon = j.meta.icon == '#' ? '' : j.meta.icon;
  //   });
  //   menus1.value.push(element);
  // });

  /** 布局风格 */
  const {
    tabs,
    collapse,
    compact,
    maximized,
    tabBar,
    layout,
    sidebarLayout,
    headerStyle,
    sidebarStyle,
    tabStyle,
    fixedHeader,
    fixedSidebar,
    fixedBody,
    fluid,
    logoInHeader,
    colorfulIcon,
    transitionName,
    uniqueOpened,
    fixedHome,
    tabInHeader,
    roundedTheme,
    menuItemTrigger,
    responsive
  } = storeToRefs(themeStore);

  /** 是否全屏 */
  const isFullscreen = ref(false);

  /** 是否显示主题设置抽屉 */
  const settingVisible = ref(false);

  /** 页签右键菜单 */
  const tabContext = computed(() => {
    return [
      {
        title: t('layout.tabs.reload'),
        command: 'reload',
        icon: ReloadOutlined,
        iconStyle: { transform: 'scale(0.98)' }
      },
      {
        title: t('layout.tabs.close'),
        command: 'close',
        icon: CloseOutlined
      },
      {
        title: t('layout.tabs.closeLeft'),
        command: 'left',
        icon: ArrowLeftOutlined,
        divided: true
      },
      {
        title: t('layout.tabs.closeRight'),
        command: 'right',
        icon: ArrowRightOutlined
      },
      {
        title: t('layout.tabs.closeOther'),
        command: 'other',
        icon: MinusCircleOutlined,
        divided: true
      },
      {
        title: t('layout.tabs.closeAll'),
        command: 'all',
        icon: CloseCircleOutlined
      }
    ];
  });

  /** 页签栏右侧下拉菜单 */
  const tabExtra = computed(() => {
    const isMax = maximized.value;
    return [
      {
        title: t(`layout.tabs.${isMax ? 'fullscreenExit' : 'fullscreen'}`),
        command: 'fullscreen',
        icon: isMax ? CompressOutlined : ExpandOutlined
      },
      ...tabContext.value
    ];
  });

  /** 侧栏折叠切换 */
  const updateCollapse = (value) => {
    themeStore.setCollapse(value);
  };

  /** 双侧栏一级折叠切换 */
  const updateCompact = (value) => {
    themeStore.setCompact(value);
  };

  /** 内容区全屏切换 */
  const updateMaximized = (value) => {
    themeStore.setMaximized(value);
  };

  /** 页签点击事件 */
  const onTabClick = (option) => {
    const { key, active, item } = option;
    const path = item?.fullPath || key;
    if (key !== active && path) {
      push(path);
    }
  };

  /** 内容区尺寸改变事件 */
  const onBodySizeChange = ({ width }) => {
    themeStore.setContentWidth(width ?? null);
    isFullscreen.value = checkFullscreen();
  };

  /** 全屏切换 */
  const toggleFullscreen = () => {
    if (isFullscreen.value) {
      exitFullscreen();
      isFullscreen.value = false;
      return;
    }
    try {
      requestFullscreen();
      isFullscreen.value = true;
    } catch (e) {
      console.error(e);
      EleMessage.error('您的浏览器不支持全屏模式');
    }
  };

  /** 页签右键菜单点击事件 */
  const onTabContextMenu = (option) => {
    const { command, key, item, active } = option;
    if (command === 'reload') {
      reloadPageTab({ fullPath: item?.fullPath || key });
    } else if (command === 'close') {
      removePageTab({ key, active });
    } else if (command === 'left') {
      removeLeftPageTab({ key, active });
    } else if (command === 'right') {
      removeRightPageTab({ key, active });
    } else if (command === 'other') {
      removeOtherPageTab({ key, active });
    } else if (command === 'all') {
      removeAllPageTab({ key, active });
    }
  };

  /** 页签栏右侧下拉菜单点击事件 */
  const onTabDropdownMenu = (command, active) => {
    if (command === 'reload') {
      reloadPageTab();
    } else if (command === 'fullscreen') {
      updateMaximized(!maximized.value);
    } else {
      onTabContextMenu({ command, key: active, active });
    }
  };

  /** 菜单标题国际化 */
  const i18n = ({ menu, locale }) => {
    if (locale && menu?.meta?.lang && menu.meta.lang[locale]) {
      return menu.meta.lang[locale];
    }
    return menu?.component ? void 0 : menu?.meta?.title;
  };

  /** 打开主题设置抽屉 */
  const openSetting = () => {
    settingVisible.value = true;
  };
  const forcePwdVisible = ref(false);
  const onForcePwdDone = () => {
    try {
      sessionStorage.removeItem('mustChangePwd');
      sessionStorage.removeItem('oldPwdMd5');
      sessionStorage.removeItem('skipPwdChange');
    } catch {}
  };
  const getIsResetPwd = async () => {
    try {
      const res = await isResetPwd();
      if (res.code === 406 || res.code === 408) {
        EleMessage.error(res.msg);
        return setTimeout(() => {
          logout(true, void 0);
        }, 1500);
      }
      if (res.code) {
        const skipped = sessionStorage.getItem('skipPwdChange') === '1';
        forcePwdVisible.value = !skipped && !!res.data;
      }
    } catch (e) {
      console.error(e);
    }
  };
  const logoText = ref(useUserStore().envType);
  const envTest = computed(() =>
    logoText.value === 'base_service_system'
      ? '基础服务系统'
      : logoText.value === 'auth_center_system'
        ? '权限管理系统'
        : logoText.value == 'crm_system'
          ? 'CRM客户管理系统'
          : logoText.value == 'benefit_system'
            ? '权益中心'
            : logoText.value === 'teaching_research_system'
              ? '教研管理系统'
              : logoText.value === 'product_marketing_center'
                ? '商品营销中心'
                : logoText.value === 'teacher_management_system'
                  ? '师资管理系统'
                  : ''
  );
  const onForcePwdSkip = () => {};

  const OVERDUE_TIP_KEY = 'ticket_overdue_tip_dismissed_count';

  const isCustomerRole = computed(() =>
    (userStore.roles || []).includes('customer')
  );

  const showOverdueTip = (count) => {
    if (!count || count <= 0) return;
    const dismissed = Number(sessionStorage.getItem(OVERDUE_TIP_KEY) || '');
    if (dismissed === count) return;
    ElNotification({
      title: '超时提醒',
      message: `我的待处理超时工单：${count}`,
      type: 'warning',
      duration: 0,
      position: 'top-right',
      onClose: () => {
        sessionStorage.setItem(OVERDUE_TIP_KEY, String(count));
      }
    });
  };

  const checkOverdueTip = async () => {
    if (!isTicketBrand.value || isCustomerRole.value) return;
    const data = await refreshTicketMenuBadge();
    showOverdueTip(Number(data?.myOverdueCount) || 0);
  };

  const onVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      checkOverdueTip();
    }
  };

  onMounted(() => {
    if (useUserStore().envType == 'crm_system') {
      getIsResetPwd();
    }
    if (isTicketBrand.value) {
      checkOverdueTip();
      document.addEventListener('visibilitychange', onVisibilityChange);
    }
  });

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', onVisibilityChange);
  });
</script>

<script>
  import * as MenuIcons from './menu-icons';

  export default {
    name: 'Layout',
    components: MenuIcons
  };
</script>
<style scoped>
  .min_class {
    min-width: 800px;
  }
  ::v-deep(.ele-admin-menus > .ele-menu) {
    display: none;
  }
  :deep(.ele-admin-sidebar) {
    --ele-sidebar-width: 248px !important;
  }

  /* 展开：logo 与菜单左对齐；折叠：居中 */
  :deep(.ele-admin-sidebar > .ele-admin-logo),
  :deep(.ele-admin-sidebar > .ele-admin-logo-title),
  :deep(.ele-admin-sidebox > .ele-admin-logo),
  :deep(.ele-admin-sidebox > .ele-admin-logo-title) {
    justify-content: flex-start;
    padding-left: 20px;
    padding-right: 20px;
    box-sizing: border-box;
  }

  :deep(.ele-admin-sidebar.is-collapse > .ele-admin-logo),
  :deep(.ele-admin-sidebar.is-collapse > .ele-admin-logo-title),
  :deep(.ele-admin-sidebox.is-collapse > .ele-admin-logo),
  :deep(.ele-admin-sidebox.is-collapse > .ele-admin-logo-title) {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .logoBox {
    display: flex;
    align-items: center;
    height: 30px;
  }
  .logoBox--ticket {
    width: 100%;
    justify-content: flex-start;
  }
  :deep(.ele-admin-sidebar.is-collapse) .logoBox--ticket,
  :deep(.ele-admin-sidebox.is-collapse) .logoBox--ticket {
    justify-content: center;
  }
  .logotext {
    width: 124px;
    margin-top: 6px;
    margin-left: 8px;
    font-weight: 400;
    font-size: 14px;
    color: #999999;
  }
  .logo {
    width: 30px;
    height: 30px;
  }
  .logo--ticket {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    overflow: hidden;
    flex-shrink: 0;
  }
  .logoTitle {
    width: 64px;
    height: 30px;
    margin-left: 8px;
  }
  .logoTitle--ticket {
    width: 88px;
    object-fit: contain;
  }
  .brandWord {
    margin-left: 10px;
    min-width: 0;
  }
  .brandWord__name {
    display: block;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 1px;
    color: #ffffff;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
