from dotenv import load_dotenv
load_dotenv()

from tradingagents.dataflows.interface import get_data_manager

dm = get_data_manager()

for symbol in ['NVDA', 'LMND', 'TSLA']:
    print(f'\n=== {symbol} 2026-02-24 ===')
    try:
        result = dm.fetch('get_stock_data', symbol, '2026-02-20', '2026-02-24')
        print(result[:500] if result else 'None')
    except Exception as e:
        print(f'Error: {e}')
