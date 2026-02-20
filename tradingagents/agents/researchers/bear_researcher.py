from langchain_core.messages import AIMessage
import time
import json
import re

from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config


# 中英双语系统提示词
SYSTEM_PROMPTS = {
    "en": """You are a Bear Analyst making the case against investing in the stock. Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.

Key points to focus on:

- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats that could hinder the stock's performance.
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position.
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Engagement: Present your argument in a conversational style, directly engaging with the bull analyst's points and debating effectively rather than simply listing facts.

IMPORTANT: At the end of your response, you MUST include a clear prediction in the format:
PREDICTION: [BUY/SELL/HOLD] (Confidence: [0-100]%)
""",

    "zh": """你是一位看跌分析师，提出反对投资该股票的论点。你的目标是提出一个论据充分的论点，强调风险、挑战和负面指标。利用提供的研究和数据来突出潜在的缺点并有效反驳看涨论点。

重点关注的关键点：

- 风险和挑战：突出可能阻碍股票表现的因素，如市场饱和、财务不稳定或宏观经济威胁。
- 竞争弱点：强调脆弱性，如较弱的市场定位、创新能力下降或来自竞争对手的威胁。
- 负面指标：使用财务数据、市场趋势或近期负面消息的证据来支持你的立场。
- 反驳看涨观点：用具体数据和合理推理批判性分析看涨论点，暴露弱点或过于乐观的假设。
- 参与度：以对话式风格提出你的论点，直接与看涨分析师的观点互动并进行有效辩论，而不是简单地列出事实。

重要：在你的回复末尾，你必须包含一个明确的预测，格式如下：
预测：[买入/卖出/持有]（置信度：[0-100]%）
"""
}


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

        # 根据语言选择系统提示词
        system_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["zh"])
        
        if language == "zh":
            prompt = f"""{system_prompt}

可用资源：

市场研究报告：{market_research_report}
社交媒体情绪报告：{sentiment_report}
最新世界事务新闻：{news_report}
公司基本面报告：{fundamentals_report}
蜡烛图分析报告：{candlestick_report}
辩论对话历史：{history}
上次看涨论点：{current_response}
类似情况下的反思和经验教训：{past_memory_str}
利用这些信息提出一个令人信服的看跌论点，反驳看涨的主张，并参与一场动态辩论，展示投资该股票的风险和弱点。你还必须解决反思问题，并从过去的经验教训中学习。"""
        else:
            prompt = f"""{system_prompt}

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
        response_content = response.content

        # 根据语言设置分析师名称
        analyst_name = "看跌分析师" if language == "zh" else "Bear Analyst"
        argument = f"{analyst_name}: {response_content}"
        
        # 解析预测结果并记录到数据库
        try:
            tracker = get_research_tracker()
            
            # 提取预测结果 - 支持中英文格式
            if language == "zh":
                prediction_match = re.search(r'预测[:：]\s*(买入|卖出|持有|BUY|SELL|HOLD).*?置信度[:：]\s*(\d+)%?', response_content, re.IGNORECASE)
            else:
                prediction_match = re.search(r'PREDICTION:\s*(BUY|SELL|HOLD).*?Confidence:\s*(\d+)%?', response_content, re.IGNORECASE)
            if prediction_match:
                prediction = prediction_match.group(1).upper()
                # 转换中文预测为英文
                prediction_map = {"买入": "BUY", "卖出": "SELL", "持有": "HOLD"}
                prediction = prediction_map.get(prediction, prediction)
                confidence = int(prediction_match.group(2)) / 100.0
            else:
                # 默认预测 - 当LLM没有按格式输出时使用
                # 尝试从内容中推断置信度
                prediction = "SELL"
                # 基于文本长度和关键词密度估算置信度
                text_length = len(response_content)
                has_strong_words = any(word in response_content.lower() for word in ['strong', 'confident', 'clear', '明显', '强烈', '确定'])
                has_weak_words = any(word in response_content.lower() for word in ['uncertain', 'unclear', 'mixed', '模糊', '不确定', '混杂'])
                
                if has_strong_words and not has_weak_words:
                    confidence = 0.75
                elif has_weak_words and not has_strong_words:
                    confidence = 0.55
                else:
                    confidence = 0.65
            
            # 记录到数据库
            tracker.record_research(
                researcher_name=f"bear_{state.get('debate_round', 0)}",
                researcher_type="bear",
                symbol=symbol,
                trade_date=trade_date,
                prediction=prediction,
                confidence=confidence,
                reasoning=response_content,  # 完整推理内容
                holding_days=5,
                metadata={
                    "debate_round": state.get("debate_round", 0),
                    "full_response": response_content
                }
            )
        except Exception as e:
            print(f"⚠️ 记录Bear Research失败: {e}")

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bear_history": bear_history + "\n" + argument,
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
