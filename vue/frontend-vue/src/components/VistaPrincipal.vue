<template>
  <div class="layout-container">
    
    <div class="ambient-light light-top"></div>
    <div class="ambient-light light-bottom"></div>

    <BarraNavegacion />

    <main class="main-content">
      <section class="hero-wrapper">
        <SeccionPrincipal />
      </section>

      <section class="container py-5">
        <div class="row mb-5 text-center">
          <div class="col-12">
            <h2 class="fw-bold text-main">Características de la Plataforma</h2>
            [cite_start]<p class="text-muted">Herramientas diseñadas para el ahorro energético [cite: 11]</p>
          </div>
        </div>

        <div class="row g-4">
          <div class="col-md-4">
            <TarjetaInfo 
              titulo="Monitoreo en Tiempo Real" 
              contenido="Visualización instantánea de sensores y consumo eléctrico."
            />
          </div>
          <div class="col-md-4">
            <TarjetaInfo 
              titulo="Análisis de Datos" 
              contenido="Detección de patrones y picos de consumo anómalos."
            />
          </div>
          <div class="col-md-4">
            <TarjetaInfo 
              titulo="Reportes Automatizados" 
              contenido="Generación de informes para la toma de decisiones estratégicas."
            />
          </div>
        </div>
      </section>
    </main>

    <footer class="text-center py-4 text-muted border-top" style="border-color: var(--border-color) !important;">
      <small>© 2025 TecNM Campus Chetumal - Plataforma IoT</small>
    </footer>
  </div>
</template>

<script>
import BarraNavegacion from './BarraNavegacion.vue';
import SeccionPrincipal from './SeccionPrincipal.vue';
import TarjetaInfo from './TarjetaInfo.vue';

export default {
  name: 'VistaPrincipal',
  components: { BarraNavegacion, SeccionPrincipal, TarjetaInfo }
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  background-color: var(--bg-app); /* IMPORTANTE */
}

/* Luces Globales */
.ambient-light {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  z-index: 0;
  opacity: var(--glow-opacity); /* Se ajusta solo en light/dark */
  transition: opacity 0.3s;
}

.light-top {
  top: -10%; left: -10%; width: 50vw; height: 50vw;
  background: radial-gradient(circle, var(--primary), transparent 70%);
}

.light-bottom {
  bottom: -10%; right: -5%; width: 40vw; height: 40vw;
  background: radial-gradient(circle, var(--accent), transparent 70%);
}

.main-content {
  position: relative;
  z-index: 1;
}

.hero-wrapper { padding-top: 60px; }
.text-main { color: var(--text-main); }
.text-muted { color: var(--text-muted); }
</style>