import requests
from datetime import datetime

class Trader:
    def __init__(self, symbol, cash, fee_percent=0.1, stop_loss_percent=5.0, max_holding_days=30):
        self.symbol = symbol
        self.cash = cash
        self.fee_percent = fee_percent  # Total platform fee in percentage
        self.holdings = 0  # Number of units (crypto coins)
        self.last_purchase_price = 0
        self.purchase_date = None
        self.stop_loss_percent = stop_loss_percent  # Maximum loss threshold
        self.max_holding_days = max_holding_days  # Max days to hold asset

    def fetch_crypto_data(self, start_date, end_date):
        # Fetch daily price data for the asset from CoinGecko
        url = f"https://api.coingecko.com/api/v3/coins/{self.symbol}/market_chart/range"
        params = {
            'vs_currency': 'usd',
            'from': start_date.timestamp(),
            'to': end_date.timestamp(),
        }

        response = requests.get(url, params=params)
        data = response.json()

        prices = {}
        for price_data in data['prices']:
            # Each entry in 'prices' is [timestamp, price]
            date = datetime.utcfromtimestamp(price_data[0] / 1000)  # Convert timestamp to datetime
            prices[date] = price_data[1]  # Store the price

        return prices

    def buy(self, price, date):
        # Calculate how many units (crypto coins) can be bought with available cash
        units = self.cash / price
        fee = self.cash * self.fee_percent / 100
        self.holdings = units
        self.last_purchase_price = price
        self.purchase_date = date
        self.cash -= (price * units + fee)
        print(f"Bought {units:.6f} units at {price:.2f} per unit on {date.strftime('%Y-%m-%d %H:%M:%S')}. Remaining cash: {self.cash:.2f}")

    def sell(self, price, date):
        # Sell all holdings
        revenue = price * self.holdings
        fee = revenue * self.fee_percent / 100
        self.cash += (revenue - fee)
        print(f"Sold {self.holdings:.6f} units at {price:.2f} per unit on {date.strftime('%Y-%m-%d %H:%M:%S')}. Total cash: {self.cash:.2f}")
        self.holdings = 0
        self.last_purchase_price = 0
        self.purchase_date = None

    def should_sell(self, current_price, current_date):
        # Calculate price decrease from the purchase price (stop-loss trigger)
        price_decrease_percent = ((self.last_purchase_price - current_price) / self.last_purchase_price) * 100

        # Stop-loss check
        if price_decrease_percent >= self.stop_loss_percent:
            print(f"Stop-loss triggered! Price dropped by {price_decrease_percent:.2f}%. Selling on {current_date.strftime('%Y-%m-%d %H:%M:%S')}...")
            return True

        # Holding period check
        if self.purchase_date and (current_date - self.purchase_date).days >= self.max_holding_days:
            print(f"Max holding period reached ({self.max_holding_days} days). Selling on {current_date.strftime('%Y-%m-%d %H:%M:%S')}...")
            return True

        return False

    def trade(self, data):
        for date, price in sorted(data.items()):
            # Check if we should buy
            if self.holdings == 0:
                self.buy(price, date)
            else:
                # Calculate price increase in percentage (net of platform fees)
                price_increase_percent = ((price - self.last_purchase_price) / self.last_purchase_price) * 100
                net_increase = price_increase_percent - self.fee_percent * 2

                # Sell if price has increased by at least 0.5% net or if safety checks are triggered
                if net_increase >= 1:
                    self.sell(price, date)
                elif self.should_sell(price, date):
                    self.sell(price, date)
        self.sell(data[sorted(data.keys())[-1]], sorted(data.keys())[-1])

if __name__ == "__main__":
    # Configuration for Bitcoin or Solana via CoinGecko
    assets = {
        'bitcoin': "bitcoin",  # Bitcoin CoinGecko ID
        'solana': "solana",  # Solana CoinGecko ID,
    }

    # Choose the asset (Bitcoin or Solana)
    asset_choice = input("Enter asset choice (bitcoin, solana): ").lower()
    if asset_choice not in assets:
        raise ValueError("Invalid asset choice. Choose from 'bitcoin' or 'solana'.")

    symbol = assets[asset_choice]
    initial_cash = 3000
    start_date = datetime.strptime("2023-11-01", "%Y-%m-%d")
    end_date = datetime.strptime("2024-10-01", "%Y-%m-%d")

    # Initialize the trader for the chosen cryptocurrency
    trader = Trader(symbol, initial_cash, stop_loss_percent=10.0, max_holding_days=30)

    # Fetch daily data for the given period from CoinGecko
    data = trader.fetch_crypto_data(start_date, end_date)

    # Simulate trading
    trader.trade(data)

    print(f"Final cash: {trader.cash:.2f}")
    print(f"Final holdings: {trader.holdings:.6f} units")
