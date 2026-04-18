// Модальное окно для выбора курса
document.addEventListener('DOMContentLoaded', function() {
    const courseModal = document.getElementById('courseModal');
    const paymentModal = document.getElementById('paymentModal');
    const chooseBtn = document.getElementById('chooseProgramBtn');
    const closeBtns = document.querySelectorAll('.close, .close-payment');
    
    let selectedCourse = null;
    let selectedPaymentMethod = null;
    let selectedDateTime = null;
    let sposobOplatiList = [];
    
    // Устанавливаем минимальную дату (завтра)
    function setMinDate() {
        const dateInput = document.getElementById('preferDate');
        if (dateInput) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const year = tomorrow.getFullYear();
            const month = String(tomorrow.getMonth() + 1).padStart(2, '0');
            const day = String(tomorrow.getDate()).padStart(2, '0');
            dateInput.min = `${year}-${month}-${day}`;
            
            // Устанавливаем дату по умолчанию - завтра
            dateInput.value = `${year}-${month}-${day}`;
        }
        
        const timeInput = document.getElementById('preferTime');
        if (timeInput && !timeInput.value) {
            timeInput.value = '10:00'; // Время по умолчанию
        }
    }
    
    // Проверка заполнения формы
    function checkFormComplete() {
        const submitBtn = document.getElementById('paymentSubmitBtn');
        const dateInput = document.getElementById('preferDate');
        const timeInput = document.getElementById('preferTime');
        
        if (submitBtn && dateInput && timeInput) {
            const isComplete = selectedPaymentMethod !== null && 
                              dateInput.value && 
                              timeInput.value;
            submitBtn.disabled = !isComplete;
        }
    }
    
    // Получение выбранной даты и времени
    function getSelectedDateTime() {
        const dateInput = document.getElementById('preferDate');
        const timeInput = document.getElementById('preferTime');
        
        if (dateInput && dateInput.value && timeInput && timeInput.value) {
            return `${dateInput.value} ${timeInput.value}:00`;
        }
        return null;
    }
    
    // Проверка авторизации
    function checkAuth() {
        console.log('Проверка авторизации...');
        return fetch('/api/check_auth', {
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            console.log('Auth data:', data);
            return data.is_authenticated;
        })
        .catch(error => {
            console.error('Ошибка проверки авторизации:', error);
            return false;
        });
    }
    
    // Загрузка способов оплаты
    function loadPaymentMethods() {
        return fetch('/api/get_sposob_oplati', {
            credentials: 'include'
        })
        .then(response => response.json())
        .then(methods => {
            sposobOplatiList = methods;
            return methods;
        });
    }
    
    // Загрузка курсов
    function loadCourses() {
        const modalBody = document.querySelector('#courseModal .modal-body');
        if (modalBody) {
            modalBody.innerHTML = '<div class="loading">Загрузка курсов...</div>';
        }
        
        fetch('/api/courses', {
            credentials: 'include'
        })
        .then(response => response.json())
        .then(courses => {
            displayCourses(courses);
        })
        .catch(error => {
            console.error('Ошибка загрузки курсов:', error);
            if (modalBody) {
                modalBody.innerHTML = '<div class="loading">Ошибка загрузки курсов</div>';
            }
        });
    }
    
    // Отображение списка курсов
    function displayCourses(courses) {
        const modalBody = document.querySelector('#courseModal .modal-body');
        
        if (!courses.length) {
            if (modalBody) {
                modalBody.innerHTML = '<div class="loading">Нет доступных курсов</div>';
            }
            return;
        }
        
        const coursesList = document.createElement('div');
        coursesList.className = 'courses-list';
        
        courses.forEach(course => {
            const card = document.createElement('div');
            card.className = 'modal-course-card';
            card.dataset.id = course.id;
            
            card.innerHTML = `
                <img src="${course.image}" alt="${course.name}" onerror="this.src='/static/img/placeholder.jpg'">
                <h3>${escapeHtml(course.name)}</h3>
                <p>${escapeHtml(course.description)}</p>
                <div class="price">${course.price} ${course.currency}</div>
            `;
            
            card.addEventListener('click', () => {
                document.querySelectorAll('.modal-course-card').forEach(c => {
                    c.classList.remove('selected');
                });
                card.classList.add('selected');
                selectedCourse = course;
                
                closeModal(courseModal);
                showPaymentModal();
            });
            
            coursesList.appendChild(card);
        });
        
        if (modalBody) {
            modalBody.innerHTML = '';
            modalBody.appendChild(coursesList);
        }
    }
    
    // Отображение модального окна оплаты
    function showPaymentModal() {
        if (!selectedCourse) {
            console.error('Нет выбранного курса');
            return;
        }
        
        const selectedCourseInfo = document.getElementById('selectedCourseInfo');
        
        // Показываем информацию о выбранном курсе
        if (selectedCourseInfo) {
            selectedCourseInfo.innerHTML = `
                <h4>Выбранный курс:</h4>
                <p><strong>${escapeHtml(selectedCourse.name)}</strong></p>
                <div class="price">${selectedCourse.price} ${selectedCourse.currency}</div>
            `;
        }
        
        // Устанавливаем минимальную дату
        setMinDate();
        
        // Добавляем обработчики для полей даты/времени
        const dateInput = document.getElementById('preferDate');
        const timeInput = document.getElementById('preferTime');
        
        if (dateInput) {
            dateInput.addEventListener('change', checkFormComplete);
        }
        if (timeInput) {
            timeInput.addEventListener('change', checkFormComplete);
        }
        
        // Загружаем способы оплаты
        const paymentMethodsList = document.getElementById('paymentMethodsList');
        if (paymentMethodsList) {
            paymentMethodsList.innerHTML = '<div class="loading">Загрузка способов оплаты...</div>';
        }
        
        // Сбрасываем выбранный способ оплаты
        selectedPaymentMethod = null;
        
        loadPaymentMethods().then(methods => {
            if (!methods.length) {
                if (paymentMethodsList) {
                    paymentMethodsList.innerHTML = '<div class="loading">Способы оплаты не найдены</div>';
                }
                return;
            }
            
            if (paymentMethodsList) {
                paymentMethodsList.innerHTML = '';
                
                methods.forEach(method => {
                    const methodDiv = document.createElement('div');
                    methodDiv.className = 'payment-method-item';
                    methodDiv.dataset.id = method.id;
                    
                    methodDiv.innerHTML = `
                        <div class="payment-method-radio"></div>
                        <div class="payment-method-info">
                            <div class="payment-method-name">${escapeHtml(method.name)}</div>
                            <div class="payment-method-desc">${getPaymentMethodDescription(method.name)}</div>
                        </div>
                    `;
                    
                    methodDiv.addEventListener('click', () => {
                        document.querySelectorAll('.payment-method-item').forEach(m => {
                            m.classList.remove('selected');
                        });
                        methodDiv.classList.add('selected');
                        selectedPaymentMethod = method;
                        checkFormComplete();
                    });
                    
                    paymentMethodsList.appendChild(methodDiv);
                });
            }
        });
        
        // Отключаем кнопку подтверждения
        const submitBtn = document.getElementById('paymentSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
        }
        
        // Показываем модальное окно
        paymentModal.style.display = 'block';
    }
    
    // Описание способов оплаты
    function getPaymentMethodDescription(methodName) {
        const descriptions = {
            'Банковская карта': 'Оплата банковской картой Visa/MasterCard/Мир',
            'Наличные': 'Наличный расчёт при получении',
            'Банковский перевод': 'Перевод по реквизитам',
            'Криптовалюта': 'Оплата в USDT/BTC',
            'Рассрочка': 'Рассрочка без переплаты на 3 месяца',
            'Кредит': 'Кредит от банков-партнёров'
        };
        return descriptions[methodName] || 'Удобный способ оплаты';
    }
    
    // Подтверждение записи на курс
    function confirmEnrollment() {
        if (!selectedCourse) {
            alert('Курс не выбран');
            return;
        }
        
        if (!selectedPaymentMethod) {
            alert('Выберите способ оплаты');
            return;
        }
        
        const preferDateTime = getSelectedDateTime();
        if (!preferDateTime) {
            alert('Выберите желаемую дату и время начала обучения');
            return;
        }
        
        const submitBtn = document.getElementById('paymentSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Отправка...';
        }
        
        console.log('Отправка заявки:', {
            course_id: selectedCourse.id,
            sposob_oplati_id: selectedPaymentMethod.id,
            prefer_time: preferDateTime
        });
        
        fetch('/api/enroll_course', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                course_id: selectedCourse.id,
                sposob_oplati_id: selectedPaymentMethod.id,
                prefer_time: preferDateTime
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Ответ сервера:', data);
            if (data.success) {
                alert('✓ ' + data.message);
                closeModal(paymentModal);
                selectedCourse = null;
                selectedPaymentMethod = null;
            } else {
                alert('✗ ' + data.message);
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Подтвердить запись';
                }
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            alert('Произошла ошибка при отправке заявки');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Подтвердить запись';
            }
        });
    }
    
    // Отображение формы авторизации
    function showAuthRequired() {
        const modalBody = document.querySelector('#courseModal .modal-body');
        if (modalBody) {
            modalBody.innerHTML = `
                <div class="auth-message">
                    <p>Для записи на курсы необходимо войти в систему или зарегистрироваться</p>
                    <div class="auth-buttons">
                        <a href="/login" class="auth-btn auth-btn-login">Войти</a>
                        <a href="/register" class="auth-btn auth-btn-register">Зарегистрироваться</a>
                    </div>
                </div>
            `;
        }
    }
    
    // Открытие модального окна курсов
    function openCourseModal() {
        selectedCourse = null;
        courseModal.style.display = 'block';
        
        checkAuth().then(isAuth => {
            if (isAuth) {
                loadCourses();
            } else {
                showAuthRequired();
            }
        });
    }
    
    // Закрытие модального окна
    function closeModal(modal) {
        modal.style.display = 'none';
        if (modal === paymentModal) {
            selectedPaymentMethod = null;
            const submitBtn = document.getElementById('paymentSubmitBtn');
            if (submitBtn) {
                submitBtn.disabled = true;
            }
        }
    }
    
    // Обработчики событий
    if (chooseBtn) {
        chooseBtn.addEventListener('click', openCourseModal);
    }
    
    closeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(courseModal);
            closeModal(paymentModal);
        });
    });
    
    window.addEventListener('click', (event) => {
        if (event.target === courseModal) {
            closeModal(courseModal);
        }
        if (event.target === paymentModal) {
            closeModal(paymentModal);
        }
    });
    
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            if (paymentModal.style.display === 'block') {
                closeModal(paymentModal);
            } else if (courseModal.style.display === 'block') {
                closeModal(courseModal);
            }
        }
    });
    
    const cancelBtn = document.getElementById('paymentCancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            closeModal(paymentModal);
            openCourseModal();
        });
    }
    
    const submitBtn = document.getElementById('paymentSubmitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', confirmEnrollment);
    }
    
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