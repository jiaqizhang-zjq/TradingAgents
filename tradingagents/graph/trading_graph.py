# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date, datetime
from typing import Dict, Any, Tuple, List, Optional

from langgraph.prebuilt import ToolNode

from tradingagents.llm_clients import create_llm_client

from tradingagents.agents import *
from tradingagents.agents.backtest import run_backtest
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.database import AnalysisReport, get_db
from tradingagents.dataflows.research_tracker import get_research_tracker
from tradingagents.report_saver import get_report_saver

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_transactions,
    get_global_news
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import SignalProcessor


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals", "candlestick"],
        debug=False,
        config: Dict[str, Any] = None,
        callbacks: Optional[List] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
            callbacks: Optional list of callback handlers (e.g., for tracking LLM/tool stats)
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG
        self.callbacks = callbacks or []

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # 初始化LLMs，使用提供商特定的思考配置
        llm_kwargs = self._get_provider_kwargs()

        # 如果提供了回调，则添加到kwargs中（传递给LLM构造函数）
        if self.callbacks:
            llm_kwargs["callbacks"] = self.callbacks

        # 创建深度思考LLM客户端
        # 深度思考LLM用于复杂的推理任务，如分析和决策
        deep_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["deep_think_llm"],  # 通常是更强大的模型，如gpt-5.2
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )
        
        # 创建快速思考LLM客户端
        # 快速思考LLM用于简单的任务，如数据处理和报告生成
        quick_client = create_llm_client(
            provider=self.config["llm_provider"],
            model=self.config["quick_think_llm"],  # 通常是更轻量的模型，如gpt-5-mini
            base_url=self.config.get("backend_url"),
            **llm_kwargs,
        )

        # 获取配置好的LLM实例
        self.deep_thinking_llm = deep_client.get_llm()
        self.quick_thinking_llm = quick_client.get_llm()
        
        # Initialize memories
        self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize components
        self.conditional_logic = ConditionalLogic(
            max_debate_rounds=self.config.get("max_debate_rounds", 2),
            max_risk_discuss_rounds=self.config.get("max_risk_discuss_rounds", 2)
        )
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _get_provider_kwargs(self) -> Dict[str, Any]:
        """获取LLM客户端创建的提供商特定参数
        
        根据不同的LLM提供商，获取相应的特定参数
        
        Returns:
            提供商特定参数的字典
        """
        kwargs = {}
        provider = self.config.get("llm_provider", "").lower()

        # Google提供商特定参数
        if provider == "google":
            thinking_level = self.config.get("google_thinking_level")
            if thinking_level:
                kwargs["thinking_level"] = thinking_level

        # OpenAI提供商特定参数
        elif provider == "openai":
            reasoning_effort = self.config.get("openai_reasoning_effort")
            if reasoning_effort:
                kwargs["reasoning_effort"] = reasoning_effort

        return kwargs

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """创建不同数据源的工具节点，使用抽象方法
        
        ToolNode是LangGraph提供的组件，用于执行工具函数并处理结果
        每个分析师类型都有自己的一组工具
        
        Returns:
            工具节点字典，键为分析师类型，值为对应的ToolNode
        """
        return {
            "market": ToolNode(
                [
                    # 核心股票数据工具
                    get_stock_data,
                    # 技术指标工具
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # 社交媒体分析的新闻工具
                    get_news,
                ]
            ),
            "news": ToolNode(
                [
                    # 新闻和内幕信息工具
                    get_news,
                    get_global_news,
                    get_insider_transactions,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # 基本面分析工具
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                ]
            ),
            "candlestick": ToolNode(
                [
                    # 蜡烛图分析工具
                    get_stock_data,
                    get_indicators,
                ]
            ),
        }

    def propagate(self, company_name, trade_date):
        """运行交易代理图，处理指定公司在特定日期的交易
        
        这是核心执行方法，协调所有代理的工作流程
        
        Args:
            company_name: 公司股票代码 (如 "NVDA")
            trade_date: 交易日期 (如 "2026-01-15")
            
        Returns:
            元组 (final_state, processed_signal)
            - final_state: 图执行完成后的最终状态
            - processed_signal: 处理后的交易决策信号
        """

        self.ticker = company_name

        # 回测配置
        backtest_enabled = self.config.get("backtest", {}).get("enabled", True)
        if backtest_enabled:
            if self.debug:
                print("\n" + "="*50)
                print("🔄 执行回测...")
                print("="*50)
            run_backtest(symbol=company_name, target_date=trade_date, debug=self.debug)
            if self.debug:
                print()

        # 初始化状态
        # 创建代理的初始状态，包含公司信息和交易日期
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )
        args = self.propagator.get_graph_args()

        if self.debug:
            # 调试模式，带跟踪输出
            # 使用stream方法逐块执行，便于调试和观察中间状态
            trace = []
            last_debate_state = None
            last_risk_state = None
            
            for chunk in self.graph.stream(init_agent_state, **args):
                # 打印所有节点的消息
                for node_name, node_data in chunk.items():
                    if node_name == "messages" and len(node_data) > 0:
                        print("\n" + "="*80)
                        print(f"📝 Messages Output:")
                        print("="*80)
                        node_data[-1].pretty_print()
                    elif node_name == "investment_debate_state":
                        print("\n" + "="*80)
                        print(f"📊 Investment Debate State:")
                        print("="*80)
                        print(f"Count: {node_data.get('count', 0)}")
                        print(f"Latest Speaker: {node_data.get('latest_speaker', 'N/A')}")
                        print(f"\n--- Bull History ---")
                        print(node_data.get('bull_history', '')[:2000] if node_data.get('bull_history') else "N/A")
                        print(f"\n--- Bear History ---")
                        print(node_data.get('bear_history', '')[:2000] if node_data.get('bear_history') else "N/A")
                        print(f"\n--- Current Response ---")
                        print(node_data.get('current_response', '')[:2000] if node_data.get('current_response') else "N/A")
                        print("="*80)
                    elif node_name == "risk_debate_state":
                        print("\n" + "="*80)
                        print(f"⚠️ Risk Debate State:")
                        print("="*80)
                        print(f"Count: {node_data.get('count', 0)}")
                        print(f"Latest Speaker: {node_data.get('latest_speaker', 'N/A')}")
                        print("="*80)
                    elif node_name == "trader_investment_plan":
                        print("\n" + "="*80)
                        print(f"💰 Trader Investment Plan:")
                        print("="*80)
                        print(str(node_data)[:2000])
                        print("="*80)
                
                trace.append(chunk)

            final_state = trace[-1] if trace else init_agent_state
        else:
            # 标准模式，不带跟踪
            # 使用invoke方法一次性执行完整个图
            final_state = self.graph.invoke(init_agent_state, **args)

        # 存储当前状态用于反思
        self.curr_state = final_state

        # 记录状态到文件
        self._log_state(trade_date, final_state)

        # 返回决策和处理后的信号
        return final_state, self.process_signal(final_state["final_trade_decision"])

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file and save to database."""
        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "candlestick_report": final_state["candlestick_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "aggressive_history": final_state["risk_debate_state"]["aggressive_history"],
                "conservative_history": final_state["risk_debate_state"]["conservative_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)
        
        # Save to database
        self._save_to_database(final_state)
        
        # Record researcher predictions for win rate tracking
        self._record_research_predictions(final_state)
    
    def _save_to_database(self, final_state):
        """Save the analysis results to database and files."""
        from tradingagents.agents.utils.agent_utils import is_market_open
        
        symbol = final_state["company_of_interest"]
        trade_date = final_state["trade_date"]
        
        # 检查指定日期是否开盘
        if not is_market_open(symbol, trade_date):
            if self.debug:
                print(f"⏰ {trade_date} 非开盘时间，跳过保存数据库")
            return
        
        try:
            db = get_db()
            
            # Create report object
            report = AnalysisReport(
                symbol=symbol,
                trade_date=trade_date,
                created_at=datetime.now().isoformat(),
                market_report=final_state.get("market_report", ""),
                fundamentals_report=final_state.get("fundamentals_report", ""),
                candlestick_report=final_state.get("candlestick_report", ""),
                sentiment_report=final_state.get("sentiment_report", ""),
                news_report=final_state.get("news_report", ""),
                investment_plan=final_state.get("investment_plan", ""),
                trader_investment_plan=final_state.get("trader_investment_plan", ""),
                final_trade_decision=final_state.get("final_trade_decision", ""),
                tool_calls_jsonl="",
                metadata=json.dumps({
                    "source": "TradingAgentsGraph",
                    "saved_at": datetime.now().isoformat()
                })
            )
            
            # Save to database
            success = db.save_analysis_report(report)
            
            if success:
                print(f"✅ 分析结果已保存到数据库: {symbol} @ {trade_date}")
            else:
                print(f"❌ 保存到数据库失败")
            
            # Save to files
            self._save_to_files(final_state)
                
        except Exception as e:
            print(f"❌ 数据库保存错误: {e}")
    
    def _save_to_files(self, final_state):
        """Save the analysis results to files."""
        try:
            saver = get_report_saver()
            
            symbol = final_state["company_of_interest"]
            trade_date = final_state["trade_date"]
            
            # Get debate states
            investment_debate_state = final_state.get("investment_debate_state", {})
            risk_debate_state = final_state.get("risk_debate_state", {})
            
            # Save all reports
            saver.save_analysis_reports(
                symbol=symbol,
                trade_date=trade_date,
                market_report=final_state.get("market_report", ""),
                sentiment_report=final_state.get("sentiment_report", ""),
                news_report=final_state.get("news_report", ""),
                fundamentals_report=final_state.get("fundamentals_report", ""),
                candlestick_report=final_state.get("candlestick_report", ""),
                investment_debate_state=investment_debate_state,
                risk_debate_state=risk_debate_state,
                trader_report=final_state.get("trader_investment_plan", ""),
                investment_plan=final_state.get("investment_plan", ""),
                final_trade_decision=final_state.get("final_trade_decision", "")
            )
                
        except Exception as e:
            print(f"❌ 文件保存错误: {e}")
    
    def _record_research_predictions(self, final_state):
        """Record bull and bear researcher predictions for win rate tracking."""
        from tradingagents.agents.utils.agent_utils import is_market_open
        
        symbol = final_state["company_of_interest"]
        trade_date = final_state["trade_date"]
        
        # 检查指定日期是否开盘
        if not is_market_open(symbol, trade_date):
            if self.debug:
                print(f"⏰ {trade_date} 非开盘时间，跳过记录预测")
            return
        
        try:
            tracker = get_research_tracker()
            
            # Extract investment debate state
            invest_debate = final_state.get("investment_debate_state", {})
            
            # Record bull researcher - bull_history is a string
            bull_history = invest_debate.get("bull_history", "")
            if bull_history:
                bull_prediction = self._extract_prediction_from_content(bull_history)
                tracker.record_research(
                    researcher_name="bull_researcher",
                    researcher_type="bull",
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=bull_prediction,
                    confidence=0.8,
                    reasoning=bull_history if bull_history else ""
                )
            
            # Record bear researcher - bear_history is a string
            bear_history = invest_debate.get("bear_history", "")
            if bear_history:
                bear_prediction = self._extract_prediction_from_content(bear_history)
                tracker.record_research(
                    researcher_name="bear_researcher",
                    researcher_type="bear",
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=bear_prediction,
                    confidence=0.8,
                    reasoning=bear_history if bear_history else ""
                )
            
            # Record research manager
            judge_decision = invest_debate.get("judge_decision", "")
            if judge_decision:
                manager_prediction = self._extract_prediction_from_content(judge_decision)
                tracker.record_research(
                    researcher_name="research_manager",
                    researcher_type="manager",
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=manager_prediction,
                    confidence=0.85,
                    reasoning=judge_decision if judge_decision else ""
                )
            
            # Record risk debate participants
            risk_debate = final_state.get("risk_debate_state", {})
            
            # Aggressive risk analyst
            aggressive_history = risk_debate.get("aggressive_history", "")
            if aggressive_history:
                aggressive_prediction = self._extract_prediction_from_content(aggressive_history)
                tracker.record_research(
                    researcher_name="aggressive_risk",
                    researcher_type="aggressive",
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=aggressive_prediction,
                    confidence=0.7,
                    reasoning=aggressive_history if aggressive_history else ""
                )
            
            # Conservative risk analyst
            conservative_history = risk_debate.get("conservative_history", "")
            if conservative_history:
                conservative_prediction = self._extract_prediction_from_content(conservative_history)
                tracker.record_research(
                    researcher_name="conservative_risk",
                    researcher_type="conservative",
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=conservative_prediction,
                    confidence=0.7,
                    reasoning=conservative_history if conservative_history else ""
                )
            
            # Neutral risk analyst
            neutral_history = risk_debate.get("neutral_history", "")
            if neutral_history:
                neutral_prediction = self._extract_prediction_from_content(neutral_history)
                tracker.record_research(
                    researcher_name="neutral_risk",
                    researcher_type="neutral",
                    symbol=symbol,
                    trade_date=trade_date,
                    prediction=neutral_prediction,
                    confidence=0.75,
                    reasoning=neutral_history if neutral_history else ""
                )
            
            # Record final trader decision
            final_decision = final_state.get("final_trade_decision", "")
            trader_prediction = self._extract_prediction_from_content(final_decision)
            tracker.record_research(
                researcher_name="trader",
                researcher_type="trader",
                symbol=symbol,
                trade_date=trade_date,
                prediction=trader_prediction,
                confidence=0.9,
                reasoning=final_decision
            )
            
            print(f"✅ 研究员预测已记录到胜率追踪器")
            
        except Exception as e:
            print(f"❌ 记录研究员预测失败: {e}")
            import traceback
            print(f"   错误详情: {traceback.format_exc()}")
    
    def _extract_prediction_from_content(self, content: str) -> str:
        """Extract BUY/SELL/HOLD prediction from text content."""
        content_upper = content.upper()
        
        if "BUY" in content_upper:
            return "BUY"
        elif "SELL" in content_upper:
            return "SELL"
        else:
            return "HOLD"

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)
