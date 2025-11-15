const video = document.querySelector('.video-backgraund');

const swiperText = new Swiper('.swiper', {
  speed: 800, // Уменьшил с 1600 до 800
  mousewheel: {},
  pagination: {
    el: '.swiper-pagination',
    clickable: true
  },
  navigation: {
    prevEl: '.swiper-button-prev',
    nextEl: '.swiper-button-next'
  }
});

// Оптимизированная анимация
swiperText.on('slideChange', function() {
  gsap.killTweensOf(video); // Останавливаем предыдущие анимации
  
  const targetTime = (video.duration / this.slides.length) * this.realIndex;
  
  gsap.to(video, {
    duration: 1.5, // Уменьшил с 4 до 1.5 секунд
    currentTime: targetTime,
    ease: "power2.out", // Более быстрая easing функция
    overwrite: true // Перезаписывает предыдущие анимации
  });
});

swiperText.on('slideChangeTransitionStart', function() {
  video.classList.add('change');
}).on('slideChangeTransitionEnd', function() {
  video.classList.remove('change');
});