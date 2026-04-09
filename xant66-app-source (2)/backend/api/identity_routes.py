import logging
import json
import os
from fastapi import APIRouter, HTTPException, status
from typing import Dict

from .models import RealNameVerifyRequest, IdentityVerifyResponse, ErrorResponse
from backend.config import settings

logger = logging.getLogger('identity_routes')

identity_router = APIRouter(
    prefix="/identity",
    tags=["identity"],
    responses={404: {"description": "未找到"}}
)


def _check_china_id(id_number: str) -> bool:
    """简单的中国身份证号码校验：长度、格式与校验码。"""
    if not isinstance(id_number, str):
        return False
    id_number = id_number.strip().upper()
    if len(id_number) != 18:
        return False
    if not id_number[:17].isdigit():
        return False
    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_map = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
    total = sum(int(n) * w for n, w in zip(id_number[:17], weights))
    check = check_map[total % 11]
    return id_number[-1] == check


@identity_router.post(
    "/verify",
    response_model=IdentityVerifyResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def verify_identity(req: RealNameVerifyRequest):
    try:
        name = req.name.strip()
        id_no = req.id_number.strip().upper()

        if not name or not id_no:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="姓名或身份证号不能为空")

        # 当启用腾讯云时，优先调用腾讯云接口，让其判定有效性；
        # 未启用腾讯云时，使用本地校验码作为门槛。
        if not settings.enable_tencent_identity_verify:
            # 基础身份证格式与校验码校验（本地模式）
            if not _check_china_id(id_no):
                logger.info("身份证校验码不通过")
                raw_fail = {"provider": "local", "error": "invalid_id", "name": name, "id_number": id_no}
                # 记录原始JSON
                logger.info(f"实名核验返回原始JSON: {json.dumps(raw_fail, ensure_ascii=False)}")
                return IdentityVerifyResponse(success=False, message="身份证号码格式或校验码无效", provider="local", detail={"raw": raw_fail})

        # 若启用腾讯云，则在此处对接腾讯云实名核验（Cloud Market API）
        if settings.enable_tencent_identity_verify:
            # 读取密钥（优先环境变量，其次配置文件）
            secret_id = os.getenv("TENCENTCLOUD_SECRET_ID") or settings.tencentcloud_secret_id
            secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY") or settings.tencentcloud_secret_key
            
            if not secret_id or not secret_key:
                logger.error("启用了腾讯云实名核验，但未配置密钥")
                # 调试模式下降级为本地校验，避免阻塞注册流程
                if settings.debug:
                    logger.warning("调试模式开启，腾讯云密钥缺失，降级到本地校验")
                    if not _check_china_id(id_no):
                        raw_fail = {"provider": "local-fallback", "error": "invalid_id", "name": name, "id_number": id_no}
                        logger.info(f"实名核验返回原始JSON: {json.dumps(raw_fail, ensure_ascii=False)}")
                        return IdentityVerifyResponse(success=False, message="身份证号码格式或校验码无效", provider="local-fallback", detail={"raw": raw_fail})
                    raw_ok = {"provider": "local-fallback", "format_valid": True, "name": name, "id_number": id_no}
                    logger.info(f"实名核验返回原始JSON: {json.dumps(raw_ok, ensure_ascii=False)}")
                    return IdentityVerifyResponse(success=True, message="本地校验通过（调试模式降级）", provider="local-fallback", detail={"raw": raw_ok})
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="腾讯云密钥未配置，请设置 TENCENTCLOUD_SECRET_ID/TENCENTCLOUD_SECRET_KEY")

            try:
                import requests
                import hmac
                import hashlib
                import base64
                import datetime
                
                # 构造请求
                url = "https://ap-beijing.cloudmarket-apigw.com/service-hcgajsa5/idcard/VerifyIdcardv2"
                
                # 生成签名
                # 获取当前GMT时间
                datetime_gmt = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                
                # 签名串: x-date: {date} (注意：不包含x-source)
                sign_str = f"x-date: {datetime_gmt}"
                
                # HmacSHA1签名
                sign = base64.b64encode(
                    hmac.new(secret_key.encode('utf-8'), sign_str.encode('utf-8'), hashlib.sha1).digest()
                ).decode('utf-8')
                
                # 构造Authorization Header (JSON格式)
                auth_header = json.dumps({
                    "id": secret_id,
                    "x-date": datetime_gmt,
                    "signature": sign
                })
                
                headers = {
                    "Authorization": auth_header,
                    # "x-source": "market", # 不需x-source
                    "Content-Type": "application/x-www-form-urlencoded"
                }
                
                params = {
                    "cardNo": id_no,
                    "realName": name
                }
                
                logger.info(f"调用腾讯云市场实名核验API: {url}")
                
                # 发起请求
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response_data = response.json()
                
                logger.info(f"实名核验返回原始JSON: {json.dumps(response_data, ensure_ascii=False)}")
                
                # 解析结果
                # 成功示例: {"error_code": 0, "reason": "Success", "result": {"isok": true, ...}}
                # 失败示例: {"error_code": 206501, ...}
                
                error_code = response_data.get("error_code")
                
                matched = False
                msg = "实名认证失败"
                
                if error_code == 0:
                    result = response_data.get("result", {})
                    if isinstance(result, dict):
                        isok = result.get("isok", False)
                        if isok:
                            matched = True
                            msg = "实名认证通过"
                        else:
                            matched = False
                            msg = "实名认证不一致"
                else:
                    reason = response_data.get("reason", "Unknown Error")
                    msg = f"实名认证服务错误: {reason}"
                    logger.warning(f"实名认证服务返回错误码: {error_code}, 原因: {reason}")

                detail: Dict = {"matched": matched, "raw": response_data}
                
                return IdentityVerifyResponse(
                    success=matched,
                    message=msg,
                    provider="TencentCloudMarket",
                    detail=detail
                )

            except Exception as err:
                logger.error(f"腾讯云实名核验异常: {str(err)}", exc_info=True)
                # 调试模式下降级为本地校验
                if settings.debug:
                    logger.warning("调试模式开启，腾讯云核验异常，降级到本地校验")
                    if not _check_china_id(id_no):
                        raw_fail = {"provider": "local-fallback", "error": "invalid_id", "name": name, "id_number": id_no}
                        logger.info(f"实名核验返回原始JSON: {json.dumps(raw_fail, ensure_ascii=False)}")
                        return IdentityVerifyResponse(success=False, message="身份证号码格式或校验码无效", provider="local-fallback", detail={"raw": raw_fail})
                    raw_ok = {"provider": "local-fallback", "format_valid": True, "name": name, "id_number": id_no}
                    logger.info(f"实名核验返回原始JSON: {json.dumps(raw_ok, ensure_ascii=False)}")
                    return IdentityVerifyResponse(success=True, message="本地校验通过（调试模式降级）", provider="local-fallback", detail={"raw": raw_ok})
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"腾讯云实名核验失败: {str(err)}")

        # 未启用腾讯云时，使用本地身份证校验通过作为最低门槛
        logger.info("未启用腾讯云实名核验，使用本地校验通过")
        raw_local = {"provider": "local", "format_valid": True, "name": name, "id_number": id_no}
        detail = {"format_valid": True, "raw": raw_local}
        # 记录原始JSON
        logger.info(f"实名核验返回原始JSON: {json.dumps(raw_local, ensure_ascii=False)}")
        return IdentityVerifyResponse(success=True, message="本地校验通过（未启用腾讯云）", provider="local", detail=detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"实名核验发生错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="实名核验服务异常")
