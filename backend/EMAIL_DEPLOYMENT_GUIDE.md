# 📧 Email Configuration for Deployment

## 🚀 **Quick Setup Options**

### **Option 1: Gmail SMTP (Easiest)**

#### **1. Create `.env` file:**
```bash
# Gmail SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_USE_TLS=true
```

#### **2. Gmail Setup:**
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and generate password
   - Use this 16-character password in `SMTP_PASS`

#### **3. Test:**
```bash
# Start your server
python -m uvicorn app.main:app --reload

# Test forgot password
curl -X POST http://localhost:8000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@gmail.com"}'
```

---

### **Option 2: Resend API (Recommended for Production)**

#### **1. Sign up at [Resend.com](https://resend.com)**
- Free tier: 3,000 emails/month
- Easy setup, great deliverability

#### **2. Create `.env` file:**
```bash
# Resend API Configuration
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=noreply@yourdomain.com
```

#### **3. Test:**
```bash
# Test forgot password
curl -X POST http://localhost:8000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

### **Option 3: SendGrid API**

#### **1. Sign up at [SendGrid.com](https://sendgrid.com)**
- Free tier: 100 emails/day
- Enterprise-grade email service

#### **2. Create `.env` file:**
```bash
# SendGrid API Configuration
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=Your App Name
```

---

### **Option 4: Mailgun API**

#### **1. Sign up at [Mailgun.com](https://mailgun.com)**
- Free tier: 5,000 emails/month for 3 months
- Great for transactional emails

#### **2. Create `.env` file:**
```bash
# Mailgun API Configuration
MAILGUN_API_KEY=your_mailgun_api_key
MAILGUN_DOMAIN=your_domain.mailgun.org
MAILGUN_FROM_NAME=Your App Name
```

---

## 🔧 **Production Deployment**

### **Docker Deployment**

#### **1. Update `docker-compose.yml`:**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    environment:
      - SMTP_HOST=smtp.gmail.com
      - SMTP_PORT=587
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASS=${SMTP_PASS}
      - SMTP_USE_TLS=true
    env_file:
      - .env
```

#### **2. Create `.env` file:**
```bash
# Email Configuration
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password

# Or use API service
RESEND_API_KEY=re_your_api_key_here
```

#### **3. Deploy:**
```bash
docker-compose up -d
```

---

### **Cloud Deployment (Railway, Render, etc.)**

#### **1. Set Environment Variables:**
```bash
# In your cloud provider dashboard
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_USE_TLS=true
```

#### **2. Or use API service:**
```bash
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM_EMAIL=noreply@yourdomain.com
```

---

## 🧪 **Testing Email Configuration**

### **Test Script:**
```bash
cd flowmaker/backend
python -c "
from app.services.email_providers import get_email_provider
provider = get_email_provider()
if provider:
    print('✅ Email provider configured:', type(provider).__name__)
    success = provider.send_email('test@example.com', 'Test Email', '<h1>Test</h1>')
    print('✅ Email sent successfully!' if success else '❌ Email failed')
else:
    print('❌ No email provider configured')
"
```

### **Test Endpoints:**
```bash
# Test verification email
curl -X POST http://localhost:8000/resend-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Test password reset email
curl -X POST http://localhost:8000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

---

## 📋 **Email Provider Comparison**

| Provider | Free Tier | Setup Difficulty | Deliverability | Best For |
|----------|-----------|------------------|----------------|----------|
| **Gmail SMTP** | Unlimited* | Easy | Good | Development, Small apps |
| **Resend** | 3,000/month | Very Easy | Excellent | Production, Modern apps |
| **SendGrid** | 100/day | Medium | Excellent | Enterprise, High volume |
| **Mailgun** | 5,000/month | Medium | Good | Transactional emails |

*Gmail has daily limits but generous for most use cases

---

## 🚨 **Security Best Practices**

### **1. Environment Variables**
- ✅ **Never commit** `.env` files to git
- ✅ **Use secrets management** in production
- ✅ **Rotate API keys** regularly

### **2. Email Security**
- ✅ **Use app passwords** for Gmail (not your main password)
- ✅ **Enable 2FA** on email accounts
- ✅ **Use dedicated email addresses** for your app

### **3. Rate Limiting**
- ✅ **Rate limiting is already implemented** (3 attempts per 5 minutes)
- ✅ **Monitor email usage** to prevent abuse
- ✅ **Set up alerts** for unusual activity

---

## 🔍 **Troubleshooting**

### **Common Issues:**

#### **1. Gmail "Less Secure Apps" Error**
```bash
# Solution: Use App Password instead of regular password
# 1. Enable 2FA on Gmail
# 2. Generate App Password
# 3. Use App Password in SMTP_PASS
```

#### **2. "Authentication Failed" Error**
```bash
# Check your credentials
echo $SMTP_USER
echo $SMTP_PASS

# Test with a simple SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_app_password')
print('✅ SMTP connection successful')
server.quit()
"
```

#### **3. API Key Issues**
```bash
# Test API key
curl -H "Authorization: Bearer $RESEND_API_KEY" \
  https://api.resend.com/domains
```

---

## 📞 **Support**

### **Need Help?**
1. **Check the console output** - it shows detailed error messages
2. **Test with curl** - verify endpoints are working
3. **Check environment variables** - make sure they're set correctly
4. **Try different providers** - Gmail → Resend → SendGrid

### **Quick Test:**
```bash
# 1. Start server
python -m uvicorn app.main:app --reload

# 2. Test forgot password
curl -X POST http://localhost:8000/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "your_email@example.com"}'

# 3. Check your email or console output
```

---

## 🎉 **You're All Set!**

Once configured, your users will receive real emails for:
- ✅ **Email verification** (account activation)
- ✅ **Password reset** (account recovery)

No more console output - real emails delivered to users' inboxes! 📧✨
