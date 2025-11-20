// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (navbarToggle && navbarMenu) {
        navbarToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (navbarMenu && navbarMenu.classList.contains('active')) {
            const isClickInside = navbarMenu.contains(event.target) || navbarToggle.contains(event.target);
            if (!isClickInside) {
                navbarMenu.classList.remove('active');
            }
        }
    });
});

// Auto-hide messages after 5 seconds
function autoHideMessages() {
    const messages = document.querySelectorAll('.alert');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s ease';
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
}

document.addEventListener('DOMContentLoaded', autoHideMessages);

// Countdown Timer Utility
function updateCountdown(elementId, targetDate) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    function update() {
        const now = new Date().getTime();
        const distance = targetDate - now;
        
        if (distance < 0) {
            element.innerHTML = "Started!";
            return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        element.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }
    
    update();
    setInterval(update, 1000);
}

// Smooth Scroll to Section
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Form Validation Helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(function(field) {
        if (!field.value.trim()) {
            field.classList.add('error');
            isValid = false;
        } else {
            field.classList.remove('error');
        }
    });
    
    return isValid;
}

// Copy to Clipboard Utility
function copyToClipboard(text, buttonElement) {
    navigator.clipboard.writeText(text).then(function() {
        const originalText = buttonElement.innerText;
        buttonElement.innerText = 'Copied!';
        buttonElement.style.background = 'var(--success-green)';
        
        setTimeout(function() {
            buttonElement.innerText = originalText;
            buttonElement.style.background = '';
        }, 2000);
    }).catch(function(err) {
        console.error('Failed to copy:', err);
    });
}

// Image Preview for File Uploads
function previewImage(input, previewElementId) {
    const preview = document.getElementById(previewElementId);
    if (!preview || !input.files || !input.files[0]) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(input.files[0]);
}

// Format Time Remaining
function formatTimeRemaining(seconds) {
    if (seconds < 60) {
        return `${seconds}s`;
    } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}m ${secs}s`;
    } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    }
}

// Add animation on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.card, .tournament-card');
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '0';
                entry.target.style.transform = 'translateY(20px)';
                
                setTimeout(function() {
                    entry.target.style.transition = 'all 0.5s ease';
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, 100);
                
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    elements.forEach(function(el) {
        observer.observe(el);
    });
}

document.addEventListener('DOMContentLoaded', animateOnScroll);

// Confirm dangerous actions
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to perform this action?');
}

// Number formatting
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Currency formatting (Nigerian Naira)
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN'
    }).format(amount);
}

// Toast notification system
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.style.animation = 'slideIn 0.3s ease';
    
    document.body.appendChild(toast);
    
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s ease';
        setTimeout(function() {
            toast.remove();
        }, 500);
    }, 3000);
}

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
