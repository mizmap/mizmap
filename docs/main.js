// Upgrade the download button to point straight at the latest installer
// asset. Falls back gracefully to the /releases/latest page if the API
// request fails (offline, rate-limited, no releases yet).
(function () {
  "use strict";

  var REPO = "mizmap/mizmap";
  var btn = document.getElementById("download-btn");
  var versionEl = document.getElementById("download-version");
  if (!btn || !versionEl) return;

  fetch("https://api.github.com/repos/" + REPO + "/releases/latest", {
    headers: { "Accept": "application/vnd.github+json" }
  })
    .then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(function (release) {
      var asset = (release.assets || []).find(function (a) {
        return /^mizmap-setup-.*\.exe$/i.test(a.name);
      });
      if (asset && asset.browser_download_url) {
        btn.href = asset.browser_download_url;
      }
      if (release.tag_name) {
        versionEl.textContent = release.tag_name;
      }
    })
    .catch(function () {
      // Leave the static href + "latest release" label in place.
    });
})();

// Click any feature screenshot to view it at full resolution in a
// lightbox. Close on any click or Escape.
(function () {
  "use strict";

  var imgs = document.querySelectorAll(".shot img");
  if (imgs.length === 0) return;

  var box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.innerHTML =
    '<button class="lightbox-close" type="button" aria-label="Close">×</button>' +
    '<img alt="" />';
  document.body.appendChild(box);

  var bigImg = box.querySelector("img");

  function open(src, alt) {
    bigImg.src = src;
    bigImg.alt = alt || "";
    box.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function close() {
    box.classList.remove("open");
    document.body.style.overflow = "";
    // Free the large image after the fade.
    setTimeout(function () { if (!box.classList.contains("open")) bigImg.src = ""; }, 150);
  }

  imgs.forEach(function (img) {
    img.addEventListener("click", function () {
      open(img.currentSrc || img.src, img.alt);
    });
  });

  box.addEventListener("click", close);
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && box.classList.contains("open")) close();
  });
})();
