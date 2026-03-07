// Step 5 & 6: Content extraction and cleaning
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "request_extraction") {
    
    let contentText = "";
    const articleElement = document.querySelector("article");
    
    if (articleElement) {
      contentText = articleElement.innerText;
    } else {
      contentText = document.body.innerText;
    }
    
    // Basic cleanup: remove excessive whitespace
    contentText = contentText.replace(/\s+/g, ' ').trim();
    
    const pageData = {
      title: document.title,
      url: window.location.href,
      timestamp: new Date().toISOString(),
      content: contentText
    };
    
    console.log("Knowledge Memory - Extracted Data:", pageData);
    
    // Step 8: Send Data Back to Popup or Background
    chrome.runtime.sendMessage({ action: "extraction_result", data: pageData });

    // Automatic popup (toast) acknowledgment when successfully saved
    showAcknowledgmentPopup();
  }
});

function showAcknowledgmentPopup() {
  // Remove if one already exists
  const existing = document.getElementById("knowledge-memory-popup");
  if (existing) existing.remove();

  const popup = document.createElement("div");
  popup.id = "knowledge-memory-popup";
  popup.innerText = "Page successfully saved to Knowledge Memory!";
  popup.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #4CAF50;
    color: white;
    padding: 16px 24px;
    border-radius: 8px;
    font-family: Arial, sans-serif;
    font-size: 16px;
    z-index: 999999;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: opacity 0.5s ease;
  `;
  
  document.body.appendChild(popup);

  // Fade out and remove after 3 seconds
  setTimeout(() => {
    popup.style.opacity = "0";
    setTimeout(() => popup.remove(), 500);
  }, 3000);
}
