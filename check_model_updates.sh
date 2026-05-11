#!/bin/bash
# 每天检查模型更新并发送通知

# macOS 通知函数
notify() {
    osascript -e "display notification \"$1\" with title \"🤖 oMLX 模型更新\""
}

# 运行检查并保存结果
OUTPUT=$(python3 /Users/berton/Github/omlx/check_model_updates.py 2>&1)

# 检查是否有"今天"或"昨天"的更新
if echo "$OUTPUT" | grep -E "更新时间: (今天|昨天)"; then
    echo "$OUTPUT"
    notify "检测到模型更新！请检查终端输出"
fi

# 保存日志
echo "=== $(date) ===" >> ~/.omlx/update_history.log
echo "$OUTPUT" >> ~/.omlx/update_history.log
