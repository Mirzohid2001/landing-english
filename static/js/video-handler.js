// Video Handler - для обработки YouTube, Vimeo и локальных видео

// Get CSRF token for AJAX requests
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
    
    // Убираем пробелы
    url = url.trim();
    
    // Паттерны для разных форматов YouTube URL
    const patterns = [
        /youtu\.be\/([a-zA-Z0-9_-]{11})/,  // Короткие ссылки
        /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,  // Embed ссылки
        /youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/,  // Обычные ссылки
        /youtube\.com\/watch\?.*[&?]v=([a-zA-Z0-9_-]{11})/,  // С дополнительными параметрами
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
    let embedHTML = '';
    
    if (videoUrl) {
        const youtubeId = extractYouTubeId(videoUrl);
        const vimeoId = extractVimeoId(videoUrl);
        
        if (youtubeId) {
            embedHTML = `
                <iframe 
                    src="https://www.youtube.com/embed/${youtubeId}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen
                    class="video-iframe"
                    loading="lazy">
                </iframe>
            `;
        } else if (vimeoId) {
            embedHTML = `
                <iframe 
                    src="https://player.vimeo.com/video/${vimeoId}" 
                    frameborder="0" 
                    allow="autoplay; fullscreen; picture-in-picture" 
                    allowfullscreen
                    class="video-iframe"
                    loading="lazy">
                </iframe>
            `;
        } else {
            embedHTML = `
                <iframe 
                    src="${videoUrl}" 
                    frameborder="0" 
                    allowfullscreen
                    class="video-iframe"
                    loading="lazy">
                </iframe>
            `;
        }
    } else if (videoFile) {
        embedHTML = `
            <video 
                controls 
                class="video-player"
                ${previewImage ? `poster="${previewImage}"` : ''}
                preload="metadata">
                <source src="${videoFile}" type="video/mp4">
                <source src="${videoFile}" type="video/webm">
                Your browser does not support the video tag.
            </video>
        `;
    }
    
    return embedHTML;
}

// Обработка кликов на кнопки воспроизведения видео
document.addEventListener('DOMContentLoaded', function() {
    // Видео курса
    document.querySelectorAll('.play-btn[data-course-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            loadCourseVideo(courseId);
        });
    });
    
    // Видео преподавателя
    document.querySelectorAll('.play-btn[data-teacher-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const teacherId = this.getAttribute('data-teacher-id');
            loadTeacherVideo(teacherId);
        });
    });
    
    // Видео отзыва
    document.querySelectorAll('.watch-video-btn[data-testimonial-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const testimonialId = this.getAttribute('data-testimonial-id');
            loadTestimonialVideo(testimonialId);
        });
    });
    
    // Видео урока
    document.querySelectorAll('.play-btn[data-video-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const videoId = this.getAttribute('data-video-id');
            loadLessonVideo(videoId);
        });
    });
    
    // Видео для главной страницы (home page videos)
    document.querySelectorAll('.play-btn-home[data-video-id]').forEach(btn => {
        btn.addEventListener('click', function() {
            const videoId = this.getAttribute('data-video-id');
            loadLessonVideo(videoId);
        });
    });
});

function loadCourseVideo(courseId) {
    showLoading();
    
    fetch(`/api/course-video/${courseId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showVideoModal(data.video_url, data.video_file, data.preview_image);
        } else {
            showAlert('Video not available', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading video:', error);
        showAlert('Error loading video', 'error');
    });
}

function loadTeacherVideo(teacherId) {
    showLoading();
    
    fetch(`/api/teacher-video/${teacherId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showVideoModal(data.video_url, data.video_file);
        } else {
            showAlert('Video not available', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading video:', error);
        showAlert('Error loading video', 'error');
    });
}

function loadTestimonialVideo(testimonialId) {
    showLoading();
    
    fetch(`/api/testimonial-video/${testimonialId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showVideoModal(data.video_url, data.video_file);
        } else {
            showAlert('Video not available', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading video:', error);
        showAlert('Error loading video', 'error');
    });
}

function loadLessonVideo(videoId) {
    showLoading();
    
    fetch(`/api/lesson-video/${videoId}/`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showVideoModal(data.video_url, data.video_file, data.preview_image);
        } else {
            showAlert('Video not available', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error loading video:', error);
        showAlert('Error loading video', 'error');
    });
}

function showVideoModal(videoUrl, videoFile, previewImage = null) {
    const modal = document.getElementById('video-modal');
    const content = document.getElementById('video-modal-content');
    
    if (modal && content) {
        const embedHTML = createVideoEmbed(videoUrl, videoFile, previewImage);
        content.innerHTML = `<div class="video-container">${embedHTML}</div>`;
        modal.style.display = 'block';
    }
}

// Закрытие модального окна видео
document.addEventListener('DOMContentLoaded', function() {
    const videoModal = document.getElementById('video-modal');
    if (videoModal) {
        const closeBtn = videoModal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                const content = document.getElementById('video-modal-content');
                if (content) {
                    content.innerHTML = '';
                }
                videoModal.style.display = 'none';
            });
        }
    }
});

