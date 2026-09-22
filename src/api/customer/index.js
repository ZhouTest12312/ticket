import request from '@/utils/request';

export async function pageCustomers(params) {
  const res = await request.get('/customers', { params });
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function getCustomer(id) {
  const res = await request.get(`/customers/${id}`);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function createCustomer(data) {
  const res = await request.post('/customers', data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function updateCustomer(id, data) {
  const res = await request.put(`/customers/${id}`, data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function pageCustomerTickets(id, params) {
  const res = await request.get(`/customers/${id}/tickets`, { params });
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}
