document.getElementById('save-btn').addEventListener('click', () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const activeTab = tabs[0];
    
    // Step 4: Inject content script
    chrome.scripting.executeScript({
      target: { tabId: activeTab.id },
      files: ['content.js']
    }, () => {
      // Send a message to the newly injected script to start extraction
      chrome.tabs.sendMessage(activeTab.id, { action: "request_extraction" });
    });
  });
});

// Step 8: Listen for the extracted data from content.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "extraction_result") {
    const statusEl = document.getElementById('status');
    const outputEl = document.getElementById('output');
    
    statusEl.style.display = 'block';
    statusEl.textContent = "Page saved successfully";
    
    outputEl.style.display = 'block';
    outputEl.textContent = JSON.stringify(message.data, null, 2);
    
    console.log("Knowledge Memory - Received in Popup:", message.data);
  }
});
