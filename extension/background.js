browser.webRequest.onBeforeRequest.addListener(
  function(details) {
    // Check if the request is coming from our Flask app
    if (details.url.includes("instagram.com") && 
        (!details.originUrl || !details.originUrl.includes("localhost:5000"))) {
      return {
        redirectUrl: "http://localhost:5000"
      };
    }
    // If it's coming from our Flask app, let it proceed to Instagram
    return { cancel: false };
  },
  {
    urls: [
      "*://instagram.com/*",
      "*://www.instagram.com/*"
    ]
  },
  ["blocking"]
);

