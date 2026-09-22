/** 接口地址 */
export const API_BASE_URL = import.meta.env.VITE_API_URL;

/** trade 服务路由前缀（goods 等业务 v1 接口，原 uber/campus） */
export const tradeBase = import.meta.env.VITE_TRADE_BASE || 'trade';

/** 项目名称 */
export const PROJECT_NAME = import.meta.env.VITE_APP_NAME;

/** 不需要登录的路由 */
export const WHITE_LIST = ['/login', '/forget'];

/** 首页路径, 为空则取第一个菜单的地址 */
export const HOME_PATH = '/welcome';

/** 外层布局的路由地址 */
export const LAYOUT_PATH = '/';

/** 刷新路由的路由地址 */
export const REDIRECT_PATH = '/redirect';

/** 开启页签栏后是否缓存组件 */
//export const TAB_KEEP_ALIVE = !import.meta.env.DEV;
export const TAB_KEEP_ALIVE = true;

/** token本地缓存的名称 */
export const TOKEN_CACHE_NAME = 'token';

/** 主题配置本地缓存的名称 */
export const THEME_CACHE_NAME = 'theme';

/** i18n本地缓存的名称 */
export const I18N_CACHE_NAME = 'i18n-lang';

/** 高德地图key, 请到高德地图官网自行申请 */
export const MAP_KEY = '006d995d433058322319fa797f2876f5';

/** EleAdminPlus授权码 */
export const LICENSE_CODE = import.meta.env.VITE_LICENSE;
// 家辉云学堂二维码
export const QR_CODE_JHYXT = 'https://res-t.jhpy.com/dev/20250624/1fd110f6d51065ce43c25210f104d9fb20a31750754367000.png';

// 二维码logo
export const QR_CODE_LOGO = 'https://res.jhpy.com/prod/20250325/596fcc9b38c152fde6f0eee6374262571742898273000.png';

// 素养二维码logo
export const QR_CODE_LOGO_SUYANG = 'https://res-t.jhpy.com/dev/20260130/d682104c19714857bee43a2a45d75d97e1769756651000.png';

// 素养服务号二维码
export const QR_CODE_SUYANG_SERVICE = "https://res-t.jhpy.com/dev/20260204/ac574416999196ec98aea81f23fc30301770177212000.png";
