# Authentication System Guide

This guide explains the complete authentication system implementation including email verification, password reset, and security features.

## 🔐 Authentication Flow Overview

### 1. User Registration
- **Endpoint**: `POST /auth/register`
- **Features**:
  - Email format validation
  - Password strength requirements (8+ chars, letters + numbers)
  - Password confirmation matching
  - Automatic email verification sending
  - Rate limiting protection

### 2. Email Verification
- **Endpoint**: `POST /auth/verify-email`
- **Features**:
  - 6-digit verification code
  - 15-minute expiration
  - One-time use tokens
  - Automatic user verification upon success

### 3. Login
- **Endpoint**: `POST /auth/login`
- **Features**:
  - Email verification requirement
  - JWT access and refresh tokens
  - Rate limiting protection
  - Clear error messages for unverified emails

### 4. Resend Verification
- **Endpoint**: `POST /auth/resend-verification`
- **Features**:
  - Rate limiting (3 attempts per 5 minutes)
  - Security-conscious responses
  - Automatic token invalidation

### 5. Password Reset
- **Endpoints**:
  - `POST /password-reset/request` - Request reset
  - `POST /password-reset/verify` - Verify code
  - `POST /password-reset/confirm` - Reset password
- **Features**:
  - 6-digit verification codes
  - 15-minute expiration
  - Rate limiting protection
  - Secure password hashing

## 🛡️ Security Features

### Rate Limiting
- **Login attempts**: 10 per minute
- **Registration attempts**: 10 per minute
- **Resend verification**: 3 per 5 minutes
- **Password reset**: 3 per 5 minutes

### Token Security
- **Access tokens**: 15-minute expiration
- **Refresh tokens**: Configurable expiration (default 7 days)
- **Verification codes**: 15-minute expiration
- **Password reset codes**: 15-minute expiration

### Password Security
- **Hashing**: bcrypt with salt
- **Requirements**: 8+ characters, letters + numbers
- **Reset**: Secure token-based reset flow

## 📧 Email System

### Email Templates
- **Verification emails**: Professional HTML templates
- **Password reset emails**: Secure code delivery
- **Fallback**: Console output when SMTP not configured

### SMTP Configuration
Configure these environment variables for real email sending:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
```

## 🧪 Testing

### Manual Testing
1. Start the server:
   ```bash
   cd flowmaker/backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Run the test script:
   ```bash
   python test_auth_flows.py
   ```

### Test Scenarios
- ✅ User registration with email verification
- ✅ Login with unverified email (should fail)
- ✅ Email verification process
- ✅ Login with verified email (should succeed)
- ✅ Resend verification email
- ✅ Forgot password flow
- ✅ Password reset flow
- ✅ Rate limiting protection

## 📋 API Endpoints

### Authentication Endpoints
```
POST /auth/register          # Register new user
POST /auth/login             # Login user
POST /auth/verify-email      # Verify email address
POST /auth/resend-verification # Resend verification email
POST /auth/refresh           # Refresh access token
POST /auth/logout            # Logout user
POST /auth/logout-all        # Logout from all devices
GET  /auth/me                # Get current user info
```

### Password Reset Endpoints
```
POST /password-reset/request  # Request password reset
POST /password-reset/verify   # Verify reset code
POST /password-reset/confirm  # Confirm password reset
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./worqly.db

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🚨 Error Handling

### Common Error Codes
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid credentials)
- `403` - Forbidden (email not verified)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error

### Error Response Format
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## 🔄 Frontend Integration

### Login Flow
```javascript
// 1. Attempt login
const loginResponse = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

// 2. Handle unverified email
if (loginResponse.status === 403) {
  const errorData = await loginResponse.json();
  if (errorData.detail.includes('Email not verified')) {
    // Show resend verification option
    showResendVerification(email);
  }
}
```

### Resend Verification
```javascript
const resendResponse = await fetch('/auth/resend-verification', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email })
});
```

### Password Reset
```javascript
// 1. Request reset
await fetch('/password-reset/request', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email })
});

// 2. Verify code
await fetch('/password-reset/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, verification_code })
});

// 3. Reset password
await fetch('/password-reset/confirm', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email, 
    verification_code, 
    new_password, 
    confirm_password 
  })
});
```

## 🛠️ Development Notes

### Database Models
- `User` - User accounts with verification status
- `VerificationToken` - Email verification tokens
- `PasswordResetToken` - Password reset tokens
- `JWTToken` - Refresh token management

### Services
- `VerificationService` - Email verification logic
- `PasswordResetService` - Password reset logic
- `EmailService` - Email sending with templates
- `JWTService` - Token creation and validation

### Security Considerations
- All tokens have expiration times
- Rate limiting prevents abuse
- Passwords are hashed with bcrypt
- Email verification is required for login
- Tokens are invalidated after use

## 📝 Troubleshooting

### Common Issues
1. **Email not sending**: Check SMTP configuration
2. **Rate limiting**: Wait for the time window to reset
3. **Token expired**: Request a new verification code
4. **Database errors**: Ensure database is properly initialized

### Debug Mode
Set `DEBUG=True` in your environment to enable:
- SQL query logging
- Detailed error messages
- API documentation at `/docs`

## 🔮 Future Enhancements

- [ ] Two-factor authentication (2FA)
- [ ] Social login integration
- [ ] Account lockout after failed attempts
- [ ] Email template customization
- [ ] Audit logging for security events
- [ ] Redis-based rate limiting for production
