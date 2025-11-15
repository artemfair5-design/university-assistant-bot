const video = document.querySelector('.video-backgraund');

const swiperText = new Swiper('.swiper', {
  speed: 800, 
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


swiperText.on('slideChange', function() {
  gsap.killTweensOf(video); 
  
  const targetTime = (video.duration / this.slides.length) * this.realIndex;
  
  gsap.to(video, {
    duration: 1.5, 
    currentTime: targetTime,
    ease: "power2.out", 
    overwrite: true 
  });
});

swiperText.on('slideChangeTransitionStart', function() {
  video.classList.add('change');
}).on('slideChangeTransitionEnd', function() {
  video.classList.remove('change');
});