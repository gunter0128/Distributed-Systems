# 社群行銷活動系統

這是一個支援社群行銷活動的分散式系統，用於管理用戶打卡、團隊組織和即時排名計算。系統採用微服務架構，使用容器化部署，並支援自動擴展。

## 系統需求

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+
- Python 3.9+
- MongoDB 5.0+
- Redis 6.0+

## 快速開始

### 1. 環境設置

首先，克隆專案並安裝依賴：

```bash
# 克隆專案
git clone https://github.com/your-org/marketing-system.git
cd marketing-system

# 安裝後端依賴
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

# 安裝前端依賴
cd ../frontend
npm install
```

### 2. 啟動開發環境


啟動前後端應用：

```bash
# 啟動後端（新終端）
cd backend
python main.py

# 啟動前端（新終端）
cd frontend
npm run dev
```

現在你可以訪問：
- 前端應用：http://localhost:3000
- API文檔：http://localhost:8000/docs
- 監控面板：http://localhost:9090

## API 測試流程

以下是完整的API測試流程，使用curl命令示範（也可以使用Postman）：

### 1. 註冊新用戶

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User",
    "phone": "0912345678"
  }'
```

### 2. 用戶登入

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# 保存返回的token
export TOKEN="你獲得的token"
```

### 3. 創建團隊

```bash
curl -X POST http://localhost:8000/teams/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試團隊",
    "members": ["user_id_1", "user_id_2"]
  }'

# 保存返回的team_id
export TEAM_ID="獲得的team_id"
```

### 4. 上傳打卡資料

```bash
curl -X POST http://localhost:8000/activities/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "teamId=$TEAM_ID" \
  -F "location=台北101店" \
  -F "photo=@/path/to/photo.jpg" \
  -F "timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  -F "members=[\"user_id_1\",\"user_id_2\"]"
```

### 5. 查看排名

```bash
curl -X GET http://localhost:8000/rankings/top?limit=20 \
  -H "Authorization: Bearer $TOKEN"
```

## 自動化測試

執行單元測試：

```bash
# 後端測試
cd backend
pytest tests/

# 前端測試
cd frontend
npm test
```

執行壓力測試：

```bash
# 啟動Locust
cd tests/load
locust -f locustfile.py --host=http://localhost:8000
```

然後訪問 http://localhost:8089 配置測試參數。

## 系統監控

1. 訪問 Grafana（http://localhost:3000）
2. 使用預設帳號密碼登入（admin/admin）
3. 導入 `monitoring/dashboards/system-metrics.json` 

## 常見問題

1. 如果遇到資料庫連接問題：
   ```bash
   docker-compose restart mongodb
   ```

2. 清除所有資料重新開始：
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

3. 查看服務日誌：
   ```bash
   docker-compose logs -f [service_name]
   ```

## 開發指引

1. 提交程式碼前：
   - 運行所有測試
   - 檢查程式碼風格 `flake8 backend/`
   - 更新文檔（如有必要）

2. 建立新分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. 提交變更：
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

## 貢獻指南

1. Fork 專案
2. 建立功能分支
3. 提交變更
4. 發送 Pull Request

## 授權協議

MIT License
