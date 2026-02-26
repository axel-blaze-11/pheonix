# 💳 UPI Payment UI - Quick Start Guide

A beautiful GPay-like interface for simulating UPI transactions!

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Start all services including Payment UI
docker-compose up -d

# Access Payment UI
open http://localhost:9992
```

### Option 2: Standalone

```bash
# Navigate to payment UI directory
cd payment_ui

# Run startup script
chmod +x run.sh
./run.sh

# OR run directly
python app.py
```

## 👥 Test Users

| Name | VPA | PIN | Balance |
|------|-----|-----|---------|
| Abhishek | abhishek@paytm | 1234 | ₹10,000 |
| Aman | aman@paytm | 1111 | ₹15,000 |
| Harsh | harsh@paytm | 1234 | ₹20,000 |

## 📱 How to Use

1. **Select User** - Choose your account from the list
2. **Pick Contact** - Select who you want to pay
3. **Enter Amount** - Type amount or use quick buttons (min ₹150)
4. **Enter PIN** - Enter your UPI PIN
5. **Pay** - Click "Pay Now" and see the magic! ✨

## 🎯 Features

- ✅ Beautiful, modern UI inspired by Google Pay
- ✅ Real-time transaction processing
- ✅ PIN validation & security
- ✅ Transaction history with local storage
- ✅ Success/error animations
- ✅ Mobile responsive design
- ✅ Quick amount buttons
- ✅ Contact management

## 🔧 Ports

- **Payment UI**: http://localhost:9992
- **Orchestrator UI**: http://localhost:9991 (for AI agents)
- **Payer PSP**: http://localhost:5060
- **NPCI**: http://localhost:5050

## 📸 Screenshots

### Main Screen
![Contact List with beautiful card design]

### Payment Screen
![Clean payment interface with amount input and PIN entry]

### Success Animation
![Smooth success animation after payment]

## ⚠️ Important Notes

- **Minimum Amount**: ₹150 (system constraint)
- **Test Environment**: This is for simulation only
- **Services Required**: Make sure Docker services are running
- **Transaction History**: Stored in browser localStorage

## 🆘 Troubleshooting

**Connection Error?**
```bash
# Make sure services are running
docker-compose up -d

# Check service status
docker-compose ps
```

**Wrong PIN Error?**
- Use the correct PINs listed above!

**Port Already in Use?**
```bash
# Change port
export PAYMENT_UI_PORT=9992
python app.py
```

## 📚 Full Documentation

For detailed documentation, see: `payment_ui/README.md`

## 🎨 Customization

Want to customize? Edit these files:
- `payment_ui/app.py` - Add users/contacts
- `payment_ui/static/style.css` - Change colors/design
- `payment_ui/static/app.js` - Modify behavior

---

**Happy Testing! 🎉**

