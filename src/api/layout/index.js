import request from '@/utils/request';
import { toURLSearch } from '@/utils/common';
import { isTicketApiEnabled, ticketChangePassword } from '@/api/ticketAuth';

/**
 * 获取当前登录用户的个人信息/菜单/权限/角色
 */
export async function getUserInfo() {
  const res = await request.get('/uber/campus/usercenter/getUserInfo', {});
  if (res.data.code) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg));
}

/**
 * 获取当前登录用户的个人信息/菜单/权限/角色
 */
export async function getUserMenu() {
  const res = await request.get('/getRouters');
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 根据父节点主键查询地区列表
 */
export async function getAdressList(parentId) {
  const res = await request.get(
    `/uber/campus/region/listByParentId/${parentId}`
  );
  if (res.data.code === 200) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 是否默认密码
 */
export async function isResetPwd() {
  const res = await request.get(
    `/uber/campus/usercenter/isResetPwd`,{}
  );
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}

/**
 * 修改当前登录用户的密码
 */
export async function updatePassword(params) {
  if (isTicketApiEnabled()) {
    // 本地模式：明文旧/新密码；兼容弹窗传入的 oldPwd/newPwd
    return ticketChangePassword({
      oldPassword: params.oldPassword || params.oldPwd,
      newPassword: params.newPassword || params.newPwd
    });
  }
  const res = await request.post('/uber/campus/usercenter/modifyPwd', params);
  if (res.data.code === 200) {
    return res.data.msg ?? '修改成功';
  }
  return Promise.reject(new Error(res.data.msg));
}

/**
 * 修改当前登录用户的个人信息
 */
export async function updateUserInfo(data) {
  const res = await request.put('/system/user/profile', data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 当前登录人菜单路由
 */
export async function getMenu(systemCode) {
  const res = await request.get(
    `uber/campus/accesscenter/role/currentUserMenu/${systemCode}`,
    {}
  );
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 *当前登录按钮权限标识
 */
export async function systemCurrentUserPermission(systemCode) {
  const res = await request.get(
    `/uber/campus/accesscenter/system/currentUserPermission/${systemCode}`,
    {}
  );
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}