import time
import json
import re

from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        investment_debate_state = state["investment_debate_state"]
        
        # 获取股票和日期信息
        symbol = state.get("company_of_interest", "UNKNOWN")
        trade_date = state.get("trade_date", "")
        
        # 获取语言配置
        config = get_config()
        language = config.get("output_language", "zh")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        if language == "zh":
            prompt = f"""作为投资组合经理和辩论主持人，你的角色是批判性地评估本轮辩论并做出明确的决定：支持看跌分析师、看涨分析师，或者只有在有充分理由的情况下才选择持有。

【重要：你的回复必须使用中文，所有内容都应该是中文】

简洁地总结双方的关键观点，专注于最有力的证据或推理。你的建议——买入、卖出或持有——必须清晰且可操作。避免仅仅因为双方都有合理的观点就默认选择持有；要基于辩论中最有力的论据坚定立场。

此外，为交易员制定详细的投资计划，包括：

你的建议：基于最有说服力的论据的果断立场。
理由：解释为什么这些论据导致你的结论。
战略行动：实施建议的具体步骤。

考虑你在类似情况下的过去错误。利用这些见解来完善你的决策，确保你在学习和改进。自然地呈现你的分析，就像正常对话一样，不要使用特殊格式。

重要：在你的回复末尾，你必须包含一个明确的最终决定，格式如下：
最终决定：[买入/卖出/持有]（置信度：[0-100]%）

以下是你在过去错误上的反思：
"{past_memory_str}"

以下是辩论内容：
辩论历史：
{history}"""
        else:
            prompt = f"""As the portfolio manager and debate facilitator, your role is to critically evaluate this round of debate and make a definitive decision: align with the bear analyst, the bull analyst, or choose Hold only if it is strongly justified based on the arguments presented.

Summarize the key points from both sides concisely, focusing on the most compelling evidence or reasoning. Your recommendation—Buy, Sell, or Hold—must be clear and actionable. Avoid defaulting to Hold simply because both sides have valid points; commit to a stance grounded in the debate's strongest arguments.

Additionally, develop a detailed investment plan for the trader. This should include:

Your Recommendation: A decisive stance supported by the most convincing arguments.
Rationale: An explanation of why these arguments lead to your conclusion.
Strategic Actions: Concrete steps for implementing the recommendation.
Take into account your past mistakes on similar situations. Use these insights to refine your decision-making and ensure you are learning and improving. Present your analysis conversationally, as if speaking naturally, without special formatting. 

IMPORTANT: At the end of your response, you MUST include a clear final decision in the format:
FINAL DECISION: [BUY/SELL/HOLD] (Confidence: [0-100]%)

Here are your past reflections on mistakes:
"{past_memory_str}"

Here is the debate:
Debate History:
{history}"""
        response = llm.invoke(prompt)
        response_content = response.content

        new_investment_debate_state = {
            "judge_decision": response_content,
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": response_content,
            "count": investment_debate_state["count"],
        }
        
        # 解析最终决策并记录到数据库
        try:
            tracker = get_research_tracker()
            
            # 提取最终决策 - 支持中英文格式
            if language == "zh":
                decision_match = re.search(r'最终决定[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?', response_content, re.IGNORECASE)
            else:
                decision_match = re.search(r'FINAL\s*DECISION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?', response_content, re.IGNORECASE)
            
            if decision_match:
                prediction = decision_match.group(1).upper()
                # 转换中文预测为英文
                prediction_map = {"买入": "BUY", "卖出": "SELL", "持有": "HOLD"}
                prediction = prediction_map.get(prediction, prediction)
                confidence = int(decision_match.group(2)) / 100.0
            else:
                # 尝试从内容推断
                content_upper = response_content.upper()
                if language == "zh":
                    if "买入" in response_content or ("BUY" in content_upper and "SELL" not in content_upper):
                        prediction = "BUY"
                    elif "卖出" in response_content or "SELL" in content_upper:
                        prediction = "SELL"
                    else:
                        prediction = "HOLD"
                else:
                    if "BUY" in content_upper and "SELL" not in content_upper:
                        prediction = "BUY"
                    elif "SELL" in content_upper:
                        prediction = "SELL"
                    else:
                        prediction = "HOLD"
                # 基于预测类型和文本内容调整置信度
                if prediction in ["BUY", "SELL"]:
                    # 检查文本中的强弱信号词
                    has_strong_words = any(word in response_content.lower() for word in ['strong', 'confident', 'clear', 'convincing', '明显', '强烈', '确定', '有说服力'])
                    has_weak_words = any(word in response_content.lower() for word in ['uncertain', 'unclear', 'mixed', 'weak', '模糊', '不确定', '混杂', '弱'])
                    
                    if has_strong_words and not has_weak_words:
                        confidence = 0.72
                    elif has_weak_words and not has_strong_words:
                        confidence = 0.58
                    else:
                        confidence = 0.65
                else:
                    confidence = 0.55
            
            # 记录到数据库
            tracker.record_research(
                researcher_name="research_manager",
                researcher_type="manager",
                symbol=symbol,
                trade_date=trade_date,
                prediction=prediction,
                confidence=confidence,
                reasoning=response_content[:500],
                holding_days=5,
                metadata={
                    "role": "research_manager",
                    "full_response": response_content
                }
            )
        except Exception as e:
            print(f"⚠️ 记录Research Manager决策失败: {e}")

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": response_content,
        }

    return research_manager_node
