# chat_utils.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天记录工具模块
提供查找和加载聊天记录文件的功能
"""

import json
import glob
import os
from typing import Dict, List, Any

def find_chat_files_by_name(name: str = None) -> List[str]:
    """
    查找指定用户的聊天记录文件
    支持模糊匹配和精确匹配
    
    Args:
        name: 要查找的用户名，如果为None则返回所有文件
        
    Returns:
        匹配的文件路径列表
    
    逻辑：
    1. 扫描 'example' 目录下的所有JSON文件
    2. 如果未指定用户名，返回所有文件
    3. 如果指定了用户名，读取每个文件并检查其中是否包含该用户的发言
    4. 如果找不到匹配文件，会列出所有可用的用户名供参考
    """
    # 查找所有JSON文件
    json_files = []
    example_dir = os.path.join(os.getcwd(), 'example')
    
    if os.path.exists(example_dir):
        json_files.extend(glob.glob(os.path.join(example_dir, '*.json')))
    
    if not json_files:
        print("❌ 未找到任何聊天记录文件")
        return []
    
    if not name:
        return json_files
    
    # 严格匹配：完全相同的用户名
    target_name = name.strip()
    matched_files = []
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
                
            if not isinstance(chat_data, list):
                continue
            
            # 严格匹配：完全相同的用户名
            # 只要文件中有一条消息是该用户发送的，就认为该文件有效
            has_exact_match = any(
                msg.get('sender', '').strip() == target_name
                for msg in chat_data
            )
            
            if has_exact_match:
                matched_files.append(file_path)
                print(f"✅ 找到用户 '{target_name}' 的聊天记录: {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"⚠️ 读取文件失败: {os.path.basename(file_path)} - {str(e)}")
    
    if not matched_files:
        print(f"❌ 未找到用户 '{target_name}' 的聊天记录")
        
        # 列出所有可用用户名，帮助用户排查拼写错误
        all_users = set()
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    if isinstance(chat_data, list):
                        users = {msg.get('sender', '').strip() for msg in chat_data if msg.get('sender', '').strip()}
                        all_users.update(users)
            except:
                continue
        
        if all_users:
            print("📋 可用的用户名：")
            for user in sorted(all_users):
                print(f"   👤 {user}")
        
        return json_files
    
    return matched_files

def load_multiple_chat_files(file_paths: List[str], user_name: str = None) -> List[Dict[str, Any]]:
    """
    严格匹配：加载指定用户的聊天记录
    
    Args:
        file_paths: 要加载的文件路径列表
        user_name: 指定用户名，如果为None则加载所有用户的消息
        
    Returns:
        加载的聊天记录列表
    """
    all_chat_data = []
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
            
            if not isinstance(chat_data, list):
                print(f"⚠️ 跳过格式错误的文件: {os.path.basename(file_path)}")
                continue
            
            if user_name and user_name.strip():
                # 严格匹配：只加载完全匹配的用户消息
                target_name = user_name.strip()
                filtered_msgs = [
                    msg for msg in chat_data
                    if isinstance(msg, dict) and msg.get('sender', '').strip() == target_name
                ]
                
                if filtered_msgs:
                    # 为消息添加源文件信息
                    for msg in filtered_msgs:
                        msg['source_file'] = os.path.basename(file_path)
                    
                    all_chat_data.extend(filtered_msgs)
                    print(f"✅ 已加载 {len(filtered_msgs)} 条来自 '{target_name}' 的消息")
                else:
                    print(f"⚠️ 文件 {os.path.basename(file_path)} 中没有用户 '{target_name}' 的消息")
            else:
                # 加载所有用户的消息
                valid_msgs = []
                for msg in chat_data:
                    if isinstance(msg, dict) and 'sender' in msg and 'message' in msg:
                        msg['source_file'] = os.path.basename(file_path)
                        valid_msgs.append(msg)
                
                all_chat_data.extend(valid_msgs)
                print(f"✅ 已加载 {len(valid_msgs)} 条消息 (所有用户)")
                
        except Exception as e:
            print(f"❌ 加载文件失败: {os.path.basename(file_path)} - {str(e)}")
    
    # 按时间戳排序
    if all_chat_data and any('timestamp' in msg for msg in all_chat_data):
        try:
            all_chat_data.sort(key=lambda x: x.get('timestamp', ''))
        except:
            pass
    
    return all_chat_data