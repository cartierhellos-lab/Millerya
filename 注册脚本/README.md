# TextNow 批量注册与管理工具

## 项目结构

```
project/ 
 ├── batch_register.py      # 批量注册主程序 
 ├── lock_accounts.py       # 批量锁定/解锁主程序 
 ├── config.yaml            # 凭据 / 运行参数 
 ├── phone_numbers.csv      # 联系人列表 
 ├── requirements.txt       # 依赖文件
 ├── Dockerfile             # 容器化部署
 ├── docker-compose.yml     # 一键编排（可选）
 ├── README.md              # 说明文档
 └── logs/                  # 运行日志 
```

## 本地部署（Windows/macOS/Linux）

1️⃣ 安装依赖
```bash
pip install -r requirements.txt
```

2️⃣ 准备手机号文件
编辑 `phone_numbers.csv`，格式：
```csv
phone_number
+15551234567
+15557654321
```

3️⃣ 填写配置
编辑 `config.yaml`，填入用户名、sid_cookie、后端信息等。

4️⃣ 批量注册
```bash
python batch_register.py
```
运行后会生成 `registration_results.csv`（包含 `account_id`）。

5️⃣ （可选）批量锁定或解锁
```bash
python lock_accounts.py
```
如需解锁，修改脚本的 `action` 为 `unlock` 或调用对应 endpoint。

## 容器化部署（推荐）

1️⃣ 构建镜像
```bash
docker build -t sms-register:latest .
```

2️⃣ 直接运行（只注册）
```bash
docker run --rm \
  -v %cd%/config.yaml:/app/config.yaml:ro \
  -v %cd%/phone_numbers.csv:/app/phone_numbers.csv:ro \
  -v %cd%/logs:/app/logs \
  -v %cd%/registration_results.csv:/app/registration_results.csv \
  sms-register:latest
```
> macOS/Linux 将 `%cd%` 替换为 `$(pwd)`。

3️⃣ 使用 Compose（注册 + 锁定串行执行）
```bash
docker compose up --build
```
Compose 将映射配置、号码表、日志和结果文件，并按定义的命令运行。

## 常见问题
- 手机号必须符合 E.164 格式（如 +1 开头）。
- 注意 `config.yaml` 中的速率限制设置，避免触发风控。
- 如不需要锁定功能，可在 `batch_register.py` 中屏蔽 `lock_after_registration` 调用。
