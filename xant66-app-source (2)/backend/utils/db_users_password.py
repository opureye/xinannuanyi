import hashlib
import secrets
import json
import datetime  # 添加datetime导入
import os  # 添加os导入

# 从core模块导入ExtendedUserDatabase基类
from .db_users_core import ExtendedUserDatabase, CRYPTO_AVAILABLE, logger

def _hash_password(self, password: str) -> str:
    """统一密码哈希接口，根据可用的加密库选择合适的哈希方法"""
    try:
        # 优先尝试使用高级加密方法
        logger.info("尝试使用高级加密方法处理密码")
        return self._highcrypt_password(password)
    except Exception as e:
        logger.error(f"高级加密密码哈希失败: {str(e)}")
        # 降级到传统哈希方法
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        password_data = {
            "version": 1,
            "hash": hashed,
            "salt": salt,
            "created_at": datetime.datetime.now().isoformat()
        }
        return json.dumps(password_data)

def _hash_password_traditional(self, password: str) -> str:
    """使用传统的哈希方法处理密码"""
    # 生成随机盐
    salt = secrets.token_hex(16)
    # 使用SHA-256哈希算法结合盐计算密码哈希
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    # 返回JSON格式的密码信息，包含版本、哈希值和盐
    return json.dumps({
        "version": 1,  # 版本号，用于未来可能的密码算法升级
        "hash": hashed,
        "salt": salt
    })

def _highcrypt_password(self, password: str) -> str:
    """使用高级加密算法加密密码"""
    try:
        # 确保private_key属性存在
        if not hasattr(self, 'private_key'):
            logger.error("系统私钥不存在，无法执行高级加密")
            # 立即尝试重新加载密钥
            self._load_or_generate_system_keys()
            if not hasattr(self, 'private_key'):
                raise RuntimeError("系统私钥不存在")
                
        salt = secrets.token_hex(16)
        
        # 检查是否可以使用密码学库进行更高级的加密
        if CRYPTO_AVAILABLE:
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                
                # 派生加密密钥
                encryption_key = self._kdf(self.private_key.encode('utf-8'), salt.encode('utf-8'), b"password_encryption", 32)
                
                # 使用AES-GCM加密模式
                aesgcm = AESGCM(encryption_key)
                nonce = os.urandom(12)  # AES-GCM推荐的nonce长度
                ciphertext = aesgcm.encrypt(nonce, password.encode('utf-8'), None)
                
                # 返回加密后的密码信息，包含版本、加密模式、盐、nonce和密文
                result = json.dumps({
                    "version": 2,
                    "mode": "aes_gcm",
                    "salt": salt,
                    "nonce": nonce.hex(),
                    "ciphertext": ciphertext.hex()
                })
                logger.debug("使用AES-GCM模式加密密码成功")
                return result
            except Exception as e:
                logger.warning(f"AES-GCM加密失败，降级使用增强哈希: {str(e)}")
        else:
            logger.warning("密码学库不可用，使用增强哈希")
            
        # 降级方案：使用增强的哈希方法
        hashed = hashlib.sha256((password + salt + self.private_key).encode('utf-8')).hexdigest()
        result = json.dumps({
            "version": 2,
            "mode": "enhanced_hash",
            "hash": hashed,
            "salt": salt
        })
        logger.debug("使用增强哈希模式加密密码")
        return result
    except Exception as e:
        logger.error(f"高级密码加密失败: {str(e)}")
        # 出错时降级使用传统哈希
        result = self._hash_password_traditional(password)
        logger.debug("降级使用传统哈希模式")
        return result

def _check_password(self, provided_password: str, stored_hash: str) -> bool:
    try:
        password_data = json.loads(stored_hash)
        version = password_data.get("version", 1)
        logger.info(f"密码验证 - 版本: {version}")

        if version == 1:
            # 传统哈希验证
            logger.info("使用传统哈希验证方法")
            hashed = hashlib.sha256((provided_password + password_data["salt"]).encode('utf-8')).hexdigest()
            result = hashed == password_data["hash"]
            logger.info(f"传统哈希验证结果: {result}")
            return result
        elif version == 2:
            # 高级加密验证
            logger.info("使用高级加密验证方法")
            
            # 确保private_key属性存在
            if not hasattr(self, 'private_key'):
                logger.error("系统私钥不存在，无法验证高级加密密码")
                return False
            
            # 根据模式选择验证方法
            mode = password_data.get("mode", "unknown")
            
            if mode == "aes_gcm":
                # AES-GCM加密模式
                logger.info("使用AES-GCM加密模式验证")
                try:
                    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                    
                    # 派生加密密钥
                    salt = password_data["salt"].encode('utf-8')
                    encryption_key = self._kdf(self.private_key.encode('utf-8'), salt, b"password_encryption", 32)
                    
                    # 创建AES-GCM对象并解密
                    aesgcm = AESGCM(encryption_key)
                    nonce = bytes.fromhex(password_data["nonce"])
                    # 修复：AES-GCM不需要单独的tag字段，tag包含在ciphertext中
                    ciphertext = bytes.fromhex(password_data["ciphertext"])
                    
                    # 验证并解密
                    try:
                        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
                        decrypted_password = decrypted.decode('utf-8')
                        result = provided_password == decrypted_password
                        logger.info(f"AES-GCM解密验证结果: {result}")
                        return result
                    except Exception as e:
                        logger.warning(f"AES-GCM解密失败: {str(e)}")
                        return False
                except ImportError:
                    logger.warning("无法导入密码学库，尝试降级到简化验证模式")
                    # 降级到简化验证模式
                    return self._simplified_password_verification(provided_password, password_data)
                except Exception as e:
                    logger.error(f"AES-GCM验证过程出错: {str(e)}")
                    # 降级到简化验证模式
                    return self._simplified_password_verification(provided_password, password_data)
            elif mode == "enhanced_hash":
                # 增强哈希模式
                logger.info("使用增强哈希模式验证")
                try:
                    from cryptography.hazmat.primitives import hashes
                        
                    # 验证哈希
                    salt = password_data["salt"].encode('utf-8')
                    digest = hashes.Hash(hashes.SHA256())
                    digest.update(salt)
                    digest.update(provided_password.encode('utf-8'))
                    hashed = digest.finalize().hex()
                    result = hashed == password_data["hash"]
                    logger.info(f"增强哈希验证结果: {result}")
                    return result
                except ImportError:
                    logger.warning("无法导入密码学库，尝试降级到简化验证模式")
                    # 降级到简化验证模式
                    return self._simplified_password_verification(provided_password, password_data)
                except Exception as e:
                    logger.error(f"增强哈希验证过程出错: {str(e)}")
                    # 降级到简化验证模式
                    return self._simplified_password_verification(provided_password, password_data)
                else:
                    # 未知模式，降级处理
                    logger.warning(f"未知的密码验证模式: {mode}，尝试降级处理")
                    # 首先尝试增强哈希验证
                    try:
                        from cryptography.hazmat.primitives import hashes
                            
                        # 尝试增强哈希验证
                        if "salt" in password_data and "hash" in password_data:
                            logger.info("尝试使用增强哈希验证")
                            salt = password_data["salt"].encode('utf-8')
                            digest = hashes.Hash(hashes.SHA256())
                            digest.update(salt)
                            digest.update(provided_password.encode('utf-8'))
                            hashed = digest.finalize().hex()
                            result = hashed == password_data["hash"]
                            logger.info(f"增强哈希验证结果: {result}")
                            return result
                    except:
                        pass
                        
                    # 尝试简化验证模式
                    logger.info("尝试使用简化验证模式")
                    return self._simplified_password_verification(provided_password, password_data)
            else:
                # 未知版本，使用简化验证模式
                logger.warning(f"未知的密码版本: {version}")
                return self._simplified_password_verification(provided_password, password_data)
    except json.JSONDecodeError as e:
        logger.error(f"密码哈希解析失败: {str(e)}")
        # 尝试使用简化验证模式
        return self._simplified_password_verification(provided_password, stored_hash)
    except Exception as e:
        logger.error(f"密码验证过程中出现未知错误: {str(e)}")
        # 尝试使用简化验证模式
        return self._simplified_password_verification(provided_password, stored_hash)

def _simplified_password_verification(self, provided_password: str, password_data: dict) -> bool:
    """简化的密码验证模式，当其他验证方法失败时使用"""
    try:
        # 检查是否有哈希值和盐
        if isinstance(password_data, dict) and "hash" in password_data and "salt" in password_data:
            # 尝试使用简单的SHA-256哈希验证
            hashed = hashlib.sha256((provided_password + password_data["salt"]).encode('utf-8')).hexdigest()
            result = hashed == password_data["hash"]
            logger.info(f"简化验证结果: {result}")
            return result
        # 如果password_data是字符串，尝试作为简单哈希比较
        elif isinstance(password_data, str):
            # 尝试解析为JSON
            try:
                data = json.loads(password_data)
                return self._simplified_password_verification(provided_password, data)
            except json.JSONDecodeError:
                # 兼容旧数据：支持无盐SHA-256或明文密码
                # 无盐SHA-256（64位十六进制）
                try:
                    if len(password_data) == 64 and all(c in "0123456789abcdefABCDEF" for c in password_data):
                        hashed = hashlib.sha256(provided_password.encode('utf-8')).hexdigest()
                        result = hashed == password_data.lower()
                        logger.info(f"无盐SHA-256验证结果: {result}")
                        return result
                except Exception:
                    pass
                # 明文比较（仅为兼容旧库，建议尽快迁移）
                result = provided_password == password_data
                logger.info(f"明文密码兼容验证结果: {result}")
                return result
            return False
    except Exception as e:
        logger.error(f"简化验证过程中发生错误: {str(e)}")
        return False

# 将方法绑定到ExtendedUserDatabase类
ExtendedUserDatabase._hash_password = _hash_password
ExtendedUserDatabase._hash_password_traditional = _hash_password_traditional
ExtendedUserDatabase._highcrypt_password = _highcrypt_password
ExtendedUserDatabase._check_password = _check_password
ExtendedUserDatabase._simplified_password_verification = _simplified_password_verification
