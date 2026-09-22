/**
 * axios实例
 */
import axios from 'axios';
import { unref } from 'vue';
import {
  ElNotification,
  ElMessageBox,
  ElMessage,
  ElLoading
} from 'element-plus/es';
import { API_BASE_URL, LAYOUT_PATH } from '@/config/setting';
import router from '@/router';
import { getToken, setToken } from './token-util';
import { logout, toURLSearch } from './common';
import { EleMessage } from 'ele-admin-plus';
/** 创建axios实例 */
const service = axios.create({
  baseURL: API_BASE_URL
  //baseURL: 'http://10.1.11.31:9930/api'
});
/**
 * 添加请求拦截器
 */
service.interceptors.request.use(
  (config) => {
    // 添加token到header
    const token = getToken();
    if (config.url.includes('/sishu/')) {
      config.headers['Use-Scene'] = 99;
      config.headers['Authorization'] = token;
    } else if (config.url.includes('/peiyou/')) {
      config.headers['Use-Scene'] = 99;
      config.headers['Authorization'] = token;
    } else if (config.url.includes('/zhongkao/')) {
    } else {
      config.headers['Authorization'] = token;
    }
    // config.headers['deviceId'] = getDeviceId();

    // get请求处理数组和对象类型参数
    if (config.method === 'get' && config.params) {
      config.url = toURLSearch(config.params, config.url);
      config.params = {};
    }
    return config;
  },
  (error) => {
    console.error(error);
    return Promise.reject(new Error('网络错误'));
  }
);

/**
 * 添加响应拦截器
 */
service.interceptors.response.use(
  (res) => {
    // 登录过期处理（登录接口本身的 401 = 账号/密码错误，不当成会话过期）
    if (res.data?.code === 401) {
      const reqUrl = String(res.config?.url || '');
      const isLoginAttempt =
        reqUrl.includes('/auth/login') ||
        reqUrl.includes('/usercenter/login');
      if (isLoginAttempt) {
        return Promise.reject(new Error(res.data.msg || '用户名或密码错误'));
      }
      const { path, fullPath } = unref(router.currentRoute);
      if (path == LAYOUT_PATH) {
        logout(true, void 0, router.push);
      } else if (path !== '/login') {
        ElMessageBox.close();
        ElMessageBox.alert('登录状态已过期, 请退出重新登录!', '系统提示', {
          confirmButtonText: '重新登录',
          callback: (action) => {
            if (action === 'confirm') {
              logout(false, fullPath);
            }
          },
          type: 'warning',
          draggable: true
        });
      }
      return Promise.reject(new Error(res.data.msg));
    } else if (res.data?.code === 994008) {
      const showCodes = res.config?.showErrorCodes;
      if (Array.isArray(showCodes) && showCodes.includes(994008)) {
        EleMessage.error({
          message: res.data?.msg,
          grouping: true
        });
      }
    }
    // 续期token
    const newToken = res.headers['authorization'];
    if (newToken) {
      setToken(newToken);
    }
    return res;
  },
  (error) => {
    if (error.response?.data?.code === 401) {
      const { path, fullPath } = unref(router.currentRoute);
      if (path == LAYOUT_PATH) {
        logout(true, void 0, router.push);
      } else if (path !== '/login') {
        ElMessageBox.close();
        ElMessageBox.alert('登录状态已过期, 请退出重新登录!', '系统提示', {
          confirmButtonText: '重新登录',
          callback: (action) => {
            if (action === 'confirm') {
              logout(false, fullPath);
            }
          },
          type: 'warning',
          draggable: true
        });
      }
    }

    return Promise.reject(new Error('网络错误'));
  }
);
const DEVICE_ID_KEY = `${import.meta.env.VITE_APP_ENV}_scWeb_device_id`;

function getDeviceId() {
  let env = import.meta.env.VITE_APP_ENV;
  let id = null;
  try {
    id = localStorage.getItem(DEVICE_ID_KEY);
  } catch (_) {}
  if (id) return id;
  try {
    const b = new Uint8Array(16);
    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(b);
    } else {
      for (let i = 0; i < 16; i++) b[i] = Math.floor(Math.random() * 256);
    }
    b[6] = (b[6] & 0x0f) | 0x40;
    b[8] = (b[8] & 0x3f) | 0x80;
    let s = '';
    for (let i = 0; i < 16; i++) {
      s +=
        (i === 4 || i === 6 || i === 8 || i === 10 ? '-' : '') +
        b[i].toString(16).padStart(2, '0');
    }
    id = s;
  } catch (_) {
    id = String(Date.now()) + '-' + Math.random().toString(16).slice(2);
  }
  try {
    localStorage.setItem(DEVICE_ID_KEY, id);
  } catch (_) {}

  return id;
}
export default service;
