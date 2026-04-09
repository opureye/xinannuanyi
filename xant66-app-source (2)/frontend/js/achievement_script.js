// 从api.js导入所需的API函数
import { getUserAchievements, getUserPostCount, getUserCollectionCount, getUserFollowerCount, getUserRegistrationInfo } from './api.js';
import { showNotification } from './utils.js';

// 定义成就类型常量
const ACHIEVEMENT_TYPES = {
    NEWBIE: 'newbie',
    POSTER: 'poster',
    COLLECTOR: 'collector',
    FOLLOWER: 'follower'
};

// 获取用户成就数据
async function getUserAchievementsData() {
    try {
        // 同时获取所有需要的数据
        const [postCount, collectionCount, followerCount, registrationInfo] = await Promise.all([
            getUserPostCount(),
            getUserCollectionCount(),
            getUserFollowerCount(),
            getUserRegistrationInfo()
        ]);

        return {
            postCount: postCount?.count || 0,
            collectionCount: collectionCount?.count || 0,
            followerCount: followerCount?.count || 0,
            isRegistered: registrationInfo?.is_registered || false,
            createdAt: registrationInfo?.created_at || ''
        };
    } catch (error) {
        console.error('获取用户数据失败:', error);
        // 提供默认的模拟数据，确保界面可以正常显示
        return {
            postCount: 0,
            collectionCount: 0,
            followerCount: 0,
            isRegistered: true,
            createdAt: new Date().toISOString()
        };
    }
}

// 生成用户成就
function generateAchievements(userData) {
    const achievements = [];
    const newAchievements = [];

    // 1. 新人报到
    const newbieAchievement = generateAchievementData(
        'newbie',
        '新人报到',
        '成功注册账号',
        'fa-user-plus',
        userData.isRegistered,
        userData.createdAt
    );
    achievements.push(newbieAchievement);
    if (newbieAchievement.unlocked && newbieAchievement.isNew) {
        newAchievements.push(newbieAchievement);
    }

    // 2. 分享官成就（帖子数量）
    const posterLevels = [
        { level: 1, title: '初级分享官', description: '发布10个帖子', threshold: 10, icon: 'fa-star-half-o' },
        { level: 2, title: '中级分享官', description: '发布50个帖子', threshold: 50, icon: 'fa-star-o' },
        { level: 3, title: '高级分享官', description: '发布100个帖子', threshold: 100, icon: 'fa-star' }
    ];

    posterLevels.forEach(level => {
        const posterAchievement = generateAchievementData(
            `poster_${level.level}`,
            level.title,
            level.description,
            level.icon,
            userData.postCount >= level.threshold,
            null,
            {
                current: userData.postCount,
                target: level.threshold
            }
        );
        achievements.push(posterAchievement);
        if (posterAchievement.unlocked && posterAchievement.isNew) {
            newAchievements.push(posterAchievement);
        }
    });

    // 3. 收藏家成就（收藏数量）
    const collectorLevels = [
        { level: 1, title: '初级收藏家', description: '收藏10个内容', threshold: 10, icon: 'fa-bookmark-o' },
        { level: 2, title: '中级收藏家', description: '收藏50个内容', threshold: 50, icon: 'fa-bookmark' },
        { level: 3, title: '高级收藏家', description: '收藏100个内容', threshold: 100, icon: 'fa-diamond' }
    ];

    collectorLevels.forEach(level => {
        const collectorAchievement = generateAchievementData(
            `collector_${level.level}`,
            level.title,
            level.description,
            level.icon,
            userData.collectionCount >= level.threshold,
            null,
            {
                current: userData.collectionCount,
                target: level.threshold
            }
        );
        achievements.push(collectorAchievement);
        if (collectorAchievement.unlocked && collectorAchievement.isNew) {
            newAchievements.push(collectorAchievement);
        }
    });

    // 4. 获赞者成就（粉丝数量）
    const followerLevels = [
        { level: 1, title: '初级获赞者', description: '获得10个粉丝', threshold: 10, icon: 'fa-thumbs-o-up' },
        { level: 2, title: '中级获赞者', description: '获得50个粉丝', threshold: 50, icon: 'fa-thumbs-up' },
        { level: 3, title: '高级获赞者', description: '获得100个粉丝', threshold: 100, icon: 'fa-heart' }
    ];

    followerLevels.forEach(level => {
        const followerAchievement = generateAchievementData(
            `follower_${level.level}`,
            level.title,
            level.description,
            level.icon,
            userData.followerCount >= level.threshold,
            null,
            {
                current: userData.followerCount,
                target: level.threshold
            }
        );
        achievements.push(followerAchievement);
        if (followerAchievement.unlocked && followerAchievement.isNew) {
            newAchievements.push(followerAchievement);
        }
    });

    return { achievements, newAchievements };
}

// 生成单个成就数据
function generateAchievementData(id, title, description, icon, unlocked, unlockedAt = null, progress = null) {
    // 从localStorage获取已解锁的成就记录
    const unlockedAchievements = JSON.parse(localStorage.getItem('unlockedAchievements') || '[]');
    const achievementRecord = unlockedAchievements.find(a => a.id === id);
    
    // 检查是否是新解锁的成就
    const isNew = unlocked && !achievementRecord;
    
    // 如果成就已解锁但本地记录中没有，则更新本地记录
    if (unlocked && isNew) {
        unlockedAchievements.push({
            id,
            unlockedAt: unlockedAt || new Date().toISOString()
        });
        localStorage.setItem('unlockedAchievements', JSON.stringify(unlockedAchievements));
    }

    return {
        id,
        title,
        description,
        icon,
        unlocked,
        unlockedAt: achievementRecord?.unlockedAt || unlockedAt || null,
        progress,
        isNew
    };
}

// 渲染成就列表
function renderAchievements(achievements) {
    const achievementList = document.querySelector('.achievement-list');
    if (!achievementList) return;

    // 清空列表
    achievementList.innerHTML = '';

    // 按分类组织成就
    const achievementsByCategory = {
        '基础成就': achievements.filter(a => a.id === 'newbie'),
        '分享官': achievements.filter(a => a.id.startsWith('poster')),
        '收藏家': achievements.filter(a => a.id.startsWith('collector')),
        '获赞者': achievements.filter(a => a.id.startsWith('follower'))
    };

    // 渲染每个分类的成就
    Object.entries(achievementsByCategory).forEach(([category, categoryAchievements]) => {
        // 创建分类标题
        const categoryTitle = document.createElement('h3');
        categoryTitle.className = 'achievement-category-title';
        categoryTitle.textContent = category;
        achievementList.appendChild(categoryTitle);

        // 创建分类容器
        const categoryContainer = document.createElement('div');
        categoryContainer.className = 'achievement-category';
        
        // 渲染分类下的成就
        categoryAchievements.forEach(achievement => {
            const achievementItem = createAchievementItem(achievement);
            categoryContainer.appendChild(achievementItem);
        });

        achievementList.appendChild(categoryContainer);
    });
}

// 创建单个成就项
function createAchievementItem(achievement) {
    const achievementItem = document.createElement('div');
    achievementItem.className = `achievement-item ${achievement.unlocked ? 'unlocked' : 'locked'}`;
    
    // 添加新成就标记
    if (achievement.unlocked && achievement.isNew) {
        achievementItem.classList.add('new-achievement');
    }

    // 成就图标
    const iconContainer = document.createElement('div');
    iconContainer.className = 'achievement-icon';
    const icon = document.createElement('i');
    icon.className = `fa ${achievement.icon}`;
    iconContainer.appendChild(icon);

    // 成就信息
    const infoContainer = document.createElement('div');
    infoContainer.className = 'achievement-info';
    
    const title = document.createElement('h4');
    title.className = 'achievement-title';
    title.textContent = achievement.title;
    
    const description = document.createElement('p');
    description.className = 'achievement-description';
    description.textContent = achievement.description;
    
    infoContainer.appendChild(title);
    infoContainer.appendChild(description);

    // 成就状态
    const statusContainer = document.createElement('div');
    statusContainer.className = 'achievement-status';
    
    // 解锁状态
    const statusBadge = document.createElement('span');
    statusBadge.className = `status-badge ${achievement.unlocked ? 'badge-unlocked' : 'badge-locked'}`;
    statusBadge.textContent = achievement.unlocked ? '已获得 ' : '未获得';
    
    statusContainer.appendChild(statusBadge);

    // 解锁时间
    if (achievement.unlocked && achievement.unlockedAt) {
        const unlockTime = document.createElement('span');
        unlockTime.className = 'unlock-time';
        const date = new Date(achievement.unlockedAt);
        unlockTime.textContent = `获得于 ${date.toLocaleDateString()}`;
        statusContainer.appendChild(unlockTime);
    }

    // 进度条（如果有进度）
    if (achievement.progress) {
        const progressContainer = document.createElement('div');
        progressContainer.className = 'achievement-progress';
        
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        
        const progressFill = document.createElement('div');
        progressFill.className = 'progress-fill';
        const progressPercent = Math.min((achievement.progress.current / achievement.progress.target) * 100, 100);
        progressFill.style.width = `${progressPercent}%`;
        
        progressBar.appendChild(progressFill);
        progressContainer.appendChild(progressBar);
        
        const progressText = document.createElement('span');
        progressText.className = 'progress-text';
        progressText.textContent = `${achievement.progress.current}/${achievement.progress.target}`;
        progressContainer.appendChild(progressText);
        
        statusContainer.appendChild(progressContainer);
    }

    // 组装成就项
    achievementItem.appendChild(iconContainer);
    achievementItem.appendChild(infoContainer);
    achievementItem.appendChild(statusContainer);

    return achievementItem;
}

// 显示新成就通知
function showNewAchievementNotifications(newAchievements) {
    if (newAchievements.length === 0) return;

    // 延迟显示通知，让页面渲染完成
    setTimeout(() => {
        newAchievements.forEach((achievement, index) => {
            // 每个通知间隔显示
            setTimeout(() => {
                showNotification(
                    '恭喜获得新成就！',
                    `🏆 ${achievement.title}: ${achievement.description}`,
                    'success',
                    5000
                );
            }, index * 1000);
        });
    }, 500);
}

// 初始化成就页面
async function initAchievementPage() {
    // 显示加载状态
    const loadingElement = document.createElement('div');
    loadingElement.className = 'loading';
    loadingElement.textContent = '加载成就中...';
    
    const achievementList = document.querySelector('.achievement-list');
    if (achievementList) {
        achievementList.innerHTML = '';
        achievementList.appendChild(loadingElement);
    }

    try {
        // 获取用户数据
        const userData = await getUserAchievementsData();
        
        // 生成成就数据
        const { achievements, newAchievements } = generateAchievements(userData);
        
        // 渲染成就列表
        renderAchievements(achievements);
        
        // 显示新成就通知
        showNewAchievementNotifications(newAchievements);
        
        // 更新成就统计
        updateAchievementStats(achievements);
    } catch (error) {
        console.error('初始化成就页面失败:', error);
        
        // 显示错误信息
        if (achievementList) {
            achievementList.innerHTML = '<p class="error-message">加载成就失败，请刷新页面重试</p>';
        }
    }
}

// 更新成就统计信息
function updateAchievementStats(achievements) {
    const totalAchievements = achievements.length;
    const unlockedAchievements = achievements.filter(a => a.unlocked).length;
    const completionRate = Math.round((unlockedAchievements / totalAchievements) * 100);

    // 更新统计元素
    const statsElement = document.querySelector('.achievement-stats');
    if (statsElement) {
        // 清空现有内容
        statsElement.innerHTML = '';

        // 创建统计卡片
        const statsCard = document.createElement('div');
        statsCard.className = 'stats-card';

        const title = document.createElement('h3');
        title.className = 'stats-title';
        title.textContent = '成就统计';

        const statsContent = document.createElement('div');
        statsContent.className = 'stats-content';

        // 已获得成就数量
        const unlockedCount = document.createElement('div');
        unlockedCount.className = 'stat-item';
        unlockedCount.innerHTML = `
            <span class="stat-label">已获得成就</span>
            <span class="stat-value">${unlockedAchievements}/${totalAchievements}</span>
        `;

        // 完成率
        const completionRateEl = document.createElement('div');
        completionRateEl.className = 'stat-item';
        completionRateEl.innerHTML = `
            <span class="stat-label">完成率</span>
            <span class="stat-value">${completionRate}%</span>
        `;

        // 组装统计卡片
        statsContent.appendChild(unlockedCount);
        statsContent.appendChild(completionRateEl);
        statsCard.appendChild(title);
        statsCard.appendChild(statsContent);

        statsElement.appendChild(statsCard);
    }
}

// 当页面加载完成时初始化成就页面
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAchievementPage);
} else {
    initAchievementPage();
}

// 导出必要的函数供其他模块使用
export { initAchievementPage };