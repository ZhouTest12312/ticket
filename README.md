# 克隆代码到本地
git clone https://codeup.aliyun.com/69428ad4c9f33056ad3d9ef3/super-campus/web.git

# 进入项目目录
cd web

# 检查当前分支（可以切换到测试分支进行启动）
git branch
git checkout test
3. 安装依赖
npm install
运行开发环境
npm run dev
执行后，浏览器会自动打开 http://localhost:90 页面。
开发与调试
- 代码修改后会自动热更新
- 开发过程中可以使用浏览器 DevTools 进行调试
- API 请求会通过代理转发到配置的后端地址
打包发布
npm run build:prod
# 构建生产环境包
运行/打包配置：/package.json
"scripts": {
    "dev": "vite --host --mode development",
    "serve": "vite build && vite preview --host",
    "build:test": "vite build --mode test",
    "build:uat": "vite build --mode uat",
    "build:prod": "vite build --mode production",
  },
常见问题
1. 端口被占用：如果 90 端口被占用，可以在 vite.config.js 中修改端口配置
2. 依赖安装失败：可以尝试删除 node_modules 和 package-lock.json 后重新安装
3. API 代理失败：检查 vite.config.js 中的代理配置是否正确
修改 API 代理配置
项目的 API 代理配置在 vite.config.js 文件的 server.proxy 中设置。当前配置如下：
server: {
  port: 90,
  host: true,
  open: true,
  proxy: {
    '/api': {
        //taget:"",
      changeOrigin: true,
      // rewrite: (p) => p.replace(/^\/api/, '')
    }
  }
}
修改代理地址
如果需要修改 API 代理地址，可以按照以下步骤操作：
1. 打开 vite.config.js 文件
2. 找到 server.proxy['/api'] 配置项
3. 修改 target 属性为新的后端地址
4. 如果需要重写 URL 路径，可以取消注释 rewrite 配置
注意事项
- 修改代理配置后，需要重启开发服务器才能生效
- 确保代理地址是可访问的
- 如果使用 HTTPS 代理，可能需要配置 SSL 证书验证
- changeOrigin: true 选项用于修改请求头中的 Host 字段，解决跨域问题
常用命令
开发与构建
# 安装依赖
npm install

# 开发模式（默认端口 90）
npm run dev

# 生产构建
npm run build:prod

# 开发环境构建
npm run build:dev

# 测试环境构建
npm run build:staging

# 构建并预览（生产环境）
npm run serve

# 构建并预览（测试环境）
npm run serve:staging

# 代码检查与修复
npm run lint:eslint

# 清理缓存
npm run clean:cache

# 清理依赖
npm run clean:lib
项目架构
目录结构
src/
├── api/              # API 接口文件（按模块组织）
├── assets/           # 静态资源
├── components/       # 通用组件
├── config/           # 配置文件
├── directive/        # 自定义指令
├── i18n/             # 国际化文件
├── layout/           # 布局组件
├── plugins/          # Vue 插件
├── router/           # 路由配置
├── store/            # Pinia 状态管理
├── styles/           # 全局样式
├── utils/            # 工具函数
├── views/            # 页面组件（按业务模块组织）
├── App.vue           # 根组件
├── as-needed.js      # 组件按需引入配置
├── global-import.js  # 组件全局引入配置
└── main.js           # 入口文件
核心技术栈
- 框架: Vue 3 (Composition API)
- UI 库: Element Plus + Ele Admin Plus
- 状态管理: Pinia
- 路由: Vue Router 4
- 构建工具: Vite 5
- HTTP 请求: Axios
- 国际化: Vue I18n
- 图表: ECharts
- 样式预处理: SCSS
- 代码规范: ESLint + Prettier