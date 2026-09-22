import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { resolve } from 'path';
import Compression from 'vite-plugin-compression';
import Components from 'unplugin-vue-components/vite';
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers';
import { EleAdminResolver } from 'ele-admin-plus/es/utils/resolvers';
import AutoImport from 'unplugin-auto-import/vite';

export default defineConfig(({ command, mode }) => {
    const isBuild = command === 'build';
    const env = loadEnv(mode, process.cwd(), '');
    /** 开发环境 /api → 本仓库 server（FastAPI，默认 :8000） */
    const ticketProxyTarget =
        env.VITE_TICKET_PROXY_TARGET || 'http://127.0.0.1:8000';
    const alias = {
        '@/': resolve('src') + '/',
        'vue-i18n': 'vue-i18n/dist/vue-i18n.cjs.js'
    };
    const plugins = [
        vue(),
        AutoImport({
            imports: ['vue', 'vue-router', 'pinia']
        }),
        // 注入构建时间 version meta 到 index.html，用于版本更新检测
        {
            name: 'inject-version-meta',
            transformIndexHtml(html) {
                // 开发环境用固定值，避免每次路由跳转误判版本更新
                const version = isBuild ? Date.now() : 'dev';
                return html.replace(
                    '<meta name="version" content="__BUILD_TIME__" />',
                    `<meta name="version" content="${version}" />`
                );
            }
        }
    ];
    if (isBuild) {
        // 组件按需引入
        plugins.push(
            Components({
                dts: false,
                resolvers: [
                    ElementPlusResolver({
                        importStyle: 'sass'
                    }),
                    EleAdminResolver({
                        importStyle: 'sass'
                    })
                ]
            })
        );
        // gzip压缩
        plugins.push(
            Compression({
                disable: !isBuild,
                threshold: 10240,
                algorithm: 'gzip',
                ext: '.gz'
            })
        );
    } else {
        // 开发环境全局安装
        alias['./as-needed'] = './global-import';
    }
    return {
        resolve: { alias },
        plugins,
        css: {
            preprocessorOptions: {
                scss: {
                    additionalData: `@use "@/styles/variables.scss" as *;`,
                    silenceDeprecations: ['legacy-js-api']
                }
            }
        },
        optimizeDeps: {
            include: [
                'echarts/core',
                'echarts/charts',
                'echarts/renderers',
                'echarts/components',
                'vue-echarts',
                'echarts-wordcloud'
            ]
        },
        build: {
            target: 'chrome63',
            chunkSizeWarningLimit: 2000
        },
        server: {
            port: 90,
            host: true,
            open: true,
            proxy: {
                '/api': {
                    target: ticketProxyTarget,
                    changeOrigin: true,
                    configure(proxy) {
                        proxy.on('proxyReq', (_proxyReq, req) => {
                            console.log(
                                '[ticket-proxy]',
                                req.method,
                                req.url,
                                '→',
                                ticketProxyTarget
                            );
                        });
                    }
                }
            }
        }
    };
});