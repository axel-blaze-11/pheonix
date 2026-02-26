# UPI-AI Project Overview

A comprehensive UPI (Unified Payments Interface) simulation system with AI-powered change management and a modern payment UI.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        UPI AI ECOSYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Payment UI     │              │  Orchestrator UI │        │
│  │   (Port 9992)    │              │   (Port 9991)    │        │
│  │  GPay-like UI    │              │  Agent Monitor   │        │
│  └────────┬─────────┘              └──────────────────┘        │
│           │                                                      │
│           │ Transaction Requests                                │
│           ↓                                                      │
│  ┌──────────────────┐                                          │
│  │   Payer PSP      │                                          │
│  │   (Port 5060)    │                                          │
│  │  PIN Validation  │                                          │
│  └────────┬─────────┘                                          │
│           │                                                      │
│           │ Forward ReqPay                                      │
│           ↓                                                      │
│  ┌──────────────────┐                                          │
│  │   NPCI Switch    │◄─────── AI Agent (Code Updates)          │
│  │   (Port 5050)    │                                          │
│  │  Transaction     │                                          │
│  │    Router        │                                          │
│  └────────┬─────────┘                                          │
│           │                                                      │
│           ├──────────────────┬──────────────────┐              │
│           ↓                  ↓                  ↓              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐      │
│  │  Remitter    │   │ Beneficiary  │   │   Payee PSP  │      │
│  │    Bank      │   │    Bank      │   │ (Port 5070)  │      │
│  │ (Port 5080)  │   │ (Port 5090)  │   │              │      │
│  │  Debit CBS   │   │  Credit CBS  │   │ Merchant     │      │
│  └──────────────┘   └──────────────┘   └──────────────┘      │
│         ▲                    ▲                                  │
│         │                    │                                  │
│         └────── AI Agents ───┘                                 │
│           (Automated Code Updates)                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Two Main Components

### 1. 💳 Payment UI (Port 9992)
**Purpose**: Simulate real UPI transactions with a beautiful, modern interface

**Features**:
- GPay-inspired design
- Multiple user accounts
- Contact management
- Real-time transactions
- PIN validation
- Transaction history
- Success/failure animations

**Use Case**: Test actual payment flows through the UPI ecosystem

**Quick Start**:
```bash
./start_payment_ui.sh
# Open http://localhost:9992
```

### 2. 🤖 Orchestrator UI (Port 9991)
**Purpose**: Monitor AI agents that automatically update code based on specification changes

**Features**:
- AI agent status tracking
- Change manifest management
- Code update monitoring
- Real-time agent logs
- Deployment coordination

**Use Case**: Test agentic capabilities to propagate spec changes across services

**Quick Start**:
```bash
docker-compose up -d
# Open http://localhost:9991
```

## 📊 Services Overview

| Service | Port | Purpose | Database |
|---------|------|---------|----------|
| Payment UI | 9992 | Transaction simulation UI | N/A |
| Orchestrator | 9991 | AI agent coordination | JSON file |
| Payer PSP | 5060 | Payer payment service | SQLite |
| Payee PSP | 5070 | Payee payment service | SQLite |
| NPCI | 5050 | Transaction switch/router | N/A |
| Remitter Bank | 5080 | Debit processing | SQLite |
| Beneficiary Bank | 5090 | Credit processing | SQLite |

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose (recommended)
- OR Python 3.11+
- Basic understanding of UPI payment flow

### Quick Setup

1. **Clone and Navigate**
```bash
cd /path/to/upi-ai-main
```

2. **Setup Environment** (optional)
```bash
cp .env.example .env
# Edit .env if needed
```

3. **Start All Services**
```bash
docker-compose up -d
```

4. **Access UIs**
- Payment UI: http://localhost:9992
- Orchestrator UI: http://localhost:9991

## 💡 Use Cases

### Use Case 1: Simulate UPI Payment
```
1. Open Payment UI (http://localhost:9992)
2. Select user: Abhishek (abhishek@paytm)
3. Choose contact: Aman (aman@phonepe)
4. Enter amount: ₹500
5. Enter PIN: 1234
6. Click "Pay Now"
7. See success animation! ✨
```

**Transaction Flow**:
```
Payment UI → Payer PSP → NPCI → Rem Bank (Debit) → Bene Bank (Credit) → Success
```

### Use Case 2: Test AI Agent Code Updates
```
1. Open Orchestrator UI (http://localhost:9991)
2. Enter specification change (e.g., "Add min amount ₹200")
3. AI agents automatically:
   - Parse the change
   - Generate code updates
   - Apply changes to services
   - Run tests
   - Mark as READY
4. View real-time status of all agents
```

**Agent Flow**:
```
NPCI Agent (Create Manifest) → Dispatch → Rem Bank Agent → Bene Bank Agent → READY
```

## 🧪 Testing

### Test Payment Flow
```bash
# Using the interactive script
python scripts/interactive_test.py

# Or use Payment UI (recommended)
./start_payment_ui.sh
```

### Test AI Agents
```bash
# Run demo
python demo.py

# Or use Orchestrator UI
docker-compose up -d
# Open http://localhost:9991
```

## 📚 Documentation

- **Payment UI**: `payment_ui/README.md` or `PAYMENT_UI_README.md`
- **AI Agents**: `PHASE2_README.md`
- **API Schemas**: `common/schemas/`
- **Project Root**: This file

## 🎨 Key Features

### Payment UI Features
✅ Modern, responsive design  
✅ Real transaction processing  
✅ Multiple user support  
✅ PIN security  
✅ Transaction history  
✅ Error handling  
✅ Success animations  

### AI Agent Features
✅ Automated code updates  
✅ LLM-powered interpretation  
✅ Multi-agent coordination  
✅ Status tracking  
✅ Change manifests  
✅ Real-time monitoring  

## 🔧 Development

### Project Structure
```
upi-ai-main/
├── payment_ui/              # GPay-like transaction UI
│   ├── app.py              # Flask backend
│   ├── static/             # HTML/CSS/JS
│   ├── Dockerfile
│   └── requirements.txt
├── orchestrator/           # AI agent coordination
│   ├── static/             # Dashboard UI
│   └── ...
├── npci/                   # NPCI switch
├── payer_psp/             # Payer PSP service
├── payee_psp/             # Payee PSP service
├── rem_bank/              # Remitter bank
├── bene_bank/             # Beneficiary bank
├── agents/                # AI agent implementations
├── common/                # Shared code (schemas, DB)
├── scripts/               # Test scripts
├── docker-compose.yml     # Docker orchestration
└── orchestrator.py        # Main orchestrator
```

### Adding New Features

**To Payment UI**:
1. Add users/contacts in `payment_ui/app.py`
2. Customize UI in `payment_ui/static/`
3. Add API endpoints as needed

**To AI Agents**:
1. Create new agent in `agents/`
2. Add manifest types in `manifest.py`
3. Update orchestrator routing

## 🐛 Troubleshooting

### Services Won't Start
```bash
# Check Docker
docker ps

# View logs
docker-compose logs

# Restart
docker-compose down
docker-compose up -d
```

### Payment Fails
- Check services are running: `docker-compose ps`
- Verify correct PIN (see PAYMENT_UI_README.md)
- Ensure amount ≥ ₹150

### Port Conflicts
```bash
# Change ports in .env
echo "PAYMENT_UI_PORT=8001" >> .env
docker-compose down
docker-compose up -d
```

## 📈 Performance

- **Payment Processing**: <1s end-to-end
- **AI Agent Updates**: 10-30s depending on LLM
- **UI Responsiveness**: <100ms interactions
- **Concurrent Transactions**: Supports multiple simultaneous

## 🔐 Security Notes

⚠️ **This is a simulation environment**:
- Do not use real payment credentials
- PINs are stored in plaintext (demo only)
- No encryption (demo only)
- Not production-ready

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📝 License

[Add license information]

## 🙏 Acknowledgments

- UPI protocol specifications
- Google Pay UI inspiration
- Flask, Docker, and Python communities

---

**Ready to test?**

```bash
# Start everything
./start_payment_ui.sh

# Open your browser
open http://localhost:9992

# Have fun! 🎉
```

