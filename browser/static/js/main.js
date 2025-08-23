// static/js/main.js
import { appState, playerState, animePlayerState, galleryState } from './state.js';
import * as api from './api.js';
import * as ui from './ui.js';

// --- 元素选择器 ---
const modeSelector = document.getElementById('mode-selector');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const backBtn = document.getElementById('back-btn');
const statsBtn = document.getElementById('stats-btn');
const mediaContainer = document.getElementById('media-container');
const openFolderBtn = document.getElementById('open-folder-btn');
const maintenanceBtn = document.getElementById('maintenance-btn');
const maintenanceMenu = document.getElementById('maintenance-menu');
const generateCoversBtn = document.getElementById('generate-covers-btn');
const editTagsBtn = document.getElementById('edit-tags-btn');

// Viewer-related
const imageViewer = document.getElementById('image-viewer');
const imageViewerCloseBtn = imageViewer.querySelector('.close-btn');
const videoPlayer = document.getElementById('video-player');
const videoPlayerCloseBtn = videoPlayer.querySelector('.close-btn');
const albumView = document.getElementById('album-view');
const albumViewCloseBtn = albumView.querySelector('.close-btn');
const animeView = document.getElementById('anime-view');
const animeViewCloseBtn = animeView.querySelector('.close-btn');
const epubViewer = document.getElementById('epub-viewer');
const epubViewerCloseBtn = epubViewer.querySelector('.close-btn');
const currentImage = document.getElementById('current-image');
const playPauseBtn = document.getElementById('play-pause-btn');
const nextBtn = document.getElementById('next-btn');
const prevBtn = document.getElementById('prev-btn');
const shuffleBtn = document.getElementById('shuffle-btn');
const repeatBtn = document.getElementById('repeat-btn');
const trackListUI = document.getElementById('track-list-ui');
const audioPlayer = document.getElementById('current-audio-player');
const episodeListUI = document.getElementById('episode-list-ui');
const subtitleSelector = document.getElementById('subtitle-selector-btn');
const toggleSubtitleBtn = document.getElementById('toggle-subtitle-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');


// --- 核心应用逻辑 ---
async function browse(path = '') {
    if(appState.isTagEditMode && !await confirmExitTagEditMode()) return;
    appState.inSearchMode = false;
    searchInput.value = '';
    appState.renderingId++;
    ui.showLoading(true);
    const data = await api.browse(appState.mode, path);
    if (data && data.items) {
        appState.currentPath = data.current_path;
        if (!appState.pathStack.length || appState.pathStack[appState.pathStack.length - 1] !== data.current_path) {
            appState.pathStack.push(data.current_path);
        }
        ui.renderPathLabel(appState.mode, appState.currentPath);
        ui.renderCardsStaggered(data.items, 0, appState.renderingId);
    } else {
        mediaContainer.innerHTML = `<p style="padding:20px;">載入失敗: ${data.error}</p>`;
    }
    ui.showLoading(false);
}

async function search(query, type = 'keyword') {
    if (!query) return;
    if(appState.isTagEditMode && !await confirmExitTagEditMode()) return;
    appState.inSearchMode = true;
    appState.renderingId++;
    ui.showLoading(true);
    const data = await api.search(appState.mode, query, type);
    if (data && data.items) {
        ui.renderSearchLabel(query, type);
        ui.renderCardsStaggered(data.items, 0, appState.renderingId);
    } else {
        mediaContainer.innerHTML = `<p style="padding:20px;">載入失敗: ${data.error}</p>`;
    }
    ui.showLoading(false);
}

async function goBack() {
    if (appState.isTagEditMode && !await confirmExitTagEditMode()) return;
    if (appState.inSearchMode) {
        appState.inSearchMode = false;
        searchInput.value = '';
        const targetPath = appState.pathStack.length > 0 ? appState.pathStack[appState.pathStack.length - 1] : '';
        browse(targetPath);
        return;
    }
    if (appState.pathStack.length > 1) {
        appState.pathStack.pop();
        const prevPath = appState.pathStack[appState.pathStack.length - 1];
        browse(prevPath);
    }
}

async function confirmExitTagEditMode() {
    const hasChanges = JSON.stringify(appState.tagsData) !== JSON.stringify(appState.tempTagsData);
    if (!hasChanges || confirm("您有未保存的Tag修改，確定要放棄嗎？")) {
        ui.exitTagEditMode();
        return true;
    }
    return false;
}

// --- 事件监听器 ---
document.addEventListener('DOMContentLoaded', async () => {
    appState.tagsData = await api.getTags().catch(() => ({}));
    browse();

    modeSelector.addEventListener('change', async (e) => {
        if (appState.isTagEditMode && !await confirmExitTagEditMode()) {
            e.target.value = appState.mode;
            return;
        }
        appState.mode = e.target.value;
        document.getElementById('media-container').className = appState.mode.toLowerCase() + '-mode';
        appState.pathStack = [];
        appState.inSearchMode = false;
        browse();
    });

    backBtn.addEventListener('click', goBack);
    searchBtn.addEventListener('click', () => search(searchInput.value, 'keyword'));
    searchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') search(searchInput.value, 'keyword'); });
    statsBtn.addEventListener('click', () => {
        if (appState.currentView === 'browse') {
            ui.toggleView('stats');
        } else {
            ui.toggleView('browse');
            browse(); // When returning from stats, refresh the browse view
        }
    });
    mediaContainer.addEventListener('click', (e) => {
        const imageWrapper = e.target.closest('.card-image-wrapper');
        if (!imageWrapper) return;
        const card = imageWrapper.closest('.card');
        if (!card) return;
        if (appState.isTagEditMode) return;
        api.recordView(card.dataset.nameNoExt);
        const {
            path: fullPath,
            mediaPath,
            isGallery: isGalleryStr,
            isDir: isDirStr,
            nameNoExt
        } = card.dataset;
        const isGallery = isGalleryStr === 'true';
        const isDir = isDirStr === 'true';
        if (isDir && appState.mode === 'ANIME') {
            ui.openAnimeView(fullPath, mediaPath, nameNoExt, appState.mode);
        } else if (isDir && appState.mode === 'MUSIC') {
            ui.openAlbumView(fullPath, mediaPath, nameNoExt);
        } else if (isGallery) {
            ui.openImageViewer(fullPath, mediaPath, nameNoExt, 0, appState.mode);
        } else if (isDir) {
            browse(fullPath);
        } else {
            const isEpub = fullPath.toLowerCase().endsWith('.epub');
            if (appState.mode === 'JAV' || appState.mode === 'ANIME') {
                ui.openVideoPlayer(mediaPath);
            } else if (isEpub) {
                ui.openEpubViewer(mediaPath);
            } else {
                alert(`點擊了檔案：${fullPath}\n此類檔案的點擊行為尚未定義。`);
            }
        }
    });

    openFolderBtn.addEventListener('click', async () => {
        if (!appState.inSearchMode && appState.pathStack.length > 0) {
            const currentDir = appState.pathStack[appState.pathStack.length - 1];
            await api.openFolder(currentDir);
        } else {
            alert("無法在搜索結果頁面打開目錄。");
        }
    });

    // Viewer Listeners
    imageViewerCloseBtn.addEventListener('click', (e) => { e.stopPropagation(); ui.closeImageViewer(); });
    videoPlayerCloseBtn.addEventListener('click', () => ui.closeVideoPlayer());
    albumViewCloseBtn.addEventListener('click', () => ui.closeAlbumView());
    animeViewCloseBtn.addEventListener('click', () => ui.closeAnimeView());
    epubViewerCloseBtn.addEventListener('click', () => ui.closeEpubViewer());

    fullscreenBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        ui.toggleFullscreen();
    });

    imageViewer.querySelector('.image-container').addEventListener('click', () => ui.changeImage(1));
    imageViewer.querySelector('.image-container').addEventListener('contextmenu', (e) => { e.preventDefault(); ui.changeImage(-1); });

    imageViewer.addEventListener('wheel', (e) => {
        e.preventDefault();
        e.stopPropagation();
        clearTimeout(galleryState.wheelDebounceTimeout);
        galleryState.wheelDebounceTimeout = setTimeout(() => {
            currentImage.style.transition = 'none';
            galleryState.rotationAngle = (galleryState.rotationAngle + (e.deltaY > 0 ? 90 : -90) + 360) % 360;
            ui.applyImageViewerTransforms();
            setTimeout(() => {
                currentImage.style.transition = '';
            }, 50);
        }, 100);
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (galleryState.isOpen) ui.closeImageViewer();
            else if (videoPlayer.classList.contains('active')) ui.closeVideoPlayer();
            else if (albumView.classList.contains('active')) ui.closeAlbumView();
            else if (animeView.classList.contains('active')) ui.closeAnimeView();
            else if (epubViewer.classList.contains('active')) ui.closeEpubViewer();
            return;
        }
        if (galleryState.isOpen) {
            if (e.key === 'ArrowRight') {
                ui.changeImage(1);
            } else if (e.key === 'ArrowLeft') {
                ui.changeImage(-1);
            }
        }
    });

    // Music Player Listeners
    playPauseBtn.addEventListener('click', ui.togglePlayPause);
    nextBtn.addEventListener('click', ui.playNextTrack);
    prevBtn.addEventListener('click', ui.playPrevTrack);
    repeatBtn.addEventListener('click', ui.cycleRepeatMode);
    shuffleBtn.addEventListener('click', ui.toggleShuffle);
    audioPlayer.addEventListener('ended', ui.handleTrackEnd);
    audioPlayer.addEventListener('play', () => { playerState.isPlaying = true; ui.updatePlayerControlsUI(); });
    audioPlayer.addEventListener('pause', () => { playerState.isPlaying = false; ui.updatePlayerControlsUI(); });
    trackListUI.addEventListener('click', (e) => {
        const trackItem = e.target.closest('.track-item');
        if (trackItem && trackItem.dataset.index) {
            ui.playTrack(parseInt(trackItem.dataset.index, 10));
        }
    });

    // Anime Player Listeners
    subtitleSelector.addEventListener('change', (event) => {
        const newSubtitlePath = event.target.value;
        if (newSubtitlePath) {
            ui.loadSubtitleTrack(newSubtitlePath);
        }
    });
    toggleSubtitleBtn.addEventListener('click', ui.toggleSubtitles);
    episodeListUI.addEventListener('click', (e) => {
        const clickedItem = e.target.closest('.episode-item');
        if (!clickedItem) return;
        if (clickedItem.classList.contains('episode-video')) {
            const videoPath = clickedItem.dataset.videoPath;
            const subtitlesAttr = clickedItem.dataset.subtitles;
            const subtitles = subtitlesAttr ? JSON.parse(subtitlesAttr) : [];
            ui.playEpisode(videoPath, subtitles);
        } else if (clickedItem.classList.contains('episode-folder')) {
            const childrenUl = clickedItem.querySelector('ul');
            if (childrenUl) {
                const isVisible = childrenUl.style.display === 'block';
                childrenUl.style.display = isVisible ? 'none' : 'block';
                clickedItem.classList.toggle('expanded', !isVisible);
            }
        }
    });

    // Maintenance Listeners
    maintenanceBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (appState.isTagEditMode) {
            ui.saveAndExitTagEditMode();
        } else {
            maintenanceMenu.style.display = maintenanceMenu.style.display === 'block' ? 'none' : 'block';
        }
    });
    document.addEventListener('click', (e) => {
        if (!maintenanceBtn.contains(e.target) && !maintenanceMenu.contains(e.target)) {
            maintenanceMenu.style.display = 'none';
        }
    });
    editTagsBtn.addEventListener('click', () => {
        if (appState.isTagEditMode) {
            ui.saveAndExitTagEditMode();
        } else {
            ui.enterTagEditMode();
        }
    });
    generateCoversBtn.addEventListener('click', async () => {
        maintenanceMenu.style.display = 'none';
        if (appState.inSearchMode) {
            alert("請在正常的資料夾瀏覽模式下使用此功能，而不是在搜索結果頁面。");
            return;
        }
        if (confirm(`您確定要掃描當前目錄：\n"${appState.currentPath}"\n\n並將找到的新封面生成到對應的 COVER 資料夾中嗎？`)) {
            const result = await api.generateCovers(appState.mode, appState.currentPath);
            if (result && result.status === 'started') {
                alert("封面生成任務已在後台開始。\n完成後，請檢查封面目錄下的 'temp_generated_covers' 文件夾。");
            } else {
                alert("啟動封面生成任務失敗。詳情請查看伺服器控制台日誌。");
            }
        }
    });

    // Misc Listeners
    document.body.addEventListener('contextmenu', (e) => {
        if (!imageViewer.classList.contains('active') && !videoPlayer.classList.contains('active') && !albumView.classList.contains('active') && !animeView.classList.contains('active') && !epubViewer.classList.contains('active')) {
            e.preventDefault();
            goBack();
        }
    });
});