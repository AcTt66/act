# 医路通 Agent Pro 启动指南

## 系统状态诊断结果 ✅

经过诊断脚本检测，您的系统配置**全部正常**：
- ✅ LLM 模型调用正常 (qwen-plus)
- ✅ VLM 模型调用正常 (qwen-vl-plus) 
- ✅ 后端服务运行正常 (http://127.0.0.1:8012)
- ✅ DMXAPI 连接正常

## 启动步骤

### 1. 启动后端服务

打开一个终端窗口：

```bash
cd d:\BaiduNetdiskDownload\医路通Agent_Pro\backend
python main.py
```

后端服务将运行在：`http://127.0.0.1:8012`

### 2. 启动前端服务（使用 PowerShell）

打开**另一个**终端窗口：

```powershell
cd d:\BaiduNetdiskDownload\医路通Agent_Pro\frontend
npm install
npm run dev
```

前端服务将运行在：`http://127.0.0.1:5178`

### 3. 访问应用

在浏览器中打开：`http://127.0.0.1:5178`

## 常见问题排查

### 问题 1：后端无法启动

**错误信息**：端口已被占用
```
Error: [Errno 10048] 通常每个套接字地址(协议/网络地址/端口)只能使用一次
```

**解决方案**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8012

# 结束进程（将 <PID> 替换为实际的进程ID）
taskkill /PID <PID> /F

# 然后重新启动后端
python main.py
```

### 问题 2：前端无法启动

**错误信息**：端口已被占用
```
ERROR: Address already in use: 127.0.0.1:5178
```

**解决方案**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :5178

# 结束进程
taskkill /PID <PID> /F

# 重新启动前端
npm run dev
```

### 问题 3：浏览器显示 "无法连接到后端"

**检查清单**：
1. ✅ 后端终端窗口是否有红色错误信息？
2. ✅ 后端是否显示 `Application startup complete.` 或类似信息？
3. ✅ 尝试访问 `http://127.0.0.1:8012/api/health`，是否返回 `{"status":"ok"}`？

**如果后端无法访问**：
```powershell
# 重启后端服务
# 在后端终端窗口按 Ctrl+C 停止
# 然后重新运行
cd d:\BaiduNetdiskDownload\医路通Agent_Pro\backend
python main.py
```

### 问题 4：模型调用超时或失败

**可能原因**：
- 网络连接不稳定
- API Key 额度用完
- DMXAPI 服务暂时不可用

**解决方案**：
1. 检查网络连接
2. 访问 DMXAPI 官网查看服务状态
3. 联系 DMXAPI 客服确认账户状态

### 问题 5：Vite 前端无法识别导入

**错误信息**：`Cannot find module` 或导入错误

**解决方案**：
```powershell
# 删除 node_modules 和 package-lock.json
cd d:\BaiduNetdiskDownload\医路通Agent_Pro\frontend
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json

# 重新安装依赖
npm install
npm run dev
```

## 诊断工具使用

如果您遇到问题，可以运行诊断脚本检查系统状态：

```powershell
cd d:\BaiduNetdiskDownload\医路通Agent_Pro\backend
python diagnose_remote_model.py
```

这个脚本会检查：
- ✅ 配置文件是否正确
- ✅ LLM 客户端是否启用
- ✅ API 连接是否正常
- ✅ 后端服务是否运行

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                  用户浏览器                      │
│            http://127.0.0.1:5178                │
└──────────────────┬──────────────────────────────┘
                   │ HTTP Request
                   ▼
┌─────────────────────────────────────────────────┐
│               FastAPI 后端服务                    │
│           http://127.0.0.1:8012                  │
│                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │ LLM Client  │  │ VLM Client  │  │ Chroma  │  │
│  │ (qwen-plus)│  │(qwen-vl-plus)│ │  RAG   │  │
│  └──────┬──────┘  └──────┬──────┘  └────┬────┘  │
└─────────┼────────────────┼───────────────┼───────┘
          │                │               │
          ▼                ▼               ▼
┌─────────────────────────────────────────────────┐
│              DMXAPI 远程模型服务                  │
│          https://www.dmxapi.cn/v1               │
└─────────────────────────────────────────────────┘
```

## 快速检查清单

启动前确保：
- [ ] 后端终端：看到 `Application startup complete.`
- [ ] 前端终端：看到 `Local: http://127.0.0.1:5178`
- [ ] 浏览器：`http://127.0.0.1:5178` 可以访问
- [ ] 后端健康检查：`http://127.0.0.1:8012/api/health` 返回 `{"status":"ok"}`

## 联系支持

如果以上方法都无法解决您的问题，请：
1. 运行诊断脚本并保存输出
2. 记录遇到的具体错误信息
3. 截屏错误页面
4. 联系技术支持并提供以上信息

祝您使用愉快！🏥💊
