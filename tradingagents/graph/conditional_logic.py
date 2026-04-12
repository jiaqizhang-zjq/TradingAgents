# TradingAgents/graph/conditional_logic.py

from typing import Dict, Any, List
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.constants import RESEARCHER_REGISTRY, DEFAULT_SELECTED_RESEARCHERS


class ConditionalLogic:
    """Handles conditional logic for determining graph flow."""

    def __init__(
        self,
        max_debate_rounds: int = 2,
        max_risk_discuss_rounds: int = 2,
        selected_researchers: List[str] = None,
    ) -> None:
        """Initialize with configuration parameters.
        
        Args:
            max_debate_rounds: 每个 researcher 的最大辩论轮次
            max_risk_discuss_rounds: 风险讨论最大轮次
            selected_researchers: 选中的 researcher 简称列表（如 ["bull", "bear", "buffett"]）
        """
        self.max_debate_rounds: int = max_debate_rounds
        self.max_risk_discuss_rounds: int = max_risk_discuss_rounds
        
        # 构建辩论者轮询顺序
        self.selected_researchers = selected_researchers or DEFAULT_SELECTED_RESEARCHERS
        self.researcher_count = len(self.selected_researchers)
        
        # 构建 speaker_label -> display_name 映射，用于辩论路由
        # 例如: {"Bull": "Bull Researcher", "Bear": "Bear Researcher", "Buffett": "Buffett Researcher"}
        self.speaker_to_display: Dict[str, str] = {}
        # 构建辩论轮询顺序列表
        # 例如: ["Bull Researcher", "Bear Researcher", "Buffett Researcher"]
        self.debate_order: List[str] = []
        # speaker_label 到 index 的映射
        self.speaker_to_index: Dict[str, int] = {}
        
        for i, key in enumerate(self.selected_researchers):
            if key in RESEARCHER_REGISTRY:
                info = RESEARCHER_REGISTRY[key]
                display_name = info["display_name"]
                speaker_label = info["speaker_label"]
                self.speaker_to_display[speaker_label] = display_name
                self.debate_order.append(display_name)
                self.speaker_to_index[speaker_label] = i

    def should_continue_market(self, state: AgentState) -> str:
        """Determine if market analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_market"
        return "Msg Clear Market"

    def should_continue_social(self, state: AgentState):
        """Determine if social media analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_social"
        return "Msg Clear Social"

    def should_continue_news(self, state: AgentState):
        """Determine if news analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_news"
        return "Msg Clear News"

    def should_continue_fundamentals(self, state: AgentState):
        """Determine if fundamentals analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_fundamentals"
        return "Msg Clear Fundamentals"

    def should_continue_candlestick(self, state: AgentState):
        """Determine if candlestick analysis should continue."""
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools_candlestick"
        return "Msg Clear Candlestick"

    def should_continue_debate(self, state: AgentState) -> str:
        """Determine if debate should continue.
        
        支持 N 方轮询辩论：按 debate_order 列表顺序循环。
        每个 researcher 发言一次算一轮，total_count >= researcher_count * max_debate_rounds 时结束。
        """
        total_count = state["investment_debate_state"]["count"]
        
        # 所有 researcher 轮询完指定轮次后，交给 Research Manager
        if total_count >= self.researcher_count * self.max_debate_rounds:
            return "Research Manager"
        
        # 确定下一个发言者
        latest = state["investment_debate_state"].get("latest_speaker", "")
        
        if latest and latest in self.speaker_to_index:
            # 找到当前发言者的 index，下一个是 (index + 1) % count
            current_idx = self.speaker_to_index[latest]
            next_idx = (current_idx + 1) % self.researcher_count
        else:
            # 没有发言者或未知发言者，从第一个开始
            next_idx = 0
        
        return self.debate_order[next_idx]

    def should_continue_risk_analysis(self, state: AgentState) -> str:
        """Determine if risk analysis should continue."""
        if (
            state["risk_debate_state"]["count"] >= 3 * self.max_risk_discuss_rounds
        ):  # 3 rounds of back-and-forth between 3 agents
            return "Risk Judge"
        if state["risk_debate_state"]["latest_speaker"].startswith("Aggressive"):
            return "Conservative Analyst"
        if state["risk_debate_state"]["latest_speaker"].startswith("Conservative"):
            return "Neutral Analyst"
        return "Aggressive Analyst"
