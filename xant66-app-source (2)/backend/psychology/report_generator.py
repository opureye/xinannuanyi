# report_generator.py
import sys
import os
import logging
import datetime  # 添加datetime模块导入
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目工具
from backend.utils.logger import get_logger

# 初始化日志器
logger = get_logger('psychology_report')

class ReportGenerator:
    """
    GDS-30心理评估报告生成器
    
    该类负责：
    1. 维护GDS-30量表的建议库（advice_map）
    2. 根据用户的回答生成针对性的健康建议
    3. 汇总得分、等级、建议，生成完整的JSON格式报告
    """
    
    # GDS-30问题建议映射表
    # 键：问题编号 (1-30)
    # 值：包含"是"和"否"两种回答对应的专业建议
    advice_map = {
        1: {
            "是": "建议建立规律的日常活动，每天设定小目标，增加生活的节奏感和成就感。",
            "否": "保持积极的生活态度，继续关注生活中的美好事物。"
        },
        2: {
            "是": "尝试每天进行短暂的散步或轻度运动，研究表明身体活动可以改善情绪。",
            "否": "保持良好的身体状态，继续当前的活动习惯。"
        },
        3: {
            "是": "建议尝试放松技巧，如深呼吸、冥想或渐进性肌肉松弛，有助于缓解焦虑。",
            "否": "保持乐观的心态，继续积极面对生活中的挑战。"
        },
        4: {
            "是": "考虑参与社区活动或兴趣小组，增加社交互动的机会。",
            "否": "保持活跃的社交生活，继续与亲友保持联系。"
        },
        5: {
            "是": "建议设定合理的饮食计划，保证充足的营养摄入，特别是富含Omega-3的食物。",
            "否": "保持健康的饮食习惯，继续关注营养均衡。"
        },
        6: {
            "是": "尝试每天记录一件值得感恩的事情，培养积极思维模式。",
            "否": "保持对生活的感恩之心，继续发现生活中的美好。"
        },
        7: {
            "是": "建议与家人或朋友分享内心感受，寻求情感支持。",
            "否": "保持良好的情绪管理能力，继续积极面对生活。"
        },
        8: {
            "是": "考虑咨询专业心理咨询师，获取更专业的帮助和建议。",
            "否": "保持积极的生活态度，继续享受生活。"
        },
        9: {
            "是": "建议尝试新的兴趣爱好，转移注意力，丰富生活内容。",
            "否": "保持多样化的兴趣爱好，继续享受丰富多彩的生活。"
        },
        10: {
            "是": "考虑调整作息时间，建立规律的睡眠习惯，创造良好的睡眠环境。",
            "否": "保持良好的睡眠习惯，继续享受高质量的休息。"
        },
        11: {
            "是": "建议与医生讨论可能的身体不适，排除生理因素对情绪的影响。",
            "否": "保持定期体检的习惯，关注身体健康。"
        },
        12: {
            "是": "尝试设定短期可实现的目标，逐步恢复自信和动力。",
            "否": "保持积极的自我认知，继续发挥个人优势。"
        },
        13: {
            "是": "建议学习应对压力的技巧，如时间管理、问题解决策略等。",
            "否": "保持良好的压力管理能力，继续应对生活中的各种挑战。"
        },
        14: {
            "是": "考虑参加支持小组，与有类似经历的人交流，获得理解和支持。",
            "否": "保持良好的社交网络，继续与他人建立积极的联系。"
        },
        15: {
            "是": "建议尝试正念冥想，帮助活在当下，减少负面思维。",
            "否": "保持平和的心态，继续享受当前的生活状态。"
        },
        16: {
            "是": "考虑调整饮食结构，增加富含色氨酸的食物，有助于改善情绪。",
            "否": "保持健康的饮食习惯，继续关注营养均衡。"
        },
        17: {
            "是": "建议与家人一起参与活动，增强家庭凝聚力和支持系统。",
            "否": "保持良好的家庭关系，继续享受家庭带来的温暖。"
        },
        18: {
            "是": "尝试培养兴趣爱好，让生活更加充实和有意义。",
            "否": "保持对生活的热情，继续追求自己的兴趣爱好。"
        },
        19: {
            "是": "建议学习放松技巧，如听轻音乐、泡热水澡等，缓解紧张情绪。",
            "否": "保持良好的情绪调节能力，继续积极面对生活。"
        },
        20: {
            "是": "考虑咨询专业人士，获取更个性化的建议和治疗方案。",
            "否": "保持积极的生活态度，继续享受生活的美好。"
        },
        21: {
            "是": "建议尝试认知行为疗法的自助技巧，挑战负面思维模式。",
            "否": "保持理性的思维方式，继续用积极的视角查看问题。"
        },
        22: {
            "是": "尝试每天进行户外活动，接触阳光，有助于改善情绪。",
            "否": "保持良好的生活习惯，继续享受大自然的美好。"
        },
        23: {
            "是": "建议与朋友保持定期联系，分享生活点滴，获得情感支持。",
            "否": "保持活跃的社交生活，继续与朋友保持良好的关系。"
        },
        24: {
            "是": "考虑参与志愿者活动，帮助他人的同时提升自我价值感。",
            "否": "保持乐于助人的品质，继续为社会做出贡献。"
        },
        25: {
            "是": "建议学习时间管理技巧，合理安排日常活动，避免过度压力。",
            "否": "保持良好的生活节奏，继续高效地安排时间。"
        },
        26: {
            "是": "尝试培养幽默感，通过笑来缓解压力，改善情绪。",
            "否": "保持乐观开朗的性格，继续用幽默面对生活。"
        },
        27: {
            "是": "建议与家人坦诚沟通，表达内心需求，寻求理解和支持。",
            "否": "保持良好的家庭沟通，继续维护和谐的家庭关系。"
        },
        28: {
            "是": "考虑尝试艺术疗法，如绘画、音乐等，表达内心感受。",
            "否": "保持对艺术的欣赏，继续丰富精神生活。"
        },
        29: {
            "是": "建议设定合理的期望值，避免过度自我要求，接受不完美。",
            "否": "保持平和的心态，继续理性地面对生活中的各种情况。"
        },
        30: {
            "是": "尝试回顾过去的成就和美好回忆，增强自我价值感和生活信心。",
            "否": "保持积极的自我认知，继续珍惜生活中的每一刻。"
        }
    }

    def __init__(self):
        """初始化报告生成器"""
        logger.info("ReportGenerator初始化成功")

    @staticmethod
    def get_question_specific_advice(question_number: int, answer: str) -> str:
        """获取特定问题的建议"""
        try:
            advice = ReportGenerator.advice_map.get(question_number, {}).get(answer, "")
            logger.debug(f"获取问题{question_number}的建议，回答：{answer}，建议：{advice}")
            return advice
        except Exception as e:
            logger.error(f"获取问题{question_number}的建议时出错: {str(e)}")
            return ""

    @staticmethod
    def generate_report(
        user_id: str,
        score: int,
        level: str,
        responses: List[Dict[str, str]],
        style_analysis: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        生成完整的心理评估报告
        
        Args:
            user_id: 用户ID或姓名
            score: GDS-30总分
            level: 抑郁等级（正常/轻度抑郁/中重度抑郁）
            responses: 详细的问题回答列表
            style_analysis: 分析方法的元数据
            
        Returns:
            Dict: 包含完整报告信息的字典
        """
        try:
            logger.info(f"开始生成心理评估报告，用户ID: {user_id}，得分: {score}，抑郁程度: {level}")
            
            # 准备报告内容结构
            report = {
                "user_id": user_id,
                "assessment_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "score": score,
                "depression_level": level,
                "analysis_method": style_analysis.get("method", "未知"),
                "model": style_analysis.get("model", "未知"),
                "responses": [],
                "summary": "",
                "recommendations": []
            }
            
            # 处理每个问题的回答和建议
            for i, response in enumerate(responses):
                question_number = i + 1
                # 根据回答查找对应的建议
                advice = ReportGenerator.get_question_specific_advice(question_number, response.get("answer", ""))
                
                report["responses"].append({
                    "question_number": question_number,
                    "question": response.get("question", f"问题{question_number}"),
                    "answer": response.get("answer", "未知"),
                    "reason": response.get("reason", "无"),
                    "advice": advice
                })
                
                # 如果有建议，添加到总体建议中
                if advice:
                    report["recommendations"].append(advice)
            
            # 根据抑郁等级生成总体总结
            if level == "正常":
                report["summary"] = "评估结果显示您的心理状态良好。建议继续保持健康的生活方式和积极的心态，定期关注自己的情绪变化。"
            elif level == "轻度抑郁":
                report["summary"] = "评估结果显示您可能存在轻度抑郁倾向。建议尝试调整生活方式，增加社交活动，培养兴趣爱好，如症状持续，可考虑咨询专业心理咨询师。"
            elif level == "中重度抑郁":
                report["summary"] = "评估结果显示您可能存在中重度抑郁倾向。建议尽快咨询专业心理医生或精神科医生，获取更专业的帮助和治疗方案。同时，家人的理解和支持也非常重要。"
            else:
                report["summary"] = "评估已完成，请结合专业医生的建议进行进一步的诊断和治疗。"
            
            # 添加通用建议
            if level != "正常":
                report["recommendations"].extend([
                    "保持规律的作息时间，确保充足的睡眠",
                    "进行适度的身体活动，如散步、太极等",
                    "保持健康的饮食习惯，多吃蔬菜水果",
                    "尝试放松技巧，如深呼吸、冥想等",
                    "与亲友保持良好的沟通，寻求情感支持"
                ])
            
            logger.info(f"心理评估报告生成完成，包含{len(report['responses'])}个问题的回答和{len(report['recommendations'])}条建议")
            return report
        except Exception as e:
            logger.error(f"生成心理评估报告时出错: {str(e)}")
            # 返回基础报告，即使出错也能提供部分信息
            return {
                "user_id": user_id,
                "assessment_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "score": score,
                "depression_level": level,
                "error": str(e),
                "summary": "报告生成过程中出现错误，请稍后重试"
            }