/**
 * 登录用户状态管理（工单/角色本地模式精简版）
 */
import { defineStore } from 'pinia';
import { isExternalLink } from 'ele-admin-plus/es';
import { API_BASE_URL } from '@/config/setting';
import { isTicketApiEnabled, ticketMe } from '@/api/ticketAuth';

export const useUserStore = defineStore('user', {
  state: () => ({
    info: null,
    peiyouUserInfo: null,
    menus: null,
    authorities: [],
    roles: [],
    dicts: {},
    userData: {},
    crmUserData: {},
    teachData: {},
    getPath: [],
    lessType: '',
    showWaitCount: false,
    systemList: [],
    envType:
      (typeof localStorage !== 'undefined' &&
        localStorage.getItem('ENV_TYPE')) ||
      '',
    systemEnvRole: null
  }),
  actions: {
    async fetchUserInfo() {
      if (isTicketApiEnabled()) {
        const me = await ticketMe();
        this.setInfo({
          userId: me.id,
          username: me.username,
          nickname: me.displayName,
          // header-user 读取 name / jobNumber
          name: me.displayName || me.username,
          jobNumber: me.username,
          avatar: ''
        });
        this.authorities = me.permissions || [];
        this.roles = (me.roles || []).map((r) => r.code);
        const menus = (me.menus || [])
          .map((m) => {
            if (!m?.children?.length) return m;
            return {
              ...m,
              children: m.children.filter(
                (c) => c.path !== '/system/user-role'
              )
            };
          })
          .filter((m) => m.path !== '/system/user-role');
        this.setMenus(menus);
        return { menus, homePath: me.homePath || '/welcome' };
      }
      return { menus: [], homePath: '/welcome' };
    },

    setWaitCount(value) {
      this.showWaitCount = value;
    },

    setInfo(data) {
      if (data) {
        if (!data.avatar) {
          data.avatar = 'https://cdn.eleadmin.com/20200610/avatar.jpg';
        } else if (!isExternalLink(data.avatar)) {
          data.avatar = API_BASE_URL + data.avatar;
        }
      }
      this.info = data || {};
      localStorage.setItem('info', JSON.stringify(data));
    },

    setPeiyouUserInfo(data) {
      this.peiyouUserInfo = data || {};
    },

    setEnvType(value) {
      const v = value == null ? '' : String(value);
      this.envType = v;
      try {
        if (v) {
          localStorage.setItem('ENV_TYPE', v);
        } else {
          localStorage.removeItem('ENV_TYPE');
        }
      } catch (_) {}
    },

    setMenus(value) {
      this.menus = value;
    },

    getUserData(value) {
      this.userData = value;
    },

    setCrmUserData(value) {
      this.crmUserData = value;
    },

    setLessonType(value) {
      this.lessType = value;
    },

    setDicts(value, code) {
      if (code == null) {
        this.dicts = value;
        return;
      }
      this.dicts[code] = value;
    },

    setSystemEnvRole(value) {
      this.systemEnvRole = value;
    },

    setSystemList(value) {
      localStorage.setItem('SYSTEM_LIST', JSON.stringify(value));
      this.systemList = value;
    },

    getSystemList() {
      return JSON.parse(localStorage.getItem('SYSTEM_LIST') || '[]');
    },

    /** 兼容旧调用：本地模式无远程菜单 */
    async getUseMenu() {
      return { menus: this.menus || [], homePath: '/system/role' };
    },

    async fetchCrmUserDetail() {
      return null;
    }
  }
});
