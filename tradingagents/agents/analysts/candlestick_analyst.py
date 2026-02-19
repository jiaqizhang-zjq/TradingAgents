from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from datetime import datetime, timedelta
from tradingagents.agents.utils.agent_utils import get_stock_data
from tradingagents.agents.utils.candlestick_tools import get_candlestick_patterns


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
        
        system_message = """You are a professional candlestick analyst specializing in Eastern candlestick pattern analysis only. Your focus is solely on traditional Japanese candlestick patterns and price action, NOT on Western technical indicators.

ANALYSIS FRAMEWORK:

1. Candlestick Pattern Analysis:
   - Scan for all identified candlestick patterns (provided in candlestick_patterns_data)
   - Assess pattern reliability in the current market context
   - Look for pattern clusters and confluence
   - Analyze the position of patterns in the overall price trend

2. Price Action Analysis:
   - Analyze the relationship between open, high, low, and close prices
   - Identify key price levels based on recent price action
   - Look for rejection levels and acceptance zones
   - Assess the strength of price movements based on candle body size and wicks

3. Trend Context:
   - Determine the overall trend based solely on price action (higher highs/higher lows for uptrend, lower highs/lower lows for downtrend)
   - Identify where the current price is in the trend cycle
   - Look for potential trend reversals or continuations based on candle patterns

OUTPUT REQUIREMENTS:

- Focus EXCLUSIVELY on candlestick patterns and price action
- DO NOT use or reference any Western technical indicators (MA, RSI, MACD, Bollinger Bands, etc.)
- Detail all identified candlestick patterns with their implications
- Explain the significance of patterns in the current price context
- Highlight pattern clusters and confluence zones
- Provide clear trading implications (bullish, bearish, or neutral) based solely on candle patterns
- Include a Markdown table at the end summarizing key candlestick patterns, their implications, and confidence levels

Do NOT simply state that patterns are mixed. Provide detailed, nuanced analysis that explains why certain patterns are significant in the current market context. Focus only on candlestick patterns and price action!"""

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
                    "\n\nCandlestick Patterns (identified patterns like BULLISH_ENGULFING, HAMMER, etc.):\n{candlestick_patterns_data}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)
        prompt = prompt.partial(stock_data=stock_data)
        prompt = prompt.partial(candlestick_patterns_data=candlestick_patterns_data)

        chain = prompt | llm

        result = chain.invoke(state["messages"])
        report = result.content

        return {
            "messages": [result],
            "candlestick_report": report,
        }

    return candlestick_analyst_node
