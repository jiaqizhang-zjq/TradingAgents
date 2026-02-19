from langchain_core.messages import AIMessage
import time
import json
from tradingagents.dataflows.config import get_config


def create_bear_researcher(llm, memory):
    def bear_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bear_history = investment_debate_state.get("bear_history", "")

        current_response = investment_debate_state.get("current_response", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        config = get_config()
        language = config.get("output_language", "en")
        
        if language == "zh":
            prompt = f"""你是一个看跌分析师，提出反对投资这支股票的理由。你的目标是提出一个理由充分的论点，强调风险、挑战和负面指标。利用提供的研究和数据来突出潜在的下行风险，并有效反驳看涨论点。

需要关注的关键点：

- 风险和挑战：强调可能阻碍股票表现的因素，如市场饱和、金融不稳定或宏观经济威胁。
- 竞争劣势：强调市场定位较弱、创新下降或竞争对手威胁等漏洞。
- 负面指标：使用财务数据、市场趋势或近期不利新闻的证据来支持你的立场。
- 反驳看涨论点：用具体数据和合理的推理批判性地分析看涨论点，暴露出弱点或过于乐观的假设。
- 互动性：以对话的方式呈现你的论点，直接与看涨分析师的观点互动，有效地辩论，而不仅仅是列出事实。

可用资源：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新国际新闻：{news_report}
公司基本面报告：{fundamentals_report}
蜡烛图分析报告：{candlestick_report}
辩论对话历史：{history}
上一个看涨论点：{current_response}
类似情况的反思和经验教训：{past_memory_str}
利用这些信息提供一个有说服力的看跌论点，反驳看涨的主张，并参与动态辩论，展示投资这支股票的风险和劣势。你还必须处理反思，并从过去的经验教训和错误中学习。
"""
        else:
            prompt = f"""You are a Bear Analyst making the case against investing in the stock. Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.

Key points to focus on:

- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats that could hinder the stock's performance.
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position.
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Engagement: Present your argument in a conversational style, directly engaging with the bull analyst's points and debating effectively rather than simply listing facts.

Resources available:

Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Candlestick analysis report: {candlestick_report}
Conversation history of the debate: {history}
Last bull argument: {current_response}
Reflections from similar situations and lessons learned: {past_memory_str}
Use this information to deliver a compelling bear argument, refute the bull's claims, and engage in a dynamic debate that demonstrates the risks and weaknesses of investing in the stock. You must also address reflections and learn from lessons and mistakes you made in the past.
"""

        response = llm.invoke(prompt)

        argument = f"Bear Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
