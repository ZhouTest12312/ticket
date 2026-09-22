import request from '@/utils/request';

export async function pageUsers(params) {
  const res = await request.get('/users', { params });
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function assignUserRoles(id, roleIds) {
  const res = await request.put(`/users/${id}/roles`, { roleIds });
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function createUser(data) {
  const res = await request.post('/users', data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function updateUser(id, data) {
  const res = await request.put(`/users/${id}`, data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}
