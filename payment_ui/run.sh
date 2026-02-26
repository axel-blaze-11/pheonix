#!/bin/bash

# Payment UI Startup Script

echo "🚀 Starting UPI Payment UI..."
echo ""

# Check if running in Docker
if [ -f "/.dockerenv" ]; then
    echo "Running in Docker container"
    python app.py
else
    echo "Running locally"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Set default environment variables if not set
    export PAYER_PSP_URL=${PAYER_PSP_URL:-http://localhost:5004}
    export PAYMENT_UI_PORT=${PAYMENT_UI_PORT:-9992}
    export FLASK_DEBUG=${FLASK_DEBUG:-false}
    
    echo ""
    echo "✅ Payment UI starting on http://localhost:${PAYMENT_UI_PORT}"
    echo ""
    echo "💡 To enable debug mode (requires proper permissions):"
    echo "   export FLASK_DEBUG=true"
    echo ""
    echo "📝 Available Users:"
    echo "   - Abhishek (abhishek@paytm) - PIN: 1234"
    echo "   - Aman (aman@paytm) - PIN: 1111"
    echo "   - Harsh (harsh@paytm) - PIN: 1234"
    echo ""
    echo "💡 Make sure other services are running:"
    echo "   docker-compose up -d"
    echo ""
    
    # Run the app
    python3 app.py
fi

