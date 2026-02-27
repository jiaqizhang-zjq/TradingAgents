# TradingAgents Cron 配置备份

**日期**: 2026-02-27  
**来源**: `crontab -l`  
**说明**: 系统 crontab 配置，8 支股票定时分析（10:00-17:00，工作日）

## 配置内容

```bash
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin

# 防睡眠机制
30 9 * * * /usr/bin/caffeinate -i &
0 22 * * * pkill -f 'caffeinate -i' &

# 股票分析任务（后台运行，无超时限制）
0 10 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh NVDA > logs/NVDA-cron.log 2>&1 &
0 11 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh TSLA > logs/TSLA-cron.log 2>&1 &
0 12 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh LMND > logs/LMND-cron.log 2>&1 &
0 13 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh APLD > logs/APLD-cron.log 2>&1 &
0 14 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh RKLB > logs/RKLB-cron.log 2>&1 &
0 15 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh INTC > logs/INTC-cron.log 2>&1 &
0 16 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh IREN > logs/IREN-cron.log 2>&1 &
0 17 * * * 1-5 cd /Users/jiaqi.zjq/workingspace/ai_trading/TradingAgents && ./run_trading.sh KTOS > logs/KTOS-cron.log 2>&1 &
```

## 恢复方法

```bash
# 1. 编辑 crontab
crontab -e

# 2. 粘贴上述配置内容保存

# 3. 验证
crontab -l
```

## 注意事项

- 所有任务使用 `&` 后台运行，无超时限制，允许长时间执行（20-30 分钟）
- 输出重定向到 `logs/{股票}-cron.log`（小文件，记录启动信息）
- 详细分析日志保存在 `logs/{股票}-2026-02-26-*.log`（按日期命名）
- **不要**再添加 OpenClaw cron 任务，避免双重触发
- 如需修改股票列表或时间，先在此备份并更新 MEMORY.md

## 历史变更

- 2026-02-27: 初始备份（清理 OpenClaw cron 后）
