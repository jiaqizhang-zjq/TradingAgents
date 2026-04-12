"""
报告保存模块
用于将所有分析报告保存到文件系统，按股票名/日期/报告类型组织
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入依赖注入容器
from tradingagents.core.container import get_container
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


# 报告类型定义: (序号, 文件名, report_type, 参数名)
_SIMPLE_REPORT_DEFS: List[Tuple[str, str, str]] = [
    ("01_market_analysis.md", "market_analysis", "market_report"),
    ("02_sentiment_analysis.md", "sentiment_analysis", "sentiment_report"),
    ("03_news_analysis.md", "news_analysis", "news_report"),
    ("04_fundamentals_analysis.md", "fundamentals_analysis", "fundamentals_report"),
    ("05_candlestick_analysis.md", "candlestick_analysis", "candlestick_report"),
    ("10_trader_report.md", "trader_report", "trader_report"),
    ("11_final_decision.md", "final_decision", "final_trade_decision"),
]


class ReportSaver:
    """
    报告保存器
    
    目录结构：
    reports/
    ├── LMND/
    │   ├── 2026-02-20/
    │   │   ├── 01_market_analysis.md
    │   │   ├── ...
    │   │   └── 11_final_decision.md
    │   └── 2026-02-19/
    └── NVDA/
        └── ...
    """
    
    def __init__(self, base_dir: str = "reports"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def _get_report_dir(self, symbol: str, trade_date: str) -> Path:
        """获取报告目录路径"""
        report_dir = self.base_dir / symbol / trade_date
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir
    
    def _save_report(self, report_dir: Path, filename: str, content: str, metadata: Dict = None):
        """保存单个报告文件"""
        filepath = report_dir / filename
        
        file_content = f"""# {filename.replace('.md', '').replace('_', ' ').title()}

**股票代码**: {report_dir.parent.name}  
**日期**: {report_dir.name}  
**生成时间**: {datetime.now().isoformat()}

---

{content}

"""
        if metadata:
            file_content += "\n---\n\n## 元数据\n\n```json\n"
            file_content += json.dumps(metadata, indent=2, ensure_ascii=False)
            file_content += "\n```\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        logger.info("✅ 报告已保存: %s", filepath)
        return filepath
    
    def save_analysis_reports(
        self,
        symbol: str,
        trade_date: str,
        market_report: str = "",
        sentiment_report: str = "",
        news_report: str = "",
        fundamentals_report: str = "",
        candlestick_report: str = "",
        investment_debate_state: Dict = None,
        risk_debate_state: Dict = None,
        trader_report: str = "",
        investment_plan: str = "",
        final_trade_decision: str = ""
    ):
        """保存所有分析报告"""
        report_dir = self._get_report_dir(symbol, trade_date)
        saved_files = []
        
        # 收集所有简单报告内容
        report_values = {
            "market_report": market_report,
            "sentiment_report": sentiment_report,
            "news_report": news_report,
            "fundamentals_report": fundamentals_report,
            "candlestick_report": candlestick_report,
            "trader_report": trader_report,
            "final_trade_decision": final_trade_decision,
        }
        
        # 数据驱动方式保存简单报告
        for filename, report_type, param_key in _SIMPLE_REPORT_DEFS:
            content = report_values.get(param_key, "")
            if content:
                saved_files.append(self._save_report(
                    report_dir, filename, content,
                    {"type": report_type, "symbol": symbol, "date": trade_date}
                ))
        
        # 辩论类报告（有特殊格式化逻辑）
        saved_files.extend(self._save_debate_reports(
            report_dir, symbol, trade_date, 
            investment_debate_state, risk_debate_state
        ))
        
        # 保存索引文件
        self._save_index_file(report_dir, symbol, trade_date, saved_files)
        
        logger.info("✅ 所有报告已保存到: %s", report_dir)
        logger.info("   共保存 %d 个文件", len(saved_files))
        
        return saved_files
    
    def _save_debate_reports(self, report_dir: Path, symbol: str, trade_date: str,
                            investment_debate_state: Dict = None,
                            risk_debate_state: Dict = None) -> list:
        """保存辩论类报告"""
        saved = []
        
        debate_configs = [
            (investment_debate_state, "研究员辩论", "06_research_debate.md", 
             "research_debate", "07_research_manager_decision.md", "research_manager_decision"),
            (risk_debate_state, "风险辩论", "08_risk_debate.md",
             "risk_debate", "09_risk_manager_decision.md", "risk_manager_decision"),
        ]
        
        for state, title, debate_file, debate_type, decision_file, decision_type in debate_configs:
            if not state:
                continue
            
            # 辩论过程
            debate_content = self._format_debate_state(state, title)
            if debate_content:
                saved.append(self._save_report(
                    report_dir, debate_file, debate_content,
                    {"type": debate_type, "symbol": symbol, "date": trade_date}
                ))
            
            # 经理决策
            if state.get("judge_decision"):
                saved.append(self._save_report(
                    report_dir, decision_file, state["judge_decision"],
                    {"type": decision_type, "symbol": symbol, "date": trade_date}
                ))
        
        return saved
    
    def _format_debate_state(self, debate_state: Dict, title: str) -> str:
        """格式化辩论状态为可读文本"""
        if not debate_state:
            return ""
        
        content = f"# {title}\n\n"
        
        if debate_state.get("history"):
            content += "## 辩论历史\n\n"
            content += debate_state["history"]
            content += "\n\n"
        
        if debate_state.get("current_response"):
            content += "## 最新观点\n\n"
            content += debate_state["current_response"]
            content += "\n\n"
        
        return content
    
    def _save_index_file(self, report_dir: Path, symbol: str, trade_date: str, saved_files: list):
        """保存索引文件"""
        index_content = f"""# 报告索引

**股票代码**: {symbol}  
**日期**: {trade_date}  
**生成时间**: {datetime.now().isoformat()}

## 报告列表

| 序号 | 报告名称 | 文件路径 |
|------|----------|----------|
"""
        
        for i, filepath in enumerate(saved_files, 1):
            filename = filepath.name
            report_name = filename.replace('.md', '').replace('_', ' ').title()
            index_content += f"| {i} | {report_name} | `{filename}` |\n"
        
        index_content += f"""

## 目录结构

```
{symbol}/
└── {trade_date}/
"""
        for filepath in saved_files:
            index_content += f"    ├── {filepath.name}\n"
        
        index_content += "```\n"
        
        index_path = report_dir / "00_index.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        logger.info("✅ 索引文件已保存: %s", index_path)
    
    def get_report_history(self, symbol: str = None, limit: int = 100) -> list:
        """获取历史报告列表"""
        history = []
        
        dirs_to_scan = [self.base_dir / symbol] if symbol else list(self.base_dir.iterdir())
        
        for symbol_dir in dirs_to_scan:
            if not symbol_dir.is_dir():
                continue
            sym = symbol_dir.name
            for date_dir in sorted(symbol_dir.iterdir(), reverse=True):
                if date_dir.is_dir():
                    history.append({
                        "symbol": sym,
                        "date": date_dir.name,
                        "path": str(date_dir),
                        "reports": [f.name for f in date_dir.glob("*.md")]
                    })
        
        history.sort(key=lambda x: x["date"], reverse=True)
        return history[:limit]


def get_report_saver(base_dir: str = "reports") -> ReportSaver:
    """获取 ReportSaver 实例（通过依赖注入容器）"""
    container = get_container()
    
    if not container.has('report_saver'):
        container.register('report_saver', lambda: ReportSaver(base_dir), singleton=True)
    
    return container.get('report_saver')
