# main.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
老年抑郁智能评估系统 - 主程序
基于GDS-30量表的智能聊天记录分析系统
"""

import json
import random
import datetime
import glob
import re
import os
import sys
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# 导入拆分后的模块
from privacy_guard import PrivacyGuard
from gds_tester import GDSTester
from openai_analyzer import OpenAIAnalyzer
from report_generator import ReportGenerator
from chat_utils import find_chat_files_by_name, load_multiple_chat_files

# ===========================
# 主程序
# ===========================

def main(name: str = None, user_id: str = "anonymous", analysis_mode: str = "openai"):
    """
    主函数：完整的聊天记录分析和GDS评估流程
    
    执行步骤：
    1. 查找聊天记录：根据用户名查找对应的JSON文件
    2. 加载数据：读取聊天记录并进行基本统计
    3. 隐私脱敏：使用PrivacyGuard移除敏感信息，生成匿名化数据
    4. 智能分析：调用LLM（OpenAI/DeepSeek）分析聊天内容，模拟GDS问卷回答
    5. 计算得分：根据分析结果计算GDS总分和抑郁等级
    6. 生成报告：生成包含建议的详细评估报告
    7. 安全清理：彻底清除所有临时文件和内存数据，保护隐私
    """
    print("=" * 70)
    print("🧠 老年抑郁智能评估系统")
    print("=" * 70)
    
    # 记录开始时间
    start_time = datetime.datetime.now()
    
    # 1. 查找聊天记录文件
    print("\n🔍 第1步：查找聊天记录文件")
    chat_file_paths = find_chat_files_by_name(name)
    
    if not chat_file_paths:
        print("\n❌ 未找到任何有效的聊天记录文件，程序终止")
        print("💡 请确保：")
        print("   1. 创建 'example' 目录")
        print("   2. 将聊天记录JSON文件放入该目录")
        print("   3. 文件格式应为包含sender和message字段的消息列表")
        return
    
    # 2. 加载聊天记录
    print("\n📂 第2步：加载聊天记录")
    try:
        raw_chat = load_multiple_chat_files(chat_file_paths, name)
        
        if not raw_chat:
            print("\n❌ 未加载到任何有效聊天记录，程序终止")
            return
            
        print(f"\n✅ 成功加载 {len(raw_chat)} 条聊天记录")
        
        # 显示统计信息
        users = {}
        for msg in raw_chat:
            sender = msg.get('sender', '未知用户')
            users[sender] = users.get(sender, 0) + 1
        
        print("\n📊 用户统计：")
        for user, count in users.items():
            print(f"   👤 {user}: {count} 条消息")
            
    except Exception as e:
        print(f"\n❌ 加载聊天记录失败：{str(e)}")
        return
    
    # 3. 匿名化处理
    print("\n🔒 第3步：匿名化处理")
    privacy_guard = PrivacyGuard()
    anonymized_chat = privacy_guard.anonymize_chat(raw_chat)    #匿名化处理聊天记录
    print("✅ 聊天记录已匿名化处理")
    
    # 可视化匿名化对比（仅展示有变化的记录）
    print("\n📊 匿名化成果可视化（原文/密文对比，仅展示有变化记录）：")
    comparison_count = 0
    for raw_msg, anon_msg in zip(raw_chat, anonymized_chat):
        raw_content = raw_msg.get('message', '')
        anon_content = anon_msg.get('message', '')
        if raw_content != anon_content:
            comparison_count += 1
            print(f"\n对比示例 {comparison_count}:(原文) {raw_content}\n(密文) {anon_content}")
            if comparison_count >= 5:
                break
    if comparison_count == 0:
        print("ℹ️ 所有消息内容匿名化后无变化")
    
    # 将匿名化处理的聊天记录保存到xinli_temp.json
    # 注意：这是临时文件，后续会被清空
    print("\n💾 保存匿名化数据到xinli_temp.json")
    try:
        with open('xinli_temp.json', 'w', encoding='utf-8') as f:
            json.dump(anonymized_chat, f, ensure_ascii=False, indent=2)
        print(f"✅ 匿名化数据已保存到xinli_temp.json，共{len(anonymized_chat)}条记录")

        # 验证保存的密文数据
        print("\n🔍 验证保存的密文数据...")
        with open('xinli_temp.json', 'r', encoding='utf-8') as f:
            saved_chat = json.load(f)
        if saved_chat and saved_chat[0].get('message'):
            print("✅ 密文数据读取成功，字段验证通过")
        else:
            print("⚠️ 警告：密文数据字段可能异常，请检查文件内容")
    except Exception as e:
        print(f"❌ 保存/读取匿名化数据失败：{e}")
    
    # 4. 分析聊天记录（仅使用OpenAI）
    print("\n🤖 第4步：分析聊天记录")
    tester = GDSTester()
    responses = []
    
    # 从xinli_temp.json读取匿名化数据
    try:
        with open('xinli_temp.json', 'r', encoding='utf-8') as f:
            anonymized_chat = json.load(f)
        print(f"✅ 已从xinli_temp.json读取{len(anonymized_chat)}条匿名化记录")
    except Exception as e:
        print(f"❌ 读取xinli_temp.json失败：{e}")
        return
    
    print("🔄 使用OpenAI API分析...")
    openai_analyzer = OpenAIAnalyzer()
    ai_pairs = openai_analyzer.analyze_chat(anonymized_chat, tester.gds_questions)
    if ai_pairs:
        responses = [{"question": q, "answer": ans, "reason": reason} for (ans, reason), q in zip(ai_pairs, tester.gds_questions)]
        style_analysis = {"method": "OpenAI API", "model": getattr(openai_analyzer, "model", "unknown")}
        print("✅ OpenAI API分析完成")
    else:
        print("⚠️ OpenAI API调用失败，改用本地模拟分析")
        style = tester.analyze_chat_style(anonymized_chat)
        responses = [(q, tester.simulate_response(q, style)) for q in tester.gds_questions]
        style_analysis = {"method": "Local simulation", "model": "heuristics"}
    
    # 5. 计算得分并生成报告
    print("\n📋 第5步：计算得分并生成报告")
    score, level, reasoning = tester.calculate_score([r["answer"] for r in responses])
    
    report = ReportGenerator.generate_report(
        user_id=user_id,
        score=score,
        level=level,
        responses=responses,
        style_analysis=style_analysis
    )
    
    # 6. 保存报告
    print("\n💾 第6步：保存报告")
    report_file = f"gds_report_{user_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"✅ 报告已保存：{os.path.abspath(report_file)}")
    except Exception as e:
        print(f"❌ 保存报告失败：{e}")
    
    # 7. 安全清理
    print("\n🧹 第7步：安全清理")
    cleanup_data = {
        'chat_data': anonymized_chat, 
        'responses': responses,
        'analysis': style_analysis
    }
    privacy_guard.secure_cleanup(cleanup_data)

    # 清空xinli_temp.json防止泄露
    # 安全关键步骤：确保临时文件不包含敏感数据
    print("\n🔐 正在清空临时数据文件 xinli_temp.json")
    temp_file_path = "xinli_temp.json"
    try:
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.truncate(0)
        print("✅ xinli_temp.json 已安全清空")
    except Exception as e:
        print(f"❌ 清空临时文件失败：{str(e)}")
    
    # 8. 结果总结
    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "=" * 70)
    print("📋 评估完成总结")
    print("=" * 70)
    print(f"🎯 GDS-30总分: {score}/30分")
    print(f"📊 抑郁程度: {level}")
    print(f"🔍 分析方法: {style_analysis.get('method')}")
    print(f"⏱️  处理时间: {duration:.1f}秒")
    print(f"💾 报告文件: {report_file}")
    print("=" * 70)

# ===========================
# 程序入口
# ===========================

if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        user_name = sys.argv[1]
        mode = sys.argv[2] if len(sys.argv) > 2 else "openai"
        main(name=user_name, analysis_mode=mode)
    else:
        # 交互式模式
        print("\n🎯 欢迎使用老年抑郁智能评估系统")
        print("-" * 50)
        
        user_name = input("请输入要分析的姓名: ").strip()
        
        # 运行主程序（仅使用OpenAI）
        main(
            name=user_name if user_name else None,
            user_id=user_name or "anonymous",
            analysis_mode="openai"
        )
