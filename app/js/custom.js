// Google Maps Initialization with Enhanced Error Handling and Accessibility
let map;
let center;

function initMap() {
    try {
        // Default location (Singapore) with fallback
        const defaultLocation = { lat: 1.3521, lng: 103.8198 };
        const mapElement = document.getElementById('map-canvas');
        
        // Validate map container exists
        if (!mapElement) {
            console.error('Map container not found');
            return;
        }
        
        // Create map with enhanced configuration
        map = new google.maps.Map(mapElement, {
            zoom: 12,
            center: defaultLocation,
            scrollwheel: false,
            mapTypeControl: true,
            streetViewControl: true,
            fullscreenControl: true,
            gestureHandling: 'cooperative', // Improved mobile interaction
            styles: [
                {
                    featureType: 'poi',
                    elementType: 'labels',
                    stylers: [{ visibility: 'off' }]
                },
                {
                    featureType: 'road',
                    elementType: 'geometry',
                    stylers: [{ color: '#f5f5f5' }]
                }
            ]
        });

        // Add marker with accessibility attributes
        const marker = new google.maps.Marker({
            position: defaultLocation,
            map: map,
            title: 'Our Location',
            label: {
                text: 'B',  // Business initial
                color: 'white',
                fontSize: '14px'
            },
            optimized: false  // For better performance
        });

        // Add info window for better accessibility
        const infoWindow = new google.maps.InfoWindow({
            content: '<div aria-label="Business Location">B.Y. Solutions Headquarters</div>'
        });

        marker.addListener('click', () => {
            infoWindow.open(map, marker);
        });

        // Set up event listeners with error handling
        google.maps.event.addListenerOnce(map, 'idle', function() {
            center = map.getCenter();
            console.log('Map loaded successfully');
        });

        window.addEventListener('resize', function() {
            if (map && center) {
                try {
                    google.maps.event.trigger(map, 'resize');
                    map.setCenter(center);
                } catch (resizeError) {
                    console.error('Map resize error:', resizeError);
                }
            }
        });

    } catch (mapError) {
        console.error('Map initialization error:', mapError);
        // Fallback UI or error notification
        const mapElement = document.getElementById('map-canvas');
        if (mapElement) {
            mapElement.innerHTML = '<p>Unable to load map. Please check your internet connection.</p>';
        }
    }
}

function loadGoogleMap() {
    // Enhanced Google Maps API loading check
    if (window.google && window.google.maps) {
        initMap();
    } else {
        console.warn('Google Maps API not loaded. Attempting to load...');
        const script = document.createElement('script');
        script.src = `https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap`;
        script.async = true;
        script.defer = true;
        script.onerror = () => {
            console.error('Failed to load Google Maps API');
        };
        document.head.appendChild(script);
    }
}

// Ensure map loads after DOM is ready
document.addEventListener('DOMContentLoaded', loadGoogleMap);

// Flexslider
$(function(){
  /* FlexSlider */
  $('.flexslider').flexslider({
      animation: "fade",
      directionNav: false
  });

  new WOW().init();

  // Magnific Pop up for Portfolio section
  $('.portfolio-container').magnificPopup({
    delegate: '.portfolio-popup', // child items selector, by clicking on it popup will open
    type: 'image',
    gallery: {
      enabled: true
    }    
  });

});

// isotope
jQuery(document).ready(function($){

  if ( $('.iso-box-wrapper').length > 0 ) { 

      var $container  = $('.iso-box-wrapper'), 
        $imgs     = $('.iso-box img');

      $container.imagesLoaded(function () {

        $container.isotope({
        layoutMode: 'fitRows',
        itemSelector: '.iso-box'
        });

        $imgs.load(function(){
          $container.isotope('reLayout');
        })

      });

      //filter items on button click
      $('.filter-wrapper li a').click(function(){

          var $this = $(this), filterValue = $this.attr('data-filter');

      $container.isotope({ 
        filter: filterValue,
        animationOptions: { 
            duration: 750, 
            easing: 'linear', 
            queue: false, 
        }                
      });             

      // don't proceed if already selected 
      if ( $this.hasClass('selected') ) { 
        return false; 
      }

      var filter_wrapper = $this.closest('.filter-wrapper');
      filter_wrapper.find('.selected').removeClass('selected');
      $this.addClass('selected');

        return false;
      }); 

  }

});

// Close mobile menu after clicking on a link
$(document).on('click', '.navbar-collapse.in', function(e) {
    if ($(e.target).is('a') && $(e.target).attr('class') !== 'dropdown-toggle') {
        $(this).collapse('hide');
    }
});

// Smooth scrolling for navigation links
$(document).ready(function() {
    $('a[href*="#"]:not([href="#"])').on('click', function(event) {
        if (location.pathname.replace(/^\//, '') === this.pathname.replace(/^\//, '') 
            && location.hostname === this.hostname) {
            
            let target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            
            if (target.length) {
                event.preventDefault();
                $('html, body').stop().animate({
                    scrollTop: target.offset().top - 68
                }, 1000, 'easeInOutExpo');
                
                // Update URL without jumping
                if (history.pushState) {
                    history.pushState(null, null, '#' + target.attr('id'));
                } else {
                    location.hash = '#' + target.attr('id');
                }
            }
        }
    });
});