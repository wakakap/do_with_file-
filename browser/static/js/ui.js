// static/js/ui.js
import { appState, galleryState, playerState, animePlayerState } from './state.js';
import * as api from './api.js';
import { truncateFilename, findFirstVideo, handleEpubKeys } from './helpers.js';

// --- 元素选择器 ---
const browseView = document.getElementById('browse-view');
const statsView = document.getElementById('stats-view');
const mediaContainer = document.getElementById('media-container');
const cardTemplate = document.getElementById('card-template');
const loadingIndicator = document.getElementById('loading-indicator');
const pathLabel = document.getElementById('current-path-label');
const backBtn = document.getElementById('back-btn');
const statsContainer = document.getElementById('stats-container');
const maintenanceMenu = document.getElementById('maintenance-menu');
const editTagsBtn = document.getElementById('edit-tags-btn');
const maintenanceBtn = document.getElementById('maintenance-btn');
const searchInput = document.getElementById('search-input');

// Viewers
const imageViewer = document.getElementById('image-viewer');
const imageContainer = imageViewer.querySelector('.image-container');
const progressBarContainer = document.getElementById('progress-bar-container');
const currentImage = document.getElementById('current-image');
const videoPlayer = document.getElementById('video-player');
const currentVideo = document.getElementById('current-video');
const albumView = document.getElementById('album-view');
const albumArtImg = document.getElementById('album-art-img');
const albumTitleText = document.getElementById('album-title-text');
const trackListUI = document.getElementById('track-list-ui');
const audioPlayer = document.getElementById('current-audio-player');
const playPauseBtn = document.getElementById('play-pause-btn');
const shuffleBtn = document.getElementById('shuffle-btn');
const repeatBtn = document.getElementById('repeat-btn');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const animeView = document.getElementById('anime-view');
const currentAnimeVideo = document.getElementById('current-anime-video');
const animeTitleText = document.getElementById('anime-title-text');
const episodeListUI = document.getElementById('episode-list-ui');
const toggleSubtitleBtn = document.getElementById('toggle-subtitle-btn');
const subtitleSelector = document.getElementById('subtitle-selector-btn');
const epubViewer = document.getElementById('epub-viewer');
const epubArea = document.getElementById('epub-area');
const prevEpubBtn = document.getElementById('prev-page-btn');
const nextEpubBtn = document.getElementById('next-page-btn');

// --- 常量 ---
const COLORS = ['#4e79a7', '#f28e2c', '#e15759', '#76b7b2', '#59a14f', '#edc949', '#af7aa1', '#ff9da7', '#9c755f', '#bab0ab'];
let epubKeyListenerAbortController = null;
let book = null;
let rendition = null;

// --- 核心UI渲染函数 ---

export function toggleView(viewName) {
    if (viewName === 'stats') {
        browseView.style.display = 'none';
        statsView.style.display = 'block';
        appState.currentView = 'stats';
        document.getElementById('stats-btn').textContent = '返回浏览';
        loadStatsData();
    } else {
        statsView.style.display = 'none';
        browseView.style.display = 'block';
        appState.currentView = 'browse';
        document.getElementById('stats-btn').textContent = '统计';
    }
}

export function showLoading(isLoading, clearContent = true) {
    loadingIndicator.style.display = isLoading ? 'block' : 'none';
    if (isLoading && clearContent) { mediaContainer.innerHTML = ''; }
}

export function renderCardsStaggered(items, index = 0, renderingId) {
    if (renderingId !== appState.renderingId || index >= items.length) return;
    const item = items[index];
    const cardClone = cardTemplate.content.cloneNode(true);
    const cardEl = cardClone.querySelector('.card');
    cardEl.dataset.path = item.full_path;
    cardEl.dataset.mediaPath = item.media_path;
    cardEl.dataset.isDir = item.is_dir;
    cardEl.dataset.isGallery = item.is_gallery;
    cardEl.dataset.nameNoExt = item.name_no_ext;
    const imgEl = cardClone.querySelector('img');
    const placeholderEl = cardClone.querySelector('.placeholder-text');
    if (item.cover_filename) {
        imgEl.src = `/api/media/${appState.mode}/cover/${encodeURIComponent(item.cover_filename)}`;
        imgEl.style.display = 'block';
        placeholderEl.style.display = 'none';
    } else {
        imgEl.style.display = 'none';
        placeholderEl.style.display = 'block';
        placeholderEl.textContent = item.name_no_ext;
    }
    const icon = item.is_dir ? '📁' : '📄';
    cardClone.querySelector('.card-filename').textContent = `${icon} ${item.name}`;
    const tagsEl = cardClone.querySelector('.card-tags');
    updateCardTagsDisplay(tagsEl, item.name_no_ext);
    mediaContainer.appendChild(cardClone);
    setTimeout(() => { if (renderingId !== appState.renderingId) return; renderCardsStaggered(items, index + 1, renderingId); }, 15);
}

export function updateCardTagsDisplay(tagsContainer, itemKey) {
    tagsContainer.innerHTML = '';
    const tags = appState.isTagEditMode ? appState.tempTagsData[itemKey] || [] : appState.tagsData[itemKey] || [];
    const visibleTags = tags.filter(tag => !tag.startsWith('*'));
    if (appState.isTagEditMode) {
        visibleTags.forEach(tag => {
            const unit = document.createElement('div');
            unit.className = 'tag-edit-unit';
            const tagEl = document.createElement('span');
            tagEl.className = 'card-tag';
            tagEl.textContent = tag;
            tagEl.style.backgroundColor = '#555';
            tagEl.style.cursor = 'default';
            const delBtn = document.createElement('span');
            delBtn.className = 'del-tag-btn';
            delBtn.textContent = '×';
            delBtn.onclick = (e) => { e.stopPropagation(); deleteTag(itemKey, tag); };
            unit.appendChild(tagEl);
            unit.appendChild(delBtn);
            tagsContainer.appendChild(unit);
        });
        const addBtn = document.createElement('span');
        addBtn.className = 'add-tag-btn';
        addBtn.textContent = '+';
        addBtn.onclick = (e) => { e.stopPropagation(); addTag(itemKey); };
        tagsContainer.appendChild(addBtn);
        const importBtn = document.createElement('span');
        importBtn.className = 'auto-import-btn';
        importBtn.textContent = '🔍';
        importBtn.title = '从DMM自动导入Tag';
        importBtn.onclick = (e) => { e.stopPropagation(); handleAutoImport(itemKey, importBtn); };
        tagsContainer.appendChild(importBtn);
    } else {
        visibleTags.forEach((tag, tagIndex) => {
            const tagEl = document.createElement('span');
            tagEl.className = 'card-tag';
            tagEl.textContent = tag;
            tagEl.dataset.tag = tag;
            const ratio = visibleTags.length > 1 ? tagIndex / (visibleTags.length - 1) : 0;
            const r = Math.round(95 * (1 - ratio) + 220 * ratio);
            const g = Math.round(15 * (1 - ratio) + 47 * ratio);
            const b = Math.round(64 * (1 - ratio) + 2 * ratio);
            tagEl.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
            tagEl.onclick = (e) => { e.stopPropagation(); searchInput.value = tag; document.getElementById('search-btn').click(); };
            tagsContainer.appendChild(tagEl);
        });
    }
}

export function refreshAllCardsTags() {
    document.querySelectorAll('.card').forEach(card => {
        const itemKey = card.dataset.nameNoExt;
        const tagsContainer = card.querySelector('.card-tags');
        if (itemKey && tagsContainer) updateCardTagsDisplay(tagsContainer, itemKey);
    });
}

export function renderPathLabel(mode, path) {
    pathLabel.textContent = `模式: ${mode} | ${path}`;
    backBtn.style.display = appState.pathStack.length > 1 ? 'inline-block' : 'none';
}

export function renderSearchLabel(query, type) {
    const searchLabel = type === 'tag' ? `標籤搜索: "${query}"` : `關鍵詞搜索: "${query}"`;
    pathLabel.textContent = searchLabel;
    backBtn.style.display = 'inline-block';
}

export function enterTagEditMode() {
    if (appState.isTagEditMode) return;
    appState.isTagEditMode = true;
    appState.tempTagsData = JSON.parse(JSON.stringify(appState.tagsData));
    editTagsBtn.textContent = "保存Tag";
    editTagsBtn.style.backgroundColor = 'red';
    maintenanceBtn.textContent = '保存中...';
    maintenanceBtn.style.backgroundColor = 'red';
    refreshAllCardsTags();
    maintenanceMenu.style.display = 'none';
}

export async function saveAndExitTagEditMode() {
    if (!appState.isTagEditMode) return;
    showLoading(true, false);
    const result = await api.saveTags(appState.tempTagsData);
    showLoading(false, false);
    if (result.status === 'success') {
        alert('Tag 已成功保存！');
        appState.tagsData = JSON.parse(JSON.stringify(appState.tempTagsData));
        exitTagEditMode();
    } else {
        alert(`Tag 保存失敗: ${result.message}`);
    }
}

export function exitTagEditMode() {
    appState.isTagEditMode = false;
    appState.tempTagsData = {};
    editTagsBtn.textContent = "编辑Tag";
    editTagsBtn.style.backgroundColor = '';
    maintenanceBtn.textContent = '维护';
    maintenanceBtn.style.backgroundColor = '';
    refreshAllCardsTags();
}

function addTag(itemKey) {
    const newTag = prompt(`為 "${itemKey}" 添加新Tag:`);
    if (newTag && newTag.trim()) {
        const tag = newTag.trim();
        if (tag.startsWith('*')) {
            alert('不能手动添加以 "*" 开头的特殊Tag。');
            return;
        }
        if (!appState.tempTagsData[itemKey]) appState.tempTagsData[itemKey] = [];
        if (!appState.tempTagsData[itemKey].includes(tag)) {
            appState.tempTagsData[itemKey].push(tag);
            refreshAllCardsTags();
        } else {
            alert(`Tag "${tag}" 已经存在。`);
        }
    }
}

function deleteTag(itemKey, tagToDelete) {
    if (appState.tempTagsData[itemKey]) {
        appState.tempTagsData[itemKey] = appState.tempTagsData[itemKey].filter(t => t !== tagToDelete);
        if (appState.tempTagsData[itemKey].length === 0) delete appState.tempTagsData[itemKey];
        refreshAllCardsTags();
    }
}

async function handleAutoImport(itemKey, buttonEl) {
    if (appState.activeImports[itemKey]) {
        appState.activeImports[itemKey].abort();
        return;
    }
    if (Object.keys(appState.activeImports).length > 0 && !appState.activeImports[itemKey]) {
        alert('其他的导入正在进行，请先完成当前的Tag导入操作。');
        return;
    }
    const originalText = buttonEl.textContent;
    buttonEl.disabled = true;
    buttonEl.textContent = '…';
    const controller = new AbortController();
    appState.activeImports[itemKey] = controller;
    try {
        const result = await api.autoImportTags(itemKey, controller.signal);
        delete appState.activeImports[itemKey];
        if (result.status === 'success') {
            if (!appState.tempTagsData[itemKey]) appState.tempTagsData[itemKey] = [];
            const existingTags = new Set(appState.tempTagsData[itemKey]);
            let newTagsAdded = 0;
            result.tags.forEach(tag => {
                if (!existingTags.has(tag)) {
                    appState.tempTagsData[itemKey].push(tag);
                    existingTags.add(tag);
                    newTagsAdded++;
                }
            });
            alert(`成功导入 ${newTagsAdded} 个新Tag！`);
            refreshAllCardsTags();
        } else {
            alert(`Tag导入失败: ${result.message}`);
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            alert(`项目 "${itemKey}" 的导入操作已取消。`);
        } else {
            alert("自动导入请求失败，请检查网络连接和服务器控制台日志。");
        }
    } finally {
        delete appState.activeImports[itemKey];
        buttonEl.disabled = false;
        buttonEl.textContent = originalText;
        refreshAllCardsTags();
    }
}

// --- 查看器相关函数 ---

export function openImageViewer(fullPath, mediaPath, itemKey, startIndex = 0, mode) {
    showLoading(true, false);
    api.getGalleryImages(mode, fullPath).then(files => {
        showLoading(false, false);
        if (files && !files.error && files.length > 0) {
            Object.assign(galleryState, {
                isOpen: true,
                baseMediaPath: mediaPath,
                files: files,
                currentIndex: -1,
                itemKey: itemKey,
                mode: mode,
            });
            imageViewer.classList.add('active');
            document.body.style.overflow = 'hidden';
            buildProgressBar();
            displayImage(startIndex);
        } else {
            alert('這個圖片集是空的或載入失敗！');
        }
    }).catch(err => {
        showLoading(false, false);
        alert('載入圖片集失敗：' + err);
    });
}

export function closeImageViewer() {
    galleryState.isOpen = false;
    imageViewer.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentImage.src = "";
    currentImage.style.opacity = 0;
    currentImage.style.transform = 'none';
    currentImage.style.maxWidth = '100%';
    currentImage.style.maxHeight = '100%';
    galleryState.rotationAngle = 0;
    if (document.fullscreenElement) {
        document.exitFullscreen();
    }
}

export function displayImage(index) {
    if (!galleryState.isOpen || galleryState.isLoading || index < 0 || index >= galleryState.files.length) return;
    if (galleryState.currentIndex !== index) api.recordView(galleryState.itemKey, index);
    galleryState.isLoading = true;
    currentImage.style.opacity = 0;
    applyImageViewerTransforms();
    setTimeout(() => {
        const imageName = galleryState.files[index];
        const imageUrl = `/api/media/${galleryState.mode}/pages/${galleryState.baseMediaPath}/${imageName}`;
        currentImage.src = imageUrl;
        currentImage.onload = () => {
            currentImage.style.opacity = 1;
            galleryState.currentIndex = index;
            updateProgressBar();
            preloadNextImage();
            galleryState.isLoading = false;
            applyImageViewerTransforms();
        };
        currentImage.onerror = () => { galleryState.isLoading = false; };
    }, 200);
}

function preloadNextImage() {
    const nextIndex = galleryState.currentIndex + 1;
    if (nextIndex < galleryState.files.length) {
        const type = 'pages';
        const nextImageName = galleryState.files[nextIndex];
        const nextImageUrl = `/api/media/${appState.mode}/${type}/${galleryState.baseMediaPath}/${nextImageName}`;
        new Image().src = nextImageUrl;
    }
}

export function applyImageViewerTransforms() {
    if (!galleryState.isOpen) return;
    const { rotationAngle } = galleryState;
    let scale = 1;
    if (rotationAngle === 90 || rotationAngle === 270) {
        currentImage.style.maxWidth = 'none';
        currentImage.style.maxHeight = 'none';
        const img = currentImage;
        const container = imageContainer;
        if (img.naturalWidth > 0 && img.naturalHeight > 0) {
            const scaleX = container.clientWidth / img.naturalHeight;
            const scaleY = container.clientHeight / img.naturalWidth;
            scale = Math.min(scaleX, scaleY);
        }
    } else {
        currentImage.style.maxWidth = '100%';
        currentImage.style.maxHeight = '100%';
    }
    currentImage.style.transformOrigin = `center center`;
    currentImage.style.transform = `rotate(${rotationAngle}deg) scale(${scale})`;
}

export function changeImage(direction) {
    if (!galleryState.isOpen) return;
    const newIndex = galleryState.currentIndex + direction;
    displayImage(newIndex);
}

function buildProgressBar() {
    progressBarContainer.innerHTML = '';
    const pageCount = galleryState.files.length;
    for (let i = 0; i < pageCount; i++) {
        const wrapper = document.createElement('div');
        wrapper.className = 'progress-segment-wrapper';
        wrapper.dataset.index = i;
        const label = document.createElement('span');
        label.className = 'progress-label';
        const segment = document.createElement('div');
        segment.className = 'progress-segment';
        if ((i + 1) % 10 === 0 && pageCount > 10) {
            wrapper.style.flexGrow = 2.2;
            label.textContent = i + 1;
        }
        wrapper.appendChild(label);
        wrapper.appendChild(segment);
        progressBarContainer.appendChild(wrapper);
    }
    progressBarContainer.addEventListener('click', (e) => {
        e.stopPropagation();
        const wrapper = e.target.closest('.progress-segment-wrapper');
        if (wrapper && wrapper.dataset.index) {
            const clickedIndex = parseInt(wrapper.dataset.index, 10);
            displayImage(clickedIndex);
        }
    });
}

function updateProgressBar() {
    const wrappers = progressBarContainer.children;
    for (let i = 0; i < wrappers.length; i++) {
        const segment = wrappers[i].querySelector('.progress-segment');
        if (segment) segment.classList.toggle('active', i === galleryState.currentIndex);
    }
}

export function toggleFullscreen() {
    if (!document.fullscreenElement) document.documentElement.requestFullscreen();
    else if (document.exitFullscreen) document.exitFullscreen();
}

export function openVideoPlayer(mediaPath) {
    const videoUrl = `/api/media/${appState.mode}/video/${mediaPath}`;
    videoPlayer.classList.add('active');
    document.body.style.overflow = 'hidden';
    currentVideo.src = videoUrl;
}

export function closeVideoPlayer() {
    videoPlayer.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentVideo.pause();
    currentVideo.src = "";
}

export async function openEpubViewer(mediaPath) {
    const closeBtn = epubViewer.querySelector('.close-btn');
    epubArea.innerHTML = '';
    epubViewer.classList.add('active');
    document.body.style.overflow = 'hidden';
    try {
        book = ePub(`/api/media/${appState.mode}/pages/${mediaPath}`);
        rendition = book.renderTo("epub-area", { manager: "default", view: "iframe", width: "100%", height: "100%", allowScriptedContent: true, sandbox: "allow-scripts allow-same-origin" });
        rendition.hooks.content.register(function(contents) {
            const stylesheet = contents.document.createElement("style");
            stylesheet.innerHTML = `html, body { width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important; box-sizing: border-box !important; } body > svg { width: 100% !important; height: 100% !important; padding: 0 !important; margin: 0 !important; } img, svg image { max-width: 100% !important; max-height: 100% !important; height: auto !important; object-fit: contain !important; display: block !important; margin: 0 auto !important; }`;
            contents.document.head.appendChild(stylesheet);
        });
        await rendition.display();
        closeBtn.onclick = () => closeEpubViewer();
        prevEpubBtn.onclick = () => { try { if (rendition && typeof rendition.prev === 'function') { rendition.prev(); } } catch (e) { console.error("无法执行 rendition.prev()，可能是EPUB文件不兼容:", e); } };
        nextEpubBtn.onclick = () => { try { if (rendition && typeof rendition.next === 'function') { rendition.next(); } } catch (e) { console.error("无法执行 rendition.next()，可能是EPUB文件不兼容:", e); } };
        epubKeyListenerAbortController = new AbortController();
        document.addEventListener('keydown', (e) => handleEpubKeys(e, rendition), { signal: epubKeyListenerAbortController.signal });
    } catch (err) {
        console.error("EPUB rendering failed:", err);
        alert("加载 EPUB 文件失败，请检查文件是否有效以及控制台错误。");
        closeEpubViewer();
    }
}

export function closeEpubViewer() {
    if (epubKeyListenerAbortController) {
        epubKeyListenerAbortController.abort();
        epubKeyListenerAbortController = null;
    }
    epubViewer.classList.remove('active');
    document.body.style.overflow = 'auto';
    prevEpubBtn.onclick = null;
    nextEpubBtn.onclick = null;
    if (book) {
        book.destroy();
        book = null;
        rendition = null;
    }
}

export async function openAlbumView(fullPath, mediaPath, nameNoExt, startTrackName = null) {
    const details = await api.getAlbumDetails(fullPath);
    if (details && !details.error && details.tracks.length > 0) {
        playerState.currentTracklist = [...details.tracks];
        playerState.originalTracklist = [...details.tracks];
        Object.assign(playerState, {
            baseMediaPath: mediaPath,
            currentIndex: -1,
            isShuffled: false,
            repeatMode: 'ALL',
            itemKey: nameNoExt,
        });
        albumTitleText.textContent = nameNoExt;
        albumArtImg.src = details.cover_image ? `/api/media/MUSIC/cover/${encodeURIComponent(details.cover_image)}` : '';
        albumArtImg.onerror = () => { albumArtImg.src = ''; };
        buildTracklistUI(details.tracks);
        albumView.classList.add('active');
        document.body.style.overflow = 'hidden';
        updatePlayerControlsUI();
        if (startTrackName) {
            const startIndex = details.tracks.findIndex(track => track === startTrackName);
            if (startIndex !== -1) {
                playTrack(startIndex);
            }
        }
    } else {
        alert('这个专辑是空的或加载失败！');
    }
}

export function closeAlbumView() {
    albumView.classList.remove('active');
    document.body.style.overflow = 'auto';
    audioPlayer.pause();
    audioPlayer.src = '';
    playerState.isPlaying = false;
}

function buildTracklistUI(tracks) {
    trackListUI.innerHTML = '';
    tracks.forEach((track, index) => {
        const li = document.createElement('li');
        li.className = 'track-item';
        li.dataset.index = index;
        const trackNum = document.createElement('span');
        trackNum.className = 'track-number';
        trackNum.textContent = index + 1;
        const trackTitleSpan = document.createElement('span');
        trackTitleSpan.className = 'track-title';
        trackTitleSpan.textContent = track.replace(/\.\w+$/, '');
        li.appendChild(trackNum);
        li.appendChild(trackTitleSpan);
        trackListUI.appendChild(li);
    });
}

export function playTrack(index) {
    if (index < 0 || index >= playerState.currentTracklist.length) {
        playerState.isPlaying = false;
        playerState.currentIndex = -1;
        audioPlayer.src = '';
        updatePlayerControlsUI();
        document.querySelectorAll('#track-list-ui .track-item.playing').forEach(item => item.classList.remove('playing'));
        return;
    }
    playerState.currentIndex = index;
    const trackName = playerState.currentTracklist[index];
    api.recordView(playerState.itemKey, trackName);
    audioPlayer.src = `/api/media/MUSIC/audio/${playerState.baseMediaPath}/${encodeURIComponent(trackName)}`;
    audioPlayer.play();
    document.querySelectorAll('#track-list-ui .track-item').forEach((item, i) => {
        item.classList.toggle('playing', i === index);
    });
}

export function togglePlayPause() {
    if (playerState.isPlaying) {
        audioPlayer.pause();
    } else {
        if (playerState.currentIndex === -1 && playerState.currentTracklist.length > 0) {
            playTrack(0);
        } else {
            audioPlayer.play();
        }
    }
}

export function playNextTrack() {
    let nextIndex;
    if (playerState.isShuffled) {
        nextIndex = Math.floor(Math.random() * playerState.currentTracklist.length);
        if (nextIndex === playerState.currentIndex && playerState.currentTracklist.length > 1) {
            nextIndex = (nextIndex + 1) % playerState.currentTracklist.length;
        }
    } else {
        nextIndex = playerState.currentIndex + 1;
    }
    if (nextIndex >= playerState.currentTracklist.length && playerState.repeatMode !== 'ALL') {
        playTrack(-1);
    } else {
        playTrack(nextIndex % playerState.currentTracklist.length);
    }
}

export function playPrevTrack() {
    if (audioPlayer.currentTime > 3) {
        playTrack(playerState.currentIndex);
    } else {
        let prevIndex = playerState.currentIndex - 1;
        if (prevIndex < 0 && playerState.repeatMode === 'ALL') {
            prevIndex = playerState.currentTracklist.length - 1;
        }
        playTrack(prevIndex);
    }
}

export function handleTrackEnd() {
    if (playerState.repeatMode === 'ONE') {
        playTrack(playerState.currentIndex);
    } else {
        playNextTrack();
    }
}

export function toggleShuffle() {
    playerState.isShuffled = !playerState.isShuffled;
    const currentTrackName = playerState.currentTracklist[playerState.currentIndex];
    if (playerState.isShuffled) {
        let array = [...playerState.originalTracklist];
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        playerState.currentTracklist = array;
    } else {
        playerState.currentTracklist = [...playerState.originalTracklist];
    }
    buildTracklistUI(playerState.currentTracklist);
    playerState.currentIndex = playerState.currentTracklist.indexOf(currentTrackName);
    if (playerState.currentIndex !== -1) {
        const currentTrackElement = trackListUI.querySelector(`.track-item[data-index='${playerState.currentIndex}']`);
        if (currentTrackElement) {
            currentTrackElement.classList.add('playing');
        }
    }
    updatePlayerControlsUI();
}

export function cycleRepeatMode() {
    const modes = ['NONE', 'ALL', 'ONE'];
    let currentModeIndex = modes.indexOf(playerState.repeatMode);
    currentModeIndex = (currentModeIndex + 1) % modes.length;
    playerState.repeatMode = modes[currentModeIndex];
    updatePlayerControlsUI();
}

export function updatePlayerControlsUI() {
    playPauseBtn.textContent = playerState.isPlaying ? '暂停' : '播放';
    shuffleBtn.textContent = playerState.isShuffled ? '随机已开' : '随机已关';
    shuffleBtn.classList.toggle('active', playerState.isShuffled);
    repeatBtn.classList.toggle('active', playerState.repeatMode !== 'NONE');
    switch (playerState.repeatMode) {
        case 'NONE': repeatBtn.textContent = '顺序播放'; break;
        case 'ALL': repeatBtn.textContent = '列表循环'; break;
        case 'ONE': repeatBtn.textContent = '单曲循环'; break;
    }
}

export async function openAnimeView(fullPath, mediaPath, nameNoExt, mode, startEpisodePath = null) {
    const details = await api.getAnimeDetails(fullPath);
    if (details && !details.error && details.tree && details.tree.length > 0) {
        Object.assign(animePlayerState, {
            baseMediaPath: mediaPath,
            episodeTree: details.tree,
            currentPlayingPath: null,
            itemKey: nameNoExt,
        });
        animeTitleText.textContent = nameNoExt;
        buildEpisodeListUI(details.tree);
        animeView.classList.add('active');
        document.body.style.overflow = 'hidden';
        let episodeToPlay = null;
        if (startEpisodePath) {
            function findEpisode(nodes, path) {
                for (const node of nodes) {
                    if (node.type === 'video' && node.path === path) return node;
                    if (node.type === 'directory') {
                        const found = findEpisode(node.children, path);
                        if (found) return found;
                    }
                }
                return null;
            }
            episodeToPlay = findEpisode(details.tree, startEpisodePath);
        }
        if (!episodeToPlay) {
            episodeToPlay = findFirstVideo(details.tree);
        }
        if (episodeToPlay) {
            playEpisode(episodeToPlay.path, episodeToPlay.subtitles);
        }
    } else {
        alert('这个文件夹是空的或加载失败！');
    }
}

export function closeAnimeView() {
    animeView.classList.remove('active');
    document.body.style.overflow = 'auto';
    currentAnimeVideo.pause();
    currentAnimeVideo.src = '';
    const oldTrack = currentAnimeVideo.querySelector('track');
    if (oldTrack) oldTrack.remove();
}

function buildEpisodeListUI(nodes) {
    episodeListUI.innerHTML = '';
    function createNode(node, parentElement) {
        const li = document.createElement('li');
        if (node.type === 'directory') {
            li.className = 'episode-item episode-folder';
            li.textContent = `📁 ${node.name}`;
            li.title = node.name;
            const childrenUl = document.createElement('ul');
            childrenUl.style.display = 'none';
            childrenUl.style.paddingLeft = '20px';
            childrenUl.style.listStyle = 'none';
            node.children.forEach(childNode => createNode(childNode, childrenUl));
            li.appendChild(childrenUl);
        } else if (node.type === 'video') {
            li.className = 'episode-item episode-video';
            li.textContent = truncateFilename(node.name);
            li.title = node.name;
            li.dataset.videoPath = node.path;
            if (node.subtitles && node.subtitles.length > 0) {
                li.dataset.subtitles = JSON.stringify(node.subtitles);
            }
            if (node.path === animePlayerState.currentPlayingPath) {
                li.classList.add('playing');
            }
        }
        parentElement.appendChild(li);
    }
    nodes.forEach(node => createNode(node, episodeListUI));
}

export function loadSubtitleTrack(subtitlePath) {
    const existingTracks = currentAnimeVideo.querySelectorAll('track');
    existingTracks.forEach(track => track.remove());
    if (!subtitlePath) {
        toggleSubtitleBtn.textContent = '无可用字幕';
        toggleSubtitleBtn.disabled = true;
        return;
    }
    const subtitleUrl = `/api/media/ANIME/pages/${animePlayerState.baseMediaPath}/${encodeURIComponent(subtitlePath)}`;
    const trackEl = document.createElement('track');
    trackEl.kind = 'subtitles';
    trackEl.label = subtitlePath.split('/').pop();
    trackEl.srclang = 'zh';
    trackEl.src = subtitleUrl;
    trackEl.default = true;
    currentAnimeVideo.appendChild(trackEl);
    setTimeout(() => {
        if (currentAnimeVideo.textTracks.length > 0) {
            currentAnimeVideo.textTracks[0].mode = animePlayerState.areSubtitlesVisible ? 'showing' : 'hidden';
        }
    }, 200);
    toggleSubtitleBtn.textContent = animePlayerState.areSubtitlesVisible ? '隐藏字幕' : '显示字幕';
    toggleSubtitleBtn.disabled = false;
}

export function playEpisode(videoPath, subtitles = []) {
    if (!videoPath) return;
    api.recordView(animePlayerState.itemKey, videoPath);
    currentAnimeVideo.onloadedmetadata = null;
    currentAnimeVideo.pause();
    currentAnimeVideo.src = '';
    currentAnimeVideo.load();
    animePlayerState.currentPlayingPath = videoPath;
    currentAnimeVideo.src = `/api/media/ANIME/pages/${animePlayerState.baseMediaPath}/${encodeURIComponent(videoPath)}`;
    const selector = document.getElementById('subtitle-selector-btn');
    selector.innerHTML = '';
    if (subtitles.length > 0) {
        selector.style.display = 'inline-block';
        subtitles.forEach(subPath => {
            const option = document.createElement('option');
            option.value = subPath;
            option.textContent = subPath.split('/').pop();
            selector.appendChild(option);
        });
        loadSubtitleTrack(subtitles[0]);
    } else {
        selector.style.display = 'none';
        loadSubtitleTrack(null);
    }
    document.querySelectorAll('#episode-list-ui .episode-item.playing').forEach(item => {
        item.classList.remove('playing');
    });
    const playingItem = episodeListUI.querySelector(`li[data-video-path="${CSS.escape(videoPath)}"]`);
    if (playingItem) playingItem.classList.add('playing');
    currentAnimeVideo.load();
    currentAnimeVideo.play().catch(error => console.error("视频播放失败:", error));
}

export function toggleSubtitles() {
    if (!currentAnimeVideo.textTracks || currentAnimeVideo.textTracks.length === 0) {
        alert("当前视频没有找到可用字幕。");
        return;
    }
    animePlayerState.areSubtitlesVisible = !animePlayerState.areSubtitlesVisible;
    const newMode = animePlayerState.areSubtitlesVisible ? 'showing' : 'hidden';
    currentAnimeVideo.textTracks[0].mode = newMode;
    toggleSubtitleBtn.textContent = animePlayerState.areSubtitlesVisible ? '隐藏字幕' : '显示字幕';
}

export async function loadStatsData() {
    showLoading(true, true);
    try {
        const statsData = await api.getStats();
        statsContainer.innerHTML = '';
        if (statsData.length === 0) {
            statsContainer.innerHTML = '<p>暂无任何访问记录。</p>';
            return;
        }
        const maxRankingViews = statsData.length > 0 ? Math.max(...statsData.map(item => item.ranking_views || 0)) : 0;
        statsData.forEach((item, itemIndex) => {
            const statRow = document.createElement('div');
            statRow.className = 'stat-row';
            const label = document.createElement('div');
            label.className = 'stat-label';
            label.textContent = item.name;
            const barWrapper = document.createElement('div');
            barWrapper.className = 'stat-bar-wrapper';
            const barContainer = document.createElement('div');
            barContainer.className = 'stat-bar-container';
            const bar = document.createElement('div');
            bar.className = 'stat-bar';
            if (maxRankingViews > 0) {
                const widthPercentage = (item.ranking_views / maxRankingViews) * 100;
                bar.style.width = `${widthPercentage}%`;
            } else {
                bar.style.width = '0%';
            }
            const mainSegment = document.createElement('div');
            mainSegment.className = 'stat-bar-segment';
            mainSegment.style.width = '100%';
            mainSegment.style.backgroundColor = COLORS[itemIndex % COLORS.length];
            mainSegment.dataSource = item;
            const hasChildren = item.type === 'directory' && item.children && item.children.length > 0;
            if (hasChildren) {
                mainSegment.classList.add('expandable');
            }
            mainSegment.addEventListener('click', handleSegmentClick);
            const mainLabel = document.createElement('span');
            mainLabel.className = 'segment-label';
            mainLabel.textContent = item.name;
            mainSegment.appendChild(mainLabel);
            bar.appendChild(mainSegment);
            const total = document.createElement('div');
            total.className = 'stat-total';
            total.textContent = item.ranking_views || 0;
            barContainer.appendChild(bar);
            barWrapper.appendChild(barContainer);
            barWrapper.appendChild(total);
            statRow.appendChild(label);
            statRow.appendChild(barWrapper);
            statsContainer.appendChild(statRow);
        });
    } catch (error) {
        statsContainer.innerHTML = `<p style="padding:20px;">加载统计数据失败: ${error.message}</p>`;
        console.error("Fetch stats error:", error);
    } finally {
        showLoading(false, false);
    }
}

function renderDrillDownBar(barElement, data, parentData) {
    barElement.innerHTML = '';
    data.slice(0, 25).forEach((child, index) => {
        const segment = document.createElement('div');
        segment.className = 'stat-bar-segment';
        segment.dataSource = child;
        const hasChildren = (child.children && child.children.length > 0) || (child.sub_children && child.sub_children.length > 0);
        
        // --- 核心修改区域 ---
        const fullPathForStats = child.full_path || parentData.full_path; // 获取文件或其父容器的路径

        if (child.type === 'page') {
            segment.classList.add('clickable');
            segment.addEventListener('click', async () => {
                await api.recordStatsView(parentData.full_path); // 先记录访问
                openImageViewer(parentData.full_path, parentData.media_path, parentData.name, child.page_index, parentData.mode);
            });
        } else if (child.type === 'item' && child.mode === 'JAV') {
            segment.classList.add('clickable');
            segment.addEventListener('click', async () => {
                await api.recordStatsView(child.full_path); // 先记录访问
                openVideoPlayer(child.media_path, child.mode);
            });
        } else if (child.type === 'item' && child.mode === 'ANIME') {
            segment.classList.add('clickable');
            segment.addEventListener('click', async () => {
                await api.recordStatsView(child.full_path); // 先记录访问
                openAnimeView(parentData.full_path, parentData.media_path, parentData.name, parentData.mode, child.media_path);
            });
        } else if (child.type === 'item' && child.mode === 'MUSIC') {
            segment.classList.add('clickable');
            segment.addEventListener('click', async () => {
                await api.recordStatsView(child.full_path); // 先记录访问
                openAlbumView(parentData.full_path, parentData.media_path, parentData.name, child.name);
            });
        } else if (hasChildren) {
            segment.classList.add('expandable');
            segment.addEventListener('click', handleSegmentClick);
        }
        const widthValue = child.aggregation_views || child.views || 0;
        segment.style.flex = `${widthValue} 1 0%`;
        segment.style.backgroundColor = COLORS[index % COLORS.length];
        let displayValue;
        if (child.type === 'directory') {
            displayValue = child.ranking_views || 0;
        } else {
            displayValue = child.views || child.aggregation_views || 0;
        }
        segment.title = `${child.name}: ${displayValue} 次`;
        const segmentLabel = document.createElement('span');
        segmentLabel.className = 'segment-label';
        segmentLabel.textContent = `${child.name} (${displayValue})`;
        segment.appendChild(segmentLabel);
        barElement.appendChild(segment);
    });
}

function removeAllSubsequentDrilldowns(startElement) {
    let currentElement = startElement;
    while (currentElement && currentElement.classList.contains('drilldown-row')) {
        const nextSibling = currentElement.nextElementSibling;
        currentElement.remove();
        currentElement = nextSibling;
    }
}

function handleSegmentClick(event) {
    event.stopPropagation();
    const segment = event.currentTarget;
    const data = segment.dataSource;
    const childrenData = data.children || data.sub_children;
    
    // 如果没有子数据，则直接返回
    if (!childrenData || childrenData.length === 0) return;

    const parentRow = segment.closest('.stat-row');
    const nextElement = parentRow.nextElementSibling;
    const isDrilldownRow = nextElement && nextElement.classList.contains('drilldown-row');
    const segmentId = data.full_path || data.name;

    // 如果点击的是已经展开的区域，则收起所有下层
    if (isDrilldownRow && nextElement.dataset.expandedBy === segmentId) {
        removeAllSubsequentDrilldowns(nextElement);
    } else {
        // 否则，收起旧的，展开新的
        if (isDrilldownRow) {
            removeAllSubsequentDrilldowns(nextElement);
        }

        // --- 核心修正区域：正确构建并嵌套元素 ---
        const drilldownRow = document.createElement('div');
        drilldownRow.className = 'drilldown-row stat-row';
        drilldownRow.dataset.expandedBy = segmentId;

        const barWrapper = document.createElement('div');
        barWrapper.className = 'stat-bar-wrapper';

        const barContainer = document.createElement('div');
        barContainer.className = 'stat-bar-container';

        const newBar = document.createElement('div');
        newBar.className = 'stat-bar';
        newBar.style.width = '100%';

        // 调用渲染函数，填充 newBar
        renderDrillDownBar(newBar, childrenData, data);
        
        // 将所有元素正确地嵌套起来
        barContainer.appendChild(newBar);
        barWrapper.appendChild(barContainer);
        drilldownRow.appendChild(barWrapper);
        
        // 将完整的行插入到 DOM 中
        parentRow.insertAdjacentElement('afterend', drilldownRow);
    }
}