document.addEventListener("DOMContentLoaded", function() {
  const elements = document.querySelectorAll('.animate-text');

  elements.forEach((el, index) => {
    const text = el.textContent;
    el.textContent = '';
    el.style.opacity = 1;

    let charIndex = 0;
    const typeWriter = () => {
      if (charIndex < text.length) {
        el.textContent += text.charAt(charIndex);
        charIndex++;
        setTimeout(typeWriter, 100); // Speed of typing (100ms per character)
      }
    };

    // Start typing after a delay based on element index
    setTimeout(typeWriter, index * 1000); // 1 second delay between elements
  });
});
