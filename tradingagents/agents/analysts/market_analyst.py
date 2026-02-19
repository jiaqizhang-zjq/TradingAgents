from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.dataflows.indicator_groups import INDICATOR_GROUPS


def create_market_analyst(llm):
    def market_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        end_date = current_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        
        stock_data = get_stock_data.invoke({"symbol": ticker, "start_date": start_date, "end_date": end_date})
        
        indicators_data = ""
        
        for group_name in INDICATOR_GROUPS.keys():
            try:
                data = get_indicators.invoke({
                    "symbol": ticker, 
                    "indicator": group_name, 
                    "curr_date": current_date, 
                    "look_back_days": 120
                })
                indicators_data += f"\n=== {group_name.upper()} INDICATOR GROUP ===\n{data}\n"
            except Exception as e:
                indicators_data += f"\n=== {group_name.upper()} INDICATOR GROUP ===\nError: {str(e)}\n"
        
        system_message = """You are a professional technical analyst specializing in market trend analysis. Based on the provided stock price data and technical indicator groups, conduct comprehensive technical analysis.

AVAILABLE INDICATOR GROUPS (Comprehensive Data Provided):
- VOLUME: Volume moving averages, volume ratios, volume change %, volume acceleration, VWMA, OBV
- SUPPORT: Support levels (20/50), resistance levels (20/50), mid-range, position in range
- TREND: Trend slopes (10/20), linear regression prediction, price relative to SMA (20/50)
- MOMENTUM: ROC (5/10/20), CCI (20), CMO (14), MFI (14)
- CROSS: SMA crossovers (5/20, 20/50), MACD crossovers, RSI overbought/oversold, Bollinger breakouts
- BOLL: Bollinger Bands (middle, upper, lower, width)
- MACD: MACD line, signal line, histogram
- ADX: ADX, +DI, -DI
- VOLATILITY: Volatility (20/50), ATR%, Bollinger width
- DIVERGENCE: Price/RSI new highs/lows

ANALYSIS FRAMEWORK:

1. Trend Analysis:
   - Determine primary, secondary, and short-term trends using TREND indicators
   - Use trend_slope and moving averages to confirm trend direction
   - Identify key moving average levels and price relative positions

2. Support/Resistance Identification:
   - Use SUPPORT group for pre-calculated support/resistance levels (20/50)
   - Mark swing highs and lows
   - Note position_in_range to understand where price is in the recent range
   - Look for confluence zones with moving averages

3. Chart Pattern Recognition:
   - Identify any chart patterns forming
   - Measure pattern targets
   - Assess pattern validity and completion

4. Volume Confirmation:
   - Use VOLUME group for comprehensive volume analysis
   - Check volume_ratio for relative volume comparison
   - Look for volume spikes with volume_change_pct
   - Confirm breakouts with volume and VWMA/OBV

5. Indicator Confluence:
   - Use CROSS group for pre-calculated crossover signals
   - Use MOMENTUM group for momentum confirmation
   - Look for divergences between price and indicators using DIVERGENCE group
   - Assess overall momentum and trend strength with ADX
   - Use Bollinger Bands for volatility and breakout confirmation
   - Use VOLATILITY group to assess current market volatility

OUTPUT REQUIREMENTS:

- Provide comprehensive analysis covering all the above areas
- Include timeframe context (what period are you analyzing?)
- Detail all identified chart patterns
- Explain support/resistance levels and trendlines (use pre-calculated SUPPORT indicators)
- Highlight confluence across multiple indicators/patterns
- Use the pre-calculated CROSS signals to identify entry/exit points
- Provide clear trading implications (bullish, bearish, or neutral)
- Include specific price targets based on patterns
- Include risk assessment with stop-loss suggestions (use ATR from VOLATILITY group)
- Make sure to append a Markdown table at the end summarizing key findings, their implications, and confidence levels

Do NOT simply state that patterns are mixed. Provide detailed, nuanced analysis that explains why certain patterns are significant in the current market context. Focus on actionable insights that traders can use. ALL INDICATORS ARE ALREADY CALCULATED - focus on ANALYSIS, not calculation!"""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    "{system_message}"
                    "\nFor your reference, the current date is {current_date}. The company we want to analyze is {ticker}."
                    "\n\nStock Data:\n{stock_data}"
                    "\n\nTechnical Indicators:\n{indicators_data}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(stock_data=stock_data)
        prompt = prompt.partial(indicators_data=indicators_data)

        chain = prompt | llm

        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "market_report": report,
        }

    return market_analyst_node
