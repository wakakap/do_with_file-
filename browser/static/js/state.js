// static/js/state.js

/**
 * 主应用状态。
 */
export const appState = {
    mode: 'MANGA',
    currentPath: '',
    pathStack: [],
    inSearchMode: false,
    isTagEditMode: false,
    renderingId: 0,
    tagsData: {},
    tempTagsData: {},
    currentView: 'browse',
    activeImports: {},
};

/**
 * 媒体播放器状态（音乐）。
 */
export const playerState = {
    currentTracklist: [],
    originalTracklist: [],
    baseMediaPath: '',
    currentIndex: -1,
    isPlaying: false,
    isShuffled: false,
    repeatMode: 'NONE',
    itemKey: '',
};

/**
 * 动画播放器状态。
 */
export const animePlayerState = {
    baseMediaPath: '',
    episodeTree: [],
    currentPlayingPath: null,
    areSubtitlesVisible: true,
    itemKey: '',
};

/**
 * 图片查看器状态。
 */
export const galleryState = {
    isOpen: false,
    baseMediaPath: '',
    itemKey: '',
    files: [],
    currentIndex: 0,
    isLoading: false,
    rotationAngle: 0,
    mode: 'MANGA',
};