(function ($) {
    "use strict";


    /*==================================================================
    [ Focus input ]*/
    $('.input100').each(function(){
        $(this).on('blur', function(){
            if($(this).val().trim() != "") {
                $(this).addClass('has-val');
            }
            else {
                $(this).removeClass('has-val');
            }
        })    
    })
  
  
    /*==================================================================
    [ Validate ]*/
    var input = $('.validate-input .input100');

    $('.validate-form').on('submit',function(){
        var check = true;

        for(var i=0; i<input.length; i++) {
            if(validate(input[i]) == false){
                showValidate(input[i]);
                check=false;
            }
        }

        return check;
    });


    $('.validate-form .input100').each(function(){
        $(this).focus(function(){
           hideValidate(this);
        });
    });

    function validate(input) {
        const value = $(input).val().trim();
        const type = $(input).attr('type');
        const name = $(input).attr('name');
        
        if (type === 'email' || name === 'email') {
            // Complex email regex that follows RFC 5322 standard
            // Balances between strict validation and real-world email formats
            const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
            return emailRegex.test(value);
        } else if ($(input).prop('required')) {
            // More comprehensive required field validation
            if (value === '') {
                return false;
            }
            // Additional type-specific validations
            if (type === 'tel') {
                // Basic phone number validation
                const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
                return phoneRegex.test(value);
            }
            if (type === 'number' || name === 'age') {
                return !isNaN(parseFloat(value)) && isFinite(value);
            }
        }
        return true;
    }

    function showValidate(input) {
        const $input = $(input);
        const $parent = $input.parent();
        const type = $input.attr('type');
        const name = $input.attr('name');
        
        // Add error class and set aria-invalid for accessibility
        $parent.addClass('alert-validate');
        $input.attr('aria-invalid', 'true');
        
        // Provide more specific error messages
        let errorMessage = 'Please enter a valid value';
        if (type === 'email' || name === 'email') {
            errorMessage = 'Please enter a valid email address';
        } else if (type === 'tel') {
            errorMessage = 'Please enter a valid phone number';
        } else if (type === 'number' || name === 'age') {
            errorMessage = 'Please enter a valid number';
        } else if ($input.prop('required')) {
            errorMessage = 'This field is required';
        }
        
        // Add error message if not already present
        if ($parent.find('.error-message').length === 0) {
            $parent.append(`<span class="error-message">${errorMessage}</span>`);
        }
    }

    function hideValidate(input) {
        const $input = $(input);
        const $parent = $input.parent();
        
        // Remove error class and clear aria-invalid
        $parent.removeClass('alert-validate');
        $input.removeAttr('aria-invalid');
        
        // Remove error message if present
        $parent.find('.error-message').remove();
    }
    
    
})(jQuery);