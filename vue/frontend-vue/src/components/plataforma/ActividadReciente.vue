<template>
  <div class="modulo-actividad-reciente" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    
    <h3 class="modulo-titulo">Actividad Reciente</h3>
    <p class="modulo-subtitulo">Ultimos eventos del sistema</p>
    
    <div v-if="loading" class="loading-message">
      <i class="bi bi-arrow-clockwise fa-spin"></i> Cargando actividad...
    </div>
    <div v-else-if="error" class="error-message">
      <i class="bi bi-exclamation-triangle-fill"></i> {{ error }}
    </div>
    <div v-else-if="recentEvents.length === 0" class="no-data-message">
      <i class="bi bi-info-circle-fill"></i> No hay actividad reciente.
    </div>
    
    <div v-else class="event-list">
      <div v-for="(event, index) in recentEvents" :key="index" class="event-item">
        <i :class="getIconClass(event.tipo)" class="event-icon"></i>
        <div class="event-details">
          <p class="event-title">{{ event.titulo }}</p>
          <p class="event-source">{{ event.fuente }}</p>
        </div>
        <span class="event-time">{{ formatRelativeTime(event.fecha) }}</span>
      </div>
    </div>

  </div>
</template>

<script>


export default {
  name: 'ActividadReciente',
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
      recentEvents: []
    };
  },
  mounted() {
    this.cargarActividadReciente();
  },
  methods: {
    async cargarActividadReciente() {
      this.loading = true;
      this.error = null;
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        this.error = "Error de autenticacion.";
        this.loading = false;
        return;
      }

      try {
        // Este endpoint ya esta preparado para la nueva tabla
        const response = await fetch(`${API_BASE_URL}/api/dashboard/actividad-reciente`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'No se pudo cargar la actividad.');
        }
        
        this.recentEvents = await response.json();
        
      } catch (err) {
        this.error = err.message;
        console.error("Error cargando actividad:", err);
      } finally {
        this.loading = false;
      }
    },

    // METODO getIconClass ACTUALIZADO
    getIconClass(type) {
      if (!type) {
        return 'bi bi-info-circle-fill';
      }

      // --- 1. Casos Especiales (Modulo Energia, Alertas) ---
      switch (type) {
        case 'LOTE_ENERGIA_CARGADO':
          return 'bi bi-file-earmark-spreadsheet-fill text-success';
        case 'SIMULACION_EJECUTADA':
          return 'bi bi-calculator-fill text-info';
        case 'ALERTA_GENERADA':
          return 'bi bi-exclamation-triangle-fill text-warning';
      }

      // --- 2. Casos Genericos (CRUD) ---
      // Revisa el sufijo del tipo de evento
      
      if (type.endsWith('_CREADO')) {
          return 'bi bi-plus-circle-fill text-success'; // CREAR
      }
      if (type.endsWith('_MODIFICADO')) {
          return 'bi bi-pencil-fill text-info'; // MODIFICAR
      }
      if (type.endsWith('_ELIMINADO')) {
          return 'bi bi-trash-fill text-danger'; // ELIMINAR
      }

      // --- 3. Caso por Defecto ---
      return 'bi bi-info-circle-fill';
    },
    
    formatRelativeTime(isoString) {
      const fecha = new Date(isoString);
      const ahora = new Date();
      const diffMs = ahora - fecha;
      const diffMins = Math.round(diffMs / 60000);

      if (diffMins < 1) return "Ahora mismo";
      if (diffMins < 60) return `Hace ${diffMins} min`;
      
      const diffHoras = Math.floor(diffMins / 60);
      if (diffHoras < 24) return `Hace ${diffHoras} h`;
      
      const diffDias = Math.floor(diffHoras / 24);
      return `Hace ${diffDias} d`;
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
$SUCCESS-COLOR: #1ABC9C;
$DANGER-COLOR: #E74C3C;
$INFO-COLOR: #3498DB;
$WARNING-COLOR: #FFC107;
$SUBTLE-BG-LIGHT: #FFFFFF;
$BG-CARD-DARK: #2B2B40; 

// ----------------------------------------
// ESTILOS PRINCIPALES DEL MODULO
// ----------------------------------------
.modulo-actividad-reciente {
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    height: 100%;
    transition: background-color 0.3s;
}

.modulo-titulo { font-size: 1.4rem; font-weight: 600; margin-bottom: 5px; }

.modulo-subtitulo {
    font-size: 0.9rem;
    margin-bottom: 20px;
    padding-bottom: 5px;
    border-bottom: 1px solid; 
}

// ----------------------------------------
// LISTA DE EVENTOS
// ----------------------------------------
.event-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.event-item {
    display: grid;
    grid-template-columns: 25px 1fr auto; 
    gap: 10px;
    align-items: center;
}

.event-icon {
    font-size: 1.1rem;
    text-align: center;
    width: 25px;
}

.text-success { color: $SUCCESS-COLOR !important; }
.text-info { color: $INFO-COLOR !important; }
.text-warning { color: $WARNING-COLOR !important; }
.text-danger { color: $DANGER-COLOR !important; }

.event-details {
    .event-title { font-weight: 500; margin: 0; font-size: 0.95rem; }
    .event-source { font-size: 0.8rem; margin: 0; }
}

.event-time { font-size: 0.8rem; text-align: right; }

.loading-message, .error-message, .no-data-message {
    text-align: center;
    padding: 20px;
    font-style: italic;
    opacity: 0.7;
    i { margin-right: 8px; }
}
.error-message {
    color: $DANGER-COLOR;
}

// ----------------------------------------
// TEMAS
// ----------------------------------------
.theme-light {
    background-color: $SUBTLE-BG-LIGHT;
    color: $DARK-TEXT;
    .modulo-subtitulo { border-bottom-color: #ddd; }
    .event-source, .event-time { color: $GRAY-COLD; }
}

.theme-dark {
    background-color: $BG-CARD-DARK; 
    color: $LIGHT-TEXT;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    
    .modulo-titulo { color: $LIGHT-TEXT; }
    .modulo-subtitulo { border-bottom-color: rgba($LIGHT-TEXT, 0.1); }
    .event-details .event-source, .event-time { color: $GRAY-COLD; }
    .loading-message, .error-message, .no-data-message {
        color: $GRAY-COLD;
    }
}
</style>