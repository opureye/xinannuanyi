// 心理学相关功能模块

// 导入必要的API和工具
// 修改导入语句，使用默认导入
import { apiRequest } from './api.js';
import utils from './utils.js';

// 心理学模块
const psychologyModule = {
    // 初始化函数
    init: function() {
        // 获取DOM元素
        this.uploadArea = document.getElementById('upload-area');
        this.fileInput = document.getElementById('file-input');
        // 支持多文件上传
        this.fileInput.setAttribute('multiple', 'multiple');
        this.browseBtn = document.getElementById('browse-btn');
        this.fileInfo = document.getElementById('file-info');
        this.startAnalysisBtn = document.getElementById('start-analysis');
        this.analysisMode = document.getElementById('analysis-mode');
        this.userId = document.getElementById('user-id');
        this.progressSection = document.getElementById('progress-section');
        this.progressBarFill = document.getElementById('progress-bar-fill');
        this.progressSteps = document.getElementById('progress-steps').querySelectorAll('.step');
        this.progressMessage = document.getElementById('progress-message');
        this.resultsSection = document.getElementById('results-section');
        this.fileCountElement = document.getElementById('file-count'); // 添加文件计数器元素
        this.totalScore = document.getElementById('total-score');
        this.depressionLevel = document.getElementById('depression-level');
        this.analysisTime = document.getElementById('analysis-time');
        this.reportContent = document.getElementById('report-content');
        this.downloadReport = document.getElementById('download-report');
    
        // 添加缺失的初始化
        this.resultsContent = document.getElementById('report-content');
    
        // 初始化状态
        this.selectedFiles = []; // 修改为数组，支持多文件
        this.analysisResult = null;
    
        // 更新文件计数器初始状态
        this.updateFileCount();
    
        // 绑定事件
        this.bindEvents();
        console.log('心理学模块已初始化');
    },

    // 绑定事件
    bindEvents: function() {
        // 浏览文件按钮点击事件
        this.browseBtn.addEventListener('click', () => {
            this.fileInput.click();
        });

        // 文件上传区域点击事件
        this.uploadArea.addEventListener('click', () => {
            this.fileInput.click();
        });

        // 文件选择变化事件
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                this.handleFileSelection(e.target.files);
            }
        });

        // 拖放事件
        this.uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.uploadArea.classList.add('drag-over');
        });

        this.uploadArea.addEventListener('dragleave', () => {
            this.uploadArea.classList.remove('drag-over');
        });

    this.uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        this.uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            this.handleFileSelection(e.dataTransfer.files);
        }
    });

        // 开始分析按钮点击事件
        this.startAnalysisBtn.addEventListener('click', () => {
            this.startAnalysis();
        });

        // 下载报告按钮点击事件
        this.downloadReport.addEventListener('click', () => {
            this.downloadReportFile();
        });
    },

    // 处理文件选择（修改为更健壮的版本）
    handleFileSelection: function(files) {
        // 确保files参数有效
        if (!files) {
            utils.showError('未选择任何文件');
            return;
        }
        
        // 正确处理FileList对象和数组
        const fileList = files instanceof FileList ? Array.from(files) : 
                        Array.isArray(files) ? files : 
                        [files];
        
        this.selectedFiles = [];
        
        // 验证并添加所有文件
        for (const file of fileList) {
            // 添加更严格的类型检查确保file是有效的文件对象
            if (!file || typeof file !== 'object' || typeof file.name !== 'string') {
                continue;
            }
            
            if (file.type !== 'application/json' && !file.name.endsWith('.json')) {
                utils.showError(`文件 ${file.name} 不是JSON格式，请重新选择`);
                continue;
            }
            this.selectedFiles.push(file);
        }
        
        if (this.selectedFiles.length === 0) {
            return;
        }
    
        // 显示文件信息（保持原有代码）
        this.fileInfo.innerHTML = `
            <div class="file-list">
                ${this.selectedFiles.map(file => `
                    <div class="file-item">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${(file.size / 1024).toFixed(2)} KB</div>
                    </div>
                `).join('')}
            </div>
            <div class="file-count">共选择 ${this.selectedFiles.length} 个文件</div>
            <button class="remove-file">移除所有文件</button>
        `;
        this.fileInfo.classList.remove('hidden');
    
        // 绑定移除文件按钮事件（保持原有代码）
        this.fileInfo.querySelector('.remove-file').addEventListener('click', () => {
            this.removeFile();
        });
    
        // 启用开始分析按钮
        this.startAnalysisBtn.disabled = false;
    
        // 更新文件计数器
        this.updateFileCount();
    },

    // 移除选中的文件
    removeFile: function() {
        this.selectedFiles = [];
        this.fileInfo.classList.add('hidden');
        this.fileInfo.innerHTML = '';
        this.startAnalysisBtn.disabled = true;
    
        // 更新文件计数器
        this.updateFileCount();
    },

    // 更新文件计数器显示
    updateFileCount: function() {
        if (this.fileCountElement) {
            this.fileCountElement.textContent = `已上传${this.selectedFiles.length}个文件`;
        }
    },

    // 开始分析（彻底修复异步请求处理和this上下文问题）
    startAnalysis: async function() {
        console.log('startAnalysis函数开始执行');
        
        // 保存this引用，确保在异步操作中能正确访问
        const self = this;
        
        if (this.selectedFiles.length === 0) {
            utils.showError('请先选择JSON文件');
            return;
        }

        console.log(`开始分析 ${this.selectedFiles.length} 个文件`);
        console.log('selectedFiles:', this.selectedFiles);

        // 显示进度区域
        if (this.progressSection) this.progressSection.classList.remove('hidden');
        if (this.resultsSection) this.resultsSection.classList.add('hidden');

        // 重置进度
        try {
            this.updateProgress(0, '准备开始分析...');
            this.updateStepStatus(1);
        } catch (err) {
            console.error('更新进度时出错:', err);
        }

        try {
            // 对每个文件分别进行分析
            const allResults = [];
            let currentProgress = 10;
            const progressStep = 80 / this.selectedFiles.length;
            
            for (let i = 0; i < this.selectedFiles.length; i++) {
                const file = this.selectedFiles[i];
                // 再次检查file对象的有效性
                if (!file || typeof file.name !== 'string') {
                    currentProgress += progressStep;
                    continue;
                }
                
                try {
                    this.updateProgress(currentProgress, `正在分析文件 ${i+1}/${this.selectedFiles.length}: ${file.name}...`);
                } catch (err) {
                    console.error('更新进度时出错:', err);
                }
                
                // 创建FormData对象
                const formData = new FormData();
                formData.append('file', file);
                formData.append('analysis_mode', this.analysisMode?.value || 'local');
                formData.append('user_id', this.userId?.value || 'anonymous');
                
                try {
                    // 使用await等待异步请求完成
                    const result = await apiRequest('/api/psychology/analyze', 
                        {
                            method: 'POST',
                            body: formData,
                        }, 
                        false  // 明确设置为不需要认证
                    );
                    
                    // 添加文件名到结果中
                    if (result) {
                        result.fileName = file.name;
                        allResults.push(result);
                    }
                } catch (apiError) {
                    console.error(`分析文件 ${file.name} 时出错:`, apiError);
                    utils.showError(`分析文件 ${file.name} 时出错: ${apiError.message || '未知错误'}`);
                }
                
                currentProgress += progressStep;
            }

            // 保存分析结果
            this.analysisResult = {
                success: true,
                multipleResults: allResults
            };

            // 更新进度并显示结果
            try {
                this.updateProgress(100, '分析完成！');
                this.updateStepStatus(4);
            } catch (err) {
                console.error('更新进度时出错:', err);
            }

            // 确保self引用正确，并使用额外的防护措施调用showResults
            console.log('准备调用showResults，self对象:', self);
            console.log('analysisResult:', this.analysisResult);
            
            // 使用立即执行函数来确保上下文正确
            (function(self, result) {
                if (typeof self.showResults === 'function' && result) {
                    setTimeout(() => {
                        try {
                            self.showResults(result);
                        } catch (showError) {
                            console.error('调用showResults时出错:', showError);
                            utils.showError('显示分析结果时出错: ' + showError.message);
                        }
                    }, 500);
                } else {
                    console.error('showResults不是函数或结果为空');
                    utils.showError('无法显示分析结果');
                }
            })(self, this.analysisResult);

        } catch (error) {
            console.error('分析过程中出错:', error);
            utils.showError('分析过程中出错: ' + (error.message || '未知错误'));
            try {
                this.updateProgress(0, '分析失败，请重试');
            } catch (err) {
                console.error('更新进度时出错:', err);
            }
        }
    },

    // 显示分析结果
    // 修改showResults函数，支持多文件结果
    showResults: function(result) {
        console.log('showResults函数被调用，result参数:', result);
        
        // 再次获取并检查DOM元素引用，确保它们存在
        const reportContent = document.getElementById('report-content');
        const totalScore = document.getElementById('total-score');
        const depressionLevel = document.getElementById('depression-level');
        const analysisTime = document.getElementById('analysis-time');
        const resultsSection = document.getElementById('results-section');
        const downloadReport = document.getElementById('download-report');
        
        console.log('DOM元素状态:', {
            reportContent: !!reportContent,
            totalScore: !!totalScore,
            depressionLevel: !!depressionLevel,
            analysisTime: !!analysisTime,
            resultsSection: !!resultsSection,
            downloadReport: !!downloadReport
        });
        
        // 确保必要元素存在
        if (!reportContent || !resultsSection) {
            console.error('关键DOM元素不存在');
            utils.showError('无法显示结果：页面元素缺失');
            return;
        }

        // 检查结果对象是否有效
        if (!result) {
            console.error('结果对象为空');
            reportContent.innerHTML = '<p class="error-message">无效的分析结果</p>';
            resultsSection.classList.remove('hidden');
            return;
        }

        // 检查是否有多文件结果
        if (result.multipleResults) {
            // 多文件结果处理
            try {
                reportContent.innerHTML = `
                    <h3>分析结果汇总 (${result.multipleResults.length}个文件)</h3>
                    ${result.multipleResults.map((fileResult, index) => `
                        <div class="file-result">
                            <h4>文件 ${index+1}: ${fileResult?.fileName || '未知'}</h4>
                            <div class="result-summary">
                                <p><strong>得分:</strong> ${fileResult?.score || 0}</p>
                                <p><strong>抑郁程度:</strong> ${fileResult?.level || '未知'}</p>
                                <p><strong>分析时间:</strong> ${fileResult?.analysis_time || '未知'}</p>
                            </div>
                            <div class="report-summary">${fileResult?.report?.summary || '无摘要信息'}</div>
                        </div>
                    `).join('')}
                `;
            } catch (innerError) {
                console.error('渲染多文件结果时出错:', innerError);
                reportContent.innerHTML = '<p class="error-message">显示结果时发生错误</p>';
            }
        } else {
            // 单文件结果处理
            try {
                // 填充结果数据
                if (totalScore) totalScore.textContent = `${result.score || 0} / 30`;
                if (depressionLevel) depressionLevel.textContent = result.level || '未知';
                if (analysisTime) analysisTime.textContent = result.analysis_time || '未知';

                // 生成报告内容
                let reportHTML = `
                    <div class="report-header">
                        <h3>老年抑郁智能评估报告</h3>
                        <p>用户ID: ${this.userId?.value || 'anonymous'}</p>
                        <p>分析时间: ${new Date().toLocaleString()}</p>
                    </div>
                    
                    <div class="report-summary">
                        <h4>评估摘要</h4>
                        <p><strong>GDS-30总分:</strong> ${result.score || 0} / 30</p>
                        <p><strong>抑郁程度:</strong> ${result.level || '未知'}</p>
                        <p><strong>分析用时:</strong> ${result.analysis_time || '未知'}</p>
                        ${result.reasoning ? `<p><strong>评估说明:</strong> ${result.reasoning}</p>` : ''}
                    </div>
                `;

                // 如果有详细的问题回答，添加到报告中
                if (result.responses && result.responses.length > 0) {
                    reportHTML += `
                        <div class="report-details">
                            <h4>详细评估结果</h4>
                            <div class="questions-list">
                    `;

                    // 每5个问题一组显示
                    for (let i = 0; i < result.responses.length; i += 5) {
                        const batch = result.responses.slice(i, i + 5);
                        reportHTML += `<div class="question-batch">`;
                        
                        batch.forEach((item, index) => {
                            const questionNum = i + index + 1;
                            reportHTML += `
                                <div class="question-item">
                                    <p class="question-text"><strong>${questionNum}. ${item?.question || '问题'}</strong></p>
                                    <p class="question-answer">回答: ${item?.answer || '无'}</p>
                                    ${item?.reason ? `<p class="question-reason">依据: ${item.reason}</p>` : ''}
                                    ${item?.advice ? `<p class="question-advice">建议: ${item.advice}</p>` : ''}
                                </div>
                            `;
                        });
                        
                        reportHTML += `</div>`;
                    }

                    reportHTML += `
                            </div>
                        </div>
                    `;
                }

                // 设置报告内容
                reportContent.innerHTML = reportHTML;
            } catch (innerError) {
                console.error('渲染报告内容时出错:', innerError);
                reportContent.innerHTML = '<p class="error-message">显示报告时发生错误</p>';
            }
        }
        
        // 显示结果区域
        try {
            resultsSection.classList.remove('hidden');
            if (this.progressSection) this.progressSection.classList.add('hidden');
            if (downloadReport) downloadReport.disabled = false;
        } catch (err) {
            console.error('显示结果区域时出错:', err);
        }
    },

    // 更新进度
    updateProgress: function(percentage, message) {
        this.progressBarFill.style.width = `${percentage}%`;
        this.progressMessage.textContent = message;
    },

    // 更新步骤状态
    updateStepStatus: function(activeStep) {
        this.progressSteps.forEach((step, index) => {
            const stepNum = parseInt(step.dataset.step);
            if (stepNum < activeStep) {
                step.classList.add('completed');
                step.classList.remove('active');
            } else if (stepNum === activeStep) {
                step.classList.add('active');
                step.classList.remove('completed');
            } else {
                step.classList.remove('active', 'completed');
            }
        });
    },

    // 下载报告文件
    downloadReportFile: function() {
        if (!this.analysisResult) {
            utils.showError('没有可下载的报告');
            return;
        }

        // 创建报告内容
        const reportContent = this.analysisResult.report || this.reportContent.innerText;
        const blob = new Blob([reportContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        
        // 创建下载链接
        const a = document.createElement('a');
        a.href = url;
        a.download = `gds_report_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        
        // 清理
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};

// 页面加载完成后初始化模块
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => psychologyModule.init());
} else {
    psychologyModule.init();
}

// 导出模块
export default psychologyModule;