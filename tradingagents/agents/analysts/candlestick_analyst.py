from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from tradingagents.agents.utils.agent_utils import get_stock_data, get_indicators
from tradingagents.dataflows.config import get_config


def create_candlestick_analyst(llm):
    def candlestick_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        company_name = state["company_of_interest"]

        tools = [
            get_stock_data,
            get_indicators,
        ]

        config = get_config()
        language = config.get("output_language", "en")

        if language == "zh":
            system_message = (
                "你是一位专业的蜡烛图技术分析师。基于提供的股票价格数据和蜡烛图形态，请撰写一份详细的蜡烛图分析报告。"
                "你的分析应包括：1.蜡烛图形态识别（单根、两根、三根蜡烛形态）2.支撑阻力位识别 3.趋势确认 4.交易量配合 5.图表形态识别。"
                "不要简单地说明趋势混合，要提供详细且精细的分析和见解，帮助交易员做出决策。"
                "确保在报告末尾添加Markdown表格，整理报告中的关键蜡烛图形态和图表形态。"
            )
        else:
            system_message = """You are a professional technical analyst specializing in candlestick patterns, price action analysis, and technical chart patterns. Your role is to conduct comprehensive technical analysis including candlestick patterns, support/resistance levels, trendlines, chart patterns, and technical indicators.

ANALYSIS GUIDELINES:

1. First, use get_stock_data to retrieve the OHLCV (Open, High, Low, Close, Volume) data. This will give you the raw candlestick data.

2. Then, use get_indicators to calculate key technical indicators, including:
   - Moving Averages (close_50_sma, close_200_sma, close_10_ema, close_20_ema, close_200_ema)
   - RSI (rsi) for momentum confirmation
   - MACD (macd, macds, macdh) for trend confirmation
   - Bollinger Bands (boll, boll_ub, boll_lb) for volatility context
   - ATR (atr) for volatility measurement
   - Stochastic Oscillator for momentum
   - CCI (Commodity Channel Index)
   - Volume indicators

COMPREHENSIVE CANDLESTICK PATTERNS:

Single Candle Patterns:
- Doji (all variations: Long-Legged, Dragonfly, Gravestone)
- Hammer
- Hanging Man
- Inverted Hammer
- Shooting Star
- Spinning Top
- Marubozu (White/Black)
- Long Upper/Lower Shadow

Two Candle Patterns:
- Bullish Engulfing
- Bearish Engulfing
- Piercing Pattern
- Dark Cloud Cover
- Tweezer Tops
- Tweezer Bottoms
- Bullish Harami
- Bearish Harami
- Kicker Pattern

Three+ Candle Patterns:
- Morning Star
- Evening Star
- Morning Doji Star
- Evening Doji Star
- Three White Soldiers
- Three Black Crows
- Three Inside Up/Down
- Rising Three Methods
- Falling Three Methods
- Abandoned Baby
- Three Line Strike

CHART PATTERNS TO IDENTIFY:

Reversal Patterns:
- Head and Shoulders (Top)
- Inverse Head and Shoulders (Bottom)
- Double Top (M Pattern)
- Double Bottom (W Pattern)
- Triple Top
- Triple Bottom
- Rounding Top
- Rounding Bottom
- Wedge (Rising/Falling)

Continuation Patterns:
- Symmetrical Triangle
- Ascending Triangle
- Descending Triangle
- Flag Pattern
- Pennant Pattern
- Rectangle Pattern
- Cup and Handle
- Channel Pattern (Up/Down/Sideways)

TREND AND SUPPORT/RESISTANCE ANALYSIS:

Trend Analysis:
- Uptrend (higher highs and higher lows)
- Downtrend (lower highs and lower lows)
- Sideways/Consolidation
- Trendline drawing and validation
- Channel identification
- Golden Cross/Death Cross (50 SMA crossing 200 SMA)

Support and Resistance:
- Horizontal support/resistance levels
- Dynamic support/resistance (moving averages)
- Swing highs and swing lows
- Fibonacci retracement levels (38.2%, 50%, 61.8%)
- Psychological levels (round numbers)
- Breakout and breakdown confirmation

VOLUME ANALYSIS:
- Volume spikes
- Volume confirmation of price moves
- Accumulation vs Distribution
- Volume divergence
- On-Balance Volume (OBV) implications

MOMENTUM INDICATORS:
- RSI overbought/oversold conditions (70/30)
- RSI divergence (bullish/bearish)
- MACD crossovers and divergences
- Stochastic crossovers
- CCI extreme readings

ANALYSIS FRAMEWORK:

1. Trend Analysis:
   - Determine primary, secondary, and short-term trends
   - Draw trendlines and channels
   - Identify key moving average levels

2. Support/Resistance Identification:
   - Mark swing highs and lows
   - Identify horizontal levels
   - Note Fibonacci levels
   - Look for confluence zones

3. Chart Pattern Recognition:
   - Identify any chart patterns forming
   - Measure pattern targets
   - Assess pattern validity and completion

4. Candlestick Pattern Analysis:
   - Scan for candlestick patterns
   - Assess pattern reliability in context
   - Look for pattern clusters

5. Volume Confirmation:
   - Check volume accompanying price action
   - Look for volume spikes
   - Confirm breakouts with volume

6. Indicator Confluence:
   - Cross-verify with multiple indicators
   - Look for divergences
   - Assess overall momentum and trend strength

OUTPUT REQUIREMENTS:

- Provide comprehensive analysis covering all the above areas
- Include timeframe context (what period are you analyzing?)
- Detail all identified chart patterns and candlestick patterns
- Explain support/resistance levels and trendlines
- Highlight confluence across multiple indicators/patterns
- Provide clear trading implications (bullish, bearish, or neutral)
- Include specific price targets based on patterns
- Include risk assessment with stop-loss suggestions
- Make sure to append two Markdown tables at the end:
  1. One summarizing key chart patterns, their implications, and confidence levels
  2. One summarizing key candlestick patterns, their implications, and confidence levels

Do NOT simply state that patterns are mixed. Provide detailed, nuanced analysis that explains why certain patterns are significant in the current market context. Focus on actionable insights that traders can use."""

        if language == "zh":
            assistant_prompt = (
                "你是一个有用的AI助手，与其他助手合作。使用提供的工具来推进问题的回答。"
                "如果你无法完全回答，没关系；另一个拥有不同工具的助手会在你离开的地方继续。"
                "执行你能做的来取得进展。如果你或任何其他助手有最终交易建议：**买入/持有/卖出**或可交付成果，"
                "请在你的回复前加上'最终交易建议：**买入/持有/卖出**'，这样团队就知道要停止了。"
                "你可以使用以下工具：{tool_names}。\n{system_message}"
                "参考信息：当前日期是{current_date}。我们要分析的公司是{ticker}"
            )
        else:
            assistant_prompt = (
                "You are a helpful AI assistant, collaborating with other assistants."
                " Use the provided tools to progress towards answering the question."
                " If you are unable to fully answer, that's OK; another assistant with different tools"
                " will help where you left off. Execute what you can to make progress."
                " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                " You have access to the following tools: {tool_names}.\n{system_message}"
                "For your reference, the current date is {current_date}. The company we want to analyze is {ticker}"
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    assistant_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = result.content

        return {
            "messages": [result],
            "candlestick_report": report,
        }

    return candlestick_analyst_node
