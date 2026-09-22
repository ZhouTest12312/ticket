import { defineStore } from 'pinia';

export const useGetNew = defineStore('getNew', {
  state: () => ({
    // status: '',
    refundCount: 0,
    orderCount: 0, // 培优订单数量
    // orderCountStatus: '',
    // refundCountStatus: '',
    mangerCount: 0,
    // mangerCountStatus: '',
    attendenceCount: 0,
    // attendenceCountStatus:'',
    // 存储的是各个页面缓存的数据
    queryParams: {},
    // 存储layout菜单栏折叠收起状态
    // isLayoutCollapsed: false,
    userInfo: {},
    // closeRouterPath:'',
    // 现金券工单待处理数量
    cashCouponPendingCount: 0,
    revokeCount: 0
    // revokeCountStatus: '',
    // isMarketingRole: false,
    // isOperatorRole: false,
    // saleTaskCount: 0, //销售线索-任务列表数量
    // saleTaskCountStatus: '',
    // operationTaskCount: 0, //运营线索-任务列表数量
    // operationTaskCountStatus: '',
    // marketingPermissions: [],
    // permIds: [],
    // menusData: [],
  }),
  actions: {
    // setState(status) {
    //     this.status = status;
    // },
    setRefundCount(refundCount) {
      this.refundCount = refundCount;
    },
    // setOrderCount(orderCount) {
    //     this.orderCount = orderCount;
    // },
    /**
     * 基于培优原有逻辑改造，请求接口设置订单数量
     * @param {*} orderCountStatus
     */
    setOrderCountStatus() {},
    setRefundCountStatus(refundCountStatus) {
      this.refundCountStatus = refundCountStatus;
    },
    setMangerRefundCount(mangerCount) {
      this.mangerCount = mangerCount;
    },
    setMangerRefundCountStatus(mangerCountStatus) {
      this.mangerCountStatus = mangerCountStatus;
    },
    // setAttendenceCount(attendenceCount) {
    //     this.attendenceCount = attendenceCount;
    // },
    // 考勤异常处理
    setAttendenceCountStatus() {},
    setQueryParams(key, value) {
      if (typeof value === 'object' && value !== null) {
        this.queryParams[key] = { ...this.queryParams[key], ...value };
      } else {
        this.queryParams[key] = value;
      }
    },
    clearQueryParams(key) {
      delete this.queryParams[key];
    },
    // clearAllQueryParams() {
    //   this.queryParams = {};
    // },
    // updateLayoutCollapsed(value) {
    //   this.isLayoutCollapsed = value;
    // },
    setUserInfo(value) {
      this.userInfo = value;
      // this.isMarketingRole = value?.roleTypeName=='学习顾问'||value?.roleTypeName=='校区主管';
      // this.isOperatorRole = value?.roleTypeName=='运营专员'||value?.roleTypeName=='TMK专员'||value?.roleTypeName=='运营主管'||value?.roleTypeName=='TMK主管';
    },
    // setMarketingPermissions(value) {
    //   this.marketingPermissions = value;
    //   this.permIds = value?.map(item => item.marketingPermissionsId);
    // },
    // setCloseRouterPath(value) {
    //   this.closeRouterPath = value;
    // },
    setCashCouponPendingCount(value) {
      this.cashCouponPendingCount = value;
    },
    // setRevokeCount(value) {
    //   this.revokeCount = value;
    // },
    setRevokeCountStatus() {}
    // setSaleTaskCount(value) {
    //   this.saleTaskCount = value;
    // },
    // setSaleTaskCountStatus(value) {
    //   this.saleTaskCountStatus = value;
    // },
    // setOperationTaskCount(value) {
    //   this.operationTaskCount = value;
    // },
    // setOperationTaskCountStatus(value) {
    //   this.operationTaskCountStatus = value;
    // },
    // setMenusData(value) {
    //   this.menusData = value;
    // },
  }
});
