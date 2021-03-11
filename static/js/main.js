document.addEventListener("DOMContentLoaded", function() {
    var inputs = document.querySelectorAll('.file-input')
    console.log(inputs)
    for (var i = 0, len = inputs.length; i < len; i++) {
        customInput(inputs[i])
    }

    function customInput (el) {
        const fileInput = el.querySelector('[type="file"]')
        const label = el.querySelector('[data-js-label]')
    
        fileInput.onchange =
        fileInput.onmouseout = function () {
            if (!fileInput.value) return
        
            var value = fileInput.value.replace(/^.*[\\\/]/, '')
            el.className += ' -chosen'
            label.innerText = value
        }
    }
});