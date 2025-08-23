// static/js/helpers.js

/**
 * 从文件名中截取一个简短、可读的版本。
 * @param {string} name - 原始文件名。
 * @returns {string}
 */
export function truncateFilename(name) {
    const nameNoExt = name.replace(/\.\w+$/, '');
    const match = nameNoExt.match(/\d+/);
    if (!match) {
        return nameNoExt.length > 20 ? nameNoExt.substring(0, 17) + '...' : nameNoExt;
    }
    const numberStr = match[0];
    const index = match.index;
    const start = Math.max(0, index - 5);
    const end = Math.min(nameNoExt.length, index + numberStr.length + 5);
    let result = nameNoExt.substring(start, end);
    if (start > 0) {
        result = '…' + result;
    }
    if (end < nameNoExt.length) {
        result = result + '…';
    }
    return result;
}

/**
 * 递归查找树形结构中的第一个视频节点。
 * @param {Array<object>} nodes - 节点数组。
 * @returns {object|null}
 */
export function findFirstVideo(nodes) {
    for (const node of nodes) {
        if (node.type === 'video') {
            return node;
        }
        if (node.type === 'directory') {
            const found = findFirstVideo(node.children);
            if (found) {
                return found;
            }
        }
    }
    return null;
}

/**
 * 处理 EPUB 阅读器的键盘事件。
 * @param {Event} e - 键盘事件对象。
 * @param {object} rendition - EPUBJS 的 Rendition 对象。
 */
export function handleEpubKeys(e, rendition) {
    if (!rendition) return;
    try {
        if (e.key === "ArrowRight") {
            if (typeof rendition.next === 'function') rendition.next();
        } else if (e.key === "ArrowLeft") {
            if (typeof rendition.prev === 'function') rendition.prev();
        }
    } catch (err) {
        console.error("EPUB键盘导航出错:", err);
    }
}