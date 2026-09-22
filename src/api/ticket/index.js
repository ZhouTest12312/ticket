import request from '@/utils/request';
import { setMenuBadge } from '@/utils/common';

function unwrap(res) {
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function ticketOptions() {
  return unwrap(await request.get('/tickets/options'));
}

export async function ticketWorkload() {
  return unwrap(await request.get('/tickets/workload'));
}

export async function ticketPendingCount() {
  return unwrap(await request.get('/tickets/pending-count'));
}

export async function refreshTicketMenuBadge() {
  try {
    const data = await ticketPendingCount();
    setMenuBadge('/ticket/list', Number(data?.count) || 0);
    return data;
  } catch (_) {
    return { count: 0, myOverdueCount: 0 };
  }
}

export async function pageTickets(params) {
  return unwrap(await request.get('/tickets', { params }));
}

export async function getTicket(id) {
  return unwrap(await request.get(`/tickets/${id}`));
}

export async function createTicket(data) {
  return unwrap(await request.post('/tickets', data));
}

export async function updateTicket(id, data) {
  return unwrap(await request.put(`/tickets/${id}`, data));
}

export async function assignTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/assign`, data));
}

export async function transferTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/transfer`, data));
}

export async function setCollaborators(id, userIds) {
  return unwrap(await request.put(`/tickets/${id}/collaborators`, { userIds }));
}

export async function addTicketNote(id, data) {
  return unwrap(await request.post(`/tickets/${id}/notes`, data));
}

export async function changeTicketStatus(id, status) {
  return unwrap(await request.post(`/tickets/${id}/status`, { status }));
}

export async function resolveTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/resolve`, data));
}

export async function requestTicketConfirm(id) {
  return unwrap(await request.post(`/tickets/${id}/confirm-request`));
}

export async function confirmTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/confirm`, data));
}

export async function closeTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/close`, data || {}));
}

export async function pageMyTickets(params) {
  return unwrap(await request.get('/tickets/mine', { params }));
}

export async function askTicket(data) {
  return unwrap(await request.post('/tickets/ask', data));
}

export async function submitHandleReply(id, data) {
  return unwrap(await request.post(`/tickets/${id}/handle-reply`, data));
}

export async function customerFeedback(id, data) {
  return unwrap(await request.post(`/tickets/${id}/customer-feedback`, data));
}

export async function reopenTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/reopen`, data));
}

export async function escalateTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/escalate`, data));
}

export async function followupTicket(id, data) {
  return unwrap(await request.post(`/tickets/${id}/followup`, data));
}

export async function uploadLocalMedia(file) {
  const form = new FormData();
  form.append('file', file);
  return unwrap(await request.post('/uploads', form));
}

export async function saveTicketAttachment(id, data) {
  return unwrap(await request.post(`/tickets/${id}/attachments`, data));
}

export async function deleteTicketAttachment(id) {
  return unwrap(await request.delete(`/tickets/attachments/${id}`));
}
