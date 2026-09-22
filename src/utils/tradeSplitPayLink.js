/**
 * 秋季交易 · 分笔线上支付 H5 跳转链接
 * 接口仅返回 paymentId；二维码内容由前端根据 orderId + paymentId 拼接。
 *
 * 配置：VITE_APP_TRADE_H5_PAY_BASE（未配置时仅创建支付单，不生成可扫码链接）
 * 示例：https://h5.example.com/user/order/pay
 */
const TRADE_SPLIT_PAY_H5_BASE =
  (import.meta.env.VITE_APP_TRADE_H5_PAY_BASE || '').trim();

/** H5 付款基址是否已配置 */
export function isTradeSplitPayLinkReady() {
  return Boolean(TRADE_SPLIT_PAY_H5_BASE);
}

/**
 * @param {string} orderId 订单 ID
 * @param {string} paymentId 支付单 ID（接口返回）
 * @returns {string} 完整付款链接；基址未配置时返回空字符串
 */
export function buildTradeSplitPayLink(orderId, paymentId) {
  if (!orderId || !paymentId || !TRADE_SPLIT_PAY_H5_BASE) {
    return '';
  }
  const base = TRADE_SPLIT_PAY_H5_BASE.replace(/\/$/, '');
  const joiner = base.includes('?') ? '&' : '?';
  return `${base}${joiner}orderId=${encodeURIComponent(orderId)}&paymentId=${encodeURIComponent(paymentId)}`;
}
