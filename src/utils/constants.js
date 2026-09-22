// 栏目选项
export const categoryOptions = [
  { label: '最新资讯', value: 1 },
  { label: '升学规划', value: 2 },
  { label: '新闻中心', value: 3 }
];
// 现金券事件
export const CASH_EVENT_TYPE = {
  COUPON_CREATE: "创建现金券",
  ORDER_PAYMENT: "订单支付",
  ORDER_REFUND_ORIGINAL: "订单退款-原路退回",
  ORDER_REFUND_NON_ORIGINAL: "订单退款-（非）原路退回",
  ORDER_REFUND_TO_COUPON: "订单退款-退到现金券",
  COUPON_INITIATE_REFUND: "现金券发起退款",
};

// 权限list
export const permissionList = [
  { label: '全部', value: '' },
  { label: '管理员', value: 1 },
  { label: '批改老师', value: 2 },
  { label: '学科教研', value: 3 },
  { label: '师资管理', value: 4 },
  { label: '老师', value: 5 },
  { label: '渠道运营', value: 6 }
];
//  状态list
export const statusList = [
  { label: '全部', value: '' },
  { label: '启用', value: 1 },
  { label: '停用', value: 2 }
];
// 评分List
export const scoreList = [
  { label: '全部', value: '' },
  { label: 'A', value: 1 },
  { label: 'B', value: 2 },
  { label: 'C', value: 3 },
  { label: 'D', value: 4 },
  { label: 'E', value: 5 }
];
// 类型list
export const typeList = [
  { label: '全部', value: '' },
  { label: '个人成长', value: 1 },
  { label: '传统文化', value: 2 },
  { label: '校园生活', value: 3 },
  { label: '人物精神', value: 4 },
  { label: '情感表达', value: 5 },
  { label: '家庭生活', value: 6 },
  { label: '风景感悟', value: 7 }
];
// 来源类型
export const sourceTypeList = [
  { label: '全部', value: '' },
  { label: '用户习文总结', value: 1 },
  { label: '后台录入', value: 2 }
];
// 地区枚举
export const areaList = [{ label: '上海', value: 1 }];
// 年级枚举
export const gradeList = [
  { label: '全部', value: '' },
  { label: '一年级', value: 1 },
  { label: '二年级', value: 2 },
  { label: '三年级', value: 3 },
  { label: '四年级', value: 4 },
  { label: '五年级', value: 5 },
  { label: '六年级', value: 6 },
  { label: '七年级', value: 7 },
  { label: '八年级', value: 8 },
  { label: '九年级', value: 9 },
  { label: '高一', value: 10 },
  { label: '高二', value: 11 },
  { label: '高三', value: 12 }
];
// 文体枚举
export const styleList = [
  { label: '全部', value: '' },
  { label: '记叙文', value: 0 },
  { label: '议论文', value: 1 }
];
// 来源枚举
export const sourceList = [
  { label: '全部', value: '' },
  { label: '是', value: true },
  { label: '否', value: false }
];
// 收否枚举
export const collectList = [
  { label: '全部', value: '' },
  { label: '是', value: 1 },
  { label: '否', value: 0 }
];
// 审批状态枚举
export const auditStatusList = [
  { label: '全部', value: '' },
  { label: '审核意见待生成', value: 1 },
  { label: '待审核', value: 2 },
  { label: '审题待生成', value: 3 },
  { label: '审题待审核', value: 4 },
  { label: '评分待生成', value: 5 },
  { label: '评分待审核', value: 6 },
  { label: '评价待生成', value: 7 },
  { label: '评价待审核', value: 8 },
  { label: '范文待生成', value: 9 },
  { label: '范文待审核', value: 10 },
  { label: '批改完成', value: 11 },
  { label: '拒绝', value: 12 }
];

// 学段列表
export const periodList = [{ label: '中考', value: 'SHSEE' }];

// 学科列表
export const subjectList = [
  { label: '全部', value: '' },
  { label: '语文', value: 1 },
  { label: '数学', value: 2 },
  { label: '英语', value: 3 },
  { label: '物理', value: 4 },
  { label: '化学', value: 5 },
  { label: '跨学科', value: 11 }
];

// 标签列表
export const tagList = [
  { label: '全部', value: '' },
  { label: '能力项', value: 1 },
  { label: '知识点', value: 0 }
];

// 标签状态列表
export const tagStatusList = [
  { label: '全部', value: '' },
  { label: '启用', value: 1 },
  { label: '停用', value: 0 }
];
// 标签地区列表
export const tagAreaList = [{ label: '上海', value: 10 }];

// 题型列表
export const questionTypeList = [
  { label: '单选题', value: 0 },
  { label: '多选题', value: 1 },
  { label: '填空题', value: 2 },
  { label: '解答题', value: 3 },
  { label: '作文题', value: 4 },
  { label: '题目组', value: 5 }
];

// 校审状态列表
export const auditList = [
  { label: '未校审', value: 0 },
  { label: '已校审', value: 1 }
];

// 来源列表
export const questionSourceList = [
  { label: '原创自研', value: 0 },
  { label: '其他', value: 1 }
];

// 试卷类型
export const paperTypeList = [
  { label: '逻辑试卷', value: 1 },
  { label: '普通试卷', value: 2 }
];

// 试卷类型
export const rightsTypeList = [
  { label: '诊断考试', value: 1 },
  { label: '英语作文批改', value: 2 },
  { label: '语文作文批改', value: 3 },
  { label: '书课包', value: 4 },
  { label: '视频课', value: 5 },
  { label: '笔记资料', value: 6 },
  { label: '常规批改服务', value: 7 },
  { label: '讲座', value: 8 }
];

//  账号管理状态list
export const accountManagementStatusList = [
  { label: '全部', value: '' },
  { label: '启用', value: 0 },
  { label: '停用', value: 1 }
];

export const thumbUrlDefault =
  'https://res-t.jhpy.com/dev/20250527/af72da7a47dec74f1cabd1ff7df1aea11748336486000.png';

// 在读院校是否必填键名配置
export const SCHOOL_SETTING_KEY = {
  4: 'superior.junior.school.required', // 培优初中
  5: 'superior.highschool.school.required', // 培优高中
  7: 'online.highschool.school.required', // 网校高中
  8: 'contest.junior.school.required', // 竞赛初中
  9: 'contest.highschool.school.required', // 竞赛高中
  6: 'online.junior.school.required', // 网校初中
}

// 在读院校是否允许自主录入开关键名配置
export const SCHOOL_SETTING_ALLOW_CREATED = {
  4: 'superior.junior.school.allowCreated', // 培优初中
  5: 'superior.highschool.school.allowCreated', // 培优高中
  7: 'online.highschool.school.allowCreated', // 网校高中
  8: 'contest.junior.school.allowCreated', // 竞赛初中
  9: 'contest.highschool.school.allowCreated', // 竞赛高中
  6: 'online.junior.school.allowCreated', // 网校初中
}

// 订单来源
export const ORDER_SOURCE_TYPE = {
  0: "家辉后台", // 家辉后台
  1: "校管家", // 校管家
};
