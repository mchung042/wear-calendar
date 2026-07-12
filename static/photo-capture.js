/**
 * In-app photo capture for closet add/edit.
 * - Take photo: mobile capture=environment, or desktop webcam modal
 * - Choose photo: standard library picker
 * Syncs a single <input name="photo"> for multipart submit.
 */
(function () {
  function isLikelyMobile() {
    return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
  }

  function setFile(input, file, sourceInput) {
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    if (sourceInput) sourceInput.value = file ? (sourceInput.dataset.from || "camera") : "";
    input.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function showPreview(root, file) {
    const preview = root.querySelector("[data-preview]");
    const img = root.querySelector("[data-preview-img]");
    if (!preview || !img) return;
    if (!file) {
      preview.hidden = true;
      img.removeAttribute("src");
      if (img.dataset.objectUrl) {
        URL.revokeObjectURL(img.dataset.objectUrl);
        delete img.dataset.objectUrl;
      }
      return;
    }
    if (img.dataset.objectUrl) URL.revokeObjectURL(img.dataset.objectUrl);
    const url = URL.createObjectURL(file);
    img.dataset.objectUrl = url;
    img.src = url;
    preview.hidden = false;
  }

  function openWebcam(root, fileInput, sourceInput) {
    const modal = root.querySelector("[data-webcam-modal]");
    const video = root.querySelector("[data-webcam-video]");
    const errEl = root.querySelector("[data-webcam-error]");
    if (!modal || !video) return;

    let stream = null;

    function stop() {
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
        stream = null;
      }
      video.srcObject = null;
      modal.hidden = true;
    }

    modal.hidden = false;
    if (errEl) {
      errEl.hidden = true;
      errEl.textContent = "";
    }

    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" }, audio: false })
      .then((s) => {
        stream = s;
        video.srcObject = s;
        return video.play();
      })
      .catch(() =>
        navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then((s) => {
          stream = s;
          video.srcObject = s;
          return video.play();
        })
      )
      .catch(() => {
        if (errEl) {
          errEl.hidden = false;
          errEl.textContent =
            "Camera access blocked or unavailable. Use Choose photo, or allow camera permission.";
        }
      });

    const snapBtn = root.querySelector("[data-webcam-snap]");
    const cancelBtn = root.querySelector("[data-webcam-cancel]");

    function onSnap() {
      if (!stream) return;
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth || 720;
      canvas.height = video.videoHeight || 960;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(
        (blob) => {
          if (!blob) return;
          const file = new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" });
          if (sourceInput) {
            sourceInput.dataset.from = "camera";
            sourceInput.value = "camera";
          }
          setFile(fileInput, file, sourceInput);
          showPreview(root, file);
          stop();
          cleanup();
        },
        "image/jpeg",
        0.9
      );
    }

    function onCancel() {
      stop();
      cleanup();
    }

    function cleanup() {
      snapBtn && snapBtn.removeEventListener("click", onSnap);
      cancelBtn && cancelBtn.removeEventListener("click", onCancel);
    }

    snapBtn && snapBtn.addEventListener("click", onSnap);
    cancelBtn && cancelBtn.addEventListener("click", onCancel);
  }

  function init(root) {
    const fileInput = root.querySelector("[data-photo-input]");
    const cameraInput = root.querySelector("[data-camera-input]");
    const sourceInput = root.querySelector("[data-photo-source]");
    const takeBtn = root.querySelector("[data-take]");
    const libraryBtn = root.querySelector("[data-library]");
    const clearBtn = root.querySelector("[data-clear]");
    if (!fileInput) return;

    takeBtn &&
      takeBtn.addEventListener("click", () => {
        if (isLikelyMobile() && cameraInput) {
          if (sourceInput) {
            sourceInput.dataset.from = "camera";
          }
          cameraInput.click();
          return;
        }
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          openWebcam(root, fileInput, sourceInput);
        } else if (cameraInput) {
          cameraInput.click();
        } else {
          fileInput.click();
        }
      });

    libraryBtn &&
      libraryBtn.addEventListener("click", () => {
        if (sourceInput) {
          sourceInput.dataset.from = "library";
          sourceInput.value = "";
        }
        fileInput.click();
      });

    cameraInput &&
      cameraInput.addEventListener("change", () => {
        const file = cameraInput.files && cameraInput.files[0];
        if (!file) return;
        if (sourceInput) {
          sourceInput.dataset.from = "camera";
          sourceInput.value = "camera";
        }
        setFile(fileInput, file, sourceInput);
        showPreview(root, file);
        cameraInput.value = "";
      });

    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      if (file && sourceInput && sourceInput.dataset.from !== "camera") {
        sourceInput.value = "library";
      }
      showPreview(root, file || null);
    });

    clearBtn &&
      clearBtn.addEventListener("click", () => {
        fileInput.value = "";
        if (cameraInput) cameraInput.value = "";
        if (sourceInput) {
          sourceInput.value = "";
          delete sourceInput.dataset.from;
        }
        showPreview(root, null);
      });
  }

  document.querySelectorAll("[data-photo-capture]").forEach(init);
})();
