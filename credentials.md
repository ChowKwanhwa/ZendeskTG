# SuperEx Zendesk-Telegram 集成所需凭据清单

## 1. Zendesk 凭据
- [ ] Zendesk 管理员邮箱
  - 当前值：chowkwunhwa@gmail.com（测试用）
  - 需要替换为：SuperEx 的官方 Zendesk 管理员邮箱
  - 用途：用于 Zendesk API 认证和工单管理

- [ ] Zendesk API Token
  - 当前值：测试 token
  - 需要替换为：SuperEx Zendesk 的正式 API Token
  - 用途：进行 API 调用的认证

- [ ] Zendesk 子域名
  - 当前值：superex4871（测试用）
  - 需要替换为：SuperEx 的官方 Zendesk 子域名
  - 用途：确定 API 调用的目标域名

## 2. Telegram Bot 凭据
- [ ] Telegram Bot Token
  - 当前值：测试 bot token
  - 需要替换为：SuperEx 官方客服 Bot Token
  - 用途：发送和接收 Telegram 消息

## 3. Webhook 配置
- [ ] Webhook URL
  - 当前值：ngrok 测试 URL
  - 需要替换为：生产环境的固定 URL
  - 用途：接收 Zendesk 的事件通知

- [ ] Webhook 安全密钥
  - 当前值：测试密钥
  - 需要替换为：生产环境的安全密钥（如果需要）
  - 用途：确保 webhook 调用的安全性

## 4. 可选配置
- [ ] 工单表单 ID
  - 用途：指定创建工单时使用的表单模板
  - 获取方式：从 Zendesk 管理面板或向客服主管询问

- [ ] 客服组 ID
  - 用途：指定工单分配的目标组
  - 获取方式：从 Zendesk 管理面板或向客服主管询问

- [ ] 特定要求
  - 工单标签要求
  - 自定义字段要求
  - 工单优先级规则
  - 其他特殊配置

