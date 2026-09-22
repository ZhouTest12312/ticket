const STATUS_DOT = {
  unassigned: { type: 'info', ripple: false },
  pending: { type: 'warning', ripple: false },
  processing: { ripple: true },
  waiting_customer: { color: '#13c2c2', ripple: false },
  overdue: { type: 'danger', ripple: false },
  resolved: { type: 'success', ripple: false },
  closed: { color: '#434343', ripple: false },
  ended: { color: '#bfbfbf', ripple: false },
  reopened: { color: '#eb2f96', ripple: true }
};

export const statusDot = (status) => STATUS_DOT[status] || { type: 'info', ripple: false };
