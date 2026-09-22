/** orderPromotion/query 等接口返回的不可用原因码 → 中文展示 */
const PROMOTION_UNAVAILABLE_REASON_MAP = {
  PLATFORM_MUTEX: '与平台优惠不可叠加',
  JOINT_REPORT_MUTEX: '与联报优惠不可叠加',
  SCOPE_MISMATCH: '当前订单中没有适用的课程',
  SCOPE_NOT_MATCH: '适用范围不匹配',
  LESSON_THRESHOLD: '未满足门次门槛要求',
  AMOUNT_THRESHOLD: '未满足金额门槛要求',
  STACK_MUTEX: '与已选优惠券不可叠加',
  SPEC_NOT_MATCH: '商品规格不匹配',
  PACKAGE_NOT_EFFECTIVE: '优惠包未生效'
};

/**
 * 将优惠不可用原因码转为中文；已是中文或未知码则原样返回。
 * @param {string | null | undefined} reason
 * @returns {string}
 */
export function formatPromotionUnavailableReason(reason) {
  if (reason == null || reason === '') return '';
  const key = String(reason).trim();
  return PROMOTION_UNAVAILABLE_REASON_MAP[key] || key;
}

/**
 * 为适用/不适用商品行补充 inapplicableReasonLabel。
 * @param {Array<object> | null | undefined} lines
 * @returns {Array<object>}
 */
export function translatePromotionMatchLines(lines) {
  if (!Array.isArray(lines)) return [];
  return lines.map((line) => {
    const reason = line?.inapplicableReason;
    if (!reason) return line;
    return {
      ...line,
      inapplicableReasonLabel: formatPromotionUnavailableReason(reason)
    };
  });
}
