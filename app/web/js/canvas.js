/**
 * Pest Bounding Box Overlay Canvas
 * Meets FR-13: Draw pest boxes (pests[].box_xyxy, pixels of the sent image) on the photo.
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

    img.onload = () => {
      // Fit to container width while preserving natural aspect ratio
      const containerWidth = canvas.parentElement ? canvas.parentElement.clientWidth : 360;
      const targetWidth = Math.min(containerWidth, 600);
      const scale = targetWidth / img.naturalWidth;
      const targetHeight = img.naturalHeight * scale;

      canvas.width = targetWidth;
      canvas.height = targetHeight;

      // Draw original photo
      ctx.drawImage(img, 0, 0, targetWidth, targetHeight);

      // Draw bounding boxes for each pest
      if (Array.isArray(pests) && pests.length > 0) {
        pests.forEach(pest => {
          if (!pest.box_xyxy || pest.box_xyxy.length !== 4) return;
          const [x1, y1, x2, y2] = pest.box_xyxy;

          const scaledX1 = x1 * scale;
          const scaledY1 = y1 * scale;
          const boxW = (x2 - x1) * scale;
          const boxH = (y2 - y1) * scale;

          // Draw neon bounding box
          ctx.lineWidth = 3;
          ctx.strokeStyle = "#e53935"; // Vibrant crimson/red
          ctx.strokeRect(scaledX1, scaledY1, boxW, boxH);

          // Subtle fill for visibility
          ctx.fillStyle = "rgba(229, 57, 53, 0.15)";
          ctx.fillRect(scaledX1, scaledY1, boxW, boxH);

          // Label text
          const conf = pest.confidence ? ` ${Math.round(pest.confidence * 100)}%` : "";
          // Short name on the photo: "Mava - sap-sucking pest (Aphids)" -> "Mava (Aphids)"
          const name = (pest.name || "Pest").replace(/ - [^(]*(?=\(|$)/, " ").replace(/\s+/g, " ").trim();
          const label = `${name}${conf}`;

          ctx.font = "bold 13px system-ui, sans-serif";
          const textMetrics = ctx.measureText(label);
          const textHeight = 18;
          const textWidth = textMetrics.width + 10;

          // Label badge background
          const labelY = Math.max(0, scaledY1 - textHeight);
          ctx.fillStyle = "#e53935";
          ctx.fillRect(scaledX1, labelY, textWidth, textHeight);

          // Label text in white
          ctx.fillStyle = "#ffffff";
          ctx.textBaseline = "middle";
          ctx.fillText(label, scaledX1 + 5, labelY + textHeight / 2);
        });
      }
    };

    img.src = imageSrc;
  }
}

window.PestCanvas = PestCanvas;
