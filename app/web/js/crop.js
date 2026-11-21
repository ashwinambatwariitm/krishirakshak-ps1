/**
 * KrishiRakshak photo crop step (offline, no library)
 *
 * After a photo is taken or chosen, the farmer sees it with a frame and can cut out the affected leaf or the insect
 * before it goes to the device: drag the frame to move it, drag a corner to resize it. "Check this part" sends the
 * cut-out as a JPEG; "Use whole photo" sends the photo unchanged. Less background helps the leaf check, the disease
 * model and the insect detector, and a smaller photo uploads faster over the hotspot.
 *
 * Coordinates: the frame is kept in photo pixels (natural size); the screen position is derived from the shown size.
 */
class PhotoCropper {
  constructor() {
    this.img = null;          // loaded photo
    this.file = null;         // the original file (sent unchanged for "whole photo")
    this.rect = null;         // frame in photo pixels {x, y, w, h}
    this.drag = null;         // current drag: {mode, startX, startY, rect}
    this.onDone = null;       // callback(blob)
  }

  // Shown photo size / natural size
  scale() {
    const el = document.getElementById("crop-image");
    return el.clientWidth / this.img.naturalWidth;
  }

  /** Show the crop screen for this file; onDone(blob) gets the cut-out or the original file. */
  open(file, onDone) {
    this.file = file;
    this.onDone = onDone;
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      this.img = img;
      document.getElementById("crop-image").src = url;
      showView("crop");
      // Start with a centred frame over 80% of the photo
      const w = img.naturalWidth, h = img.naturalHeight;
      this.rect = { x: w * 0.1, y: h * 0.1, w: w * 0.8, h: h * 0.8 };
      // The shown size is known only after layout
      requestAnimationFrame(() => this.draw());
    };
    img.onerror = () => { URL.revokeObjectURL(url); onDone(file); };   // not decodable here: let the device decide
    img.src = url;
  }

  draw() {
    const box = document.getElementById("crop-frame");
    if (!box || !this.img) return;
    const s = this.scale();
    box.style.left = `${this.rect.x * s}px`;
    box.style.top = `${this.rect.y * s}px`;
    box.style.width = `${this.rect.w * s}px`;
    box.style.height = `${this.rect.h * s}px`;
  }

  // Keep the frame inside the photo and at least 10% of the shorter side
  clamp(r) {
    const W = this.img.naturalWidth, H = this.img.naturalHeight;
    const min = Math.min(W, H) * 0.1;
    r.w = Math.max(min, Math.min(r.w, W));
    r.h = Math.max(min, Math.min(r.h, H));
    r.x = Math.max(0, Math.min(r.x, W - r.w));
    r.y = Math.max(0, Math.min(r.y, H - r.h));
    return r;
  }

  bind() {
    const frame = document.getElementById("crop-frame");
    if (!frame) return;
    frame.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      frame.setPointerCapture(e.pointerId);
      const handle = e.target.getAttribute("data-handle");     // nw, ne, sw, se or null (move)
      this.drag = { mode: handle || "move", startX: e.clientX, startY: e.clientY, rect: { ...this.rect } };
    });
    frame.addEventListener("pointermove", (e) => {
      if (!this.drag) return;
      const s = this.scale();
      const dx = (e.clientX - this.drag.startX) / s, dy = (e.clientY - this.drag.startY) / s;
      const r0 = this.drag.rect;
      let r = { ...r0 };
      if (this.drag.mode === "move") {
        r.x = r0.x + dx; r.y = r0.y + dy;
        this.rect = this.clamp(r);
      } else {
        // Resize from a corner; the opposite corner stays where it is
        const right = r0.x + r0.w, bottom = r0.y + r0.h;
        if (this.drag.mode.includes("w")) { r.x = Math.min(r0.x + dx, right - 1); r.w = right - r.x; }
        if (this.drag.mode.includes("e")) { r.w = r0.w + dx; }
        if (this.drag.mode.includes("n")) { r.y = Math.min(r0.y + dy, bottom - 1); r.h = bottom - r.y; }
        if (this.drag.mode.includes("s")) { r.h = r0.h + dy; }
        // Clamp to the photo without moving the fixed corner
        const W = this.img.naturalWidth, H = this.img.naturalHeight, min = Math.min(W, H) * 0.1;
        if (r.x < 0) { r.w += r.x; r.x = 0; }
        if (r.y < 0) { r.h += r.y; r.y = 0; }
        r.w = Math.min(Math.max(r.w, min), W - r.x);
        r.h = Math.min(Math.max(r.h, min), H - r.y);
        if (this.drag.mode.includes("w")) r.x = right - r.w;
        if (this.drag.mode.includes("n")) r.y = bottom - r.h;
        this.rect = r;
      }
      this.draw();
    });
    const end = () => { this.drag = null; };
    frame.addEventListener("pointerup", end);
    frame.addEventListener("pointercancel", end);
    window.addEventListener("resize", () => this.draw());

    document.getElementById("btn-crop-use").addEventListener("click", () => this.finish(true));
    document.getElementById("btn-crop-whole").addEventListener("click", () => this.finish(false));
    document.getElementById("btn-crop-cancel").addEventListener("click", () => showView("home"));
  }

  /** Cut-out as JPEG (longest side at most 1600 px, enough for every model) or the original file. */
  finish(cut) {
    if (!cut || !this.img) { this.onDone(this.file); return; }
    const r = this.rect;
    const k = Math.min(1, 1600 / Math.max(r.w, r.h));
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(r.w * k);
    canvas.height = Math.round(r.h * k);
    canvas.getContext("2d").drawImage(this.img, r.x, r.y, r.w, r.h, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => this.onDone(blob || this.file), "image/jpeg", 0.92);
  }
}

window.photoCropper = new PhotoCropper();
document.addEventListener("DOMContentLoaded", () => window.photoCropper.bind());
