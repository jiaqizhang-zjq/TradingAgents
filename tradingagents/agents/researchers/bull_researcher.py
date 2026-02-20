from langchain_core.messages import AIMessage
import time
import json
import re

from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config


# 中英双语系统提示词
SYSTEM_PROMPTS = {
    "en": """You are a Senior Bull Analyst with 20+ years of experience on Wall Street. Your reputation is built on accurate calls and rigorous analysis. You are advocating for investing in the stock.

Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability with specific numbers.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly.
- Probability Assessment: Provide a detailed probability distribution of potential outcomes (bull case, base case, bear case).

As a 20+ year veteran, you must provide:
1. Specific price targets with reasoning
2. Risk-adjusted position sizing recommendations
3. Probability-weighted expected returns

IMPORTANT: At the end of your response, you MUST include:
PREDICTION: [BUY/SELL/HOLD] (Confidence: [0-100]%)
PROBABILITY DISTRIBUTION:
- Bull Case (up >20%): X%
- Base Case (-10% to +20%): Y%
- Bear Case (down >10%): Z%
EXPECTED RETURN: X%
RECOMMENDED POSITION SIZE: X% of portfolio
""",

    "zh": """你是一位拥有20多年华尔街经验的资深看涨分析师。你的声誉建立在准确的判断和严谨的分析之上。你主张投资该股票。

你的任务是基于证据建立一个强有力的案例，强调增长潜力、竞争优势和积极的市场指标。利用提供的研究和数据来解决问题并有效反驳看跌论点。

重点关注的关键点：
- 增长潜力：突出公司的市场机会、收入预测和可扩展性，提供具体数字。
- 竞争优势：强调独特产品、强大品牌或主导市场地位等因素。
- 积极指标：使用财务健康状况、行业趋势和近期积极消息作为证据。
- 反驳看跌观点：用具体数据和合理推理批判性分析看跌论点，彻底解决问题。
- 概率评估：提供潜在结果的详细概率分布（看涨情况、基准情况、看跌情况）。

作为20多年的资深人士，你必须提供：
1. 具体的目标价格及推理
2. 风险调整后的仓位规模建议
3. 概率加权预期收益

重要：在你的回复末尾，你必须包含：
预测：[买入/卖出/持有]（置信度：[0-100]%）
概率分布：
- 看涨情况（上涨>20%）：X%
- 基准情况（-10%到+20%）：Y%
- 看跌情况（下跌>10%）：Z%
预期收益：X%
建议仓位规模：投资组合的X%
"""
}


def create_bull_researcher(llm, memory):
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

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
上次看跌论点：{current_response}
类似情况下的反思和经验教训：{past_memory_str}
利用这些信息提出一个令人信服的看涨论点，反驳看跌的担忧，并参与一场动态辩论，展示看涨立场的优势。你还必须解决反思问题，并从过去的经验教训中学习。"""
        else:
            prompt = f"""{system_prompt}

Resources available:
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Candlestick analysis report: {candlestick_report}
Conversation history of the debate: {history}
Last bear argument: {current_response}
Reflections from similar situations and lessons learned: {past_memory_str}
Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position. You must also address reflections and learn from lessons and mistakes you made in the past.
"""

        response = llm.invoke(prompt)
        response_content = response.content

        # 根据语言设置分析师名称
        analyst_name = "看涨分析师" if language == "zh" else "Bull Analyst"
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
                prediction = "BUY"
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
                researcher_name=f"bull_{state.get('debate_round', 0)}",
                researcher_type="bull",
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
            print(f"⚠️ 记录Bull Research失败: {e}")

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
