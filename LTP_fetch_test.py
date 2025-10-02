from LTP_fetch import get_crypto_ltp

# Get comprehensive ETH data


if __name__ == "__main__":
 eth_data = get_crypto_ltp('ETH')

#  print("ETH Data:", eth_data)

 if eth_data['success']:
    # Bybit data
    bybit_ltp = eth_data['bybit_data']['ltp']
    bybit_timestamp = eth_data['bybit_data']['timestamp']

    # CoinDCX data
    coindcx_ltp = eth_data['coindcx_data']['ltp']
    coindcx_timestamp = eth_data['coindcx_data']['timestamp']
    current_funding = eth_data['coindcx_data']['current_funding_rate']
    estimated_funding = eth_data['coindcx_data']['estimated_funding_rate']
    funding_timestamp = eth_data['coindcx_data']['funding_timestamp']

    print(f"ETH - Bybit: {bybit_ltp} at {bybit_timestamp}")
    print(f"ETH - CoinDCX: {coindcx_ltp} at {coindcx_timestamp}")
    print(f"Current Funding Rate: {current_funding}")
