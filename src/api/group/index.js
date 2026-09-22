import request from '@/utils/request';

function unwrap(res) {
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function listHandlerGroups() {
  return unwrap(await request.get('/handler-groups'));
}

export async function createHandlerGroup(data) {
  return unwrap(await request.post('/handler-groups', data));
}

export async function updateHandlerGroup(id, data) {
  return unwrap(await request.put(`/handler-groups/${id}`, data));
}

export async function deleteHandlerGroup(id) {
  return unwrap(await request.delete(`/handler-groups/${id}`));
}
