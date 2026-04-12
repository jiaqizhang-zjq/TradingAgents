from datetime import datetime

from tradingagents.constants import TOOL_CALL_LOG_PATH
from tradingagents.utils.logger import get_logger

logger = get_logger(__name__)


def log_tool_call(tool_name: str, vendor_used: str, result: str) -> None:
    """记录工具调用信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = TOOL_CALL_LOG_PATH
    
    log_entry = f"\n{'='*100}\n"
    log_entry += f"[{timestamp}] 🔧 Tool: {tool_name}\n"
    log_entry += f"          📊 Vendor Used: {vendor_used}\n"
    log_entry += f"          📄 Result Preview:\n"
    log_entry += f"{result[:500]}{'...' if len(result) > 500 else ''}\n"
    log_entry += f"{'='*100}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    logger.debug("🔧 [TOOL CALL] %s (Vendor: %s)", tool_name, vendor_used)
