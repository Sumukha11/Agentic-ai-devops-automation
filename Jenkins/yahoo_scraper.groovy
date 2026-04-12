pipeline {
    agent any

    stages {
        stage('Fetch Stock Price') {
            steps {
                sh '''
                python <<EOF
import yfinance as yf

stock = yf.Ticker("AAPL")
data = stock.history(period="1d")

if data.empty:
    print("No data found")
    exit(1)

price = data["Close"].iloc[-1]
print("Apple Stock Price:", price)
EOF
                '''
            }
        }
    }
}