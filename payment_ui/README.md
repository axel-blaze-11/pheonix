# UPI Payment UI - GPay Style

A beautiful, modern GPay-like interface for simulating UPI transactions in the UPI-AI ecosystem.

## Features

✨ **Modern UI**: Clean, intuitive interface inspired by Google Pay
💳 **Multiple Users**: Switch between different payer accounts
👥 **Contact List**: Easy selection of payees
💰 **Quick Amounts**: Fast payment with preset amounts
🔐 **PIN Security**: UPI PIN validation
📱 **Mobile Responsive**: Works great on all devices
📊 **Transaction History**: Track all your payments
✅ **Real-time Validation**: Instant feedback on transaction status

## Screenshots

### Home Screen
- Select from multiple user accounts
- View account balance

### Pay Screen
- Beautiful contact grid
- Quick amount selection
- Secure PIN entry
- Transaction confirmation

### History Screen
- Complete transaction history
- Success/failure indicators
- Timestamps and details

## Getting Started

### Prerequisites

- Docker and Docker Compose (recommended)
- OR Python 3.11+ with pip

### Running with Docker (Recommended)

1. Start all services including the payment UI:
```bash
docker-compose up -d
```

2. Access the Payment UI:
```
http://localhost:9992
```

### Running Standalone

1. Install dependencies:
```bash
cd payment_ui
pip install -r requirements.txt
```

2. Set environment variables (optional):
```bash
export PAYER_PSP_URL=http://localhost:5060  # Default
export PAYMENT_UI_PORT=9992  # Default
```

3. Run the application:
```bash
python app.py
```

4. Open browser:
```
http://localhost:9992
```

## Usage

### 1. Select User Account

When you first open the app, select a user account:
- **Abhishek** (abhishek@paytm) - PIN: 1234, Balance: ₹10,000
- **Aman** (aman@paytm) - PIN: 1111, Balance: ₹15,000
- **Harsh** (harsh@paytm) - PIN: 1234, Balance: ₹20,000

### 2. Choose Contact

Select a contact from the grid to pay:
- Abhishek (abhishek@phonepe)
- Aman (aman@phonepe)
- Harsh (harsh@phonepe)

### 3. Enter Amount

- Type the amount manually (minimum ₹150)
- OR use quick amount buttons (₹500, ₹1000, ₹2000, ₹5000)

### 4. Enter UPI PIN

Enter your 4-6 digit UPI PIN for the selected user account.

### 5. Complete Payment

Click "Pay Now" to process the transaction. You'll see:
- ✅ Success animation if payment is successful
- ❌ Error message if payment fails

### 6. View History

Navigate to the History tab to see all your transactions.

## API Endpoints

### `GET /api/users`
Get list of available payer users.

**Response:**
```json
{
  "users": [
    {
      "vpa": "abhishek@paytm",
      "name": "Abhishek",
      "balance": 10000.00
    }
  ]
}
```

### `GET /api/contacts`
Get list of payee contacts.

**Response:**
```json
{
  "contacts": [
    {
      "vpa": "abhishek@phonepe",
      "name": "Abhishek",
      "avatar": "👨",
      "bank": "PhonePe"
    }
  ]
}
```

### `POST /api/transaction`
Create a new UPI transaction.

**Request:**
```json
{
  "payer_vpa": "abhishek@paytm",
  "payee_vpa": "abhishek@phonepe",
  "amount": 500.00,
  "pin": "1234"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Transaction successful!",
  "txn_id": "20260128123456",
  "status_code": 202
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "INVALID_PIN",
  "details": "Incorrect UPI PIN",
  "status_code": 400
}
```

## Architecture

```
┌─────────────┐
│  Payment UI │
│  (Port 9992)│
└──────┬──────┘
       │
       ├─ HTTP POST /api/reqpay (XML)
       ↓
┌──────────────┐
│  Payer PSP   │
│  (Port 5060) │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│     NPCI     │
│  (Port 5050) │
└──────┬───────┘
       │
       ├─────────────────┐
       ↓                 ↓
┌──────────────┐  ┌──────────────┐
│  Rem Bank    │  │  Bene Bank   │
│  (Port 5080) │  │  (Port 5090) │
└──────────────┘  └──────────────┘
```

## Transaction Flow

1. **User Input**: User enters amount and PIN in Payment UI
2. **Validation**: Frontend validates amount (≥₹150) and PIN format
3. **XML Generation**: Backend generates UPI ReqPay XML message
4. **Payer PSP**: Validates PIN against database, checks amount
5. **NPCI**: Routes transaction to appropriate banks
6. **Remitter Bank**: Debits amount from payer account
7. **Beneficiary Bank**: Credits amount to payee account
8. **Response**: Success/failure message returned to UI

## Validation Rules

- **Minimum Amount**: ₹150.00 (system constraint)
- **PIN**: Must match user's registered PIN
- **VPA**: Must be valid and registered
- **Balance**: Payer must have sufficient balance

## Error Handling

The UI handles various error scenarios:

- ❌ **INVALID_PIN**: Incorrect UPI PIN entered
- ❌ **INVALID_AMOUNT**: Amount below minimum (₹150)
- ❌ **PAYER_NOT_FOUND**: Invalid payer VPA
- ❌ **Connection Error**: Services not running
- ❌ **Timeout**: Transaction took too long

## Development

### Project Structure

```
payment_ui/
├── app.py              # Flask backend
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── README.md          # This file
└── static/
    ├── index.html     # Main UI
    ├── style.css      # Styles
    └── app.js         # Frontend logic
```

### Customization

**Add New Contacts:**
Edit the `CONTACTS` list in `app.py`:
```python
CONTACTS = [
    {"vpa": "user@bank", "name": "Name", "avatar": "👤", "bank": "Bank"}
]
```

**Add New Users:**
Edit the `PAYER_USERS` list in `app.py`:
```python
PAYER_USERS = [
    {"vpa": "user@psp", "name": "Name", "pin": "1234", "balance": 10000.00}
]
```

**Change Colors:**
Edit CSS variables in `static/style.css`:
```css
:root {
    --primary-color: #1A73E8;
    --success-color: #4CAF50;
    /* ... */
}
```

## Integration with Orchestrator UI

This Payment UI is **separate** from the Orchestrator UI:

- **Orchestrator UI** (Port 9991): For monitoring AI agents and code changes
- **Payment UI** (Port 9992): For simulating actual UPI transactions

Both UIs can run simultaneously and serve different purposes in the UPI-AI ecosystem.

## Troubleshooting

### Services Not Running
```
Error: Connection failed. Make sure services are running
```
**Solution**: Start Docker services:
```bash
docker-compose up -d
```

### Port Already in Use
```
Error: Port 9992 already in use
```
**Solution**: Change the port:
```bash
export PAYMENT_UI_PORT=8001
python app.py
```

### Invalid PIN Error
```
Error: INVALID_PIN - Incorrect UPI PIN
```
**Solution**: Use correct PINs:
- abhishek@paytm: 1234
- aman@paytm: 1111
- harsh@paytm: 1234

### Amount Too Low
```
Error: Minimum transaction amount is INR 150.00
```
**Solution**: Enter amount ≥ ₹150

## Contributing

To add new features:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

Part of the UPI-AI project.

## Support

For issues or questions, please refer to the main project documentation or create an issue in the repository.

---

**Note**: This is a simulation UI for testing purposes. Do not use with real payment credentials.

