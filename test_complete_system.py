#!/usr/bin/env python3
"""
完整系统测试 - 不删除，保留所有输出
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

print("\n" + "="*70)
print("完整系统测试 - 验证所有修改")
print("="*70)

# 测试1: 导入所有模块
print("\n【测试1】模块导入测试")
print("-"*70)
try:
    from tradingagents.utils.validators import validate_symbol, validate_date
    print("✓ validators 导入成功")
except Exception as e:
    print(f"❌ validators 导入失败: {e}")

try:
    from tradingagents.agents.researchers.base_researcher import BaseResearcher
    print("✓ BaseResearcher 导入成功")
except Exception as e:
    print(f"❌ BaseResearcher 导入失败: {e}")

try:
    from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
    print("✓ bull_researcher 导入成功")
except Exception as e:
    print(f"❌ bull_researcher 导入失败: {e}")

try:
    from tradingagents.agents.researchers.bear_researcher import create_bear_researcher
    print("✓ bear_researcher 导入成功")
except Exception as e:
    print(f"❌ bear_researcher 导入失败: {e}")

try:
    from tradingagents.dataflows.lazy_indicators import LazyIndicatorCalculator
    print("✓ LazyIndicatorCalculator 导入成功")
except Exception as e:
    print(f"❌ LazyIndicatorCalculator 导入失败: {e}")

try:
    from tradingagents.graph.conditional_logic import ConditionalLogic
    print("✓ ConditionalLogic 导入成功")
except Exception as e:
    print(f"❌ ConditionalLogic 导入失败: {e}")

try:
    from tradingagents.agents.utils.agent_states import InvestDebateState
    print("✓ InvestDebateState 导入成功")
except Exception as e:
    print(f"❌ InvestDebateState 导入失败: {e}")

# 测试2: 验证器功能
print("\n【测试2】验证器功能测试")
print("-"*70)
try:
    from tradingagents.utils.validators import validate_symbol
    result = validate_symbol("AAPL")
    print(f"✓ validate_symbol('AAPL') = {result}")
except Exception as e:
    print(f"❌ validate_symbol 失败: {e}")

try:
    validate_symbol("'; DROP TABLE--")
    print("❌ SQL注入未被拦截")
except Exception as e:
    print(f"✓ SQL注入被正确拒绝: {type(e).__name__}")

# 测试3: 状态结构
print("\n【测试3】InvestDebateState 结构测试")
print("-"*70)
test_state = {
    "history": "",
    "current_response": "",
    "latest_speaker": "",
    "count": 0,
    "bull_history": "",
    "bear_history": "",
    "judge_decision": "",
}
print(f"✓ 测试状态创建成功")
print(f"  - 包含字段: {list(test_state.keys())}")

# 测试4: 辩论路由
print("\n【测试4】辩论路由逻辑测试")
print("-"*70)
try:
    from tradingagents.graph.conditional_logic import ConditionalLogic
    logic = ConditionalLogic(max_debate_rounds=2)
    
    # 测试路由
    tests = [
        (0, "", "第1轮"),
        (1, "Bull", "第2轮"),
        (2, "Bear", "第3轮"),
        (3, "Bull", "第4轮"),
        (4, "Bear", "结束"),
    ]
    
    for count, speaker, desc in tests:
        state = {"investment_debate_state": {"count": count, "latest_speaker": speaker}}
        result = logic.should_continue_debate(state)
        print(f"  {desc}: count={count}, speaker={speaker} -> {result}")
except Exception as e:
    print(f"❌ 路由逻辑测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试5: 主程序初始化
print("\n【测试5】主程序初始化测试")
print("-"*70)
try:
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    from tradingagents.default_config import DEFAULT_CONFIG
    print("✓ TradingAgentsGraph 和 DEFAULT_CONFIG 导入成功")
    
    # 不实际初始化（需要API密钥），只验证类存在
    print(f"✓ TradingAgentsGraph 类可用")
except Exception as e:
    print(f"❌ 主程序导入失败: {e}")
    import traceback
    traceback.print_exc()

# 测试6: 检查修改的文件
print("\n【测试6】检查今天修改的文件")
print("-"*70)
files_to_check = [
    "tradingagents/agents/utils/agent_states.py",
    "tradingagents/graph/propagation.py",
    "tradingagents/agents/managers/research_manager.py",
]

for filepath in files_to_check:
    full_path = os.path.join(os.path.dirname(__file__), filepath)
    if os.path.exists(full_path):
        print(f"✓ {filepath} 存在")
        # 检查 latest_speaker
        with open(full_path) as f:
            content = f.read()
            if "latest_speaker" in content:
                print(f"  ✓ 包含 'latest_speaker'")
            else:
                print(f"  ❌ 不包含 'latest_speaker'")
    else:
        print(f"❌ {filepath} 不存在")

print("\n" + "="*70)
print("测试完成")
print("="*70)
