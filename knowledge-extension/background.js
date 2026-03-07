// Step 1: background.js Placeholder message handler
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Can be used later for data storage pipeline
  if (message.action === "extraction_result") {
    console.log("Knowledge Memory - Background script received:", message.data);
    if (typeof Logger !== 'undefined') Logger.log(message.data);
  } else {
    console.log("Knowledge Memory - Background script received:", message);
    if (typeof Logger !== 'undefined') Logger.log(message);
  }
});

// Step 9: Listen for keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
  console.log("Command triggered:", command);
  if (command === "save_page") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length === 0) return;
      const activeTab = tabs[0];
      
      // Inject content script and send extraction request
      chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        files: ['content.js']
      }, () => {
        chrome.tabs.sendMessage(activeTab.id, { action: "request_extraction" });
      });
    });
  }
});
