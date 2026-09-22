import request from '@/utils/request';

function unwrap(res) {
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function listDictTypes() {
  return unwrap(await request.get('/dict-types'));
}

export async function createDictType(data) {
  return unwrap(await request.post('/dict-types', data));
}

export async function updateDictType(id, data) {
  return unwrap(await request.put(`/dict-types/${id}`, data));
}

export async function deleteDictType(id) {
  return unwrap(await request.delete(`/dict-types/${id}`));
}

export async function pageDictItems(params) {
  return unwrap(await request.get('/dict-items', { params }));
}

export async function getDictItem(id) {
  return unwrap(await request.get(`/dict-items/${id}`));
}

export async function createDictItem(data) {
  return unwrap(await request.post('/dict-items', data));
}

export async function updateDictItem(id, data) {
  return unwrap(await request.put(`/dict-items/${id}`, data));
}

export async function deleteDictItem(id) {
  return unwrap(await request.delete(`/dict-items/${id}`));
}
