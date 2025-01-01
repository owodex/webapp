(function ($) {
    "use strict";

    $(document).ready(function() {
        // Spinner
        var spinner = function () {
            setTimeout(function () {
                if ($('#spinner').length > 0) {
                    $('#spinner').removeClass('show');
                }
            }, 1);
        };
        spinner();
        
        // Initiate the wowjs
        new WOW().init();

        // Logo Carousel
        $(".logo-carousel").owlCarousel({
            loop: true,
            margin: 45,
            dots: false,
            autoplay: true,
            autoplayTimeout: 3000,
            smartSpeed: 1000,
            responsive: {
                0: { items: 2 },
                576: { items: 3 },
                768: { items: 4 },
                992: { items: 5 }
            }
        });

        // Sticky Navbar
        $(window).scroll(function () {
            if ($(this).scrollTop() > 45) {
                $('.navbar').addClass('sticky-top shadow-sm');
            } else {
                $('.navbar').removeClass('sticky-top shadow-sm');
            }
        });

        // Blog Carousel
        $(".blog-carousel").owlCarousel({
            autoplay: true,
            smartSpeed: 1000,
            center: true,
            margin: 30,
            dots: true,
            loop: true,
            nav: true,
            navText: [
                '<i class="bi bi-arrow-left"></i>',
                '<i class="bi bi-arrow-right"></i>'
            ],
            responsive: {
                0: { items: 1 },
                768: { items: 2 },
                992: { items: 3 }
            },
            onInitialized: function(event) {
                $('.owl-item.active.center').addClass('current');
            },
            onTranslated: function(event) {
                $('.owl-item').removeClass('current');
                $('.owl-item.active.center').addClass('current');
            }
        });

        // Custom Navigation for Blog Carousel
        $(".blog-carousel-nav .owl-prev").click(function(){
            $(".blog-carousel").trigger('prev.owl.carousel');
        });
        $(".blog-carousel-nav .owl-next").click(function(){
            $(".blog-carousel").trigger('next.owl.carousel');
        });
   
        // Dropdown on mouse hover
        const $dropdown = $(".dropdown");
        const $dropdownToggle = $(".dropdown-toggle");
        const $dropdownMenu = $(".dropdown-menu");
        const showClass = "show";
        
        $(window).on("load resize", function() {
            if (this.matchMedia("(min-width: 992px)").matches) {
                $dropdown.hover(
                function() {
                    const $this = $(this);
                    $this.addClass(showClass);
                    $this.find($dropdownToggle).attr("aria-expanded", "true");
                    $this.find($dropdownMenu).addClass(showClass);
                },
                function() {
                    const $this = $(this);
                    $this.removeClass(showClass);
                    $this.find($dropdownToggle).attr("aria-expanded", "false");
                    $this.find($dropdownMenu).removeClass(showClass);
                }
                );
            } else {
                $dropdown.off("mouseenter mouseleave");
            }
        });
        
        // Back to top button
        $(window).scroll(function () {
            if ($(this).scrollTop() > 300) {
                $('.back-to-top').fadeIn('slow');
            } else {
                $('.back-to-top').fadeOut('slow');
            }
        });
        $('.back-to-top').click(function () {
            $('html, body').animate({scrollTop: 0}, 1500, 'easeInOutExpo');
            return false;
        });

        // Facts counter
        $('[data-toggle="counter-up"]').counterUp({
            delay: 10,
            time: 2000
        });

        // Modal Video
        var $videoSrc;
        $('.btn-play').click(function () {
            $videoSrc = $(this).data("src");
        });

        $('#videoModal').on('shown.bs.modal', function (e) {
            $("#video").attr('src', $videoSrc + "?autoplay=1&amp;modestbranding=1&amp;showinfo=0");
        });

        $('#videoModal').on('hide.bs.modal', function (e) {
            $("#video").attr('src', $videoSrc);
        });

        // Testimonials carousel
        $(".testimonial-carousel").owlCarousel({
            autoplay: true,
            smartSpeed: 1000,
            center: true,
            margin: 24,
            dots: true,
            loop: true,
            nav : false,
            responsive: {
                0: { items: 1 },
                768: { items: 2 },
                992: { items: 3 }
            }
        });

        // Image carousel
        $(".image-carousel").owlCarousel({
            items: 1,
            loop: true,
            autoplay: true,
            autoplayTimeout: 5000,
            autoplayHoverPause: true,
            nav: false,
            dots: true,
            animateOut: 'fadeOut',
            animateIn: 'fadeIn'
        });

        // Add your signup.js code here
        const countrySelect = document.getElementById('country-code');
    
        function updateFlag() {
            const selectedOption = this.options[this.selectedIndex];
            const flag = selectedOption.getAttribute('data-flag');
            this.style.backgroundImage = `url(https://flagcdn.com/24x18/${flag}.png)`;
        }

        if (countrySelect) {
            countrySelect.addEventListener('change', updateFlag);

            // Trigger change event to set initial flag
            updateFlag.call(countrySelect);
        }


    });
})(jQuery);