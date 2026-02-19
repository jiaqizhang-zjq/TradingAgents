import time
import json
import re

from tradingagents.dataflows.research_tracker import get_research_tracker


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

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

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
            
            # 提取最终决策
            decision_match = re.search(r'FINAL\s*DECISION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?', response_content, re.IGNORECASE)
            if decision_match:
                prediction = decision_match.group(1).upper()
                confidence = int(decision_match.group(2)) / 100.0
            else:
                # 尝试从内容推断
                if "BUY" in response_content.upper() and "SELL" not in response_content.upper():
                    prediction = "BUY"
                    confidence = 0.6
                elif "SELL" in response_content.upper():
                    prediction = "SELL"
                    confidence = 0.6
                else:
                    prediction = "HOLD"
                    confidence = 0.5
            
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
