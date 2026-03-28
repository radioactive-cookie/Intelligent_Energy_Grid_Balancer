import React, { useEffect, useRef } from 'react';

const TunnelBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let width, height;

    const resize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };

    window.addEventListener('resize', resize);
    resize();

    // Tunnel config
    const rings = [];
    const ringCount = 30;
    const speed = 0.035;
    const ringSpacing = 1.2;

    // Cyan rings: rgba(0,229,255,0.35)
    // Magenta rings: rgba(255,0,200,0.2)
    for (let i = 0; i < ringCount; i++) {
      rings.push({
        z: i * ringSpacing,
        color: i % 5 === 0 ? 'rgba(255, 0, 200, 0.2)' : 'rgba(0, 229, 255, 0.35)'
      });
    }

    const draw = () => {
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, width, height);

      const centerX = width / 2;
      const centerY = height / 2;
      const fov = 450;

      // Draw radial perspective lines
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(0, 229, 255, 0.08)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i < 360; i += 15) {
        const rad = (i * Math.PI) / 180;
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(
          centerX + Math.cos(rad) * width,
          centerY + Math.sin(rad) * height
        );
      }
      ctx.stroke();

      rings.sort((a, b) => b.z - a.z);

      rings.forEach((ring) => {
        ring.z -= speed;
        if (ring.z < 0.1) {
          ring.z = ringCount * ringSpacing;
        }

        const scale = fov / ring.z;
        const ringWidth = width * 1.2 * scale;
        const ringHeight = height * 1.2 * scale;

        const x = centerX - ringWidth / 2;
        const y = centerY - ringHeight / 2;

        ctx.strokeStyle = ring.color;
        ctx.lineWidth = Math.max(0.5, 1.5 * scale / 10);
        ctx.globalAlpha = Math.min(1, (ringCount * ringSpacing - ring.z) / (ringCount * ringSpacing / 1.5));
        
        ctx.beginPath();
        ctx.rect(x, y, ringWidth, ringHeight);
        ctx.stroke();
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0, background: '#000000' }}
    />
  );
};

export default TunnelBackground;
