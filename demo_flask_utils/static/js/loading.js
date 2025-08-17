class LoadingModal {
    constructor() {
        this.modal = null;
        this.titleElement = null;
        this.contentElement = null;
        this.isVisible = false;
        this.updateInterval = null;
    }

    create() {
        if (this.modal) return;

        // 创建模态框
        this.modal = document.createElement('div');
        this.modal.className = 'loading-modal';
        
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        
        const content = document.createElement('div');
        content.className = 'loading-content';
        
        // 标题
        this.titleElement = document.createElement('h3');
        this.titleElement.className = 'loading-title';
        this.titleElement.textContent = '处理中...';
        
        // 内容
        this.contentElement = document.createElement('div');
        this.contentElement.className = 'loading-text';
        this.contentElement.textContent = '请稍候...';
        
        // 加载动画
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        
        content.appendChild(this.titleElement);
        content.appendChild(spinner);
        content.appendChild(this.contentElement);
        overlay.appendChild(content);
        this.modal.appendChild(overlay);
        
        document.body.appendChild(this.modal);
    }

    show(title = '处理中...', content = '请稍候...') {
        this.create();
        this.titleElement.textContent = title;
        this.contentElement.textContent = content;
        this.modal.style.display = 'block';
        this.isVisible = true;
        
        // 添加显示动画
        setTimeout(() => {
            if (this.modal) {
                this.modal.classList.add('show');
            }
        }, 10);
    }

    updateContent(content) {
        if (this.contentElement) {
            this.contentElement.textContent = content;
        }
    }

    updateTitle(title) {
        if (this.titleElement) {
            this.titleElement.textContent = title;
        }
    }

    // 新增：模拟处理进度的方法
    showWithProgress(title, stages) {
        this.show(title, stages[0] || '开始处理...');
        
        let currentStage = 0;
        this.updateInterval = setInterval(() => {
            currentStage++;
            if (currentStage < stages.length) {
                this.updateContent(stages[currentStage]);
            } else {
                this.clearUpdateInterval();
            }
        }, 2000); // 每2秒更新一次
    }

    clearUpdateInterval() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    hide() {
        this.clearUpdateInterval();
        if (this.modal && this.isVisible) {
            this.modal.classList.remove('show');
            setTimeout(() => {
                if (this.modal) {
                    this.modal.style.display = 'none';
                    this.isVisible = false;
                }
            }, 300);
        }
    }

    destroy() {
        this.clearUpdateInterval();
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
            this.titleElement = null;
            this.contentElement = null;
            this.isVisible = false;
        }
    }
}

// 创建全局实例
window.loadingModal = new LoadingModal();
