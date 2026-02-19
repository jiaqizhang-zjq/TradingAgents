from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.agents.utils.candlestick_tools import get_candlestick_patterns
from tradingagents.dataflows.config import get_config


def create_candlestick_analyst(llm):
    def candlestick_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        
        end_date = current_date
        start_date = (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=180)).strftime("%Y-%m-%d")
        
        stock_data = get_stock_data.invoke({"symbol": ticker, "start_date": start_date, "end_date": end_date})
        
        # 获取蜡烛图形态 - 直接传递已获取的stock_data，避免重复获取
        try:
            candlestick_patterns_data = get_candlestick_patterns.invoke({
                "symbol": ticker,
                "start_date": start_date,
                "end_date": end_date,
                "stock_data": stock_data
            })
        except Exception as e:
            candlestick_patterns_data = f"Error getting candlestick patterns: {str(e)}"
        
        indicator_groups_to_get = [
            "volume", "support", "trend", "momentum", "cross", "boll", "macd", "adx"
        ]
        
        indicators_data = ""
        for group in indicator_groups_to_get:
            try:
                data = get_indicators.invoke({
                    "symbol": ticker, 
                    "indicator": group, 
                    "curr_date": current_date, 
                    "look_back_days": 120
                })
                indicators_data += f"\n=== {group.upper()} INDICATOR GROUP ===\n{data}\n"
            except Exception as e:
                indicators_data += f"\n=== {group.upper()} INDICATOR GROUP ===\nError: {str(e)}\n"
        
        system_message = """You are a professional technical analyst specializing in candlestick patterns, price action analysis, and technical chart patterns. Based on the provided stock price data and technical indicators, conduct comprehensive technical analysis including candlestick patterns, support/resistance levels, trendlines, chart patterns, and technical indicators.

AVAILABLE INDICATOR GROUPS (Comprehensive Data Provided):
- VOLUME: Volume moving averages (5/10/20/50), volume ratios (5/20), volume change %, volume acceleration, VWMA, OBV
- SUPPORT: Support levels (20/50), resistance levels (20/50), mid-range, position in range
- TREND: Trend slopes (10/20), linear regression prediction, price relative to SMA (20/50)
- MOMENTUM: ROC (5/10/20), CCI (20), CMO (14), MFI (14)
- CROSS: SMA crossovers (5/20, 20/50), MACD crossovers, RSI overbought/oversold, Bollinger breakouts
- BOLL: Bollinger Bands (middle, upper, lower, width)
- MACD: MACD line, signal line, histogram
- ADX: ADX, +DI, -DI

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

4. Candlestick Pattern Analysis:
   - Scan for candlestick patterns (provided in candlestick_patterns_data)
   - Assess pattern reliability in context
   - Look for pattern clusters

5. Volume Confirmation:
   - Use VOLUME group for comprehensive volume analysis
   - Check volume_ratio for relative volume comparison
   - Look for volume spikes with volume_change_pct
   - Confirm breakouts with volume and VWMA/OBV

6. Indicator Confluence:
   - Use CROSS group for pre-calculated crossover signals
   - Use MOMENTUM group for momentum confirmation
   - Look for divergences between price and indicators
   - Assess overall momentum and trend strength with ADX
   - Use Bollinger Bands for volatility and breakout confirmation

OUTPUT REQUIREMENTS:

- Provide comprehensive analysis covering all the above areas
- Include timeframe context (what period are you analyzing?)
- Detail all identified chart patterns and candlestick patterns
- Explain support/resistance levels and trendlines (use pre-calculated SUPPORT indicators)
- Highlight confluence across multiple indicators/patterns
- Use the pre-calculated CROSS signals to identify entry/exit points
- Provide clear trading implications (bullish, bearish, or neutral)
- Include specific price targets based on patterns
- Include risk assessment with stop-loss suggestions (use ATR from VOLUME group)
- Make sure to append two Markdown tables at the end:
  1. One summarizing key chart patterns, their implications, and confidence levels
  2. One summarizing key candlestick patterns, their implications, and confidence levels

Do NOT simply state that patterns are mixed. Provide detailed, nuanced analysis that explains why certain patterns are significant in the current market context. Focus on actionable insights that traders can use. ALL BASIC INDICATORS ARE ALREADY CALCULATED - focus on ANALYSIS, not calculation!"""

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
                    "\n\nCandlestick Patterns (identified patterns like BULLISH_ENGULFING, HAMMER, etc.):\n{candlestick_patterns_data}"
                    "\n\nTechnical Indicators:\n{indicators_data}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(stock_data=stock_data)
        prompt = prompt.partial(candlestick_patterns_data=candlestick_patterns_data)
        prompt = prompt.partial(indicators_data=indicators_data)

        chain = prompt | llm

        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "candlestick_report": report,
        }

    return candlestick_analyst_node
