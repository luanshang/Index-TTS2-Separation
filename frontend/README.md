# IndexTTS2 Vue3 前端

这是 IndexTTS2 项目的 Vue3 前端应用，使用 Element Plus UI 框架构建。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Element Plus** - Vue 3 UI 组件库
- **Axios** - HTTP 客户端
- **TypeScript** (可选)

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 组件目录
│   │   └── TTSGenerator.css # TTS 生成器样式
│   ├── services/            # 服务层
│   │   └── api.js          # API 接口封装
│   ├── assets/              # 静态资源
│   ├── App.vue             # 根组件
│   ├── TTSGenerator.vue    # TTS 生成器主组件
│   └── main.js             # 入口文件
├── public/                  # 公共资源
├── package.json            # 项目配置
└── vite.config.js          # Vite 配置
```

## 环境要求

- Node.js >= 20.19.0 或 >= 22.12.0
- npm 或 yarn

## 安装依赖

```bash
npm install
```

## 开发环境运行

### 1. 启动后端服务

首先需要启动后端 API 服务器（在 `backend` 目录下）：

```bash
cd ../backend
python api_server.py --port 8000
```

### 2. 启动前端开发服务器

```bash
npm run dev
```

前端开发服务器会在 `http://localhost:5173` 启动，并自动代理 API 请求到后端服务器（`http://localhost:8000`）。

## 生产环境构建

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 配置说明

### Vite 代理配置

开发环境下，API 请求通过 Vite 代理转发到后端。配置文件：`vite.config.js`

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
    // ... 其他代理配置
  },
}
```

### 环境变量

可以在 `.env` 文件中配置环境变量：

```
VITE_API_BASE_URL=/api
```

## 功能特性

- ✅ 音色参考音频上传和管理
- ✅ 文本转语音生成
- ✅ 情感控制（多种方式）
  - 与音色参考音频相同
  - 使用情感参考音频
  - 使用情感向量控制
- ✅ 高级生成参数配置
- ✅ 文本分句预览
- ✅ 示例加载功能
- ✅ 响应式设计

## 开发建议

### 推荐 IDE

- [VS Code](https://code.visualstudio.com/) + [Vue Language Features (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.volar)

### 浏览器扩展

- [Vue.js devtools](https://devtools.vuejs.org/) - Vue 调试工具

## 故障排除

### 1. API 请求失败

- 确保后端服务已启动并运行在 `http://localhost:8000`
- 检查 Vite 代理配置是否正确
- 查看浏览器控制台的错误信息

### 2. 样式不生效

- 确保 Element Plus 样式已正确导入
- 检查 CSS 文件是否正确引入

### 3. 依赖安装问题

- 清除 `node_modules` 和 `package-lock.json`，重新安装：
  ```bash
  rm -rf node_mo