import request from '@/utils/request';
import { setToken } from '@/utils/token-util';
import { isTicketApiEnabled, ticketLogin } from '@/api/ticketAuth';

/**
 * 登录
 */
export async function login(data) {
  if (isTicketApiEnabled()) {
    const result = await ticketLogin({
      username: data.account || data.username,
      password: data.password
    });
    setToken(result.token, true);
    return {
      msg: '登录成功',
      homePath: result.user?.homePath || '/welcome'
    };
  }
  const res = await request.post('/uber/campus/usercenter/login', data);
  if (res.data.code === 200) {
    setToken(res.data.data, true);
    console.log('登录成功', res.data);

    return { msg: res.data.msg, homePath: '/welcome' };
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 内部用户验证码登录
 */
export async function mobileLogin(params) {
  const res = await request.post('/uber/campus/usercenter/employee/mobileLogin', params);
  if (res.data.code === 200) {
    setToken(res.data.data, params.remember);
    console.log('登录成功', res.data);

    return res.data.msg;
  }
  return Promise.reject(new Error(res.data.msg));
}

/**
 * 获取验证码
 */
export async function getCaptcha(params) {
  const res = await request.get('/uber/campus/usercenter/getSmsCode', { params });
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 退出
 */
export async function toLogout() {
  const res = await request.get('/uber/campus/usercenter/logOut');
  if (res.data.code) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 当前登录人所属系统
 */
export async function currentUserSystems() {
  const res = await request.get('/uber/campus/accesscenter/system/currentUser');
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 当前登录人角色
 */
export async function currentUser(systemCode) {
  const res = await request.get(
    `/uber/campus/accesscenter/role/currentUser/${systemCode}`
  );
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
/**
 * 校验员工系统状态
 */
export async function checkEmploySystem(systemCode) {
  const res = await request.get(
    `/uber/campus/usercenter/checkEmploySystem/${systemCode}`
  );
  if (res.data.code) {
    return res.data;
  }
  return Promise.reject(new Error(res.data.msg));
}
