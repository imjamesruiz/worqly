# Password Reset Implementation Guide

This guide explains how to set up and use the real email password reset functionality in Worqly.

## 🚀 Quick Start

### 1. Configure SMTP Settings

Create or update your `.env` file in the backend directory with the following SMTP configuration:

```env
# Email Configuration (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
FRONTEND_URL=http://localhost:3000
```

### 2. Gmail Setup (Recommended)

For Gmail, you'll need to:

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate an App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate a new app password for "Mail"
   - Use this password in `SMTP_PASS`

### 3. Alternative Email Providers

#### SendGrid
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=your_sendgrid_api_key
```

#### Outlook/Hotmail
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASS=your_password
```

#### Custom SMTP
```env
SMTP_HOST=your_smtp_server.com
SMTP_PORT=587
SMTP_USER=your_username
SMTP_PASS=your_password
```

## 🧪 Testing

### Test Email Configuration

Run the test script to verify your SMTP setup:

```bash
cd flowmaker/backend
python test_email.py
```

### Test the Complete Flow

1. **Start the backend**:
   ```bash
   cd flowmaker/backend
   python -m uvicorn app.main:app --reload
   ```

2. **Start the frontend**:
   ```bash
   cd flowmaker/frontend
   npm run dev
   ```

3. **Test the flow**:
   - Visit `http://localhost:3000/forgot-password`
   - Enter your email address
   - Check your email for the verification code
   - Use the code to reset your password

## 🔧 How It Works

### Backend Flow

1. **Request Reset** (`POST /password-reset/request`):
   - Validates email format
   - Generates 6-digit verification code
   - Stores token in database with 15-minute expiry
   - Sends email via SMTP

2. **Verify Code** (`POST /password-reset/verify`):
   - Validates the verification code
   - Returns success if code is valid and not expired

3. **Confirm Reset** (`POST /password-reset/confirm`):
   - Validates verification code again
   - Updates user password (hashed)
   - Marks token as used
   - Returns success message

### Frontend Flow

1. **Forgot Password Page** (`/forgot-password`):
   - User enters email address
   - Sends request to backend
   - Redirects to reset page on success

2. **Reset Password Page** (`/reset-password/:email`):
   - User enters verification code and new password
   - Validates password confirmation
   - Sends reset request to backend
   - Redirects to login on success

## 🛡️ Security Features

- **Token Expiry**: Reset tokens expire after 15 minutes
- **One-time Use**: Tokens are marked as used after successful reset
- **Rate Limiting**: Prevents abuse of reset requests
- **Secure Tokens**: Uses cryptographically secure random tokens
- **Password Hashing**: Passwords are hashed using bcrypt
- **Email Validation**: Validates email format before processing

## 📧 Email Template

The system sends a professional HTML email with:
- Clear subject line
- Verification code prominently displayed
- Expiry time information
- Security notice
- Professional styling

## 🐛 Troubleshooting

### Common Issues

1. **"SMTP credentials not configured"**:
   - Check your `.env` file has all required SMTP settings
   - Restart the backend after updating `.env`

2. **"Authentication failed"**:
   - Verify your SMTP credentials are correct
   - For Gmail, ensure you're using an App Password, not your regular password
   - Check if 2FA is enabled (required for Gmail App Passwords)

3. **"Connection refused"**:
   - Check SMTP host and port are correct
   - Ensure your firewall allows outbound SMTP connections
   - Try different ports (465 for SSL, 587 for TLS)

4. **Emails not received**:
   - Check spam/junk folder
   - Verify the email address is correct
   - Check SMTP server logs for delivery issues

### Debug Mode

The system will log detailed information when sending emails:
- SMTP server details
- Authentication status
- Delivery confirmation
- Error messages

## 🔄 Development vs Production

### Development Mode
- If SMTP is not configured, emails are logged to console
- Helpful configuration hints are displayed
- No real emails are sent

### Production Mode
- Requires proper SMTP configuration
- Real emails are sent via SMTP
- Professional email templates are used
- Error handling is more robust

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/password-reset/request` | Request password reset email |
| POST | `/password-reset/verify` | Verify reset code |
| POST | `/password-reset/confirm` | Confirm password reset |

## 🎯 Next Steps

1. **Configure SMTP** with your preferred email provider
2. **Test the flow** using the test script
3. **Customize email template** if needed
4. **Set up monitoring** for email delivery
5. **Configure rate limiting** for production use

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the backend logs for error messages
3. Test SMTP configuration with the test script
4. Verify your email provider's SMTP settings
