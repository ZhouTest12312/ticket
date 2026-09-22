// 仅展示 根据实际对应
export const dict = {
  roleSystemDictProd: {
    'jcfw.jhpy.com': {
      label: '基础服务系统',
      value: 'base_service_system'
    },
    'qxzx.jhpy.com': {
      label: '权限中心系统',
      value: 'auth_center_system'
    },
    'crm.jhpy.com': { label: 'CRM系统', value: 'crm_system' },
    'qyzx.jhpy.com': { label: '权益中心', value: 'benefit_system' },
    'jyxt.jhpy.com': {
      label: '教研系统',
      value: 'teaching_research_system'
    },
    'zdk.jhjy.tech': {
      label: '诊断考管理工作台',
      value: 'diagnostic_exam_system'
    },
    'portal.jhpy.com': {
      label: '门户登录单页',
      value: 'portal_system'
    },
    'spzx.jhpy.com': {
      label: '商品营销中心',
      value: 'product_marketing_center'
    },
    'szgl.jhpy.com': {
      label: '师资管理系统',
      value: 'teacher_management_system'
    }
  },
  roleSystemDictUat: {
    'uat-jcfw.jhjy.tech': {
      label: '基础服务系统',
      value: 'base_service_system'
    },
    'uat-qxzx.jhjy.tech': {
      label: '权限中心系统',
      value: 'auth_center_system'
    },
    'uat-crm.jhjy.tech': { label: 'CRM系统', value: 'crm_system' },
    'uat-qyzx.jhjy.tech': {
      label: '权益中心',
      value: 'benefit_system'
    },
    'uat-jyxt.jhjy.tech': {
      label: '教研系统',
      value: 'teaching_research_system'
    },
    'uat-zdk.jhjy.tech': {
      label: '诊断考管理工作台',
      value: 'diagnostic_exam_system'
    },
    'uat-portal.jhjy.tech': {
      label: '门户登录单页',
      value: 'portal_system'
    },
    'uat-spzx.jhjy.tech': {
      label: '商品营销中心',
      value: 'product_marketing_center'
    },
    'uat-szgl.jhjy.tech': {
      label: '师资管理系统',
      value: 'teacher_management_system'
    }
  },
  roleSystemDictTest: {
    'test-jcfw.jhjy.tech': {
      label: '基础服务系统',
      value: 'base_service_system'
    },
    'test-qxzx.jhjy.tech': {
      label: '权限中心系统',
      value: 'auth_center_system'
    },
    'test-crm.jhjy.tech': { label: 'CRM系统', value: 'crm_system' },
    'test-qyzx.jhjy.tech': {
      label: '权益中心',
      value: 'benefit_system'
    },
    'test-jyxt.jhjy.tech': {
      label: '教研系统',
      value: 'teaching_research_system'
    },
    'test-zdk.jhjy.tech': {
      label: '诊断考管理工作台',
      value: 'diagnostic_exam_system'
    },
    'test-portal.jhjy.tech': {
      label: '门户登录单页',
      value: 'portal_system'
    },
    'test-spzx.jhjy.tech': {
      label: '商品营销中心',
      value: 'product_marketing_center'
    },
    'test-szgl.jhjy.tech': {
      label: '师资管理系统',
      value: 'teacher_management_system'
    }
  },
  roleSystemDictDev: {
    'dev-jcfw.jhjy.tech': {
      label: '基础服务系统',
      value: 'base_service_system'
    },
    'dev-qxzx.jhjy.tech': {
      label: '权限中心系统',
      value: 'auth_center_system'
    },
    'dev-crm.jhjy.tech': { label: 'CRM系统', value: 'crm_system' },
    'dev-qyzx.jhjy.tech': {
      label: '权益中心',
      value: 'benefit_system'
    },
    'dev-jyxt.jhjy.tech': {
      label: '教研系统',
      value: 'teaching_research_system'
    },
    'dev-zdk.jhjy.tech': {
      label: '诊断考管理工作台',
      value: 'diagnostic_exam_system'
    },
    'dev-portal.jhjy.tech': {
      label: '门户登录单页',
      value: 'portal_system'
    },
    'dev-spzx.jhjy.tech': {
      label: '商品营销中心',
      value: 'product_marketing_center'
    },
    'dev-szgl.jhjy.tech': {
      label: '师资管理系统',
      value: 'teacher_management_system'
    }
  },
  /** 本地开发：各系统均指向本机前端 */
  roleSystemDictDevLocal: {
    'localhost:90': {
      label: '商品营销中心',
      value: 'product_marketing_center'
    },
    '127.0.0.1:90': {
      label: '商品营销中心',
      value: 'product_marketing_center'
    }
  }
};

export const roleEnv = {
  production: 'roleSystemDictProd',
  uat: 'roleSystemDictUat',
  test: 'roleSystemDictTest',
  dev: 'roleSystemDictDev',
  devLocal: 'roleSystemDictDevLocal'
};

/** 是否本地开发环境（localhost / devLocal / testLocal） */
export const isLocalDevEnv = () => {
  const env = import.meta.env.VITE_APP_ENV;
  if (env === 'devLocal' || env === 'testLocal') return true;
  const host = typeof location !== 'undefined' ? location.hostname : '';
  return host === 'localhost' || host === '127.0.0.1';
};

/**
 * 获取当前环境，当前用户存在多个身份时通过域名区分
 * 本地环境直接返回
 **/
export const getCurrentSystemEnvRole = () => {
  const env = import.meta.env.VITE_APP_ENV;
  const domain = location.host;
  if (isLocalDevEnv()) {
    return 'jyxt';
  }
  if (['production', 'uat', 'test', 'dev'].includes(env)) {
    const res = dict[roleEnv[env]]?.[domain]?.value;
    return res;
  }
  return 'jyxt';
};
