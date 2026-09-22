<template>
  <div class="login-wrapper" ref="loginWrapper">
    <div class="login-pageHeader" style="display: flex; align-items: flex-end">
      <!-- <img style="width: 130px" src="@/assets/companyLogo.png" />
      <span
        v-if="envTest"
        style="
          color: #7a869a;
          font-size: 17px;
          height: 34px;
          display: flex;
          align-items: flex-end;
        "
        >丨{{ envTest }}</span
      > -->
    </div>
    <ele-card shadow="never" class="login-card">
      <div class="login-cover" :style="loginCoverStyle"></div>
      <div class="login-body">
        <div class="login-heading">
          <h1 class="login-title-text">用户登录</h1>
          <p class="login-desc">客户问题工单系统 · 请使用分配的账号进入</p>
        </div>
        <el-form
          v-if="tabActive === 1"
          ref="formRef"
          size="large"
          :model="form"
          :rules="rules"
          @keyup.enter="submit"
          @submit.prevent=""
        >
          <el-form-item prop="account">
            <el-input
              clearable
              v-model.trim="form.account"
              placeholder="账号"
              maxlength="32"
              :input-style="inputStyle"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              ref="passwordInputRef"
              v-model.trim="form.password"
              placeholder="密码"
              :input-style="inputStyle"
              :type="passwordType"
            >
              <template #suffix>
                <el-icon
                  color="#a8abb2"
                  @click="togglePassword"
                  style="cursor: pointer"
                >
                  <Hide v-if="passwordType === 'password'" />
                  <View v-else />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="form.remember">
              <span class="rememberText">记住登录信息</span>
            </el-checkbox>
          </el-form-item>
          <el-button
            size="large"
            type="primary"
            :loading="loading"
            @click="submit"
            color="#0096ff"
            class="loginBtn"
          >
            {{ t('login.login') }}
          </el-button>
        </el-form>
      </div>
    </ele-card>
    <div class="login-interText">
      <!-- <a href="http://beian.miit.gov.cn/" target="_blank"
        >沪ICP备2020030265号-1</a
      >
      <a
        target="_blank"
        href="http://www.beian.gov.cn/portal/registerSystemInfo?recordcode=31011502016287"
        >沪公网安备 31011502016287号</a
      > -->
    </div>
  </div>
</template>

<script setup>
  import {
    ref,
    reactive,
    unref,
    computed,
    onMounted,
    nextTick,
    watch,
    onBeforeMount
  } from 'vue';
  import { dict, roleEnv } from '@/utils/envRole';
  import { useRouter } from 'vue-router';
  import { EleMessage } from 'ele-admin-plus/es';
  import { useUserStore } from '@/store/modules/user';
  import { getToken } from '@/utils/token-util';
  import { usePageTab } from '@/utils/use-page-tab';
  import { login, getCaptcha, mobileLogin } from '@/api/login';
  import { useI18n } from 'vue-i18n';
  import { removeToken, setToken } from '@/utils/token-util';
  import { isTicketApiEnabled } from '@/api/ticketAuth';
  import { Hide, View } from '@element-plus/icons-vue';
  import { getMenu } from '@/api/layout';
  import { currentUserSystems, toLogout } from '@/api/login';
  import CryptoJS from 'crypto-js';
  const userStore = useUserStore();
  const envRole = ref('');
  const currentSystemCode = ref('');
  const { t } = useI18n();

  const loginCoverStyle = computed(() => ({}));
  const { currentRoute, push, replace } = useRouter();
  const { goHomeRoute, cleanPageTabs } = usePageTab();
  const inputStyle = {
    height: '42px'
  };
  /** 密码输入框类型 */
  const passwordType = ref('password');
  const passwordInputRef = ref(null);
  /** 密码明密文切换 */
  const togglePassword = () => {
    passwordType.value = passwordType.value === 'password' ? '' : 'password';
    const inputElement = passwordInputRef.value?.input;
    if (inputElement) {
      const length = inputElement.value.length;
      setTimeout(() => {
        inputElement.setSelectionRange(length, length);
        inputElement.focus();
      });
    }
  };
  const loginWrapper = ref(null);
  /** 页签选中 */
  const tabActive = ref(1);
  const onTabChange = (active) => {};

  /** 表单 */
  const formRef = ref();

  /** 加载状态 */
  const loading = ref(false);

  /** 表单数据 */
  const form = reactive({
    account: '',
    password: '',
    remember: false
  });

  /** 表单验证规则 */
  const rules = computed(() => {
    return {
      account: [
        {
          required: true,
          message: '账号不能为空',
          type: 'string',
          trigger: 'blur'
        }
      ],
      password: [
        {
          required: true,
          message: '密码不能为空',
          type: 'string',
          trigger: 'blur'
        }
      ],
      code: [
        {
          required: true,
          message: t('login.code'),
          type: 'string',
          trigger: 'blur'
        }
      ]
    };
  });

  /** 二维码 */
  const qrcode = ref('');

  // 倒计时的秒数
  const countdown = ref(0);

  // 发送验证码函数
  const sendVerificationCode = () => {
    formRef?.value?.validateField('account', (valid) => {
      if (!valid) {
        return;
      }
      console.log('发送验证码');

      // 如果倒计时已经开始，则直接返回
      if (countdown.value > 0 || !form.account) return;
      getCaptcha({ mobile: form.account }).then((res) => {
        if (res.code == 200) {
          // 设置倒计时为60秒
          countdown.value = 60;

          // 启动定时器，每秒减少一秒
          const timer = setInterval(() => {
            countdown.value--;

            // 当倒计时结束时，清除定时器
            if (countdown.value === 0) {
              clearInterval(timer);
            }
          }, 1000);
        } else {
          EleMessage.error(res.msg);
        }
      });
    });
  };

  /** 提交 */
  const submit = () => {
    formRef.value?.validate?.((valid) => {
      if (!valid) {
        return;
      }
      loading.value = true;
      const payload = {
        ...form,
        password: CryptoJS.MD5(String(form.password)).toString()
      };
      const loginByMessageParams = {
        smsCode: form.code,
        mobile: form.account,
        remember: form.remember
      };
      const loginApi = tabActive.value == 1 ? login : mobileLogin;
      const params = tabActive.value == 1 ? payload : loginByMessageParams;
      loginApi(params)
        .then((result) => {
          if (form.remember) {
            loginSuccess(form.account, form.password);
          } else {
            localStorage.removeItem('account');
            localStorage.removeItem('password');
          }
          try {
            if (tabActive.value === 1 && String(form.password) === '123456') {
              sessionStorage.setItem('mustChangePwd', '1');
              sessionStorage.setItem(
                'oldPwdMd5',
                CryptoJS.MD5(String(form.password)).toString()
              );
            } else {
              sessionStorage.removeItem('mustChangePwd');
              sessionStorage.removeItem('oldPwdMd5');
            }
            sessionStorage.removeItem('skipPwdChange');
          } catch {}
          cleanPageTabs();
          const homePath =
            result && typeof result === 'object' ? result.homePath : undefined;
          goHome(homePath);
        })
        .catch((e) => {
          loading.value = false;
          EleMessage({
            showClose: true,
            message: e.message,
            type: 'error',
            appendTo: loginWrapper.value
          });
        });
    });
  };
  // 登录成功后
  function loginSuccess(account, password) {
    const encryptedPassword = encryptPassword(password);
    localStorage.setItem('account', account);
    localStorage.setItem('password', encryptedPassword);
  }

  // 加密
  function encryptPassword(password) {
    return CryptoJS.AES.encrypt(password, 'secret-key').toString();
  }

  // 解密
  function decryptPassword(encryptedPassword) {
    const bytes = CryptoJS.AES.decrypt(encryptedPassword, 'secret-key');
    return bytes.toString(CryptoJS.enc.Utf8);
  }

  // 页面加载时自动填充
  function getPassword() {
    const account = localStorage.getItem('account');
    const encryptedPassword = localStorage.getItem('password');
    if (account && encryptedPassword) {
      form.account = account;
      form.password = decryptPassword(encryptedPassword);
      form.remember = true;
    }
  }

  /** 刷新二维码 */
  const refreshQrCode = () => {
    qrcode.value = `https://api.eleadmin.com/v2/auth/login?code=${Date.now()}`;
  };
  const logoText = ref(useUserStore().envType);
  const envTest = computed(() =>
    logoText.value === 'base_service_system'
      ? '基础服务系统'
      : logoText.value === 'auth_center_system'
        ? '权限管理系统'
        : logoText.value == 'crm_system'
          ? 'CRM客户管理系统'
          : logoText.value == 'benefit_system'
            ? '权益中心'
            : logoText.value === 'teaching_research_system'
              ? '教研管理系统'
              : ''
  );
  const waitCount = ref(0);
  const payCount = ref(0);
  /** 跳转到首页 */
  const goHome = (homePath) => {
    if (isTicketApiEnabled()) {
      loading.value = false;
      // 清空 menus，让路由守卫重新拉取并注册动态路由
      useUserStore().setMenus(null);
      replace(homePath || '/welcome');
      return;
    }
    currentUserSystems().then((systems) => {
      loading.value = false;
      console.log(systems, 'systems');
      if (systems.code == 200) {
        const systemList = systems.data;
        useUserStore().setSystemList(systemList);
        const { query } = unref(currentRoute);
        console.log('跳转：', query);
        const storeRole = useUserStore().systemEnvRole;
        console.log(storeRole, 'storeRo-login');
        if (!storeRole) {
          // 本仓库无 /mySystem 页面，避免登录后白屏
          EleMessage.error('未识别到系统环境，请检查配置');
          removeToken();
          loading.value = false;
        } else {
          if (storeRole == 'portal_system' || storeRole == 'jyxt') {
            useUserStore().fetchUserInfo();
            EleMessage.error('当前环境未接入系统选择页');
            removeToken();
            loading.value = false;
            return;
          }
          useUserStore().setEnvType(storeRole);
          if (storeRole != 'portal_system' && storeRole != null) {
            getMenu(storeRole).then((res) => {
              if (res.code != 200) {
                EleMessage.error(res.msg);
                loading.value = false;
                removeToken();
              } else {
                useUserStore().getUseMenu();
                replace('/welcome');
              }
            });
          }
        }
      } else {
        EleMessage.error(systems.msg);
      }
    }).catch((e) => {
      loading.value = false;
    });
  };

  onMounted(() => {
    getPassword();
  });
  const envSys = ref('');
  // 立即执行的环境检测和跳转逻辑
  const checkAndRedirect = () => {
    const storeRole = useUserStore().systemEnvRole;
    envSys.value = useUserStore().systemEnvRole;
    const envT = useUserStore().envType;
    console.log(envT, 'envT');

    const env = import.meta.env.VITE_APP_ENV;

    if (storeRole == 'jyxt') {
      envRole.value = '';
    }
    envRole.value = storeRole;

    // 在非本地环境时，根据域名从字典获取正确的系统代码值
    if (['production', 'uat', 'test', 'dev'].includes(env)) {
      const domain = window.location.host;
      console.log(domain);

      const envKey = roleEnv[env];
      const systemInfo = dict[envKey]?.['https://' + domain];
      if (systemInfo) {
        currentSystemCode.value = systemInfo.value;
      } else {
        currentSystemCode.value = envRole.value;
      }
    } else {
      currentSystemCode.value = '';
    }

    return false; // 表示未跳转
  };

  onBeforeMount(() => {
    // 先检查是否是 portal 系统，如果是则跳转到 /mySystem
    if (checkAndRedirect()) {
      // 如果已经跳转到 /mySystem，不再执行后续逻辑（包括登录检查）
      return;
    }

    // 如果不是 portal 系统，继续执行原有的登录检查
    if (getToken()) {
      goHome();
    }
  });
</script>

<style lang="scss" scoped>
  .login-wrapper {
    min-height: 100vh;
    box-sizing: border-box;
    padding: 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-image: url('@/assets/loginBackground.jpg');
    background-repeat: no-repeat;
    background-size: 100% 100%;
    position: relative;
    :deep(.ele-message) {
      position: absolute !important;
      top: 92px !important;
      right: 24px !important;
    }
    .login-pageHeader {
      position: absolute;
      top: 0;
      left: 0;
      background-color: #ffffff;
      width: 100%;
      text-align: left;
    }
    .login-card {
      width: 920px;
      max-width: 100%;
      overflow: hidden;
      background-color: transparent;
      border-radius: 0;
      box-sizing: content-box;
      padding: 20px;

      :deep(.ele-card-body) {
        display: flex;
        padding: 0;
        height: 428px;
        justify-content: space-between;
      }

      :deep(.el-form-item--large) {
        margin-bottom: 22px;
      }
    }
    .loginBtn {
      width: calc(100% - 60px);
      position: absolute;
      bottom: 56px;
      color: #fff;
    }
  }

  .login-cover {
    box-sizing: border-box;
    background-image: var(--login-cover-bg, url('@/assets/Jhbackstage.png'));
    background-repeat: no-repeat;
    background-position: bottom;
    background-size: contain;
    text-align: center;
    width: 428px;
  }

  .login-body {
    width: 368px;
    flex-shrink: 0;
    padding: 48px 30px 55px;
    box-sizing: border-box;
    background: #ffffff;
    box-shadow: 0px 2px 25px 0px rgba(222, 232, 255, 0.5);
    border-radius: 8px;
    position: relative;

    .login-heading {
      margin-bottom: 18px;
    }

    .login-eyebrow {
      margin: 0 0 6px;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #0096ff;
    }

    .login-title-text {
      margin: 0;
      font-size: 22px;
      line-height: 1.3;
      font-weight: 700;
      color: #000;
    }

    .login-desc {
      margin: 8px 0 0;
      font-size: 13px;
      line-height: 1.5;
      color: #7a869a;
    }

    :deep(.el-checkbox) {
      height: auto;

      .el-checkbox__label {
        color: inherit;
      }
      .is-checked .el-checkbox__inner {
        background: #0096ff;
        border-color: #0096ff;
      }
    }

    :deep(.el-input__prefix-inner > .el-icon) {
      margin-right: 12px;
      transform: scale(1.16);
    }
    .rememberText {
      font-size: 14px;
      color: #606266;
    }
  }

  .login-captcha-group {
    width: 100%;
    display: flex;
    align-items: center;

    :deep(.el-input) {
      flex: 1;
    }

    .login-captcha {
      flex-shrink: 0;
      width: 108px;
      height: 40px;
      margin-left: 8px;
      border-radius: var(--el-border-radius-base);
      border: 1px solid var(--el-border-color);
      transition: border 0.2s;
      box-sizing: border-box;
      background: #fff;
      overflow: hidden;
      cursor: pointer;

      img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
      }

      &:hover {
        border-color: var(--el-color-primary);
      }
    }
  }

  .login-interText {
    position: absolute;
    bottom: 36px;
    font-family:
      PingFangSC,
      PingFang SC;
    font-weight: 400;
    font-size: 12px;
    color: #999999;
    a {
      text-decoration: none;
      margin: 0 3px;
      color: #999999;
    }
  }

  @media screen and (max-width: 680px) {
    .login-wrapper {
      padding: 0;
      display: block;
      background: #fff;
      text-align: center;

      .login-card {
        width: 100%;
        background: none;
        box-shadow: none;
        border-radius: 0;
        box-sizing: border-box;
        padding-bottom: 100px;
        position: static;

        :deep(.ele-card-body) {
          display: block;
          height: auto;
        }
      }

      .loginBtn {
        position: static;
        width: 100%;
        margin-top: 47px;
      }
      .login-interText {
        left: 50%;
        transform: translate(-50%, -50%);
        bottom: 20px;
        width: 100%;
        a {
          text-decoration: none;
          display: flex;
          justify-content: center;
          flex-wrap: nowrap;
        }
      }
    }

    .login-cover {
      width: 100%;
      position: relative;
      height: 343px;
    }

    .login-body {
      width: 100%;
    }
  }
</style>

<style lang="scss">
  html.dark .login-wrapper {
    background: #000;
  }
</style>
