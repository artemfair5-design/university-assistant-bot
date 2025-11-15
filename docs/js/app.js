const video = document.querySelector(`.video-backgraund`)

const swiperText = new Swiper(`.swiper`, {
  speed: 1600,
  mousewhell: {  },
  pagination: {
    el: `.swiper-pagination`,
    clicable: true
  },
  navigation: {
    prevEl: `.swiper-button-prev`,
    nextEl: `.swiper-button-next`
  }
})
swiperText.on(`slideChange`, function() {
  gsap.to(video, 2, {
    currentTime: (video.duration / this.slides.length - .1) * this.realIndex,
    ease: Power2.easeOut
  })
})
swiperText.on(`slideChangeTransitionStart`, function() {
  video.classList.add(`change`)
}).on(`slideChangeTransitionEnd`,function() {
  video.classList.remove(`change`)
})