# 配置文件说明

## ⚠️ 重要安全提示

此目录包含敏感的配置文件，**请勿将真实配置文件提交到Git仓库！**

## 🔐 Gemini LLM 配置

### 1. 复制模板文件

```bash
cp config/gemini_config.json.template config/gemini_config.json
```

### 2. 获取Google Cloud服务账号密钥

1. **登录Google Cloud Console**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建新项目或选择现有项目

2. **启用Vertex AI API**
   ```bash
   # 或在控制台中搜索"Vertex AI API"并启用
   gcloud services enable aiplatform.googleapis.com
   ```

3. **创建服务账号**
   - 转到 "IAM和管理" > "服务账号"
   - 点击 "创建服务账号"
   - 输入服务账号名称和描述
   - 选择角色: "Vertex AI用户" 和 "AI平台开发者"

4. **生成密钥**
   - 在服务账号列表中，点击刚创建的服务账号
   - 转到 "密钥" 标签页
   - 点击 "添加密钥" > "创建新密钥"
   - 选择 "JSON" 格式并下载

### 3. 配置文件

将下载的JSON文件内容复制到 `config/gemini_config.json` 中，替换模板中的占位符：

```json
{
  "type": "service_account",
  "project_id": "your-actual-project-id",
  "private_key_id": "your-actual-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-actual-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
```

## 🛡️ 安全检查清单

在提交代码前，请确认：

- [ ] `config/gemini_config.json` 未被Git跟踪
- [ ] 没有在代码中硬编码任何API密钥
- [ ] 所有敏感文件都在 `.gitignore` 中
- [ ] 服务账号权限设置为最小必需权限

```bash
# 检查文件是否被Git忽略
git check-ignore -v config/gemini_config.json

# 应该输出类似：.gitignore:158:config/gemini_config.json
```

## 📁 忽略的文件类型

以下文件类型会被自动忽略：

```gitignore
# API配置和密钥
config/gemini_config.json
config/*_config.json
config/*.key
config/*.pem
*.credentials
*_credentials.json
service_account*.json

# 环境变量
.env*
*.secret
*secret*
*_key.json
*_keys.json
```

## 🚨 如果意外提交了敏感文件

### 立即响应步骤：

1. **从仓库中移除文件**：
   ```bash
   git rm --cached config/gemini_config.json
   git commit -m "Remove sensitive config file"
   git push
   ```

2. **清理Git历史** (如果已推送到远程)：
   ```bash
   git filter-branch --force --index-filter \
   'git rm --cached --ignore-unmatch config/gemini_config.json' \
   --prune-empty --tag-name-filter cat -- --all
   ```

3. **强制推送更新** (⚠️ 危险操作)：
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```

4. **撤销并重新生成API密钥**：
   - 在Google Cloud Console中撤销被泄露的服务账号密钥
   - 生成新的密钥文件
   - 更新本地配置

## 💡 最佳实践

### 权限管理

为服务账号设置最小必需权限：

```json
{
  "roles": [
    "roles/aiplatform.user",
    "roles/ml.developer"
  ]
}
```

### 环境变量方式 (可选)

也可以通过环境变量配置：

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/config/gemini_config.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 密钥轮换

建议定期轮换API密钥：

1. 生成新密钥
2. 更新配置文件
3. 测试应用正常工作
4. 删除旧密钥

## 🔍 故障排除

### 常见错误

1. **权限不足错误**
   ```
   Error: Permission denied when calling Gemini API
   ```
   解决：确保服务账号有正确的Vertex AI权限

2. **项目ID错误**
   ```
   Error: Project not found
   ```
   解决：检查`project_id`是否正确

3. **配置文件格式错误**
   ```
   Error: Invalid JSON format
   ```
   解决：验证JSON格式是否正确

### 验证配置

运行以下命令验证配置：

```bash
./docker-run.sh python -c "
from src.gemini_llm import GeminiLLM, gemini_config
try:
    llm = GeminiLLM(gemini_config)
    print('✅ Gemini配置成功')
except Exception as e:
    print(f'❌ 配置失败: {e}')
"
```

## 📞 获取帮助

如果遇到配置问题：

1. 检查 [Google Cloud文档](https://cloud.google.com/vertex-ai/docs)
2. 验证服务账号权限设置
3. 确认项目启用了Vertex AI API
4. 检查网络连接和防火墙设置
