import { h } from 'vue';
import { removeToken } from '@/utils/token-util';
import { toLogout } from '@/api/login/index.js';
import { ElMessage, ElMessageBox } from 'element-plus/es';
import { useUserStore } from '@/store/modules/user';
/**
 * 退出登录
 * @param route 是否使用路由跳转
 * @param from 登录后跳转的地址
 * @param push 路由跳转方法
 */
export function logout(route, from, push) {
  toLogout();
  localStorage.removeItem('ENV_TYPE');
  removeToken();
  if (route && push) {
    push({
      path: '/login',
      query: from ? { from: encodeURIComponent(from) } : void 0
    });
    return;
  }
  // 这样跳转避免再次登录重复注册动态路由, hash 路由模式使用 location.reload();
  const BASE_URL = import.meta.env.BASE_URL;
  const url = BASE_URL + 'login';
  location.replace(from ? `${url}?from=${encodeURIComponent(from)}` : url);
}

/**
 * 下载文件
 * @param data 二进制数据
 * @param name 文件名
 * @param type 文件类型
 */
export function download(data, name, type) {
  const blob = new Blob([data], { type: type || 'application/octet-stream' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * 参数转url字符串
 * @param params 参数
 * @param url 需要拼接参数的地址
 */
export function toURLSearch(params, url) {
  if (typeof params !== 'object' || params == null) {
    return '';
  }
  const result = transformParams(params)
    .map((d) => `${encodeURIComponent(d[0])}=${encodeURIComponent(d[1])}`)
    .join('&');
  if (!url) {
    return result;
  }
  return (url.includes('?') ? `${url}&` : `${url}?`) + result;
}

/**
 * 参数转表单数据
 * @param params 参数
 */
export function toFormData(params) {
  const formData = new FormData();
  if (typeof params !== 'object' || params == null) {
    return formData;
  }
  transformParams(params).forEach((d) => {
    formData.append(d[0], d[1]);
  });
  return formData;
}

/**
 * get请求处理数组和对象类型参数
 * @param params 参数
 */
export function transformParams(params) {
  const result = [];
  if (params != null && typeof params === 'object') {
    Object.keys(params).forEach((key) => {
      const value = params[key];
      if (value != null && value !== '') {
        if (typeof value === 'object' && !isBlobFile(value)) {
          getObjectParamsArray(value).forEach((item) => {
            result.push([`${key}${item[0]}`, item[1]]);
          });
        } else {
          result.push([key, value]);
        }
      }
    });
  }
  return result;
}

/**
 * 处理CRM接口响应
 * @param {import('axios').AxiosResponse} response
 * @returns {Promise<Record<string, unknown>>}
 */
export function handleCrmResponse(response) {
  const body = response?.data;
  if (body == null || typeof body !== 'object') {
    ElMessage.error('接口返回异常');
    return Promise.reject(new Error('接口返回异常'));
  }
  if (body.code === 200) {
    return Promise.resolve(body);
  } else if (body.code === 406 || body.code === 408) {
    const msg = body.msg ?? body.message ?? '您的账号暂无权限，请联系管理员';
    ElMessage.error(String(msg));
    setTimeout(() => {
      logout(true, void 0);
    }, 1500);
    return Promise.reject(new Error(msg));
  }
  const msg = body.msg ?? body.message ?? '请求失败';
  ElMessage.error(String(msg));
  return Promise.reject(body);
}

/**
 * 对象转参数数组
 * @param obj 对象
 */
export function getObjectParamsArray(obj) {
  const result = [];
  Object.keys(obj).forEach((key) => {
    const value = obj[key];
    if (value != null && value !== '') {
      const name = `[${key}]`;
      if (typeof value === 'object' && !isBlobFile(value)) {
        getObjectParamsArray(value).forEach((item) => {
          result.push([`${name}${item[0]}`, item[1]]);
        });
      } else {
        result.push([name, value]);
      }
    }
  });
  return result;
}

/**
 * 判断是否是文件
 * @param obj 对象
 */
export function isBlobFile(obj) {
  return obj != null && (obj instanceof Blob || obj instanceof File);
}

// 限制金额只允许输入小数点后两位(6+2)
export function formatPrice(val) {
  val = val + '';
  return val
    .replace(/[^\d.]/g, '')
    .replace(/(\..*)\./g, '$1')
    .replace(/^0+(\d+)/, '$1')
    .replace(/^\./, '0.')
    .replace(/(\.\d{2})\d+/, '$1')
    .replace(/^(\d{6})\d+/, '$1');
}

// 限制金额只允许输入数字
export function formatNumber(val) {
  return val.replace(/\D/g, '');
}

// 限制只允许输入字母和数字
export function formatAlphaNumber(val) {
  return val.replace(/[^a-zA-Z0-9]/g, '');
}

// 四舍五入消除精度问题
export function mathRound(num) {
  return Math.round(num * 100) / 100;
}

// 判断是否是数字
export function isNumber(value) {
  return !isNaN(parseFloat(value)) && isFinite(value);
}

/**
 * 限制手机号输入，只能输入-和数字
 * @param {String} mobile 手机号
 *
 */
export function sanitizeNumericHyphen(input) {
  if (input == null) return '';
  const str = String(input);
  const halfWidth = str
    .replace(/[\uFF10-\uFF19]/g, (s) =>
      String.fromCharCode(s.charCodeAt(0) - 0xff10 + 48)
    )
    .replace(/\uFF0D/g, '-');
  return halfWidth.replace(/[^0-9-]/g, '');
}

/**
 * 千分位分隔符，保留两位小数
 * @param {Number} count 需转化数字
 * @param {Number} separator 位数（默认3位）
 * @returns {String} 格式化后的字符串
 */
export function separator(count, separator = 3) {
  if (count == null || count == "") {
    return 0;
  }
  // 将数字转换为字符串并保留两位小数
  count = parseFloat(count).toFixed(2);
  
  // 分离整数部分和小数部分
  let [integerPart, decimalPart] = count.split('.');

  // 对整数部分进行千分位格式化
  const pattern = /(\d)(?=(\d{3})+(?!\d))/g;
  integerPart = integerPart.replace(pattern, "$1,");

  // 返回格式化后的结果
  return `${integerPart}.${decimalPart}`;
}

/**
 * textarea + execCommand，兼容 iOS Safari
 */
const copyTextByExecCommand = (text) => {
  const input = String(text);
  const element = document.createElement('textarea');
  const previouslyFocusedElement = document.activeElement;

  element.value = input;
  element.setAttribute('readonly', '');
  element.style.contain = 'strict';
  element.style.position = 'absolute';
  element.style.left = '-9999px';
  element.style.fontSize = '12pt';

  const selection = document.getSelection();
  const originalRange = selection.rangeCount > 0 && selection.getRangeAt(0);

  document.body.append(element);
  element.select();
  element.selectionStart = 0;
  element.selectionEnd = input.length;

  let isSuccess = false;
  try {
    isSuccess = document.execCommand('copy');
  } catch (err) {
    console.error('execCommand 失败:', err);
  }

  element.remove();

  if (originalRange) {
    selection.removeAllRanges();
    selection.addRange(originalRange);
  }

  if (previouslyFocusedElement) {
    previouslyFocusedElement.focus();
  }

  return isSuccess;
};

const showCopyFallback = (text) => {
  ElMessageBox({
    title: '复制手机号',
    message: () =>
      h('div', null, [
        h(
          'p',
          { style: 'margin: 0 0 8px; color: #909399; font-size: 14px' },
          '自动复制失败，请长按下方号码复制'
        ),
        h('input', {
          value: String(text),
          readonly: true,
          style: {
            width: '100%',
            padding: '8px',
            fontSize: '16px',
            textAlign: 'center',
            border: '1px solid #dcdfe6',
            borderRadius: '4px',
            boxSizing: 'border-box'
          },
          onVnodeMounted: (vnode) => {
            const el = vnode.el;
            if (el) {
              el.focus();
              el.select();
            }
          }
        })
      ]),
    showCancelButton: false,
    confirmButtonText: '我知道了'
  }).catch(() => {});
};

const copyTextWithFallback = async (text) => {
  if (!text) {
    ElMessage.warning('没有可复制的内容');
    return false;
  }
  if (copyTextByExecCommand(text)) {
    ElMessage.success('复制成功');
    return true;
  }
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(String(text));
      ElMessage.success('复制成功');
      return true;
    } catch (err) {
      console.error('Clipboard API 失败:', err);
    }
  }
  showCopyFallback(text);
  return false;
};

/** 同步复制（文本已就绪） */
export function copyText(text) {
  copyTextWithFallback(text);
}

/**
 * 异步复制（接口返回后再写入剪贴板）
 * 须在用户点击回调中同步调用，内部用 ClipboardItem + Promise 保留用户手势
 */
export function copyTextAsync(getText) {
  const textPromise = Promise.resolve().then(getText);

  if (navigator.clipboard?.write && typeof ClipboardItem !== 'undefined') {
    return navigator.clipboard
      .write([
        new ClipboardItem({
          'text/plain': textPromise.then((text) => {
            if (!text) {
              throw new Error('没有可复制的内容');
            }
            return new Blob([String(text)], { type: 'text/plain' });
          })
        })
      ])
      .then(() => textPromise)
      .then((text) => {
        if (!text) {
          ElMessage.warning('没有可复制的内容');
          return null;
        }
        ElMessage.success('复制成功');
        return text;
      })
      .catch((err) => {
        console.error('ClipboardItem 异步复制失败:', err);
        return textPromise.then((text) => {
          if (!text) {
            return null;
          }
          return copyTextWithFallback(text).then(() => text);
        });
      });
  }

  return textPromise.then((text) => {
    if (!text) {
      return null;
    }
    return copyTextWithFallback(text).then(() => text);
  });
}

export function getEndTime(originalDateTime) {
  // 创建Date对象
  let date = new Date(originalDateTime);
  // 设置时间为当天的最后一秒
  date.setHours(23, 59, 59, 999);
  // 格式化日期时间为所需的格式
  let year = date.getFullYear();
  let month = String(date.getMonth() + 1).padStart(2, '0');
  let day = String(date.getDate()).padStart(2, '0');
  let hours = String(date.getHours()).padStart(2, '0');
  let minutes = String(date.getMinutes()).padStart(2, '0');
  let seconds = String(date.getSeconds()).padStart(2, '0');

  let formattedDateTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  return formattedDateTime;
}

// 私塾 - 适配优惠为负数的金额 用于直涨券
export function calcMinus(value) {
  if (value < 0) {
    return `涨￥-${separator(0 - value)}`;
  }
  return `￥${separator(value)}`;
}

// 节流
export function throttle(fn, interval = 1000, leading = true) {
  // 该变量用于记录上一次函数的执行事件
  let lastTime = 0;
  // 内部的控制是否立即执行的变量
  let isLeading = true;

  const _throttle = function (...args) {
    // 获取当前时间
    const nowTime = new Date().getTime();

    // 第一次不需要立即执行
    if (!leading && isLeading) {
      // 将lastTime设置为nowTime，这样就不会导致第一次时remainTime大于interval
      lastTime = nowTime;
      // 将isLeading设置为false，这样就才不会对后续的lastTime产生影响。
      isLeading = false;
    }

    // 剩余时间
    const remainTime = nowTime - lastTime;
    // 如果剩余时间大于间隔时间，也就是说可以再次执行函数
    if (remainTime - interval >= 0) {
      fn.apply(this, args);
      // 将上一次函数执行的时间设置为nowTime，这样下次才能重新进入cd
      lastTime = nowTime;
    }
  };
  // 返回_throttle函数
  return _throttle;
}

// 防抖
export function debounce(func, interval = 1000, leading) {
  let timeout; // 定义一个计时器变量，用于延迟执行函数
  return function (...args) {
    // 返回一个包装后的函数
    const context = this; // 保存函数执行上下文对象
    const later = function () {
      // 定义延迟执行的函数
      timeout = null; // 清空计时器变量
      if (!leading) func.apply(context, args); // 若非立即执行，则调用待防抖函数
    };
    const callNow = leading && !timeout; // 是否立即调用函数的条件
    clearTimeout(timeout); // 清空计时器
    timeout = setTimeout(later, interval); // 创建新的计时器，延迟执行函数
    if (callNow) func.apply(context, args); // 如果满足立即调用条件，则立即执行函数
  };
}

/**
 * 下载文件 -- 私塾
 * @param url 阿里云url
 * @param name 文件名
 */
export async function downloadUrl(url, name) {
  const response = await fetch(url);
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = name;
  link.click();
  URL.revokeObjectURL(blobUrl);
}

// 判断设备端 -- 私塾
export function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent,
  );
}

/**
 * 设置菜单数量
 * @param {String} path 菜单path
 * @param {Number} count 数量
 */
export function setMenuBadge(path, count) {
  const userStore = useUserStore();
  const formatCount = typeof count === 'number' ? count : Number(count);
  userStore.menus &&
    userStore.menus.find((item) => {
      if (
        item.children &&
        item.children.find((child) => {
          if (child.path === path) {
            child.meta.props = {
              badge:
                formatCount > 0
                  ? { value: formatCount }
                  : { value: 0, hidden: true },
            };
            return true;
          }
          return false;
        })
      ) {
        return true;
      }
    });
}

/** 大陆手机号：1 开头共 11 位数字，与后端 TeacherPhoneValidator 一致 */
export const MAINLAND_PHONE_PATTERN = /^1\d{10}$/;

export function isValidMainlandPhone(phone) {
  if (phone == null || String(phone).trim() === '') {
    return false;
  }
  return MAINLAND_PHONE_PATTERN.test(String(phone).trim());
}

// 本地存储
export function setItem(key, value) {
  localStorage.setItem(key, value);
}
// 获取本地存储
export function getItem(key) {
  return localStorage.getItem(key);
}
// 移除存储
export function removeItem(key) {
  localStorage.removeItem(key);
}
