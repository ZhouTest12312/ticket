import request from '@/utils/request';

/**
 * 工单系统本地登录
 * @param {{ username: string, password: string }} data
 */
export async function ticketLogin(data) {
  const res = await request.post('/auth/login', data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '登录失败'));
}

/**
 * 当前用户（角色/权限/菜单）
 */
export async function ticketMe() {
  const res = await request.get('/auth/me');
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '获取用户信息失败'));
}

/**
 * 修改密码（请求体为 MD5 密文，与登录一致）
 * @param {{ oldPassword: string, newPassword: string }} data
 */
export async function ticketChangePassword(data) {
  const res = await request.put('/auth/password', data);
  if (res.data.code === 200) {
    return res.data.msg || '密码修改成功';
  }
  return Promise.reject(new Error(res.data.msg || '修改失败'));
}

export function isTicketApiEnabled() {
  return String(import.meta.env.VITE_USE_TICKET_API || '') === 'true';
}
