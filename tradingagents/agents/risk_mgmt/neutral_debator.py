import time
import json
from tradingagents.dataflows.config import get_config


def create_neutral_debator(llm):
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_conservative_response = risk_debate_state.get("current_conservative_response", "")

        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        trader_decision = state["trader_investment_plan"]

        # 获取语言配置，默认为英文
        config = get_config()
        language = config.get("output_language", "zh")

        if language == "zh":
            prompt = f"""【重要：你的回复必须使用中文，所有内容都应该是中文】

作为中立型风险分析师，你的角色是提供平衡的视角，权衡交易员决策或计划的潜在收益和风险。你优先考虑全面的方法，评估上行和下行空间，同时考虑更广泛的市场趋势、潜在的经济变化和多元化策略。以下是交易员的决策：

{trader_decision}

你的任务是挑战激进型和保守型分析师，指出每种观点可能在哪些方面过于乐观或过于谨慎。利用以下数据源的见解来支持调整交易员决策的温和、可持续策略：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
K线分析报告：{candlestick_report}
这是当前的对话历史：{history} 以下是激进型分析师的上一次回应：{current_aggressive_response} 以下是保守型分析师的上一次回应：{current_conservative_response}。如果其他观点没有回应，不要编造，只需陈述你的观点。

通过批判性地分析双方来积极参与，解决激进型和保守型论点中的弱点，倡导更平衡的方法。挑战他们的每一个观点，以说明为什么适度的风险策略可能提供两全其美，在防范极端波动的同时提供增长潜力。专注于辩论而不是简单地呈现数据，旨在表明平衡的观点可以带来最可靠的结果。以对话方式输出，就像你在说话一样，不要使用任何特殊格式。"""
        else:
            prompt = f"""As the Neutral Risk Analyst, your role is to provide a balanced perspective, weighing both the potential benefits and risks of the trader's decision or plan. You prioritize a well-rounded approach, evaluating the upsides and downsides while factoring in broader market trends, potential economic shifts, and diversification strategies.Here is the trader's decision:

{trader_decision}

Your task is to challenge both the Aggressive and Conservative Analysts, pointing out where each perspective may be overly optimistic or overly cautious. Use insights from the following data sources to support a moderate, sustainable strategy to adjust the trader's decision:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Candlestick Analysis Report: {candlestick_report}
Here is the current conversation history: {history} Here is the last response from the aggressive analyst: {current_aggressive_response} Here is the last response from the conservative analyst: {current_conservative_response}. If there are no responses from the other viewpoints, do not hallucinate and just present your point.

Engage actively by analyzing both sides critically, addressing weaknesses in the aggressive and conservative arguments to advocate for a more balanced approach. Challenge each of their points to illustrate why a moderate risk strategy might offer the best of both worlds, providing growth potential while safeguarding against extreme volatility. Focus on debating rather than simply presenting data, aiming to show that a balanced view can lead to the most reliable outcomes. Output conversationally as if you are speaking without any special formatting."""

        # 调试信息：打印完整prompt（由debug开关控制）
        debug_config = config.get("debug", {})
        if debug_config.get("enabled", False) and debug_config.get("show_prompts", False):
            print("=" * 80)
            print("DEBUG: Neutral Risk Debator Prompt Before LLM Call:")
            print("=" * 80)
            print(f"Language: {language}")
            print(f"Prompt: {prompt[:800]}..." if len(prompt) > 800 else f"Prompt: {prompt}")
            print("=" * 80)
        
        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": risk_debate_state.get("conservative_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": risk_debate_state.get("current_conservative_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
