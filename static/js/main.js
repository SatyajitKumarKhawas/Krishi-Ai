document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeComponents();
    
    // Add loading animations
    addLoadingAnimations();
    
    // Setup form validations
    setupFormValidations();
    
    // Initialize file upload handlers
    initializeFileUploads();
    
    // Setup language support
    setupLanguageSupport();
});

// Initialize main components
function initializeComponents() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            if (alert.classList.contains('alert-dismissible')) {
                const closeButton = alert.querySelector('.btn-close');
                if (closeButton) {
                    closeButton.click();
                }
            }
        });
    }, 5000);
    
    // Initialize tooltips if Bootstrap is loaded
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

// Add loading animations to buttons
function addLoadingAnimations() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                submitButton.classList.add('btn-loading');
                submitButton.disabled = true;
                
                // Re-enable button after 10 seconds as failsafe
                setTimeout(() => {
                    submitButton.classList.remove('btn-loading');
                    submitButton.disabled = false;
                }, 10000);
            }
        });
    });
}

// Setup form validations
function setupFormValidations() {
    // Phone number validation
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            const phonePattern = /^[6-9]\d{9}$/;
            const value = this.value.replace(/\D/g, '');
            
            if (value.length > 10) {
                this.value = value.substring(0, 10);
            } else {
                this.value = value;
            }
            
            if (value.length === 10 && phonePattern.test(value)) {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            } else if (value.length > 0) {
                this.classList.remove('is-valid');
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-valid', 'is-invalid');
            }
        });
    });
    
    // Email validation
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (this.value && !emailPattern.test(this.value)) {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            } else if (this.value) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            }
        });
    });
    
    // Password strength indicator
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        if (input.name === 'password') {
            input.addEventListener('input', function() {
                const strength = getPasswordStrength(this.value);
                showPasswordStrength(this, strength);
            });
        }
    });
}

// Password strength calculation
function getPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 6) strength += 1;
    if (password.length >= 10) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    return strength;
}

// Show password strength indicator
function showPasswordStrength(input, strength) {
    let existingIndicator = input.parentNode.querySelector('.password-strength');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    if (input.value.length > 0) {
        const indicator = document.createElement('div');
        indicator.className = 'password-strength mt-1';
        
        const colors = ['#dc3545', '#fd7e14', '#ffc107', '#20c997', '#28a745', '#17a2b8'];
        const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
        
        indicator.innerHTML = `
            <small style="color: ${colors[strength]}">
                Strength: ${labels[strength]}
            </small>
        `;
        
        input.parentNode.insertBefore(indicator, input.nextSibling);
    }
}

// File upload handlers
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        // Create custom file upload area
        createCustomFileUpload(input);
        
        // Handle file selection
        input.addEventListener('change', function() {
            handleFileSelection(this);
        });
    });
}

// Create custom file upload interface
function createCustomFileUpload(input) {
    if (input.dataset.customized) return;
    
    const wrapper = document.createElement('div');
    wrapper.className = 'file-upload-wrapper';
    
    const uploadArea = document.createElement('div');
    uploadArea.className = 'file-upload-area';
    uploadArea.innerHTML = `
        <i class="fas fa-cloud-upload-alt fa-2x text-success mb-2"></i>
        <p class="mb-1"><strong>Click to select file</strong> or drag and drop</p>
        <small class="text-muted">Supported formats: JPG, PNG, GIF, MP3, WAV, OGG</small>
    `;
    
    // Insert wrapper before input
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    wrapper.appendChild(uploadArea);
    
    // Hide original input
    input.style.display = 'none';
    input.dataset.customized = 'true';
    
    // Add click handler
    uploadArea.addEventListener('click', () => input.click());
    
    // Add drag and drop handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        input.files = e.dataTransfer.files;
        handleFileSelection(input);
    });
}

// Handle file selection
function handleFileSelection(input) {
    const uploadArea = input.parentNode.querySelector('.file-upload-area');
    const file = input.files[0];
    
    if (file) {
        const fileSize = (file.size / 1024 / 1024).toFixed(2);
        uploadArea.innerHTML = `
            <i class="fas fa-file-${getFileIcon(file.type)} fa-2x text-success mb-2"></i>
            <p class="mb-1"><strong>${file.name}</strong></p>
            <small class="text-muted">Size: ${fileSize} MB</small>
            <button type="button" class="btn btn-sm btn-outline-danger mt-2" onclick="clearFileSelection(this)">
                <i class="fas fa-times"></i> Remove
            </button>
        `;
    }
}

// Clear file selection
function clearFileSelection(button) {
    const wrapper = button.closest('.file-upload-wrapper');
    const input = wrapper.querySelector('input[type="file"]');
    input.value = '';
    
    const uploadArea = wrapper.querySelector('.file-upload-area');
    uploadArea.innerHTML = `
        <i class="fas fa-cloud-upload-alt fa-2x text-success mb-2"></i>
        <p class="mb-1"><strong>Click to select file</strong> or drag and drop</p>
        <small class="text-muted">Supported formats: JPG, PNG, GIF, MP3, WAV, OGG</small>
    `;
}

// Get file icon based on file type
function getFileIcon(fileType) {
    if (fileType.startsWith('image/')) return 'image';
    if (fileType.startsWith('audio/')) return 'music';
    return 'file';
}

// Language support
function setupLanguageSupport() {
    const languageSelect = document.getElementById('preferred_language');
    if (languageSelect) {
        languageSelect.addEventListener('change', function() {
            // Store language preference
            localStorage.setItem('preferredLanguage', this.value);
            
            // Update page language hints
            updateLanguageHints(this.value);
        });
        
        // Load saved language preference
        const savedLanguage = localStorage.getItem('preferredLanguage');
        if (savedLanguage) {
            languageSelect.value = savedLanguage;
            updateLanguageHints(savedLanguage);
        }
    }
}

// Update language hints on page
function updateLanguageHints(language) {
    const hints = document.querySelectorAll('.language-hint');
    hints.forEach(hint => {
        if (language === 'ml') {
            hint.textContent = 'Malayalam ൽ ടൈപ്പ് ചെയ്യുക';
        } else {
            hint.textContent = 'Type in English';
        }
    });
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed notification`;
    notification.style.cssText = 'top: 100px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// AJAX form submission helper
function submitFormAjax(form, callback) {
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Add loading state
    if (submitButton) {
        submitButton.classList.add('btn-loading');
        submitButton.disabled = true;
    }
    
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (callback) callback(data);
        
        // Show notification
        if (data.status === 'success') {
            showNotification(data.message || 'Operation successful!', 'success');
        } else {
            showNotification(data.message || 'An error occurred!', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Network error occurred!', 'danger');
        if (callback) callback({ status: 'error', message: 'Network error' });
    })
    .finally(() => {
        // Remove loading state
        if (submitButton) {
            submitButton.classList.remove('btn-loading');
            submitButton.disabled = false;
        }
    });
}

// Voice input support (Web Speech API)
function initializeVoiceInput() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.log('Speech recognition not supported');
        return;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'ml-IN'; // Malayalam
    
    // Add voice input buttons to text areas
    document.querySelectorAll('textarea, input[type="text"]').forEach(input => {
        if (input.dataset.voiceEnabled !== 'false') {
            addVoiceButton(input, recognition);
        }
    });
}

// Add voice input button to form field
function addVoiceButton(input, recognition) {
    const wrapper = document.createElement('div');
    wrapper.className = 'input-group';
    
    // Wrap input
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);
    
    // Add voice button
    const voiceButton = document.createElement('button');
    voiceButton.type = 'button';
    voiceButton.className = 'btn btn-outline-success';
    voiceButton.innerHTML = '<i class="fas fa-microphone"></i>';
    voiceButton.title = 'Voice input';
    
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'input-group-append';
    buttonGroup.appendChild(voiceButton);
    wrapper.appendChild(buttonGroup);
    
    // Voice button click handler
    voiceButton.addEventListener('click', () => {
        if (voiceButton.classList.contains('recording')) {
            recognition.stop();
        } else {
            startVoiceRecognition(input, voiceButton, recognition);
        }
    });
}

// Start voice recognition
function startVoiceRecognition(input, button, recognition) {
    button.classList.add('recording');
    button.innerHTML = '<i class="fas fa-stop text-danger"></i>';
    button.title = 'Stop recording';
    
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        input.value = transcript;
        input.dispatchEvent(new Event('input'));
    };
    
    recognition.onend = () => {
        button.classList.remove('recording');
        button.innerHTML = '<i class="fas fa-microphone"></i>';
        button.title = 'Voice input';
    };
    
    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        showNotification('Voice recognition error. Please try again.', 'danger');
        button.classList.remove('recording');
        button.innerHTML = '<i class="fas fa-microphone"></i>';
        button.title = 'Voice input';
    };
    
    recognition.start();
}

// Initialize voice input when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure all elements are loaded
    setTimeout(initializeVoiceInput, 1000);
});

// Query form specific functionality
if (document.getElementById('queryForm')) {
    document.addEventListener('DOMContentLoaded', function() {
        // Handle query type changes
        const queryTypeRadios = document.querySelectorAll('input[name="query_type"]');
        queryTypeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                const imageSection = document.getElementById('image_upload_section');
                const voiceSection = document.getElementById('voice_upload_section');
                
                // Hide all sections first
                if (imageSection) imageSection.classList.add('d-none');
                if (voiceSection) voiceSection.classList.add('d-none');
                
                // Show relevant section
                if (this.value === 'image' && imageSection) {
                    imageSection.classList.remove('d-none');
                } else if (this.value === 'voice' && voiceSection) {
                    voiceSection.classList.remove('d-none');
                }
            });
        });
        
        // Handle form submission
        document.getElementById('queryForm').addEventListener('submit', function(e) {
            const queryText = document.getElementById('query_text').value.trim();
            if (!queryText) {
                e.preventDefault();
                showNotification('Please enter your query', 'danger');
                return false;
            }
            
            // Show success message
            showNotification('Submitting your query...', 'info');
        });
    });
}

// Export functions for global use
window.KrishiAI = {
    showNotification,
    submitFormAjax,
    clearFileSelection
};
