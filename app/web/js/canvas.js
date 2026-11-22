/**
 * Pest Bounding Box Overlay Canvas
 * Meets FR-13: Draw pest boxes (pests[].box_xyxy, pixels of the sent image) on the photo.
 *
 * Drawn at the screen's pixel density (sharp on high-resolution phones) and with the app's own font, which is
 * loaded first so that Indic pest names are not drawn with a fallback font that lacks the script.
 */

class PestCanvas {
  /**
   * Render image and draw pest bounding boxes
   * @param {HTMLCanvasElement} canvas
   * @param {string} imageSrc Object URL or base64
   * @param {Array} pests Array of detected pest objects
   */
  static render(canvas, imageSrc, pests = []) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const img = new Image();
    const FONT = '700 13px "KR Sans", system-ui, sans-serif';

    // Short name on the photo: "Mava - sap-sucking pest (Aphids)" -> "Mava (Aphids)", with the confidence
    const labelOf = (pest) => {
      const conf = pest.confidence ? ` ${Math.round(pest.confidence * 100)}%` : "";
      const name = (pest.name || "Pest").replace(/ - [^(]*(?=\(|$)/, " ").replace(/\s+/g, " ").trim();
      return `${name}${conf}`;
    };

    const draw = () => {
      // Fit to container width while preserving natural aspect ratio
      const containerWidth = canvas.parentElement ? canvas.parentElement.clientWidth : 360;
      const targetWidth = Math.min(containerWidth, 600);
      const scale = targetWidth / img.naturalWidth;
      const targetHeight = img.naturalHeight * scale;
      const dpr = Math.min(3, window.devicePixelRatio || 1);

      canvas.width = Math.round(targetWidth * dpr);
      canvas.height = Math.round(targetHeight * dpr);
      canvas.style.width = `${targetWidth}px`;
      canvas.style.height = `${targetHeight}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Original photo
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight);

      // One box per insect, label above it
      (Array.isArray(pests) ? pests : []).forEach(pest => {
        if (!pest.box_xyxy || pest.box_xyxy.length !== 4) return;
        const [x1, y1, x2, y2] = pest.box_xyxy;
        const bx = x1 * scale, by = y1 * scale, bw = (x2 - x1) * scale, bh = (y2 - y1) * scale;

        ctx.lineWidth = 2.5;
        ctx.strokeStyle = "#f59e0b";
        ctx.fillStyle = "rgba(245, 158, 11, 0.12)";
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(bx, by, bw, bh, 6); else ctx.rect(bx, by, bw, bh);
        ctx.fill();
        ctx.stroke();

        const label = labelOf(pest);
        ctx.font = FONT;
        const textHeight = 22;
        const textWidth = ctx.measureText(label).width + 14;
        const labelX = Math.min(bx, Math.max(0, targetWidth - textWidth));
        const labelY = by - textHeight - 4 >= 0 ? by - textHeight - 4 : by + 4;
        ctx.fillStyle = "#f59e0b";
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(labelX, labelY, textWidth, textHeight, 6); else ctx.rect(labelX, labelY, textWidth, textHeight);
        ctx.fill();
        ctx.fillStyle = "#1f1300";
        ctx.textBaseline = "middle";
        ctx.fillText(label, labelX + 7, labelY + textHeight / 2 + 1);
      });
    };

    img.onload = () => {
      // Wait for the app font with the glyphs of the labels (Devanagari, Tamil, ...); draw anyway if it fails
      const text = (Array.isArray(pests) ? pests : []).map(labelOf).join(" ");
      if (text && document.fonts && document.fonts.load) {
        document.fonts.load(FONT, text).then(draw, draw);
      } else {
        draw();
      }
    };

    img.src = imageSrc;
  }
}

window.PestCanvas = PestCanvas;
