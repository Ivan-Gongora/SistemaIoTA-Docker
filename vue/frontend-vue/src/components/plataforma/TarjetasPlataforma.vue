<template>
  <div class="plataforma-tarjetas" :class="{ 'theme-dark': isDark, 'theme-light': !isDark }">
    <div class="row row-cols-1 row-cols-md-4 g-4">
      
      <div class="col">
        <div class="metric-card h-100">
          <div class="card-body">
            <div class="icon-container" style="background: linear-gradient(to bottom right, #6F00FF, #A300FF);">
              <i class="bi bi-folder-fill metric-icon"></i>
            </div>
            <div class="metric-content">
              <p class="metric-value">{{ loading ? '...' : kpis.conteo_proyectos_iot }}</p>
              <p class="metric-label">Proyectos IoT</p>
            </div>
            <div class="metric-details">
              <span class="detail-new"></span> <router-link to="/mis-proyectos" class="detail-link">Explorar →</router-link>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col">
        <div class="metric-card h-100">
          <div class="card-body">
            <div class="icon-container" style="background: linear-gradient(to bottom right, #00C853, #1ABC9C);">
            <i class="bi bi-cpu-fill metric-icon"></i>
            </div>
            <div class="metric-content">
              <p class="metric-value">{{ loading ? '...' : kpis.conteo_dispositivos_iot }}</p>
              <p class="metric-label">Dispositivos IoT</p>
            </div>
            </div>
        </div>
      </div>
      
      <div class="col">
        <div class="metric-card h-100">
          <div class="card-body">
            <div class="icon-container" style="background: linear-gradient(to bottom right, #FF8C00, #FFA500);">
              <i class="bi bi-file-earmark-spreadsheet-fill metric-icon"></i>
            </div>
            <div class="metric-content">
              <p class="metric-value">{{ loading ? '...' : kpis.conteo_lotes_energia }}</p>
              <p class="metric-label">Lotes de Energía</p>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col">
        <div class="metric-card h-100">
          <div class="card-body">
            <div class="icon-container" style="background: linear-gradient(to bottom right, #3498DB, #1E90FF);">
              <i class="bi bi-calculator-fill metric-icon"></i>
            </div>
            <div class="metric-content">
              <p class="metric-value">{{ loading ? '...' : kpis.conteo_simulaciones }}</p>
              <p class="metric-label">Simulaciones</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>


export default {
  name: 'TarjetasPlataforma',
  data() {
    return {
      isDark: false,
      loading: true, // 👈 Empezar en true para mostrar '...'
      error: null,
      
      // 🚨 kpis ahora recibirá los datos de la API
      kpis: {
        conteo_proyectos_iot: 0,
        conteo_dispositivos_iot: 0,
        conteo_lotes_energia: 0,
        conteo_simulaciones: 0,
      }
    };
  },
  mounted() {
    this.detectarTemaSistema();
    this.cargarResumenKPIs(); // 👈 Llamar a la API al montar
    
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', this.handleThemeChange);
    }
  },
  beforeUnmount() { 
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', this.handleThemeChange);
    }
  },
  methods: {
    // 🚨 NUEVO MÉTODO: Llama al endpoint del backend
    async cargarResumenKPIs() {
      this.loading = true;
      this.error = null;
      const token = localStorage.getItem('accessToken');
      
      if (!token) {
        this.error = "Error de autenticación.";
        this.loading = false;
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/plataforma/resumen-kpis`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!response.ok) {
          const errData = await response.json();
          throw new Error(errData.detail || 'No se pudo cargar el resumen de KPIs.');
        }
        
        this.kpis = await response.json(); // Actualizar el estado con los datos reales
        
      } catch (err) {
        this.error = err.message;
        console.error("Error cargando KPIs:", err);
      } finally {
        this.loading = false;
      }
    },
    
    // --- Métodos de Tema (Sin cambios) ---
    handleThemeChange(event) {
      this.isDark = event.matches;
    },
    detectarTemaSistema() {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        this.isDark = true;
      } else {
        this.isDark = false;
      }
    }
  }
};
</script>

<style scoped lang="scss">
// // ----------------------------------------
// // VARIABLES DE LA PALETA "IoT SPECTRUM"
// // (Estas variables deben estar disponibles globalmente o definidas aquí)
// // ----------------------------------------
// $PRIMARY-PURPLE: #8A2BE2; 
// $ACCENT-COLOR: #7B1FA2;  
// $SUCCESS-COLOR: #1ABC9C; 

// // GRADIENTES
// $GRADIENT-SUCCESS: linear-gradient(to right, #00C853, #1ABC9C);
// $PURPLE-GRADIENT: linear-gradient(to right, #6F00FF, #A300FF);

// // COLORES BASE (Asumidos si no son globales)
// $WHITE-SOFT: #F7F9FC;
// $BLUE-MIDNIGHT: #1A1A2E;
// $DARK-TEXT: #333333;
// $LIGHT-TEXT: #E4E6EB;
// $SUBTLE-BG-DARK: #2B2B40;
// $SUBTLE-BG-LIGHT: #FFFFFF;
// $GRAY-COLD: #99A2AD;
// $DARK-BG-CONTRAST: #131322;
// $DARK-DETAILS: rgba($LIGHT-TEXT, 0.4);

// ----------------------------------------
// ESTRUCTURA GENERAL
// ----------------------------------------
.plataforma-tarjetas {
  padding: 0; /* El padding se maneja en la vista principal */
  transition: background-color 0.3s; 
}

// ----------------------------------------
// CARD DE MÉTRICAS INDIVIDUAL
// ----------------------------------------
.metric-card {
  border: none;
  border-radius: 20px; 
  padding: 28px;
  transition: all 0.2s ease-in-out;
  height: 100%;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
  }
}

// ----------------------------------------
// ELEMENTOS DE LA CARD
// ----------------------------------------

.icon-container {
  width: 45px;
  height: 45px;
  border-radius: 10px;
  margin-bottom: 20px;
  float: right; 
  display: flex;
  justify-content: center;
  align-items: center;
  
  .metric-icon {
    color: #fff;
    font-size: 1.2rem;
  }
}

.metric-content {
  text-align: left;
  
  .metric-value {
    color: $LIGHT-TEXT; 
    font-size: 2.5rem;
    font-weight: 800;
    margin-bottom: 0px;
    line-height: 1;
  }
  .metric-label {
    font-weight: 500;
    text-transform: uppercase;
    margin-top: 5px;
    margin-bottom: 20px;
    clear: both; 
    color: $GRAY-COLD;
    font-size: 0.85rem; 
    letter-spacing: 0.8px;
  }
}

.metric-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
  padding-top: 10px;
  border-top-style: solid; 
  border-top-width: 1px;

  .detail-new {
    font-size: 0.85rem;
    font-weight: 500;
    color: $PRIMARY-PURPLE;
  }
  .detail-link {
    font-size: 0.85rem;
    color: $PRIMARY-PURPLE;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
    
    &:hover {
      opacity: 0.8;
    }
  }
}

// ----------------------------------------
// TEMAS (DARK/LIGHT)
// ----------------------------------------

// MODO CLARO
.theme-light {
    .metric-card {
        background-color: $SUBTLE-BG-LIGHT; 
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        color: $DARK-TEXT;
    }
    .metric-label {
        color: $GRAY-COLD;
    }
    .metric-details {
        border-top-color: rgba($DARK-TEXT, 0.1);
    }
}

// MODO OSCURO
.theme-dark {
    .metric-card {
        background-color: $SUBTLE-BG-DARK;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4); 
        border-radius: 20px; 
    }
    .metric-value {
        color: $LIGHT-TEXT;
    }
    .metric-label {
        color: $DARK-DETAILS;
    }
    .metric-details {
        border-top-color: rgba($LIGHT-TEXT, 0.2);
    }
    .detail-new, .detail-link {
        color: $LIGHT-TEXT;
    }
}
</style>