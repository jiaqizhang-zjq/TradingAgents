from langchain_core.messages import AIMessage
import time
import json
import re
from tradingagents.dataflows.config import get_config


def create_conservative_debator(llm):
    def conservative_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        conservative_history = risk_debate_state.get("conservative_history", "")

        current_aggressive_response = risk_debate_state.get("current_aggressive_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

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

作为保守型风险分析师，你的首要目标是保护资产、最小化波动性并确保稳定、可靠的增长。你优先考虑稳定性、安全性和风险缓解，仔细评估潜在损失、经济衰退和市场波动。在评估交易员的决策或计划时，批判性地检查高风险因素，指出决策可能在哪些地方使公司面临不当风险，以及在哪些地方更谨慎的替代方案可以确保长期收益。以下是交易员的决策：

{trader_decision}

你的任务是积极反驳激进型和中立型分析师的论点，强调他们的观点可能在哪些方面忽视潜在威胁或未能优先考虑可持续性。直接回应他们的观点，从以下数据源中汲取信息，为交易员决策的低风险方法调整建立一个令人信服的案例：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务报告：{news_report}
公司基本面报告：{fundamentals_report}
K线分析报告：{candlestick_report}
这是当前的对话历史：{history} 以下是激进型分析师的上一次回应：{current_aggressive_response} 以下是中立型分析师的上一次回应：{current_neutral_response}。如果其他观点没有回应，不要编造，只需陈述你的观点。

通过质疑他们的乐观情绪并强调他们可能忽视的潜在缺点来参与讨论。回应他们的每一个反驳观点，以展示为什么保守立场最终是公司资产的最安全路径。专注于辩论和批评他们的论点，以证明低风险策略相对于他们方法的优势。以对话方式输出，就像你在说话一样，不要使用任何特殊格式。"""
        else:
            prompt = f"""As the Conservative Risk Analyst, your primary objective is to protect assets, minimize volatility, and ensure steady, reliable growth. You prioritize stability, security, and risk mitigation, carefully assessing potential losses, economic downturns, and market volatility. When evaluating the trader's decision or plan, critically examine high-risk elements, pointing out where the decision may expose the firm to undue risk and where more cautious alternatives could secure long-term gains. Here is the trader's decision:

{trader_decision}

Your task is to actively counter the arguments of the Aggressive and Neutral Analysts, highlighting where their views may overlook potential threats or fail to prioritize sustainability. Respond directly to their points, drawing from the following data sources to build a convincing case for a low-risk approach adjustment to the trader's decision:

Market Research Report: {market_research_report}
Social Media Sentiment Report: {sentiment_report}
Latest World Affairs Report: {news_report}
Company Fundamentals Report: {fundamentals_report}
Candlestick Analysis Report: {candlestick_report}
Here is the current conversation history: {history} Here is the last response from the aggressive analyst: {current_aggressive_response} Here is the last response from the neutral analyst: {current_neutral_response}. If there are no responses from the other viewpoints, do not hallucinate and just present your point.

Engage by questioning their optimism and emphasizing the potential downsides they may have overlooked. Address each of their counterpoints to showcase why a conservative stance is ultimately the safest path for the firm's assets. Focus on debating and critiquing their arguments to demonstrate the strength of a low-risk strategy over their approaches. Output conversationally as if you are speaking without any special formatting."""

        # 调试信息：打印完整prompt（由debug开关控制）
        debug_config = config.get("debug", {})
        if debug_config.get("enabled", False) and debug_config.get("show_prompts", False):
            print("=" * 80)
            print("DEBUG: Conservative Risk Debator Prompt Before LLM Call:")
            print("=" * 80)
            print(f"Language: {language}")
            print(f"Prompt: {prompt[:800]}..." if len(prompt) > 800 else f"Prompt: {prompt}")
            print("=" * 80)
        
        response = llm.invoke(prompt)
        response_content = response.content

        # 提取预测结果
        prediction = "HOLD"
        confidence = 0.7
        if language == "zh":
            pred_match = re.search(r'预测[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?', response_content, re.IGNORECASE)
        else:
            pred_match = re.search(r'PREDICTION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?', response_content, re.IGNORECASE)
        
        if pred_match:
            prediction = pred_match.group(1).upper()
            pred_map = {"买入": "BUY", "卖出": "SELL", "持有": "HOLD"}
            prediction = pred_map.get(prediction, prediction)
            confidence = int(pred_match.group(2)) / 100.0

        argument = f"Conservative Analyst: {response_content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "aggressive_history": risk_debate_state.get("aggressive_history", ""),
            "conservative_history": conservative_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Conservative",
            "current_aggressive_response": risk_debate_state.get(
                "current_aggressive_response", ""
            ),
            "current_conservative_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
            "conservative_prediction": prediction,
            "conservative_confidence": confidence,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return conservative_node
