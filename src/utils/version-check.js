import { ElMessageBox } from 'element-plus/es';

const VERSION_META_KEY = 'version';

let checking = false;

/**
 * 检测是否有新版本（路由守卫中调用，自动节流）
 * 检测到新版本后弹窗提示刷新
 */
export async function checkVersion() {
  if (checking) return;
  const currentVersion = document.querySelector(
    `meta[name="${VERSION_META_KEY}"]`
  )?.content;
  if (!currentVersion) return;

  checking = true;
  try {
    const res = await fetch(`/index.html?t=${Date.now()}`, {
      cache: 'no-cache'
    });
    const html = await res.text();
    const match = html.match(
      new RegExp(`<meta name="${VERSION_META_KEY}" content="(.+?)"`)
    );
    if (match && match[1] !== currentVersion) {
      ElMessageBox.confirm('检测到新版本，是否刷新页面？', '版本更新', {
        confirmButtonText: '刷新',
        cancelButtonText: '稍后',
        type: 'warning',
        closeOnClickModal: false
      }).then(() => {
        window.location.reload();
      });
    }
  } catch (_) {
    // 网络异常静默忽略
  } finally {
    checking = false;
  }
}
