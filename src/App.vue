<template>
  <el-config-provider :locale="elLocale">
    <ele-config-provider
      :locale="eleLocale"
      :table="tableConfig"
      :map-key="MAP_KEY"
      :license="LICENSE_CODE"
    >
      <ele-app>
        <router-view :key="route.path" />
      </ele-app>
    </ele-config-provider>
  </el-config-provider>
</template>

<script setup>
  import { MAP_KEY, LICENSE_CODE } from '@/config/setting';
  import { useGlobalConfig } from '@/config/use-global-config';
  import { useThemeStore } from '@/store/modules/theme';
  import { useLocale } from '@/i18n/use-locale';
  import { useRoute } from 'vue-router';
  import { useUserStore } from '@/store/modules/user';
  import { setPageTitle, setSystemName } from '@/utils/page-title-util';
  import { watch } from 'vue';
  const route = useRoute();

    // 动态设置页面标题
    const userStore = useUserStore();
    const setDocumentTitle = () => {
      const systemName = '客户问题工单系统';
      setSystemName(systemName);
      setPageTitle(systemName);
    };
    // 监听用户存储变化
    watch(
      () => userStore.envType,
      () => {
        setTimeout(() => {
          setDocumentTitle();
        }, 300);
      }
    );

    // 初始化时也设置一次标题
    if (userStore.envType) {
      setDocumentTitle();
    }


    /** 组件全局配置 */
    const { tableConfig } = useGlobalConfig();

    /** 恢复缓存主题 */
    const themeStore = useThemeStore();
    themeStore.recoverTheme();

    /** 国际化配置 */
    const { elLocale, eleLocale } = useLocale();
</script>
<style lang="scss">

</style>