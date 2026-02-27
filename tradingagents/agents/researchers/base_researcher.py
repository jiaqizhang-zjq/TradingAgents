"""
基础研究员类 - 消除 Bull/Bear Researcher 的重复代码
"""

from langchain_core.messages import AIMessage
import time
import json
import re
from typing import Callable, Dict, Any

from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.dataflows.config import get_config


class BaseResearcher:
    """
    基础研究员类
    
    提供 Bull 和 Bear Researcher 的通用逻辑，减少代码重复
    """
    
    def __init__(
        self,
        researcher_type: str,
        system_prompts: Dict[str, str],
        llm,
        memory,
        default_win_rate: float = 0.50
    ):
        """
        初始化基础研究员
        
        Args:
            researcher_type: 研究员类型 ("bull_researcher" 或 "bear_researcher")
            system_prompts: 系统提示词字典 {"en": ..., "zh": ...}
            llm: LLM 客户端
            memory: 记忆存储
            default_win_rate: 默认胜率
        """
        self.researcher_type = researcher_type
        self.system_prompts = system_prompts
        self.llm = llm
        self.memory = memory
        self.default_win_rate = default_win_rate
    
    def _build_win_rate_string(
        self,
        symbol: str,
        language: str,
        tracker: Any
    ) -> str:
        """构建胜率信息字符串"""
        # 获取特定股票的胜率
        symbol_win_rate = tracker.get_researcher_win_rate(
            self.researcher_type, symbol, default_win_rate=self.default_win_rate
        )
        # 获取研究员平均胜率
        avg_win_rate = tracker.get_researcher_win_rate(
            self.researcher_type, None, default_win_rate=self.default_win_rate
        )
        
        # 构建胜率信息字符串
        if language == "zh":
            if symbol_win_rate['total_predictions'] >= 1:
                symbol_part = f"该股票胜率：{symbol_win_rate['win_rate']:.1%}（{symbol_win_rate['total_predictions']}次）"
            else:
                symbol_part = "该股票暂无历史数据"
            
            avg_part = f"平均胜率：{avg_win_rate['win_rate']:.1%}（{avg_win_rate['total_predictions']}次）"
            return f"{symbol_part} | {avg_part}"
        else:
            if symbol_win_rate['total_predictions'] >= 1:
                symbol_part = f"This stock: {symbol_win_rate['win_rate']:.1%} ({symbol_win_rate['total_predictions']} trades)"
            else:
                symbol_part = "No history for this stock"
            
            avg_part = f"Average: {avg_win_rate['win_rate']:.1%} ({avg_win_rate['total_predictions']} trades)"
            return f"{symbol_part} | {avg_part}"
    
    def _build_prompt(
        self,
        language: str,
        win_rate_str: str,
        market_research_report: str,
        sentiment_report: str,
        news_report: str,
        fundamentals_report: str,
        candlestick_report: str,
        history: str,
        current_response: str,
        past_memory_str: str,
        opponent_type: str  # "看跌" 或 "看涨" (zh) / "bearish" 或 "bullish" (en)
    ) -> str:
        """构建提示词（模板方法）"""
        system_prompt = self.system_prompts.get(language, self.system_prompts["zh"])
        
        if language == "zh":
            return f"""{system_prompt}

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
上次{opponent_type}论点：{current_response}
类似情况下的反思和经验教训：{past_memory_str}
利用这些信息提出一个令人信服的{self._get_stance_zh()}论点，反驳{opponent_type}的{'担忧' if opponent_type == '看跌' else '主张'}，并参与一场动态辩论，展示{self._get_stance_zh()}立场的优势。你还必须解决反思问题，并从过去的经验教训中学习。"""
        else:
            return f"""{system_prompt}

[HISTORICAL WIN RATE REFERENCE]
{win_rate_str}
Please adjust your confidence level based on your historical performance. If your win rate is above industry average, you can moderately increase confidence; if below, be more cautious.

Resources available:
Market research report: {market_research_report}
Social media sentiment report: {sentiment_report}
Latest world affairs news: {news_report}
Company fundamentals report: {fundamentals_report}
Candlestick analysis report: {candlestick_report}
Debate conversation history: {history}
Last {opponent_type} argument: {current_response}
Reflections and lessons learned from similar situations: {past_memory_str}
Use this information to make a compelling {self._get_stance_en()} case, counter the {opponent_type} {'concerns' if opponent_type == 'bearish' else 'claims'}, and engage in a dynamic debate showcasing the strengths of the {self._get_stance_en()} position. You must also address the reflection questions and learn from past lessons."""
    
    def _get_stance_zh(self) -> str:
        """获取立场的中文描述"""
        return "看涨" if self.researcher_type == "bull_researcher" else "看跌"
    
    def _get_stance_en(self) -> str:
        """获取立场的英文描述"""
        return "bullish" if self.researcher_type == "bull_researcher" else "bearish"
    
    def _get_opponent_stance_zh(self) -> str:
        """获取对手立场的中文描述"""
        return "看跌" if self.researcher_type == "bull_researcher" else "看涨"
    
    def _get_opponent_stance_en(self) -> str:
        """获取对手立场的英文描述"""
        return "bearish" if self.researcher_type == "bull_researcher" else "bullish"
    
    def _parse_llm_response(
        self,
        response_content: str,
        symbol: str,
        trade_date: str,
        language: str
    ) -> Dict[str, Any]:
        """
        解析 LLM 响应
        
        返回格式：
        {
            "recommendation": str,
            "confidence": float,
            "reasoning": str
        }
        """
        recommendation = "HOLD"
        confidence = 0.0
        reasoning = response_content

        # 提取推荐
        if language == "zh":
            if "推荐：买入" in response_content or "推荐：BUY" in response_content:
                recommendation = "BUY"
            elif "推荐：卖出" in response_content or "推荐：SELL" in response_content:
                recommendation = "SELL"
            elif "推荐：持有" in response_content or "推荐：HOLD" in response_content:
                recommendation = "HOLD"
        else:
            if "Recommendation: BUY" in response_content:
                recommendation = "BUY"
            elif "Recommendation: SELL" in response_content:
                recommendation = "SELL"
            elif "Recommendation: HOLD" in response_content:
                recommendation = "HOLD"

        # 提取置信度
        confidence_pattern = r"(?:置信度|Confidence)[：:]\s*([0-9]+(?:\.[0-9]+)?)"
        match = re.search(confidence_pattern, response_content)
        if match:
            try:
                confidence = float(match.group(1))
                if confidence > 1.0:
                    confidence = confidence / 100.0
            except ValueError:
                confidence = 0.0

        return {
            "recommendation": recommendation,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def create_node(self) -> Callable:
        """
        创建研究员节点函数
        
        Returns:
            节点函数
        """
        def node_function(state) -> dict:
            investment_debate_state = state["investment_debate_state"]
            history = investment_debate_state.get("history", "")
            
            # 根据研究员类型获取对应的历史
            if self.researcher_type == "bull_researcher":
                researcher_history = investment_debate_state.get("bull_history", "")
            else:
                researcher_history = investment_debate_state.get("bear_history", "")

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
            past_memories = self.memory.get_memories(curr_situation, n_matches=2)

            past_memory_str = ""
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"

            # 获取历史胜率
            tracker = get_research_tracker()
            win_rate_str = self._build_win_rate_string(symbol, language, tracker)
            
            # 构建提示词
            opponent_stance = self._get_opponent_stance_zh() if language == "zh" else self._get_opponent_stance_en()
            prompt = self._build_prompt(
                language=language,
                win_rate_str=win_rate_str,
                market_research_report=market_research_report,
                sentiment_report=sentiment_report,
                news_report=news_report,
                fundamentals_report=fundamentals_report,
                candlestick_report=candlestick_report,
                history=history,
                current_response=current_response,
                past_memory_str=past_memory_str,
                opponent_type=opponent_stance
            )
            
            # 调用 LLM
            messages = [{"role": "user", "content": prompt}]
            result = self.llm.invoke(messages)
            response_content = result.content if hasattr(result, "content") else str(result)

            # 解析响应
            parsed = self._parse_llm_response(response_content, symbol, trade_date, language)
            recommendation = parsed["recommendation"]
            confidence = parsed["confidence"]
            reasoning = parsed["reasoning"]

            # 保存研究记录
            tracker.save_research_record(
                researcher_name=self.researcher_type,
                researcher_type=self.researcher_type,
                symbol=symbol,
                trade_date=trade_date,
                prediction=recommendation,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "language": language,
                    "win_rate_str": win_rate_str
                }
            )

            # 更新状态
            updated_history = f"{history}\n\n{self._get_stance_zh() if language == 'zh' else self._get_stance_en()}: {response_content}"
            updated_researcher_history = f"{researcher_history}\n\n{response_content}"

            investment_debate_state["history"] = updated_history
            investment_debate_state["current_response"] = response_content
            
            # 更新 latest_speaker 用于 conditional_logic 判断
            speaker_name = "Bull" if self.researcher_type == "bull_researcher" else "Bear"
            investment_debate_state["latest_speaker"] = speaker_name
            
            # 更新 count 用于轮次控制
            current_count = investment_debate_state.get("count", 0)
            investment_debate_state["count"] = current_count + 1
            
            if self.researcher_type == "bull_researcher":
                investment_debate_state["bull_history"] = updated_researcher_history
            else:
                investment_debate_state["bear_history"] = updated_researcher_history

            time.sleep(1)

            return {"investment_debate_state": investment_debate_state}
        
        return node_function
