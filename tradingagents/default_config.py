import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings - 使用 OpenCode Zen (Minimax/GLM)
    "llm_provider": "openai",
    "deep_think_llm": "minimax-m2.5-free",
    "quick_think_llm": "minimax-m2.5-free",
    "backend_url": "https://opencode.ai/zen/v1",
    # Provider-specific thinking configuration
    "google_thinking_level": None,      # "high", "minimal", etc.
    "openai_reasoning_effort": None,    # "medium", "high", "low"
    # Debate and discussion settings
    "max_debate_rounds": 2,
    "max_risk_discuss_rounds": 2,
    "max_recur_limit": 100,
    # Language configuration - 输出语言设置
    # Options: "zh" (中文), "en" (English), "auto" (自动检测)
    "output_language": "zh",
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "longbridge",     # Options: alpha_vantage, yfinance, longbridge
        "technical_indicators": "longbridge",# Options: alpha_vantage, yfinance, longbridge
        "fundamental_data": "longbridge",    # Options: alpha_vantage, yfinance, longbridge
        "news_data": "yfinance",             # Options: alpha_vantage, yfinance, longbridge
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_stock_data": "longbridge",      # 使用长桥API
    },
    # Debug settings
    "debug": {
        "enabled": True,  # 调试模式开关
        "verbose": True,  # 详细日志
        "show_prompts": True,  # 显示完整prompt
        "log_level": "INFO",  # 日志级别: DEBUG, INFO, WARNING, ERROR
    },
}
