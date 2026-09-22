import { createApp } from 'vue';
import App from './App.vue';
import store from './store';
import router from './router';
import Cookies from 'js-cookie';
import permission from './utils/permission';
import DictData from '@/components/DictData/index.vue';
import i18n from './i18n';
import installer from './as-needed';
import 'element-plus/theme-chalk/display.css';
import 'ele-admin-plus/es/style/nprogress.scss';
import './styles/themes/rounded.scss';
import './styles/themes/dark.scss';
import './styles/index.scss';
import ElementPlus from 'element-plus';
import locale from 'element-plus/es/locale/lang/zh-cn'; // 中文语言
import print from 'vue3-print-nb';
import plugins from './plugins'; // plugins
import * as ElementPlusIconsVue from '@element-plus/icons-vue';
// 字典标签组件
import DictTag from '@/components/DictTag/index.vue';
import directive from './directive'; // directive
import { useDict } from '@/utils/dict';
import {
  parseTime,
  resetForm,
  addDateRange,
  handleTree,
  selectDictLabel,
  selectDictLabels,
  rRdown,
  rRup
} from '@/utils/ruoyi';

const app = createApp(App);
app.component('DictTag', DictTag);
app.component('ElementPlusIconsVue', ElementPlusIconsVue);

// 全局方法挂载
app.config.globalProperties.useDict = useDict;
app.config.globalProperties.parseTime = parseTime;
app.config.globalProperties.resetForm = resetForm;
app.config.globalProperties.handleTree = handleTree;
app.config.globalProperties.addDateRange = addDateRange;
app.config.globalProperties.selectDictLabel = selectDictLabel;
app.config.globalProperties.selectDictLabels = selectDictLabels;
app.config.globalProperties.rRdown = rRdown;
app.config.globalProperties.rRup = rRup;

app.use(store);
app.use(router);
app.use(print);
app.use(plugins);
app.use(permission);
app.use(i18n);
app.use(installer);
app.component('DictData', DictData);

directive(app);

// 使用element-plus 并且设置全局的大小
app.use(ElementPlus, {
  locale: locale,
  // 支持 large、default、small
  size: Cookies.get('size') || 'default'
});

app.mount('#app');
