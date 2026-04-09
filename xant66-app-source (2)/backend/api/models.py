# 所有API请求和响应模型定义
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# 基础模型
class Message(BaseModel):
    role: str = Field(..., description="消息角色，'user'或'assistant'")
    content: str = Field(..., description="消息内容")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="错误信息")
    code: str = Field(..., description="错误代码")

class SearchRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")

class SearchResponse(BaseModel):
    success: bool = Field(..., description="搜索是否成功")
    results: List[Dict[str, Any]] = Field([], description="搜索结果")
    message: str = Field(..., description="提示消息")

# 聊天相关模型
class ChatCompletionRequest(BaseModel):
    messages: List[Message] = Field(..., description="消息列表")
    model: str = Field("deepseek-chat", description="使用的模型名称")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="生成温度")
    max_tokens: int = Field(1024, ge=1, le=4096, description="最大生成令牌数")
    stream: bool = Field(False, description="是否启用流式响应")

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="用户输入的提示文本")
    model: str = Field("deepseek-chat", description="使用的模型名称")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="生成温度")
    max_tokens: int = Field(1024, ge=1, le=4096, description="最大生成令牌数")

class GenerateResponse(BaseModel):
    response: str = Field(..., description="AI生成的响应内容")
    model: str = Field(..., description="使用的模型")
    timestamp: str = Field(..., description="响应时间戳")

# 认证相关模型
class LoginRequest(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class LoginResponse(BaseModel):
    success: bool = Field(..., description="登录是否成功")
    role: Optional[str] = Field(None, description="用户角色")
    message: Optional[str] = Field(None, description="提示消息")
    token: Optional[str] = Field(None, description="会话令牌")
    access_token: Optional[str] = Field(None, description="访问令牌")
    token_type: Optional[str] = Field(None, description="令牌类型")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    is_admin: Optional[bool] = Field(None, description="是否为管理员")

class RegisterRequest(BaseModel):
    username: str = Field(..., description="用户名")
    phone: str = Field(..., description="手机号码")
    email: str = Field(..., description="电子邮箱")
    password: str = Field(..., description="密码")
    # 可选：前端在实名成功后携带，用于写入数据库
    real_name: Optional[str] = Field(None, description="真实姓名")
    id_number: Optional[str] = Field(None, description="身份证号")

class RegisterResponse(BaseModel):
    success: bool = Field(..., description="注册是否成功")
    message: str = Field(..., description="提示消息")

# 实名核验相关模型
class RealNameVerifyRequest(BaseModel):
    name: str = Field(..., description="真实姓名")
    id_number: str = Field(..., description="身份证号")

class IdentityVerifyResponse(BaseModel):
    success: bool = Field(..., description="核验是否通过")
    message: str = Field(..., description="提示消息")
    provider: Optional[str] = Field(None, description="核验提供方，如Tencent或local")
    detail: Optional[Dict[str, Any]] = Field(None, description="额外核验信息")

# 用户相关模型
class UserResponse(BaseModel):
    user_id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="电子邮箱")
    phone: str = Field("", description="手机号码")  # 添加phone字段，默认为空字符串
    created_at: str = Field(..., description="创建时间")
    role: str = Field("使用者", description="用户角色")  # 添加role字段，默认为"使用者"
    is_admin: bool = Field(False, description="是否为管理员")
    is_banned: bool = Field(False, description="是否被封禁")
    avatar: Optional[str] = Field(None, description="头像URL")

class UserListResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    users: List[UserResponse] = Field([], description="用户列表")
    total: int = Field(..., description="用户总数")
    page: Optional[int] = Field(1, description="当前页码")
    page_size: Optional[int] = Field(10, description="每页大小")
    message: str = Field(..., description="提示消息")

class UserProfileResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    user_info: Optional[Dict[str, Any]] = Field(None, description="用户资料信息")
    message: str = Field(..., description="提示消息")

class UpdateProfileRequest(BaseModel):
    bio: Optional[str] = Field(None, description="个人签名")
    email: Optional[str] = Field(None, description="电子邮箱")
    phone: Optional[str] = Field(None, description="手机号码")
    avatar: Optional[str] = Field(None, description="头像URL")
    gender: Optional[str] = Field(None, description="性别")
    birthday: Optional[str] = Field(None, description="出生日期，格式YYYY-MM-DD")

class UpdateProfileResponse(BaseModel):
    success: bool = Field(..., description="更新是否成功")
    message: str = Field(..., description="提示消息")

class UserPostsResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    posts: List[Dict[str, Any]] = Field([], description="用户帖子列表")
    total: int = Field(..., description="帖子总数")
    message: str = Field(..., description="提示消息")

class UserCollectionsResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    collections: List[Dict[str, Any]] = Field([], description="用户收藏列表")
    total: int = Field(..., description="收藏总数")
    message: str = Field(..., description="提示消息")

# 管理员相关模型
class DeactivateUserRequest(BaseModel):
    username: str = Field(..., description="要停用的用户名")

class DeactivateUserResponse(BaseModel):
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="提示消息")

class UserStatusRequest(BaseModel):
    username: str = Field(..., description="用户名")

class SearchUsersRequest(BaseModel):
    keyword: str = Field(..., description="搜索关键词")
    page: Optional[int] = Field(1, description="当前页码")
    page_size: Optional[int] = Field(10, description="每页大小")

class SearchUsersResponse(BaseModel):
    success: bool = Field(..., description="搜索是否成功")
    users: List[UserResponse] = Field([], description="搜索到的用户列表")
    total: int = Field(..., description="用户总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    message: str = Field(..., description="提示消息")

class AuditArticleRequest(BaseModel):
    status: str = Field(..., description="审核状态（'approved' 或 'rejected'）")
    reason: Optional[str] = Field(None, description="审核原因")

# 用户收藏和成就相关模型
class CollectionItem(BaseModel):
    collection_id: int = Field(..., description="收藏ID")
    item_id: int = Field(..., description="收藏项ID")
    item_type: str = Field(..., description="收藏项类型")
    title: str = Field(..., description="收藏项标题")
    created_at: str = Field(..., description="收藏时间")

class AchievementResponse(BaseModel):
    achievement_id: int = Field(..., description="成就ID")
    name: str = Field(..., description="成就名称")
    description: str = Field(..., description="成就描述")
    unlocked: bool = Field(..., description="是否已解锁")
    unlocked_at: Optional[str] = Field(None, description="解锁时间")

class AchievementsResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    achievements: List[AchievementResponse] = Field([], description="成就列表")
    total: int = Field(..., description="成就总数")
    unlocked_count: int = Field(..., description="已解锁成就数")
    message: str = Field(..., description="提示消息")

# 文章相关模型
class PendingArticlesResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    articles: List[Dict[str, Any]] = Field([], description="待审核文章列表")
    total: int = Field(..., description="待审核文章总数")
    message: str = Field(..., description="提示消息")

class ArticleAuditResponse(BaseModel):
    success: bool = Field(..., description="审核操作是否成功")
    message: str = Field(..., description="审核结果消息")

class SubmitArticleRequest(BaseModel):
    title: str = Field(..., description="文章标题")
    category: str = Field(..., description="文章分类")
    content: str = Field(..., description="文章内容")

class SubmitArticleResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    article_id: Optional[int] = Field(None, description="新创建的文章ID")
    message: str = Field(..., description="提示消息")

class ArticleResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    article_id: Optional[int] = Field(None, description="文章ID")
    title: Optional[str] = Field(None, description="文章标题")
    content: Optional[str] = Field(None, description="文章内容")
    category: Optional[str] = Field(None, description="文章分类")
    created_at: Optional[str] = Field(None, description="创建时间")
    status: Optional[str] = Field(None, description="文章状态")
    message: str = Field(..., description="提示消息")