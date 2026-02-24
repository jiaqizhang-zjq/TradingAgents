from langchain_core.messages import AIMessage
import time
import json
import re

from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config
from tradingagents.agents.prompt_templates import STANDARD_BEAR_PROMPT_EN, STANDARD_BEAR_PROMPT_ZH


# 使用模板中的提示词
SYSTEM_PROMPTS = {
    "en": STANDARD_BEAR_PROMPT_EN,
    "zh": STANDARD_BEAR_PROMPT_ZH
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

        # 获取历史胜率
        tracker = get_research_tracker()
        win_rate_info = tracker.get_researcher_win_rate("bear_researcher", symbol, default_win_rate=0.48)
        
        # 构建胜率信息字符串
        if language == "zh":
            if win_rate_info['source'] == 'symbol_specific':
                win_rate_str = f"你在该股票上的历史胜率：{win_rate_info['win_rate']:.1%}（基于{win_rate_info['total_predictions']}次预测）"
            elif win_rate_info['source'] == 'researcher_average':
                win_rate_str = f"你的平均胜率：{win_rate_info['win_rate']:.1%}（基于{win_rate_info['total_predictions']}次预测）"
            elif win_rate_info['source'] == 'type_average':
                win_rate_str = f"看跌分析师类型平均胜率：{win_rate_info['win_rate']:.1%}（行业参考）"
            else:
                win_rate_str = f"使用行业默认胜率：{win_rate_info['win_rate']:.1%}（看跌分析师行业均值）"
        else:
            if win_rate_info['source'] == 'symbol_specific':
                win_rate_str = f"Your win rate on this stock: {win_rate_info['win_rate']:.1%} (based on {win_rate_info['total_predictions']} predictions)"
            elif win_rate_info['source'] == 'researcher_average':
                win_rate_str = f"Your average win rate: {win_rate_info['win_rate']:.1%} (based on {win_rate_info['total_predictions']} predictions)"
            elif win_rate_info['source'] == 'type_average':
                win_rate_str = f"Bear analyst type average win rate: {win_rate_info['win_rate']:.1%} (industry reference)"
            else:
                win_rate_str = f"Using industry default win rate: {win_rate_info['win_rate']:.1%} (bear analyst industry average)"
        
        # 根据语言选择系统提示词
        system_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["zh"])
        
        if language == "zh":
            prompt = f"""{system_prompt}

【历史胜率参考】
{win_rate_str}
请结合你的历史表现来调整本次分析的置信度。如果你的历史胜率高于行业均值，可以适度提高置信度；如果低于均值，需要更加谨慎。

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

[HISTORICAL WIN RATE REFERENCE]
{win_rate_str}
Please adjust your confidence level based on your historical performance. If your win rate is above industry average, you can moderately increase confidence; if below, be more cautious.

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

        # 调试信息：打印完整prompt（由debug开关控制）
        debug_config = config.get("debug", {})
        if debug_config.get("enabled", False) and debug_config.get("show_prompts", False):
            print("=" * 80)
            print("DEBUG: Bear Researcher Prompt Before LLM Call:")
            print("=" * 80)
            print(f"Language: {language}")
            print(f"Prompt: {prompt[:1000]}..." if len(prompt) > 1000 else f"Prompt: {prompt}")
            print("=" * 80)
        
        response = llm.invoke(prompt)
        response_content = response.content

        # 获取胜率信息添加到输出中
        win_rate_percent = win_rate_info['win_rate'] * 100
        
        # 根据语言设置分析师名称和胜率
        if language == "zh":
            analyst_name = "Bear Analyst"
            win_rate_display = f"[胜率: {win_rate_percent:.1f}%]"
            argument = f"{analyst_name} {win_rate_display}: {response_content}"
        else:
            analyst_name = "Bear Analyst"
            win_rate_display = f"[Win Rate: {win_rate_percent:.1f}%]"
            argument = f"{analyst_name} {win_rate_display}: {response_content}"
        
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
                researcher_name="bear_researcher",
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
            "bear_prediction": prediction,
            "bear_confidence": confidence,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bear_node
