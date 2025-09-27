# TimeAPI Authentication Guide

Your Vercel deployment has authentication protection enabled. Here's how to handle it:

## 🔒 **Current Issue**

Your API at `https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/` requires authentication to access.

## ✅ **Solutions**

### **Option 1: Disable Authentication Protection (Recommended)**

**For a public API, disable authentication protection:**

1. **Go to [Vercel Dashboard](https://vercel.com/dashboard)**
2. **Select your project** (`promptly-m5lk5lrg1-krishs-projects-32b186bc`)
3. **Go to Settings** → **Security**
4. **Under "Deployment Protection"**:
   - Set to **"None"** for public access
   - Or **"Password"** with a simple password
5. **Save changes**

### **Option 2: Use Bypass Token (For Testing)**

**If you want to keep protection enabled:**

1. **In Vercel Dashboard** → **Project Settings** → **Security**
2. **Generate a bypass token**
3. **Use it in your requests:**

```bash
# Test with bypass token
curl -X GET "https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/health?x-vercel-protection-bypass=YOUR_BYPASS_TOKEN"

# Using the Python client
python3 client.py "Test API" --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app --bypass-token YOUR_BYPASS_TOKEN
```

### **Option 3: Environment Variable**

**Set bypass token as environment variable:**

```bash
# Set environment variable
export VERCEL_BYPASS_TOKEN=your_bypass_token_here

# Use client normally
python3 client.py "Test API" --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app
```

## 🧪 **Testing Your API**

### **After disabling protection:**

```bash
# Test health endpoint
curl https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/health

# Test scheduling
curl -X POST https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app/schedule \
  -H "Content-Type: application/json" \
  -d '{"text": "I have a meeting at 2pm"}'

# Using Python client
python3 client.py "I have a meeting at 2pm" --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app
```

### **With bypass token:**

```bash
# Test with bypass token
python3 client.py "I have a meeting at 2pm" \
  --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app \
  --bypass-token YOUR_BYPASS_TOKEN
```

## 🔧 **Updated Client Features**

The Python client now supports:

- **Bypass token parameter**: `--bypass-token`
- **Environment variable**: `VERCEL_BYPASS_TOKEN`
- **Automatic token handling** for protected deployments

## 📋 **Quick Commands**

```bash
# Test local API
python3 client.py "Test local API"

# Test deployed API (after disabling protection)
python3 client.py "Test deployed API" --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app

# Test with bypass token
python3 client.py "Test with token" --url https://promptly-m5lk5lrg1-krishs-projects-32b186bc.vercel.app --bypass-token YOUR_TOKEN
```

## 🎯 **Recommendation**

For a **public API**, **disable authentication protection** in Vercel settings. This allows:
- ✅ Easy access for users
- ✅ Simple integration
- ✅ No token management needed
- ✅ Better user experience

For a **private API**, keep protection enabled and use bypass tokens for testing.

## 🚀 **Next Steps**

1. **Choose your preferred option** (disable protection recommended)
2. **Test your API** using the commands above
3. **Update your documentation** with the correct URL
4. **Share your API** with others!

Your TimeAPI is successfully deployed and ready to use! 🎉


