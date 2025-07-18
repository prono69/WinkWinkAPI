tsParticles.load("tsparticles", {
  fullScreen: { enable: true, zIndex: 0 },
  background: { color: "transparent" },
  particles: {
    number: { value: 40 },
    color: { value: ["#00c6ff", "#0072ff", "#ffffff"] },
    shape: { type: "circle" },
    opacity: { value: 0.6 },
    size: { value: { min: 2, max: 4 } },
    move: { enable: true, speed: 1.5, direction: "none", outModes: "bounce" }
  },
  interactivity: {
    events: { onHover: { enable: true, mode: "repulse" } },
    modes: { repulse: { distance: 80, duration: 0.4 } }
  }
});