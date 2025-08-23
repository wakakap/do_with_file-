// static/js/api.js

/**
 * 通用的数据获取函数。
 * @param {string} url - API 路由。
 * @returns {Promise<any>} - 成功时返回JSON数据。
 */
async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Fetch error:", error);
        return { error: error.message };
    }
}

/**
 * 浏览指定路径的媒体项目。
 * @param {string} mode - 当前模式。
 * @param {string} path - 要浏览的路径。
 * @returns {Promise<any>}
 */
export async function browse(mode, path = '') {
    const url = path ? `/api/browse?mode=${mode}&path=${encodeURIComponent(path)}` : `/api/browse?mode=${mode}`;
    return fetchData(url);
}

/**
 * 搜索媒体项目。
 * @param {string} mode - 当前模式。
 * @param {string} query - 搜索关键词。
 * @param {string} type - 搜索类型 ('keyword' 或 'tag')。
 * @returns {Promise<any>}
 */
export async function search(mode, query, type = 'keyword') {
    if (!query) return { search_term: "", items: [] };
    const url = `/api/search?mode=${mode}&q=${encodeURIComponent(query)}&type=${encodeURIComponent(type)}`;
    return fetchData(url);
}

/**
 * 获取画廊（图片集）的图片列表。
 * @param {string} mode - 模式。
 * @param {string} fullPath - 完整文件路径。
 * @returns {Promise<any>}
 */
export async function getGalleryImages(mode, fullPath) {
    const url = `/api/gallery?mode=${mode}&path=${encodeURIComponent(fullPath)}`;
    return fetchData(url);
}

/**
 * 记录项目的访问次数。
 * @param {string} itemKey - 项目的唯一键。
 * @param {number|string} [identifier=null] - 页面索引或媒体文件名。
 * @returns {Promise<void>}
 */
export async function recordView(itemKey, identifier = null) {
    try {
        await fetch('/api/record_view', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_key: itemKey, identifier: identifier }),
        });
    } catch (error) {
        console.error('Failed to record view:', error);
    }
}

/**
 * 获取所有标签数据。
 * @returns {Promise<any>}
 */
export async function getTags() {
    return fetchData('/api/tags');
}

/**
 * 保存标签数据。
 * @param {object} tagsData - 要保存的标签数据。
 * @returns {Promise<any>}
 */
export async function saveTags(tagsData) {
    return fetch('/api/tags', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tagsData),
    }).then(res => res.json());
}

/**
 * 自动导入标签。
 * @param {string} itemName - 项目名称。
 * @param {AbortSignal} signal - 用于取消请求的信号。
 * @returns {Promise<any>}
 */
export async function autoImportTags(itemName, signal) {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_name: itemName }),
        signal: signal
    };
    return fetch('/api/auto_import_tags', options).then(res => res.json());
}

/**
 * 获取专辑详情。
 * @param {string} fullPath - 专辑的完整路径。
 * @returns {Promise<any>}
 */
export async function getAlbumDetails(fullPath) {
    return fetchData(`/api/album_details?mode=MUSIC&path=${encodeURIComponent(fullPath)}`);
}

/**
 * 获取动画详情。
 * @param {string} fullPath - 动画的完整路径。
 * @returns {Promise<any>}
 */
export async function getAnimeDetails(fullPath) {
    return fetchData(`/api/anime_details?mode=ANIME&path=${encodeURIComponent(fullPath)}`);
}

/**
 * 获取统计数据。
 * @returns {Promise<any>}
 */
export async function getStats() {
    return fetchData('/api/structured_stats');
}

/**
 * 生成封面。
 * @param {string} mode - 模式。
 * @param {string} path - 路径。
 * @returns {Promise<any>}
 */
export async function generateCovers(mode, path) {
    const options = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: mode, path: path }),
    };
    return fetch('/api/generate_covers', options).then(res => res.json());
}

/**
 * 打开本地文件夹。
 * @param {string} path - 文件夹路径。
 * @returns {Promise<any>}
 */
export async function openFolder(path) {
    return fetchData(`/api/open_folder?path=${encodeURIComponent(path)}`);
}

/**
 * 从统计页面记录一次特殊的、递归的访问。
 * @param {string} fullPath - 被点击项的完整物理路径。
 * @returns {Promise<any>}
 */
export async function recordStatsView(fullPath) {
    return fetch('/api/record_stats_view', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_path: fullPath }),
    }).then(res => res.json());
}