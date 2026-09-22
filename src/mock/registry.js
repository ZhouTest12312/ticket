/**
 * 开发 Mock 注册表 — 单一环境变量控制，避免每个功能单独加 VITE_USE_*_MOCK
 *
 * .env.devLocal 示例：
 *   VITE_API_MOCK=classStudentList              # 只 Mock 学员列表
 *   VITE_API_MOCK=classStudentList,coursePackage # 多个逗号分隔
 *   VITE_API_MOCK=all                           # 启用全部已注册 Mock
 *   # 不配置或留空 → 全部走真实接口
 */

/** 已注册的 Mock 模块 key（新增功能在此追加常量即可） */
export const MOCK_KEYS = {
  classStudentList: 'classStudentList',
  coursePackage: 'coursePackage',
  textbook: 'textbook',
  /** 试听下单整模块 Mock（班级/课次/试算/创建）；联调 campus-trade 时勿包含 */
  trialOrder: 'trialOrder',
  formalOrder: 'formalOrder',
  studentEnrolledClass: 'studentEnrolledClass',
  studentTuitionFee: 'studentTuitionFee',
  studentLessonDetail: 'studentLessonDetail',
  studentLessonOperateLog: 'studentLessonOperateLog',
  studentLessonOperate: 'studentLessonOperate',
  addReportOrder: 'addReportOrder',
  /** 结转换班整模块 Mock；联调 campus-trade 时勿包含 */
  settlementTransferOrder: 'settlementTransferOrder',
  /** 退班 · 发起退款工单 Mock；联调 campus-trade 时勿包含 */
  withdrawClassOrder: 'withdrawClassOrder',
  studentOrder: 'studentOrder',
  studentClassFlow: 'studentClassFlow',
  studentAudition: 'studentAudition',
  classSchedule: 'classSchedule',
  /** 分笔支付全局 Mock（旧配置）；开启后创建成功页 / 列表线上支付也会 Mock */
  tradeOperationPayments: 'tradeOperationPayments',
  /** 列表「线下支付申请」Drawer Mock；须 mockScope=offlineApply */
  tradeOfflinePayment: 'tradeOfflinePayment'
};

function parseMockList() {
  const raw = import.meta.env.VITE_API_MOCK;
  if (raw == null || String(raw).trim() === '') {
    return [];
  }
  if (String(raw).trim().toLowerCase() === 'all') {
    return Object.values(MOCK_KEYS);
  }
  return String(raw)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

/** 判断某 Mock 模块是否启用 */
export function isMockEnabled(key) {
  return parseMockList().includes(key);
}
