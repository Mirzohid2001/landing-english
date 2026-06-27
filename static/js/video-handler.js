// Video Handler — YouTube, Vimeo va lokal/remote MP4

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCsrfToken() {
    return getCookie('csrftoken');
}

function extractYouTubeId(url) {
    if (!url || !url.trim()) {
        return null;
    }

    url = url.trim();
    const patterns = [
        /youtu\.be\/([a-zA-Z0-9_-]{11})/,
        /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
        /youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/,
        /youtube\.com\/watch\?.*[&?]v=([a-zA-Z0-9_-]{11})/,
    ];

    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1] && match[1].length === 11) {
            return match[1];
        }
    }

    return null;
}

function extractVimeoId(url) {
    const regExp = /(?:vimeo)\.com.*(?:videos|video|channels|)\/([\d]+)/i;
    const match = url.match(regExp);
    return match ? match[1] : null;
}

function createVideoEmbed(videoUrl, videoFile, previewImage = null) {
    if (videoUrl) {
        const youtubeId = extractYouTubeId(videoUrl);
        const vimeoId = extractVimeoId(videoUrl);

        if (youtubeId) {
            return `
                <iframe
                    src="https://www.youtube.com/embed/${youtubeId}?rel=0&modestbranding=1"
                    frameborder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen
                    class="video-iframe"
                    loading="lazy">
                </iframe>
            `;
        }
        if (vimeoId) {
            return `
                <iframe
                    src="https://player.vimeo.com/video/${vimeoId}?title=0&byline=0&portrait=0"
                    frameborder="0"
                    allow="autoplay; fullscreen; picture-in-picture"
                    allowfullscreen
                    class="video-iframe"
                    loading="lazy">
                </iframe>
            `;
        }
        return `
            <iframe
                src="${videoUrl}"
                frameborder="0"
                allowfullscreen
                class="video-iframe"
                loading="lazy">
            </iframe>
        `;
    }

    if (videoFile) {
        const poster = previewImage ? `poster="${previewImage}"` : '';
        return `
            <div class="video-player-wrap">
                <div class="video-modal-loader" aria-live="polite">
                    <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
                    <span>Video yuklanmoqda...</span>
                </div>
                <video
                    controls
                    playsinline
                    class="video-player"
                    ${poster}
                    preload="metadata">
                    <source src="${videoFile}" type="video/mp4">
                    <source src="${videoFile}" type="video/webm">
                    Brauzeringiz video tegini qo'llab-quvvatlamaydi.
                </video>
            </div>
        `;
    }

    return '';
}

function attachVideoLoader(container) {
    const wrap = container.querySelector('.video-player-wrap');
    if (!wrap) {
        return;
    }

    const video = wrap.querySelector('video');
    const loader = wrap.querySelector('.video-modal-loader');
    if (!video || !loader) {
        return;
    }

    const hideLoader = () => loader.classList.add('is-hidden');

    video.addEventListener('canplay', hideLoader, { once: true });
    video.addEventListener('loadeddata', hideLoader, { once: true });
    video.addEventListener('error', () => {
        loader.innerHTML = '<span>Video yuklanmadi. Qayta urinib ko\'ring.</span>';
        loader.classList.remove('is-hidden');
    });
}

function closeVideoModal() {
    const modal = document.getElementById('video-modal');
    const content = document.getElementById('video-modal-content');
    if (!modal) {
        return;
    }

    if (content) {
        content.querySelectorAll('video').forEach((video) => {
            video.pause();
            video.removeAttribute('src');
            video.load();
        });
        content.querySelectorAll('iframe').forEach((frame) => {
            frame.src = '';
        });
        content.innerHTML = '';
    }

    modal.style.display = 'none';
    document.body.classList.remove('video-modal-open');
}

function showVideoModal(videoUrl, videoFile, previewImage = null) {
    const modal = document.getElementById('video-modal');
    const content = document.getElementById('video-modal-content');

    if (!modal || !content) {
        return;
    }

    const embedHTML = createVideoEmbed(videoUrl, videoFile, previewImage);
    if (!embedHTML) {
        if (typeof showAlert === 'function') {
            showAlert('Video mavjud emas', 'error');
        }
        return;
    }

    content.innerHTML = `<div class="video-container">${embedHTML}</div>`;
    modal.style.display = 'block';
    document.body.classList.add('video-modal-open');
    attachVideoLoader(content);
}

function getVideoContainer(el) {
    return el.closest(
        '.video-preview, .video-preview-home, .student-video-overlay, .course-video-overlay'
    );
}

function readInlineVideoData(container) {
    if (!container) {
        return null;
    }

    const videoUrl = (container.getAttribute('data-video-url') || '').trim();
    const videoFile = (container.getAttribute('data-video-file') || '').trim();
    const previewImage = (container.getAttribute('data-preview') || '').trim();

    if (!videoUrl && !videoFile) {
        return null;
    }

    return {
        videoUrl: videoUrl || null,
        videoFile: videoFile || null,
        previewImage: previewImage || null,
    };
}

function openVideoFromContainer(container) {
    const inline = readInlineVideoData(container);
    if (inline) {
        showVideoModal(inline.videoUrl, inline.videoFile, inline.previewImage);
        return true;
    }
    return false;
}

function fetchVideoModal(url, errorMessage) {
    const modal = document.getElementById('video-modal');
    const content = document.getElementById('video-modal-content');
    if (!modal || !content) {
        return;
    }

    modal.style.display = 'block';
    document.body.classList.add('video-modal-open');
    content.innerHTML = `
        <div class="video-container">
            <div class="video-modal-loader is-centered" aria-live="polite">
                <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
                <span>Video yuklanmoqda...</span>
            </div>
        </div>
    `;

    fetch(url, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        },
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                showVideoModal(data.video_url, data.video_file, data.preview_image);
            } else if (typeof showAlert === 'function') {
                closeVideoModal();
                showAlert(errorMessage, 'error');
            } else {
                closeVideoModal();
            }
        })
        .catch((error) => {
            console.error('Error loading video:', error);
            closeVideoModal();
            if (typeof showAlert === 'function') {
                showAlert(errorMessage, 'error');
            }
        });
}

function handleVideoTrigger(trigger) {
    const container = getVideoContainer(trigger);
    if (container && openVideoFromContainer(container)) {
        return;
    }

    const videoId = trigger.getAttribute('data-video-id');
    if (videoId) {
        fetchVideoModal(`/api/lesson-video/${videoId}/`, 'Video mavjud emas');
        return;
    }

    const courseId = trigger.getAttribute('data-course-id');
    if (courseId) {
        fetchVideoModal(`/api/course-video/${courseId}/`, 'Video mavjud emas');
        return;
    }

    const studentId = trigger.getAttribute('data-student-id');
    if (studentId) {
        fetchVideoModal(`/api/student-video/${studentId}/`, 'Video mavjud emas');
        return;
    }

    const teacherId = trigger.getAttribute('data-teacher-id');
    if (teacherId) {
        fetchVideoModal(`/api/teacher-video/${teacherId}/`, 'Video mavjud emas');
        return;
    }

    const testimonialId = trigger.getAttribute('data-testimonial-id');
    if (testimonialId) {
        fetchVideoModal(`/api/testimonial-video/${testimonialId}/`, 'Video mavjud emas');
    }
}

function isVideoClickTarget(target) {
    return Boolean(
        target.closest('.video-preview--clickable') ||
        target.closest('.video-preview-home.video-preview--clickable') ||
        target.closest('.student-video-overlay.video-preview--clickable') ||
        target.closest('.course-video-overlay.video-preview--clickable') ||
        target.closest('.play-btn[data-video-id]') ||
        target.closest('.play-btn-home[data-video-id]') ||
        target.closest('.play-btn[data-course-id]') ||
        target.closest('.play-btn[data-student-id]') ||
        target.closest('.play-btn[data-teacher-id]') ||
        target.closest('.watch-video-btn[data-testimonial-id]')
    );
}

function initVideoModalClose() {
    const videoModal = document.getElementById('video-modal');
    if (!videoModal) {
        return;
    }

    const closeBtn = videoModal.querySelector('.close-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeVideoModal);
    }

    videoModal.addEventListener('click', (event) => {
        if (event.target === videoModal) {
            closeVideoModal();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && videoModal.style.display === 'block') {
            closeVideoModal();
        }
    });
}

function initVideoHandlers() {
    document.addEventListener('click', (event) => {
        if (!isVideoClickTarget(event.target)) {
            return;
        }

        const clickable = event.target.closest(
            '.video-preview--clickable, .video-preview-home.video-preview--clickable, ' +
            '.student-video-overlay.video-preview--clickable, .course-video-overlay.video-preview--clickable'
        );
        if (clickable) {
            event.preventDefault();
            if (!openVideoFromContainer(clickable)) {
                const trigger = clickable.querySelector(
                    '[data-video-id], [data-course-id], [data-student-id], [data-teacher-id], [data-testimonial-id]'
                );
                if (trigger) {
                    handleVideoTrigger(trigger);
                }
            }
            return;
        }

        const trigger = event.target.closest(
            '.play-btn, .play-btn-home, .watch-video-btn'
        );
        if (trigger) {
            event.preventDefault();
            event.stopPropagation();
            handleVideoTrigger(trigger);
        }
    });

    document.querySelectorAll('.video-preview--clickable, .video-preview-home.video-preview--clickable').forEach((el) => {
        el.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                if (!openVideoFromContainer(el)) {
                    const trigger = el.querySelector('[data-video-id]');
                    if (trigger) {
                        handleVideoTrigger(trigger);
                    }
                }
            }
        });
    });

    initVideoModalClose();
}

document.addEventListener('DOMContentLoaded', initVideoHandlers);
