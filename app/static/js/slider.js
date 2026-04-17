document.addEventListener('DOMContentLoaded', function() {
    const slider = document.getElementById('slider');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const dotsContainer = document.getElementById('dots');
    
    let currentIndex = 0;
    let slides = [];
    let dots = [];
    let autoInterval = null;
    
    // Загрузка курсов с сервера
    fetch('/api/courses')
        .then(response => {
            if (!response.ok) throw new Error('Ошибка загрузки курсов');
            return response.json();
        })
        .then(courses => {
            if (!courses.length) {
                slider.innerHTML = '<p class="no-courses">Нет доступных курсов</p>';
                return;
            }
            
            // Очищаем контейнеры
            slider.innerHTML = '';
            dotsContainer.innerHTML = '';
            
            // Создаём слайды и точки
            courses.forEach((course, idx) => {
                // Слайд
                const slide = document.createElement('div');
                slide.className = 'slide';
                slide.innerHTML = `
                    <img src="${course.image}" alt="${course.name}" onerror="this.src='/static/img/placeholder.jpg'">
                    <h3>${escapeHtml(course.name)}</h3>
                    <p>${escapeHtml(course.description)}</p>
                    <div class="price">${course.price} ${course.currency}</div>
                `;
                slider.appendChild(slide);
                
                // Точка
                const dot = document.createElement('span');
                dot.className = 'dot';
                dot.addEventListener('click', () => {
                    currentIndex = idx;
                    updateSlider();
                    resetAutoPlay();
                });
                dotsContainer.appendChild(dot);
            });
            
            slides = document.querySelectorAll('.slide');
            dots = document.querySelectorAll('.dot');
            
            // Функция обновления позиции
            function updateSlider() {
                const slideWidth = slides[0].clientWidth;
                slider.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
                dots.forEach((dot, i) => {
                    dot.classList.toggle('active', i === currentIndex);
                });
            }
            
            // Обработчики кнопок
            prevBtn.addEventListener('click', () => {
                currentIndex = (currentIndex - 1 + slides.length) % slides.length;
                updateSlider();
                resetAutoPlay();
            });
            
            nextBtn.addEventListener('click', () => {
                currentIndex = (currentIndex + 1) % slides.length;
                updateSlider();
                resetAutoPlay();
            });
            
            // Автопрокрутка (опционально)
            function startAutoPlay() {
                autoInterval = setInterval(() => {
                    nextBtn.click();
                }, 5000);
            }
            
            function resetAutoPlay() {
                if (autoInterval) clearInterval(autoInterval);
                startAutoPlay();
            }
            
            // При наведении на слайдер останавливаем автопрокрутку
            const sliderSection = document.querySelector('.slider-section');
            sliderSection.addEventListener('mouseenter', () => {
                if (autoInterval) clearInterval(autoInterval);
            });
            sliderSection.addEventListener('mouseleave', startAutoPlay);
            
            // Запуск автопрокрутки
            startAutoPlay();
            
            // Обновление при изменении размера окна
            window.addEventListener('resize', () => updateSlider());
            
            // Инициализация
            updateSlider();
        })
        .catch(error => {
            console.error('Ошибка:', error);
            slider.innerHTML = '<p class="error">Не удалось загрузить курсы</p>';
        });
    
    // Функция для защиты от XSS
    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
});