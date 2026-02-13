<template>
  <div class="modulo-estado-sistema" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <h3 class="modulo-titulo">
      <i class="bi bi-activity"></i> Estado de la Red IoT
    </h3>
    <p class="modulo-subtitulo">Metricas de conexion de la infraestructura</p>
    
    <div v-if="loading" class="metric-loading">
      <i class="bi bi-arrow-clockwise fa-spin"></i> Cargando estado de la red...
    </div>
    <div v-else-if="error" class="metric-error">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    
    <div v-else class="metric-list">
      <div class="metric-item">
        <div class="metric-icon metric-icon-primary"><i class="bi bi-wifi"></i></div>
        <div class="metric-label">Dispositivos Conectados</div>
        <div class="metric-value">{{ estado.activos }} / {{ estado.total }}</div>
      </div>

      <div class="metric-item">
        <div class="metric-icon metric-icon-success"><i class="bi bi-graph-up-arrow"></i></div>
        <div class="metric-label">Uptime</div>
        <div class="metric-value">99.9%</div>
      </div>

      <div class="metric-item">
        <div class="metric-icon metric-icon-accent"><i class="bi bi-lightning-fill"></i></div>
        <div class="metric-label">Latencia</div>
        <div class="metric-value">12ms</div>
      </div>
    </div>
  </div>
</template>

<script>


export default {
  name: 'EstadoSistema',
  props: {
    isDark: {
      type: Boolean,
      required: true
    }
  },
  data() {
    return {
      loading: true, 
      error: null,   
      estado: {     
        activos: 0,
        total: 0
      }
    };
  },
  mounted() {
    this.cargarEstadoDispositivos();
  },
  methods: {
    async cargarEstadoDispositivos() {
      this.loading = true;
      this.error = null;
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        this.error = "Error de autenticacion.";
        this.loading = false;
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/estado-dispositivos`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'No se pudo cargar el estado de los dispositivos.');
        }
        
        this.estado = await response.json();
        
      } catch (err) {
        this.error = err.message;
        console.error("Error cargando estado de dispositivos:", err);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped lang="scss">
// ----------------------------------------
// VARIABLES DE LA PALETA (Asegurate de tenerlas definidas)
// ----------------------------------------
$LIGHT-TEXT: #E4E6EB;
$DARK-TEXT: #333333;
$GRAY-COLD: #99A2AD;
$BLUE-MIDNIGHT: #1A1A2E; 
$SUBTLE-BG-DARK: #2B2B40; 
$PRIMARY-PURPLE: #8A2BE2;
$SUCCESS-COLOR: #1ABC9C;
$ACCENT-COLOR: #FFC107; 
$SUBTLE-BG-LIGHT: #FFFFFF;
$DANGER-COLOR: #E74C3C;

// ----------------------------------------
// ESTILOS PRINCIPALES DEL MODULO
// ----------------------------------------
.modulo-estado-sistema {
    padding: 25px;
    border-radius: 15px;
    height: 100%;
    transition: background-color 0.3s;
}

.modulo-titulo {
    font-size: 1.4rem;
    font-weight: 600;
    margin-bottom: 5px;
    
    i { margin-right: 8px; color: $SUCCESS-COLOR; }
}

.modulo-subtitulo {
    font-size: 0.9rem;
    margin-bottom: 20px;
}

// ----------------------------------------
// ESTILOS DE METRICAS INDIVIDUALES
// ----------------------------------------
.metric-list {
    display: flex;
    flex-direction: column;
    gap: 5px; 
}

.metric-item {
    display: grid;
    grid-template-columns: 30px 1fr auto;
    align-items: center;
    padding: 15px 0;
    border-bottom: 1px solid; 
    
    &:last-child {
        border-bottom: none;
    }
}

.metric-icon {
    font-size: 1.2rem;
    text-align: center;
    width: 30px;
}

.metric-icon-success i { color: $SUCCESS-COLOR; }
.metric-icon-accent i { color: $ACCENT-COLOR; }
.metric-icon-primary i { color: $PRIMARY-PURPLE; }

.metric-label {
    font-weight: 500;
    margin-left: 10px;
}

.metric-value {
    font-weight: 700;
    font-size: 1.1rem;
    
    .metric-item:first-child & { color: $PRIMARY-PURPLE; }
    .metric-item:nth-child(2) & { color: $SUCCESS-COLOR; }
    .metric-item:nth-child(3) & { color: $ACCENT-COLOR; }
}

.metric-loading, .metric-error {
  padding: 20px;
  font-style: italic;
  text-align: center;
  i { margin-right: 8px; }
}
.metric-error { color: $DANGER-COLOR; }

// ----------------------------------------
// TEMAS
// ----------------------------------------

.theme-light {
    background-color: $SUBTLE-BG-LIGHT; 
    color: $DARK-TEXT;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    
    .modulo-subtitulo { color: $GRAY-COLD; }
    .metric-list .metric-item {
        border-bottom-color: #eee;
    }
}

.theme-dark {
    background-color: $SUBTLE-BG-DARK; 
    color: $LIGHT-TEXT;
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.4);
    
    .modulo-titulo { color: $LIGHT-TEXT; }
    .modulo-subtitulo { color: $GRAY-COLD; }
    .metric-list .metric-item {
        border-bottom-color: rgba($LIGHT-TEXT, 0.1);
    }
    .metric-loading, .metric-error {
        color: $GRAY-COLD;
    }
    .metric-error { color: $DANGER-COLOR; }
}
</style>