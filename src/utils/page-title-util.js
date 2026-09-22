import { PROJECT_NAME } from '@/config/setting';

// 动态系统名称（可由外部设置，优先级高于 PROJECT_NAME）
let dynamicSystemName = null;

/**
 * 设置动态系统名称
 * @param {string} name - 系统名称
 */
export function setSystemName(name) {
  dynamicSystemName = name;
}

/**
 * 获取当前系统名称
 */
export function getSystemName() {
  return dynamicSystemName || PROJECT_NAME || '';
}

/**
 * 修改浏览器标题
 * @param title 标题
 */
export function setPageTitle(title) {
  const names = [];
  if (title) {
    names.push(title);
  }
  const systemName = getSystemName();
  if (systemName) {
    names.push(systemName);
  }
  document.title = names.join(' - ');
}
