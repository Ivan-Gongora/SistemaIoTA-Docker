<template>
  <div class="info-card h-100">
    <div class="card-body">
      <div class="icon-container mb-4">
        <i class="bi" :class="getIcono"></i>
      </div>
      
      <h5 class="card-title">{{ titulo }}</h5>
      <p class="card-text">{{ contenido }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TarjetaInfo',
  props: {
    titulo: { type: String, required: true },
    contenido: { type: String, required: true }
  },
  computed: {
    getIcono() {
      const t = this.titulo.toLowerCase();
      if (t.includes('monitoreo')) return 'bi-activity';
      if (t.includes('análisis') || t.includes('datos')) return 'bi-pie-chart-fill';
      if (t.includes('alertas')) return 'bi-bell-fill';
      return 'bi-layers-fill';
    }
  }
}
</script>

<style scoped>
.info-card {
  background: var(--bg-card); /* Blanco o Cristal Oscuro */
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  box-shadow: var(--card-shadow);
}

.info-card:hover {
  transform: translateY(-8px);
  border-color: var(--primary);
  /* Sombra coloreada suave al hover */
  box-shadow: 0 15px 30px -10px rgba(124, 58, 237, 0.15); 
}

.icon-container {
  width: 50px; height: 50px;
  background: rgba(124, 58, 237, 0.1); /* Violeta siempre suave */
  color: var(--primary);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
  transition: all 0.3s ease;
}

.info-card:hover .icon-container {
  background: var(--primary);
  color: #fff;
  transform: scale(1.1);
}

.card-title {
  color: var(--text-main);
  font-weight: 700;
  margin-bottom: 10px;
}

.card-text {
  color: var(--text-muted);
  font-size: 0.95rem;
  line-height: 1.6;
}
</style>