# Worqly Workflow Execution Guide

This guide explains how to use the newly implemented workflow execution engine in Worqly.

## 🚀 Quick Start

### 1. Start the System

```bash
# Start all services
docker-compose up --build

# Or start individual services
docker-compose up postgres redis backend celery_worker celery_beat frontend
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎨 Frontend Features

### Workflow Canvas
- **Drag & Drop**: Drag nodes from the palette to create workflows
- **Joint.js Integration**: Professional workflow canvas with zoom, pan, and grid
- **Real-time Updates**: See execution status with color-coded nodes
- **Configuration Panel**: Configure node parameters and settings

### Node Types Available
- **Triggers**: Gmail, Webhook, Schedule, Slack
- **Actions**: Send Email, Slack Message, HTTP Request, Google Sheets
- **Logic**: Conditions, Data Transformers, Filters
- **Data**: Variables, JSON Parser, CSV Parser

## ⚙️ Backend Features

### Workflow Execution Engine
- **DAG Compilation**: Automatically compiles workflows into execution graphs
- **Celery Integration**: Asynchronous task execution with Redis
- **Retry Logic**: Automatic retries with exponential backoff
- **Error Handling**: Comprehensive error logging and recovery

### API Endpoints

#### Workflow Execution
```bash
# Execute workflow
POST /api/v1/workflows/{workflow_id}/execute
{
  "trigger_data": {...},
  "test_mode": false
}

# Test workflow (synchronous)
POST /api/v1/workflows/{workflow_id}/test
{
  "trigger_data": {...}
}

# Get execution history
GET /api/v1/workflows/{workflow_id}/executions

# Get execution details
GET /api/v1/executions/{execution_id}
```

#### Webhooks
```bash
# Generic webhook
POST /api/v1/webhooks/{webhook_id}

# Gmail webhook
POST /api/v1/webhooks/gmail/{webhook_id}

# Slack webhook
POST /api/v1/webhooks/slack/{webhook_id}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://worqly_user:worqly_password@localhost:5432/worqly

# Redis
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OAuth (for integrations)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### OAuth Setup

1. **Google/Gmail**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 credentials
   - Add redirect URI: `http://localhost:8000/oauth/google/callback`

2. **Slack**:
   - Go to [Slack API](https://api.slack.com/apps)
   - Create a new app
   - Add OAuth redirect URL: `http://localhost:8000/oauth/slack/callback`

## 📊 Monitoring

### Execution Logs
- Real-time execution tracking
- Node-level success/failure status
- Execution time metrics
- Error messages and stack traces

### Celery Monitoring
```bash
# Monitor Celery workers
celery -A worker flower

# Check worker status
celery -A worker inspect active

# View task results
celery -A worker inspect stats
```

## 🧪 Testing

### Test Workflow Execution
```bash
# Test a workflow synchronously
curl -X POST "http://localhost:8000/api/v1/workflows/1/test" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"trigger_data": {"test": true}}'
```

### Webhook Testing
```bash
# Test webhook trigger
curl -X POST "http://localhost:8000/api/v1/webhooks/test-webhook-123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from webhook!"}'
```

## 🔄 Workflow Examples

### Gmail to Slack Notification
1. **Gmail Trigger**: New email received
2. **Condition**: Check if subject contains "urgent"
3. **Slack Action**: Send message to #alerts channel

### HTTP Request to Database
1. **Webhook Trigger**: Receive HTTP POST
2. **Data Transformer**: Parse JSON payload
3. **HTTP Action**: Send data to external API
4. **Condition**: Check response status
5. **Slack Action**: Notify on success/failure

## 🐛 Troubleshooting

### Common Issues

1. **Celery Worker Not Starting**:
   ```bash
   # Check Redis connection
   redis-cli ping
   
   # Restart worker
   docker-compose restart celery_worker
   ```

2. **OAuth Token Issues**:
   - Check OAuth credentials in environment
   - Verify redirect URIs match
   - Check token expiration

3. **Database Connection**:
   ```bash
   # Check PostgreSQL
   docker-compose logs postgres
   
   # Test connection
   psql -h localhost -U worqly_user -d worqly
   ```

### Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

## 📈 Performance

### Optimization Tips
- Use Redis for caching frequently accessed data
- Configure Celery worker concurrency based on CPU cores
- Monitor memory usage for large workflows
- Use database connection pooling

### Scaling
- Add more Celery workers: `docker-compose up --scale celery_worker=3`
- Use Redis Cluster for high availability
- Implement database read replicas for read-heavy workloads

## 🔒 Security

### Best Practices
- Use HTTPS in production
- Rotate OAuth tokens regularly
- Implement rate limiting
- Validate all webhook payloads
- Use environment variables for secrets

### Production Deployment
- Use Docker secrets for sensitive data
- Configure proper CORS origins
- Enable SSL/TLS termination
- Set up monitoring and alerting

## 📚 API Documentation

Full API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
