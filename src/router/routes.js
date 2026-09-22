import { menuToRoutes, eachTree } from 'ele-admin-plus/es';
import { HOME_PATH, LAYOUT_PATH, REDIRECT_PATH } from '@/config/setting';
import Layout from '@/layout/index.vue';
import RedirectLayout from '@/components/RedirectLayout/index.vue';
const modules = import.meta.glob([
  '/src/views/login/**/*.vue',
  '/src/views/welcome/**/*.vue',
  '/src/views/exception/**/*.vue',
  '/src/views/system/**/*.vue',
  '/src/views/customer/**/*.vue',
  '/src/views/ticket/**/*.vue'
]);

/**
 * 静态路由
 */
export const routes = [
  {
    path: '/login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录' }
  },
];

/**
 * 根据菜单生成动态路由
 * @param menus 菜单数据
 * @param homePath 主页地址
 */
export function getMenuRoutes(menus, homePath) {
  const childRoutes = [
    {
      path: REDIRECT_PATH + '/:path(.*)',
      component: RedirectLayout,
      meta: { hideFooter: true }
    },
    {
      path: 'welcome',
      component: () => import('@/views/welcome/index.vue'),
      meta: { title: '首页' }
    }
  ];
  const layoutRoutes = [
    {
      path: LAYOUT_PATH,
      component: Layout,
      redirect: HOME_PATH ?? homePath,
      children: childRoutes
    }
  ];
  eachTree(menuToRoutes(menus, getComponent, routes), (route) => {
    const temp = Object.assign({}, route, { children: void 0 });
    if (route.meta?.visible === 123) {
      layoutRoutes.push(temp);
    } else {
      childRoutes.push(temp);
    }
  });
  return layoutRoutes;
}

/**
 * 解析路由组件
 * @param component 组件名称
 */
function getComponent(component) {
  if (!component) {
    return;
  }
  const exactView = modules[`/src/views${component}.vue`];
  if (exactView) {
    return exactView;
  }
  const indexView = modules[`/src/views${component}/index.vue`];
  if (indexView) {
    return indexView;
  }
  console.warn(
    `[Router] 找不到视图组件: /src/views${component}.vue 或 /src/views${component}/index.vue`
  );
  return () => import('@/views/exception/404/index.vue');
}
