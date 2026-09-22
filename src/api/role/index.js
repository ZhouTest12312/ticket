import request from '@/utils/request';

export async function pageRoles(params) {
  const res = await request.get('/roles', { params });
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function getRole(id) {
  const res = await request.get(`/roles/${id}`);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function createRole(data) {
  const res = await request.post('/roles', data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function updateRole(id, data) {
  const res = await request.put(`/roles/${id}`, data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function deleteRole(id) {
  const res = await request.delete(`/roles/${id}`);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function listPermissions() {
  const res = await request.get('/permissions');
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}
