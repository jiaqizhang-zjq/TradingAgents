import functools
import time
import json
from tradingagents.dataflows.config import get_config


def create_trader(llm, memory):
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        candlestick_report = state.get("candlestick_report", "")

        # 获取语言配置，默认为英文
        config = get_config()
        language = config.get("output_language", "en")

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}\n\n{candlestick_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found." if language == "en" else "没有找到过去的记忆。"

        if language == "zh":
            context = {
                "role": "user",
                "content": f"基于分析师团队的综合分析，这里是为{company_name}制定的投资计划。该计划整合了当前技术市场趋势、宏观经济指标和社交媒体情绪的见解。请以此为基础评估你的下一个交易决策。\n\n建议投资计划：{investment_plan}\n\n利用这些见解做出明智和战略性的决策。",
            }
            system_content = f"""你是一位交易分析师，负责分析市场数据并做出投资决策。基于你的分析，提供具体的买入、卖出或持有建议。以明确的决策结束，并始终以'最终交易建议：**买入/持有/卖出**'来确认你的建议。不要忘记利用过去决策的经验教训来避免错误。以下是你过去在类似情况下的交易反思和经验教训：{past_memory_str}"""
        else:
            context = {
                "role": "user",
                "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
            }
            system_content = f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold. End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situatiosn you traded in and the lessons learned: {past_memory_str}"""

        messages = [
            {
                "role": "system",
                "content": system_content,
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
