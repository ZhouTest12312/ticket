/**
 * 路由配置
 */
import NProgress from 'nprogress';
import { createRouter, createWebHistory } from 'vue-router';
import { WHITE_LIST, REDIRECT_PATH, LAYOUT_PATH } from '@/config/setting';
import { useUserStore } from '@/store/modules/user';
import { getToken, setToken, removeToken } from '@/utils/token-util';
import { setPageTitle } from '@/utils/page-title-util';
import { getRouteTitle } from '@/i18n/use-locale';
import { routes, getMenuRoutes } from './routes';
import { getCurrentSystemEnvRole } from '@/utils/envRole.js';
import { checkVersion } from '@/utils/version-check.js';
import { isTicketApiEnabled } from '@/api/ticketAuth';

NProgress.configure({
  speed: 200,
  minimum: 0.02,
  trickleSpeed: 200,
  showSpinner: false
});

const router = createRouter({
  routes,
  history: createWebHistory(),
  scrollBehavior: () => {
    return { top: 0 };
  }
});

/**
 * 路由守卫
 */
router.beforeEach(async (to) => {
  const userStore = useUserStore();

  if (!to.path.includes(REDIRECT_PATH)) {
    NProgress.start();
    setPageTitle(getRouteTitle(to));
  }
  if(to.query.token){
    setToken(to.query.token,true);
    return { path: to.path, query: {} };
  }
   if(to.query.noToken){
    removeToken();
  }
  // 获取当前系统环境角色
  const systemEnvRole = getCurrentSystemEnvRole();
  userStore.setSystemEnvRole(systemEnvRole);
  if(systemEnvRole!='portal_system' && systemEnvRole!='jyxt' && systemEnvRole!=null){
    userStore.setEnvType(systemEnvRole);
  }else {
    if(systemEnvRole!='jyxt'){
      userStore.setEnvType('');
    }
  }
  if (!getToken()) {
    // 未登录跳转登录界面
    if (!WHITE_LIST.includes(to.path)) {
      const query = { from: encodeURIComponent(to.fullPath) };
      return { path: '/login', query: to.path === LAYOUT_PATH ? {} : query };
    }
    return;
  }
  // 版本更新检测
  checkVersion();
  // 注册动态路由
  const notLoginPaths = ['/login', '/404', '/401'];
  // 工单本地模式没有 /mySystem 页；菜单为空时回登录，避免白屏
  if (!userStore.menus && !notLoginPaths.includes(to.path) && to.path !== '/mySystem') {
    try {
      const { menus, homePath } = (await userStore.fetchUserInfo()) ?? {};
      if (menus && menus.length > 0) {
        getMenuRoutes(menus, homePath).forEach((r) => {
          router.addRoute(r);
        });
        router.addRoute({
          path: '/:path(.*)*',
          name: 'NotFound',
          component: () => import('@/views/exception/404/index.vue')
        });
        return { ...to, replace: true };
      }
      removeToken();
      userStore.setMenus(null);
      if (isTicketApiEnabled()) {
        return { path: '/login' };
      }
      // 旧门户：系统选择页（本仓库未实现该页时也会白屏）
      return { path: '/mySystem' };
    } catch (e) {
      console.error('[Router] 获取用户信息异常:', e);
      removeToken();
      userStore.setMenus(null);
      return { path: '/login', query: { from: encodeURIComponent(to.fullPath) } };
    }
  }
});

router.afterEach((to) => {
  if (!to.path.includes(REDIRECT_PATH) && NProgress.isStarted()) {
    setTimeout(() => {
      NProgress.done(true);
    }, 200);
  }
});

/**
 * 路由错误处理
 */
router.onError((error, to) => {
  console.error('[Router] 导航错误:', error, '目标路径:', to.path);
  NProgress.done(true);
  // chunk 加载失败（版本更新/网络问题）时强制刷新
  if (error.message?.includes('Failed to fetch') || error.message?.includes('Loading chunk') || error.message?.includes('Importing a module')) {
    console.warn('[Router] 组件加载失败，尝试刷新页面');
    window.location.href = to.fullPath;
  }
});

export default router;
