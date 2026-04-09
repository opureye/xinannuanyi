import logging
import os
from .db_users_core import ExtendedUserDatabase as UserDatabase  # 修复：从db_users_core导入正确的类
# 修改配置导入语句
# 从 .config import settings 改为正确的导入路径
import backend.config as config
settings = config.settings

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'initializer.log'),
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sample_users_initializer')

# 示例用户数据
SAMPLE_USERS = [
    {
        'username': '洪汉博',
        'password': '15157112180@Cuz',
        'email': 'HongshengyueJeff@163.com',
        'phone': '15157112180',
        'role': '管理员'
    },
    {
        'username': '石皓文',
        'password': '16630635068@Cuz',
        'email': '949548682@qq.com',
        'phone': '16630635068',
        'role': '管理员'
    },
    {
        'username': '张心泽',
        'password': '13031836967@Cuz',
        'email': '2262433476@qq.com',
        'phone': '13031836967',
        'role': '管理员'
    },
    {
        'username': '郑伊萍',
        'password': '15698781959@Cuz',
        'email': '1247213356@qq.com',
        'phone': '15698781959',
        'role': '管理员'
    },
    {
        'username': '笪媛媛',
        'password': '15150651579@Cuz',
        'email': '1339979388@qq.com',
        'phone': '15150651579',
        'role': '管理员'
    },
    {
        'username': '孟尚婉',
        'password': '15657126891@Cuz',
        'email': '3872465975@qq.com',
        'phone': '15657126891',
        'role': '使用者'
    },
    {
        'username': '陈宇轩',
        'password': '12345678901',
        'email': 'chenyuxuan@example.com',
        'phone': '12345678901',
        'role': '使用者'
    },
    {
        'username': '李明哲',
        'password': '12345678902',
        'email': 'limingzhe@example.com',
        'phone': '12345678902',
        'role': '使用者'
    },
    {
        'username': '王浩宇',
        'password': '12345678903',
        'email': 'wanghaoyu@example.com',
        'phone': '12345678903',
        'role': '使用者'
    },
    {
        'username': '刘嘉豪',
        'password': '12345678904',
        'email': 'liujiahao@example.com',
        'phone': '12345678904',
        'role': '使用者'
    },
    {
        'username': '张子轩',
        'password': '12345678905',
        'email': 'zhangzixuan@example.com',
        'phone': '12345678905',
        'role': '使用者'
    },
    {
        'username': '杨博文',
        'password': '12345678906',
        'email': 'yangbowen@example.com',
        'phone': '12345678906',
        'role': '使用者'
    },
    {
        'username': '黄俊凯',
        'password': '12345678907',
        'email': 'huangjunkai@example.com',
        'phone': '12345678907',
        'role': '使用者'
    },
    {
        'username': '吴泽宇',
        'password': '12345678908',
        'email': 'wuzeyu@example.com',
        'phone': '12345678908',
        'role': '使用者'
    },
    {
        'username': '周星辰',
        'password': '12345678909',
        'email': 'zhouxingchen@example.com',
        'phone': '12345678909',
        'role': '使用者'
    },
    {
        'username': '徐浩然',
        'password': '12345678910',
        'email': 'xuhaoran@example.com',
        'phone': '12345678910',
        'role': '使用者'
    },
    {
        'username': '孙嘉乐',
        'password': '12345678911',
        'email': 'sunjiale@example.com',
        'phone': '12345678911',
        'role': '使用者'
    },
    {
        'username': '马天宇',
        'password': '12345678912',
        'email': 'matianyu@example.com',
        'phone': '12345678912',
        'role': '使用者'
    },
    {
        'username': '朱梓晨',
        'password': '12345678913',
        'email': 'zuzichen@example.com',
        'phone': '12345678913',
        'role': '使用者'
    },
    {
        'username': '胡文杰',
        'password': '12345678914',
        'email': 'huwenjie@example.com',
        'phone': '12345678914',
        'role': '使用者'
    },
    {
        'username': '林泽宇',
        'password': '12345678915',
        'email': 'linzeyu@example.com',
        'phone': '12345678915',
        'role': '使用者'
    },
    {
        'username': '李雨桐',
        'password': '12345678916',
        'email': 'liyutong@example.com',
        'phone': '12345678916',
        'role': '使用者'
    },
    {
        'username': '王若曦',
        'password': '12345678917',
        'email': 'wangruoxi@example.com',
        'phone': '12345678917',
        'role': '使用者'
    },
    {
        'username': '张梓涵',
        'password': '12345678918',
        'email': 'zhangzihan@example.com',
        'phone': '12345678918',
        'role': '使用者'
    },
    {
        'username': '刘梦瑶',
        'password': '12345678919',
        'email': 'liumengyao@example.com',
        'phone': '12345678919',
        'role': '使用者'
    },
    {
        'username': '陈欣怡',
        'password': '12345678920',
        'email': 'chenxinyi@example.com',
        'phone': '12345678920',
        'role': '使用者'
    },
    {
        'username': '杨雨薇',
        'password': '12345678921',
        'email': 'yangyuwei@example.com',
        'phone': '12345678921',
        'role': '使用者'
    },
    {
        'username': '黄诗涵',
        'password': '12345678922',
        'email': 'huangshihan@example.com',
        'phone': '12345678922',
        'role': '使用者'
    },
    {
        'username': '吴雨萱',
        'password': '12345678923',
        'email': 'wuyuxuan@example.com',
        'phone': '12345678923',
        'role': '使用者'
    },
    {
        'username': '周思彤',
        'password': '12345678924',
        'email': 'zhousitong@example.com',
        'phone': '12345678924',
        'role': '使用者'
    },
    {
        'username': '徐佳宁',
        'password': '12345678925',
        'email': 'xujianing@example.com',
        'phone': '12345678925',
        'role': '使用者'
    },
    {
        'username': '孙雅琪',
        'password': '12345678926',
        'email': 'sunyaqi@example.com',
        'phone': '12345678926',
        'role': '使用者'
    },
    {
        'username': '马语桐',
        'password': '12345678927',
        'email': 'mayutong@example.com',
        'phone': '12345678927',
        'role': '使用者'
    },
    {
        'username': '朱欣悦',
        'password': '12345678928',
        'email': 'zhuxinyue@example.com',
        'phone': '12345678928',
        'role': '使用者'
    },
    {
        'username': '胡静怡',
        'password': '12345678929',
        'email': 'hujingyi@example.com',
        'phone': '12345678929',
        'role': '使用者'
    },
    {
        'username': '林婉清',
        'password': '12345678930',
        'email': 'linwanqing@example.com',
        'phone': '12345678930',
        'role': '使用者'
    }
]


class SampleUserInitializer:
    """
    示例用户初始化器类
    """
    def __init__(self, db_path=None):
        """
        初始化器构造函数
        :param db_path: 数据库路径，如果未提供则使用配置中的路径
        """
        # 如果提供了db_path参数就使用它，否则使用配置中的路径
        self.db_path = db_path if db_path else settings.db_path  # 修改为小写的db_path
        # 创建数据库实例
        self.db = UserDatabase(self.db_path)
        logger.info(f"初始化SampleUserInitializer，使用数据库路径: {self.db_path}")
        
    # 在SampleUserInitializer类中修改initialize_sample_users方法
    def initialize_sample_users(self):
        """
        初始化示例用户
        """
        try:
            for user in SAMPLE_USERS:
                # 检查用户是否已存在
                existing_user = self.db.get_user_by_username(user['username'])
                if existing_user:
                    logger.info(f"用户已存在，跳过添加: {user['username']}")
                    # 如果用户存在但角色不是管理员，更新为管理员角色
                    if user['role'] == '管理员' and existing_user.get('role') != '管理员':
                        try:
                            with self.db._get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute(
                                    "UPDATE users SET role = ? WHERE username = ?",
                                    (user['role'], user['username'])
                                )
                                conn.commit()
                                logger.info(f"用户角色已更新为管理员: {user['username']}")
                        except Exception as e:
                            logger.error(f"更新用户角色失败: {str(e)}")
                    continue
                
                # 使用数据库实例添加用户
                result = self.db.add_user(
                    username=user['username'],
                    password=user['password'],
                    email=user['email'],
                    phone=user['phone'],
                    role=user['role']
                )
                
                if result:
                    logger.info(f"成功添加示例用户: {user['username']}")
                else:
                    logger.error(f"添加示例用户失败: {user['username']}")
            return True  # 添加这一行，确保函数返回True表示成功
        except Exception as e:
            logger.error(f"初始化示例用户时发生错误: {str(e)}")
            return False


# 函数接口保持不变，确保向后兼容
def initialize_sample_users():
    """
    初始化示例用户的函数接口
    """
    initializer = SampleUserInitializer()
    return initializer.initialize_sample_users()


if __name__ == '__main__':
    print("开始初始化示例用户...")
    success = initialize_sample_users()
    if success:
        print("示例用户初始化成功!")
    else:
        print("示例用户初始化失败!")
