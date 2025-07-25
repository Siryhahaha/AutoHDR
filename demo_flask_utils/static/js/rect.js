const CHINESE_NUMS = [
    "一","二","三","四","五","六","七","八","九","十",
    "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
    "二十一","二十二","二十三","二十四","二十五","二十六","二十七","二十八","二十九","三十"
];

class Rect {
    constructor(x, y, width, height, color, id = null, label = null) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;
        this.color = color;
        this.id = id;
        this.label = label;
    }
    toJSON() {
        return {
            x: this.x,
            y: this.y,
            width: this.width,
            height: this.height,
            color: this.color,
            id: this.id,
            label: this.label
        };
    }
    static fromJSON(obj) {
        return new Rect(obj.x, obj.y, obj.width, obj.height, obj.color, obj.id, obj.label);
    }
}

class RectManager {
    constructor(drawArea) {
        this.rects = [];
        this.rectId = 1;
        this.drawArea = drawArea;
        this.enableDraw = false;
        this.onChange = null;
    }

    add(rect) {
        // 统一的添加方法
        rect.id = rect.id || this.rectId++;
        if (!rect.label) {
            rect.label = CHINESE_NUMS[rect.id-1] || String(rect.id);
        }
        this.rects.push(rect);
        if (this.onChange) this.onChange();
        return rect.id;
    }

    setRects(rectArr) {
        // 统一的批量设置方法
        this.clearRects();
        rectArr.forEach(obj => {
            const rect = (obj instanceof Rect) ? obj : Rect.fromJSON(obj);
            if (rect.id >= this.rectId) {
                this.rectId = rect.id + 1;
            }
            this.rects.push(rect);
        });
        if (this.onChange) this.onChange();
    }

    setDrawMode(enable) {
        this.enableDraw = enable;
        this.renderRects();
    }
    addRect(rect) {
        rect.id = this.rectId++;
        if (!rect.label) rect.label = CHINESE_NUMS[rect.id-1] || String(rect.id);
        this.rects.push(rect);
        if (this.onChange) this.onChange();
    }
    removeRectById(id) {
        this.rects = this.rects.filter(r => r.id !== id);
        if (this.onChange) this.onChange();
    }
    clearRects() {
        this.rects = [];
        if (this.onChange) this.onChange();
    }
    renderRects(selectedRectId = null, onSelect = null, onDrag = null, onResize = null, showAllLabels = false, scale = 1) {
        this.drawArea.querySelectorAll('.rect-box').forEach(e => e.remove());
        this.rects.forEach(r => {
            const box = document.createElement('div');
            box.className = 'rect-box';
            if (selectedRectId === r.id) box.classList.add('selected');
            box.style.left = (r.x * scale) + 'px';
            box.style.top = (r.y * scale) + 'px';
            box.style.width = (r.width * scale) + 'px';
            box.style.height = (r.height * scale) + 'px';
            box.style.borderColor = r.color;
            box.style.background = RectManager.hexToRgba(r.color, 0.2);

            // 外部label
            if (showAllLabels || selectedRectId === r.id) {
                const label = document.createElement('span');
                label.className = 'rect-label-outer';
                label.style.background = r.color;
                if (r.color === "#7fffd4" || r.color === "#ffffff") {
                    label.style.color = "#222";
                } else {
                    label.style.color = "#fff";
                }
                // 修改：只显示标签文字，不显示序号
                label.textContent = r.label;
                label.style.left = '0px';
                // 标签字号随缩放放大
                label.style.fontSize = (13 * Math.max(scale, 1)) + 'px';
                label.style.top = (-22 * Math.max(scale, 1)) + 'px';
                label.style.position = 'absolute';
                // 不再缩放整个label（避免太小），只放大字号和top
                // label.style.transform = `scale(${scale})`;
                // label.style.transformOrigin = 'left bottom';
                box.appendChild(label);
            }

            // 拖动
            if (onDrag) {
                box.onmousedown = (e) => onDrag(e, r, box);
            }

            // 只添加右下角缩放手柄
            if (selectedRectId === r.id && onResize) {
                const handle = document.createElement('div');
                handle.className = 'rect-handle';
                Object.assign(handle.style, {
                    position: 'absolute',
                    width: (12 * scale) + 'px',
                    height: (12 * scale) + 'px',
                    background: '#fff',
                    border: '2px solid #1976d2',
                    borderRadius: '50%',
                    zIndex: 20,
                    right: (-6 * scale) + 'px',
                    bottom: (-6 * scale) + 'px',
                    cursor: 'nwse-resize'
                });
                handle.onmousedown = (e) => onResize(e, r, box);
                box.appendChild(handle);
            }

            // 选中（无论点击哪里都能选中）
            if (onSelect) {
                box.onclick = (e) => {
                    e.stopPropagation();
                    onSelect(e, r);
                };
            }

            this.drawArea.appendChild(box);
        });
    }
    getRects() {
        return this.rects.map(r => r.toJSON());
    }
    static hexToRgba(hex, alpha) {
        let c = hex.replace('#','');
        if (c.length === 3) c = c[0]+c[0]+c[1]+c[1]+c[2]+c[2];
        let rgb = [
            parseInt(c.substr(0,2),16),
            parseInt(c.substr(2,2),16),
            parseInt(c.substr(4,2),16)
        ];
        return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${alpha})`;
    }

    to_json() {
        return JSON.stringify(this.getRects());
    }

    static from_json(json_str) {
        const manager = new RectManager();
        if (json_str) {
            const data = JSON.parse(json_str);
            data.forEach(rect_data => {
                manager.add(new Rect(
                    rect_data.x,
                    rect_data.y,
                    rect_data.width,
                    rect_data.height,
                    rect_data.color,
                    rect_data.id,
                    rect_data.label
                ));
            });
        }
        return manager;
    }
}

class RectUI {
    constructor(drawArea, rectFormList, colorInput, drawBtn, otherBtn, zoomBtn) {
        this.drawArea = drawArea;
        this.rectFormList = rectFormList;
        this.colorInput = colorInput;
        this.drawBtn = drawBtn;
        this.rectColor = colorInput.value;
        this.selectedRectId = null;
        this.drawing = false;
        this.enableDraw = false;
        this.startX = 0;
        this.startY = 0;
        this.previewRect = null;
        this.previewLabel = null;
        this.dragInfo = null;
        this.showAllLabels = true; // 修改为true，默认显示所有标签
        this.otherBtn = otherBtn;
        this.zoomBtn = zoomBtn;
        this.scaleMode = 'original'; // 'original' or 'fit'
        this.scale = 1;

        // 确保只创建一个RectManager实例
        this.rectManager = new RectManager(drawArea);
        this.rectManager.onChange = () => {
            // 使用统一的渲染方式
            this.rectManager.renderRects(
                this.selectedRectId,
                this._onSelect.bind(this),
                this._onDrag.bind(this),
                this._onResize.bind(this),
                this.showAllLabels,
                this.scale
            );
            this.updateRectFormList();
        };

        this._bindUIEvents();
        this.rectManager.onChange(); // 初始化渲染和左侧栏
        this._autoInitScale();
    }

    _bindUIEvents() {
        this.drawBtn.onclick = () => {
            this.enableDraw = true;
            this.rectManager.setDrawMode(true);
            this.drawBtn.disabled = true;
            this.drawBtn.textContent = "添加中";
            // 修正：画框时也要用当前缩放比例渲染
            this.rectManager.renderRects(
                this.selectedRectId,
                this._onSelect.bind(this),
                this._onDrag.bind(this),
                this._onResize.bind(this),
                this.showAllLabels,
                this.scale
            );
        };
        this.colorInput.onchange = () => {
            this.rectColor = this.colorInput.value;
        };

        this.drawArea.onmousedown = (e) => this._onDrawAreaMouseDown(e);
        this.drawArea.onmousemove = (e) => this._onDrawAreaMouseMove(e);
        this.drawArea.onmouseup = (e) => this._onDrawAreaMouseUp(e);

        // 拖动和缩放
        document.addEventListener('mousemove', (e) => this._onGlobalMouseMove(e));
        document.addEventListener('mouseup', (e) => this._onGlobalMouseUp(e));

        if (this.otherBtn) {
            this.otherBtn.onclick = () => {
                this.showAllLabels = !this.showAllLabels;
                this.otherBtn.textContent = this.showAllLabels ? "隐藏标签" : "显示标签";
                this.rectManager.renderRects(
                    this.selectedRectId,
                    this._onSelect.bind(this),
                    this._onDrag.bind(this),
                    this._onResize.bind(this),
                    this.showAllLabels,
                    this.scale
                );
            };
            // 初始化按钮文本
            this.otherBtn.textContent = this.showAllLabels ? "隐藏标签" : "显示标签";
        }

        if (this.zoomBtn) {
            this.zoomBtn.onclick = () => {
                if (this.scaleMode === 'original') {
                    this.scaleMode = 'fit';
                    this.zoomBtn.textContent = "原始大小";
                } else {
                    this.scaleMode = 'original';
                    this.zoomBtn.textContent = "适应页面";
                }
                this._updateScaleAndRender();
            };
            this.zoomBtn.textContent = "适应页面";
        }
        // 初始化画框按钮文本
        this.drawBtn.textContent = "添加框";
    }

    _updateScaleAndRender() {
        const img = this.drawArea.querySelector('img');
        if (!img) return;
        if (this.scaleMode === 'fit') {
            // 适应页面宽度
            const content = document.querySelector('.content');
            let maxWidth = content ? content.clientWidth : 800;
            maxWidth -= 24;
            img.style.width = maxWidth + 'px';
            img.style.maxWidth = maxWidth + 'px';
            img.style.height = 'auto';
            img.style.removeProperty('min-width');
            img.style.removeProperty('min-height');
            img.style.zIndex = 0;
            img.style.display = 'block';
        } else {
            // 原始大小：彻底移除所有宽高限制，强制覆盖max-width
            img.style.width = img.naturalWidth + 'px';
            img.style.height = img.naturalHeight + 'px';
            img.style.maxWidth = 'none';
            img.style.maxHeight = 'none';
            img.style.minWidth = '0';
            img.style.minHeight = '0';
            img.style.display = 'block';
        }
        // 保证所有rect-box都在图片之上
        this._ensureRectsAboveImage();
        this.scale = (this.scaleMode === 'fit') ? (parseFloat(img.style.width) / img.naturalWidth) : 1;
        this.rectManager.renderRects(
            this.selectedRectId,
            this._onSelect.bind(this),
            this._onDrag.bind(this),
            this._onResize.bind(this),
            this.showAllLabels,
            this.scale
        );
    }

    _onDrawAreaMouseDown(e) {
        if (!this.enableDraw) return;
        const img = this.drawArea.querySelector('img');
        if (e.target !== img) return;
        this.drawing = true;
        // 修正：拉框时预览框应跟随缩放显示（即预览框的 left/top/width/height 需乘以 this.scale）
        const pos = this._getOffset(e, this.scale);
        this.startX = pos.x;
        this.startY = pos.y;

        this.previewRect = document.createElement('div');
        this.previewRect.className = 'rect-box';
        // 预览框初始位置和大小都要乘以缩放比例
        this.previewRect.style.left = (this.startX * this.scale) + 'px';
        this.previewRect.style.top = (this.startY * this.scale) + 'px';
        this.previewRect.style.width = '0px';
        this.previewRect.style.height = '0px';
        this.previewRect.style.borderColor = this.rectColor;
        this.previewRect.style.background = RectManager.hexToRgba(this.rectColor, 0.2);
        this.previewRect.style.zIndex = 10;

        this.previewLabel = document.createElement('span');
        this.previewLabel.className = 'rect-label-outer';
        this.previewLabel.style.background = this.rectColor;
        this.previewLabel.style.color = this.rectColor === "#7fffd4" ? "#222" : "#fff";
        const nextId = this.rectManager.rectId;
        const CHINESE_NUMS = [
            "一","二","三","四","五","六","七","八","九","十",
            "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
            "二十一","二十二","二十三","二十四","二十五","二十六","二十七","二十八","二十九","三十"
        ];
        // 修改：预览时只显示汉字，不显示序号
        this.previewLabel.textContent = CHINESE_NUMS[nextId-1] || String(nextId);
        this.previewLabel.style.left = '0px';
        this.previewLabel.style.top = '-22px';
        this.previewLabel.style.position = 'absolute';
        this.previewRect.appendChild(this.previewLabel);

        if (img.nextSibling) {
            this.drawArea.insertBefore(this.previewRect, img.nextSibling);
        } else {
            this.drawArea.appendChild(this.previewRect);
        }
    }

    _onDrawAreaMouseMove(e) {
        if (!this.drawing || !this.previewRect) return;
        // 修正：拉框时预览框应跟随缩放显示
        const pos = this._getOffset(e, this.scale);
        let x = Math.min(this.startX, pos.x);
        let y = Math.min(this.startY, pos.y);
        let w = Math.abs(pos.x - this.startX);
        let h = Math.abs(pos.y - this.startY);
        // 保证整数像素
        x = Math.round(x);
        y = Math.round(y);
        w = Math.round(w);
        h = Math.round(h);
        // 预览框的 left/top/width/height 都要乘以缩放比例
        this.previewRect.style.left = (x * this.scale) + 'px';
        this.previewRect.style.top = (y * this.scale) + 'px';
        this.previewRect.style.width = (w * this.scale) + 'px';
        this.previewRect.style.height = (h * this.scale) + 'px';
        this.previewLabel.style.left = '0px';
        this.previewLabel.style.top = '-22px';
    }

    _onDrawAreaMouseUp(e) {
        if (!this.drawing || !this.previewRect) return;
        this.drawing = false;
        const pos = this._getOffset(e, this.scale);
        let x = Math.min(this.startX, pos.x);
        let y = Math.min(this.startY, pos.y);
        let w = Math.abs(pos.x - this.startX);
        let h = Math.abs(pos.y - this.startY);
        x = Math.round(x);
        y = Math.round(y);
        w = Math.round(w);
        h = Math.round(h);
        if (w < 5 || h < 5) {
            this.previewRect.remove();
            this.previewRect = null;
            this.previewLabel = null;
            return;
        }
        
        // 使用统一的Rect创建方式
        const newRect = new Rect(x, y, w, h, this.rectColor);
        // 使用统一的RectManager添加方式
        this.selectedRectId = this.rectManager.add(newRect);
        
        this.previewRect = null;
        this.previewLabel = null;
        this.enableDraw = false;
        this.rectManager.setDrawMode(false);
        this.drawBtn.disabled = false;
        this.drawBtn.textContent = "添加框";
        
        // 更新显示
        if (this.rectManager.onChange) {
            this.rectManager.onChange();
        }
        
        this.highlightSidebarForm(this.selectedRectId);
    }

    _getOffset(e, scale = 1) {
        const rect = this.drawArea.getBoundingClientRect();
        return {
            x: Math.round((e.clientX - rect.left) / scale),
            y: Math.round((e.clientY - rect.top) / scale)
        };
    }

    _onSelect(e, r) {
        if (this.enableDraw) return;
        e.stopPropagation();
        this.selectedRectId = r.id;
        // 同步更新左右两侧
        this.rectManager.renderRects(
            this.selectedRectId, 
            this._onSelect.bind(this), 
            this._onDrag.bind(this), 
            this._onResize.bind(this), 
            this.showAllLabels,
            this.scale
        );
        this.highlightSidebarForm(r.id);
    }

    _onDrag(e, r, box) {
        if (this.enableDraw) return;
        if (e.button !== 0) return;
        if (e.target.classList.contains('rect-handle')) return;
        e.stopPropagation();
        this.selectedRectId = r.id;
        this.highlightSidebarForm(r.id);
        this.rectManager.renderRects(this.selectedRectId, this._onSelect.bind(this), this._onDrag.bind(this), this._onResize.bind(this), this.showAllLabels, this.scale);
        this.dragInfo = {
            type: 'move',
            rect: r,
            startX: e.clientX,
            startY: e.clientY,
            origX: r.x,
            origY: r.y
        };
        document.body.style.cursor = 'move';
    }

    _onResize(e, r, box) {
        if (this.enableDraw) return;
        e.stopPropagation();
        this.dragInfo = {
            type: 'resize',
            rect: r,
            startX: e.clientX,
            startY: e.clientY,
            origW: r.width,
            origH: r.height
        };
        document.body.style.cursor = 'nwse-resize';
    }

    _onGlobalMouseMove(e) {
        if (!this.dragInfo) return;
        const r = this.dragInfo.rect;
        const scale = this.dragInfo.scale || this.scale || 1;
        if (this.dragInfo.type === 'move') {
            // 修正：移动时四舍五入，保证整数像素
            let dx = Math.round((e.clientX - this.dragInfo.startX) / scale);
            let dy = Math.round((e.clientY - this.dragInfo.startY) / scale);
            r.x = Math.max(0, Math.round(this.dragInfo.origX + dx));
            r.y = Math.max(0, Math.round(this.dragInfo.origY + dy));
            this.rectManager.renderRects(this.selectedRectId, this._onSelect.bind(this), this._onDrag.bind(this), this._onResize.bind(this), this.showAllLabels, this.scale);
            this.updateRectFormList();
        } else if (this.dragInfo.type === 'resize') {
            // 修正：缩放时四舍五入，保证整数像素
            let dx = Math.round((e.clientX - this.dragInfo.startX) / scale);
            let dy = Math.round((e.clientY - this.dragInfo.startY) / scale);
            let w = Math.round(this.dragInfo.origW + dx);
            let h = Math.round(this.dragInfo.origH + dy);
            if (w < 10) w = 10;
            if ( h < 10) h = 10;
            r.width = w;
            r.height = h;
            this.rectManager.renderRects(this.selectedRectId, this._onSelect.bind(this), this._onDrag.bind(this), this._onResize.bind(this), this.showAllLabels, this.scale);
            this.updateRectFormList();
        }
    }

    _onGlobalMouseUp(e) {
        if (this.dragInfo) {
            this.dragInfo = null;
            document.body.style.cursor = '';
        }
    }

    highlightSidebarForm(rectId) {
        const groups = this.rectFormList.querySelectorAll('.form-group');
        groups.forEach(g => g.classList.remove('active'));
        const group = Array.from(groups).find(g => {
            const label = g.querySelector('span');  // 改为查找 span 元素
            return label && label.textContent.startsWith(rectId + '.');  // 改为使用 startsWith 匹配
        });
        if (group) {
            group.classList.add('active');
            group.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
        }
    }

    updateRectFormList() {
        this.rectFormList.innerHTML = '';
        this.rectManager.rects.forEach((r, idx) => {
            const group = document.createElement('div');
            group.className = 'form-group';
            // 当前选中的框需要高亮显示
            if (this.selectedRectId === r.id) {
                group.classList.add('active');
            }

            group.onclick = (e) => {
                e.stopPropagation();
                this.selectedRectId = r.id;
                this.enableDraw = false;
                this.rectManager.setDrawMode(false);
                
                // 同步更新左右两侧
                this.rectManager.renderRects(
                    this.selectedRectId,
                    this._onSelect.bind(this),
                    this._onDrag.bind(this),
                    this._onResize.bind(this),
                    this.showAllLabels,
                    this.scale
                );
                this.highlightSidebarForm(r.id);
            };

            // 第一行：序号.文字 + 删除按钮
            const row1 = document.createElement('div');
            row1.style.display = 'flex';
            row1.style.alignItems = 'center';
            row1.style.justifyContent = 'space-between';

            const label = document.createElement('span');
            label.style.fontWeight = 'bold';
            label.style.fontSize = '15px';
            // 修改：侧边栏保留序号和文字，方便区分
            label.textContent = `${r.id}.${r.label}`;
            row1.appendChild(label);

            const delBtn = document.createElement('button');
            delBtn.textContent = '删除';
            delBtn.type = 'button';
            delBtn.style.marginLeft = '12px';
            delBtn.style.fontSize = '13px';
            delBtn.style.padding = '4px 12px';
            delBtn.onclick = (ev) => {
                ev.stopPropagation();
                this.rectManager.removeRectById(r.id);
            };
            row1.appendChild(delBtn);

            group.appendChild(row1);

            // 第二行：位置和大小
            const param = document.createElement('div');
            param.className = 'param';
            param.style.margin = '2px 0 2px 0';
            param.textContent = `位置(${r.x},${r.y}) 大小(${r.width}x${r.height})`;
            group.appendChild(param);

            // 第三行：文本输入和颜色选择并排
            const row3 = document.createElement('div');
            row3.style.display = 'flex';
            row3.style.gap = '8px';
            row3.style.alignItems = 'center';

            const input = document.createElement('input');
            input.type = 'text';
            input.value = r.label;
            input.style.flex = '1 1 0';
            input.style.fontSize = '13px';
            input.onchange = () => {
                r.label = input.value;
                if (this.rectManager.onChange) this.rectManager.onChange();
            };
            row3.appendChild(input);

            const colorSelect = document.createElement('select');
            colorSelect.className = 'rect-color-select';
            colorSelect.style.flex = '0 0 90px';
            [
                {value: "#7fffd4", text: "绿色"},
                {value: "#ff0000", text: "红色"},
                {value: "#888888", text: "灰色"},
                {value: "#060ac9", text: "蓝色"},
                {value: "#097b7e", text: "青色"},
                {value: "#e4710a", text: "橙色"},
                {value: "#ffffff", text: "白色"}
            ].forEach(opt => {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.text;
                if (r.color === opt.value) option.selected = true;
                colorSelect.appendChild(option);
            });
            colorSelect.onchange = () => {
                r.color = colorSelect.value;
                if (this.rectManager.onChange) this.rectManager.onChange();
            };
            row3.appendChild(colorSelect);

            group.appendChild(row3);

            this.rectFormList.appendChild(group);
        });

        // 如果有选中的框，确保滚动到视图中
        if (this.selectedRectId) {
            this.highlightSidebarForm(this.selectedRectId);
        }
    }

    _autoInitScale() {
        const img = this.drawArea.querySelector('img');
        if (!img) return;
        img.onload = () => {
            this._updateScaleAndRender();
        };
        if (img.complete) {
            this._updateScaleAndRender();
        }
    }

    _ensureRectsAboveImage() {
        // 保证所有.rect-box都在图片之后（即在图片上方）
        const img = this.drawArea.querySelector('img');
        if (!img) return;
        // 获取所有rect-box
        const rects = Array.from(this.drawArea.querySelectorAll('.rect-box'));
        rects.forEach(rect => {
            if (rect.nextSibling !== img.nextSibling) {
                // 移动到图片之后
                if (img.nextSibling) {
                    this.drawArea.insertBefore(rect, img.nextSibling);
                } else {
                    this.drawArea.appendChild(rect);
                }
            }
            rect.style.zIndex = 10;
        });
    }

    // 添加外部调用接口
    addRectFromExternal(x, y, width, height, color = "#7fffd4", label = null) {
        // 使用统一的Rect创建方式
        const newRect = new Rect(
            Math.round(x),
            Math.round(y),
            Math.round(width),
            Math.round(height),
            color,
            null,  // id会由manager自动分配
            label
        );
        
        // 使用统一的RectManager添加方式
        this.selectedRectId = this.rectManager.add(newRect);
        
        // 更新显示
        if (this.rectManager.onChange) {
            this.rectManager.onChange();
        }
        
        // 高亮显示新添加的框
        this.highlightSidebarForm(this.selectedRectId);
        
        return this.selectedRectId;  // 返回新框的ID
    }
}

window.Rect = Rect;
window.RectManager = RectManager;
window.RectUI = RectUI;