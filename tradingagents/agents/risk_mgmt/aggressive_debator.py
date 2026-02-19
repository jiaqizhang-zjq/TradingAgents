import time
import json
from tradingagents.dataflows.config import get_config


def create_aggressive_debator(llm):
    def aggressive_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        aggressive_history = risk_debate_state.get("aggressive_history", "")

        current_conservative_response = risk_debate_state.get("current_conservative_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        trader_decision = state["trader_investment_plan"]

        # 获取语言配置，默认为英文
        config = get_config()
        language = config.get("output_language", "en")

        if language == "zh":
            prompt = f"""作为激进型风险分析师，你的角色是积极倡导高风险高回报的投资机会，强调大胆的策略和竞争优势。在评估交易员的决策或计划时，密切关注潜在的上行空间、增长潜力和创新收益——即使这些伴随着较高的风险。利用提供的市场数据和情绪分析来加强你的论点并挑战对立观点。具体来说，直接回应保守型和中立型分析师提出的每一点，用数据驱动的反驳和有说服力的推理进行反击。指出他们的谨慎可能错过哪些关键机会，或者他们的假设可能过于保守的地方。以下是交易员的决策：

{trader_decision}

你的任务是通过质疑和批评保守型和中立型的立场，为交易员的决策创造一个令人信服的案例，以证明你的高回报视角提供了最佳的前进道路。将以下来源的见解纳入你的论点：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
K线分析报告：{candlestick_report}
这是当前的对话历史：{history} 以下是保守型分析师的上一次论点：{current_conservative_response} 以下是中立型分析师的上一次论点：{current_neutral_response}。如果其他观点没有回应，不要编造，只需陈述你的观点。

积极参与，解决提出的任何具体关切，驳斥他们逻辑中的弱点，并主张冒险的好处以超越市场规范。保持专注于辩论和说服，而不仅仅是呈现数据。挑战每一个反驳观点，以强调为什么高风险方法是最优的。以对话方式输出，就像你在说话一样，不要使用任何特殊格式。"""
        else:
            prompt = f"""As the Aggressive Risk Analyst, your role is to actively champion high-reward, high-risk opportunities, emphasizing bold strategies and competitive advantages. When evaluating the trader's decision or plan, focus intently on the potential upside, growth potential, and innovative benefits—even when these come with elevated risk. Use the provided market data and sentiment analysis to strengthen your arguments and challenge the opposing views. Specifically, respond directly to each point made by the conservative and neutral analysts, countering with data-driven rebuttals and persuasive reasoning. Highlight where their caution might miss critical opportunities or where their assumptions may be overly conservative. Here is the trader's decision:

{trader_decision}

Your task is to create a compelling case for the trader's decision by questioning and critiquing the conservative and neutral stances to demonstrate why your high-reward perspective offers the best path forward. Incorporate insights from the following sources into your arguments:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Candlestick Analysis Report: {candlestick_report}
Here is the current conversation history: {history} Here are the last arguments from the conservative analyst: {current_conservative_response} Here are the last arguments from the neutral analyst: {current_neutral_response}. If there are no responses from the other viewpoints, do not hallucinate and just present your point.

Engage actively by addressing any specific concerns raised, refuting the weaknesses in their logic, and asserting the benefits of risk-taking to outpace market norms. Maintain a focus on debating and persuading, not just presenting data. Challenge each counterpoint to underscore why a high-risk approach is optimal. Output conversationally as if you are speaking without any special formatting."""

        response = llm.invoke(prompt)

        argument = f"Aggressive Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": aggressive_history + "\n" + argument,
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Aggressive",
            "current_aggressive_response": argument,
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return aggressive_node
