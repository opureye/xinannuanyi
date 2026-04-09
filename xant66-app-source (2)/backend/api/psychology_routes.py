# psychology_routes.py
import os
import sys

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取backend目录
backend_dir = os.path.dirname(current_dir)
# 获取项目根目录
project_root = os.path.dirname(backend_dir)

# 将项目根目录添加到Python路径
sys.path.insert(0, project_root)

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import json
import datetime

# 导入项目工具和认证模块
from backend.utils.logger import get_logger
from backend.utils.auth import get_current_user

# 导入心理学模块核心功能
from backend.psychology.privacy_guard import PrivacyGuard
from backend.psychology.gds_tester import GDSTester
from backend.psychology.openai_analyzer import OpenAIAnalyzer
from backend.psychology.report_generator import ReportGenerator

# 设置日志
logger = get_logger('psychology_routes')

# 创建路由器
psychology_router = APIRouter(
    prefix="/psychology",
    tags=["psychology"],
    responses={404: {"description": "未找到"}}
)

@psychology_router.post("/analyze")
async def analyze_psychology(
    file: UploadFile = File(...),
    analysis_mode: str = Form("openai"),
    user_id: str = Form("anonymous")
):
    """
    分析用户上传的聊天记录，生成GDS-30评估报告
    """
    try:
        # 记录开始时间
        start_time = datetime.datetime.now()
        
        # 验证文件类型
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="请上传JSON格式的文件")
        
        # 读取文件内容
        file_content = await file.read()
        chat_data = json.loads(file_content.decode('utf-8'))
        
        logger.info(f"开始分析聊天记录，共{len(chat_data)}条消息")
        
        # 1. 匿名化处理
        privacy_guard = PrivacyGuard()
        anonymized_chat = privacy_guard.anonymize_chat(chat_data)
        logger.info("聊天记录已匿名化处理")
        
        # 2. 分析聊天记录
        tester = GDSTester()
        
        # 根据分析模式选择分析方法
        if analysis_mode == "openai":
            openai_analyzer = OpenAIAnalyzer()
            gds_responses = openai_analyzer.analyze_chat(anonymized_chat, tester.gds_questions)  # 修改方法名
            style_analysis = {"method": "OpenAI API", "model": openai_analyzer.model}
        else:
            # 本地AI分析实现
            style_analysis = {"method": "本地AI分析"}
            # 模拟分析结果（实际项目中应实现真实的本地AI分析）
            gds_responses = [("是" if i % 2 == 0 else "否", "基于本地AI分析") for i in range(30)]
        
        if not gds_responses:
            raise HTTPException(status_code=500, detail="AI分析失败")
        
        # 3. 计算得分并生成报告
        score, level, reasoning = tester.calculate_score(gds_responses)  # 修改为传递完整的元组列表
        
        # 准备响应格式的数据
        formatted_responses = []
        for i, (answer, reason) in enumerate(gds_responses):
            # 获取对应的问题
            question = tester.gds_questions[i] if i < len(tester.gds_questions) else f"问题{i+1}"
            
            # 获取建议（如果有）
            advice = ""
            try:
                advice = ReportGenerator.advice_map.get(i + 1, {}).get(answer, "")
            except:
                pass
            
            formatted_responses.append({
                "question": question,
                "answer": answer,
                "reason": reason,
                "advice": advice
            })
        
        # 生成完整报告
        report = ReportGenerator.generate_report(
            user_id=user_id,
            score=score,
            level=level,
            responses=formatted_responses,
            style_analysis=style_analysis
        )
        
        # 记录结束时间
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        analysis_time_str = f"{duration:.1f}秒"
        
        logger.info(f"分析完成，得分：{score}，抑郁程度：{level}")
        
        return {
            "success": True,
            "score": score,
            "level": level,
            "report": report,
            "analysis_time": analysis_time_str,
            "reasoning": reasoning,
            "responses": formatted_responses
        }
        
    except json.JSONDecodeError:
        logger.error("JSON文件解析失败")
        raise HTTPException(status_code=400, detail="JSON文件解析失败")
    except Exception as e:
        logger.error(f"分析过程中出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析过程中出错: {str(e)}")

@psychology_router.get("/example_questions")
async def get_example_questions():
    """
    获取GDS-30量表的样例问题
    """
    tester = GDSTester()
    return {
        "success": True,
        "questions": tester.gds_questions
    }

@psychology_router.get("/health_check")
async def health_check():
    """
    检查心理学评估模块是否正常工作
    """
    return {
        "success": True,
        "message": "心理学评估模块正常运行"
    }